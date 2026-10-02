#!/usr/bin/env python3
"""求解 initramfs 内所有 ELF 的动态库依赖闭包，并从目标根文件系统补齐缺失的 .so。

在 chrootless 构建下，initramfs-tools 常常漏掉基础运行库（busybox 需要
libresolv.so.2，systemd-udevd 需要 libsystemd-shared-257.so），导致内核执行
/init 时以 127 退出、直接 panic。本脚本用 readelf 逐层解析 NEEDED 直到收敛。

用法：lib-closure.py <initramfs 解开的目录> <目标根文件系统>
"""
import os
import re
import shutil
import subprocess
import sys

# 目标系统内动态库可能所在的目录（按查找优先级）
SEARCH_DIRS = [
    "usr/lib/x86_64-linux-gnu",
    "lib/x86_64-linux-gnu",
    "usr/lib/x86_64-linux-gnu/systemd",
    "usr/lib/systemd",
    "usr/lib/x86_64-linux-gnu/fakechroot",
    "usr/lib",
    "lib",
    "usr/lib64",
]

# 补齐的库统一放到这里（该路径属于动态链接器默认搜索路径）
DEST_SUBDIR = "usr/lib/x86_64-linux-gnu"


def elf_needed(path):
    """返回该 ELF 的 NEEDED 动态库名列表；非 ELF 或无动态段返回空。"""
    try:
        out = subprocess.run(
            ["readelf", "-d", path], capture_output=True, text=True, timeout=30
        ).stdout
    except Exception:
        return []
    if "Dynamic section" not in out:
        return []
    return re.findall(r"\(NEEDED\)\s+Shared library:\s+\[([^\]]+)\]", out)


def find_in_target(root, name):
    for d in SEARCH_DIRS:
        p = os.path.join(root, d, name)
        if os.path.exists(p):
            return p
    return None


def place(root, name, src):
    """把库文件（含同名符号链接指向的实体）复制进 initramfs。"""
    d = os.path.join(root, DEST_SUBDIR)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name)
    if os.path.exists(dst):
        return False
    if os.path.islink(src):
        real = os.path.realpath(src)
        base = os.path.basename(real)
        if not os.path.exists(os.path.join(d, base)):
            shutil.copy2(real, os.path.join(d, base))
        os.symlink(base, dst)
    else:
        shutil.copy2(src, dst)
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    root, target = sys.argv[1], sys.argv[2]

    elves = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if os.path.islink(p):
                continue
            try:
                with open(p, "rb") as f:
                    if f.read(4) != b"\x7fELF":
                        continue
            except OSError:
                continue
            elves.append(p)
    print(f"initramfs 内 ELF 文件: {len(elves)}")

    total = 0
    for rnd in range(1, 9):
        added = 0
        for e in elves:
            for need in elf_needed(e):
                if os.path.exists(os.path.join(root, DEST_SUBDIR, need)):
                    continue
                src = find_in_target(target, need)
                if not src:
                    print(f"  [未找到] {need}  (需要者 {os.path.relpath(e, root)})")
                    continue
                if place(root, need, src):
                    added += 1
                    # 新补进的库本身也可能有依赖，加入待扫描队列
                    elves.append(os.path.join(root, DEST_SUBDIR, need))
        total += added
        print(f"  第 {rnd} 轮补齐: {added}")
        if added == 0:
            break

    print(f"共补齐库文件: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
