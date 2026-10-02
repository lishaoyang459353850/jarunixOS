# -*- coding: utf-8 -*-
# jarunixOS 安装向导 —— 载荷打包工具（构建期使用）
# Copyright (C) 2026 jarunixOS Project
# SPDX-License-Identifier: GPL-3.0-or-later
#
# 本程序是自由软件：你可以依据自由软件基金会发布的 GNU 通用公共许可证
# （第 3 版或任何更高版本）的条款重新发布和/或修改它。

"""把各版本镜像追加到已编译的安装程序 exe 尾部，生成单文件安装程序。

用法：
    python pack_payload.py <基础exe> <输出exe> <镜像1> [镜像2 ...]

生成的文件结构：
    [基础exe 原始字节][镜像1][镜像2]...[索引 JSON][40 字节页脚]

页脚格式（小端）：
    magic(8) + 索引偏移(8) + 索引长度(8) + 载荷总长(8) + 保留(8)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import sys

MAGIC = b"JRNXPAY1"
FOOTER_FMT = "<8sQQQQ"
FOOTER_SIZE = 40
BUF = 8 * 1024 * 1024

KEYWORDS = [("personal", "personal"), ("professional", "professional")]


def sha256_file(path, progress=None):
    h = hashlib.sha256()
    done = 0
    total = os.path.getsize(path)
    with open(path, "rb") as fp:
        while True:
            b = fp.read(BUF)
            if not b:
                break
            h.update(b)
            done += len(b)
            if progress:
                progress(done, total)
    return h.hexdigest()


def guess_key(name):
    low = os.path.basename(name).lower()
    for kw, key in KEYWORDS:
        if kw in low:
            return key
    return os.path.splitext(os.path.basename(name))[0].lower()


def strip_payload(path):
    """如果 exe 尾部已经带有本工具的载荷，返回去掉载荷后的长度。"""
    size = os.path.getsize(path)
    if size < FOOTER_SIZE:
        return size
    with open(path, "rb") as fp:
        fp.seek(size - FOOTER_SIZE)
        magic, idx_off, idx_len, total, _ = struct.unpack(FOOTER_FMT, fp.read(FOOTER_SIZE))
        if magic != MAGIC:
            return size
        fp.seek(idx_off)
        try:
            index = json.loads(fp.read(idx_len).decode("utf-8"))
        except Exception:
            return size
        starts = [rec["offset"] for rec in index.values() if isinstance(rec, dict)]
        return min(starts) if starts else size


def main(argv):
    if len(argv) < 4:
        sys.stdout.write(__doc__)
        return 2

    base, out = os.path.abspath(argv[1]), os.path.abspath(argv[2])
    isos = [os.path.abspath(p) for p in argv[3:]]

    for p in [base] + isos:
        if not os.path.isfile(p):
            sys.stderr.write("找不到文件：%s\n" % p)
            return 1

    base_len = strip_payload(base)
    tmp = out + ".packing"
    if os.path.exists(tmp):
        os.remove(tmp)

    # 复制基础 exe 的有效部分
    with open(base, "rb") as src, open(tmp, "wb") as dst:
        left = base_len
        while left > 0:
            b = src.read(min(BUF, left))
            if not b:
                break
            dst.write(b)
            left -= len(b)

    index = {}
    offset = base_len
    with open(tmp, "ab") as dst:
        for p in isos:
            key = guess_key(p)
            size = os.path.getsize(p)
            sys.stdout.write("追加 %s（%s）…\n" % (key, _human(size)))
            sys.stdout.flush()
            with open(p, "rb") as src:
                while True:
                    b = src.read(BUF)
                    if not b:
                        break
                    dst.write(b)
            digest = sha256_file(p)
            index[key] = {"offset": offset, "size": size, "sha256": digest,
                          "filename": os.path.basename(p)}
            offset += size

        blob = json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        idx_off = dst.tell()
        dst.write(blob)
        payload_total = idx_off - base_len
        dst.write(struct.pack(FOOTER_FMT, MAGIC, idx_off, len(blob), payload_total, 0))

    if os.path.exists(out):
        os.remove(out)
    shutil.move(tmp, out)

    sys.stdout.write("\n完成：%s\n" % out)
    sys.stdout.write("基础程序 %s + 载荷 %s = %s\n" % (
        _human(base_len), _human(os.path.getsize(out) - base_len),
        _human(os.path.getsize(out))))
    for k, v in index.items():
        sys.stdout.write("  %-14s %12s  sha256=%s…\n" % (
            k, _human(v["size"]), v["sha256"][:16]))
    return 0


def _human(n):
    v = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if v < 1024 or u == "GB":
            return "%.1f %s" % (v, u)
        v /= 1024.0
    return "%.1f GB" % v


if __name__ == "__main__":
    sys.exit(main(sys.argv))
