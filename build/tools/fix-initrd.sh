#!/usr/bin/env bash
# 重建 initramfs：补入挂载根文件系统所需的内核模块，并求解动态库依赖闭包。
#
# 背景：在 mmdebstrap --mode=chrootless + fakechroot 路径下，initramfs-tools 的
# dracut-install 钩子无法把 .ko 写进暂存目录，最终 initrd 里一个模块都没有；
# 同时基础运行库（libresolv.so.2 等）也会漏掉。两者任一缺失都会导致
# /init 以 127 退出、内核 panic（Attempted to kill init）。
#
# 用法：fix-initrd.sh <根文件系统> <内核版本> [lib-closure.py 路径]
set -u

R="$1"
KVER="$2"
CLOSURE="${3:-$(dirname "$0")/lib-closure.py}"
IR="$R/boot/initrd.img-$KVER"
W="${JARUNIX_IR_WORK:-/tmp/jarunix-initrd-work}"
MODDIR="$R/usr/lib/modules/$KVER/kernel"

[ -f "$IR" ] || { echo "找不到 $IR" >&2; exit 1; }

rm -rf "$W"; mkdir -p "$W"

echo "### 1. 拆分 initrd（早期微码 cpio + zstd 主 cpio）"
OFF=$(python3 -c "d=open('$IR','rb').read(); print(d.find(b'\x28\xb5\x2f\xfd'))")
[ "$OFF" -gt 0 ] || { echo "initrd 不是 zstd 压缩，暂不支持" >&2; exit 1; }
head -c "$OFF" "$IR" > "$W/early.cpio"
tail -c +$((OFF + 1)) "$IR" > "$W/main.zst"
zstd -d -f "$W/main.zst" -o "$W/main.cpio" 2>/dev/null

echo "### 2. 解开主 cpio"
mkdir -p "$W/root"; cd "$W/root"
cpio -idm --quiet --no-absolute-filenames < "$W/main.cpio" 2>/dev/null
echo "解开条目: $(find . | wc -l)"

echo "### 3. 补入启动必需的内核模块子树"
SUBS="fs/squashfs fs/overlayfs fs/isofs fs/ext4 fs/jbd2 fs/mbcache fs/nls fs/fat fs/vfat
drivers/block drivers/ata drivers/cdrom drivers/scsi drivers/virtio drivers/md
drivers/usb/storage drivers/usb/host drivers/usb/core drivers/hid/usbhid
lib crypto arch/x86/crypto drivers/firmware/efi"
for s in $SUBS; do
  [ -d "$MODDIR/$s" ] || continue
  mkdir -p "$W/root/usr/lib/modules/$KVER/kernel/$(dirname "$s")"
  cp -a "$MODDIR/$s" "$W/root/usr/lib/modules/$KVER/kernel/$(dirname "$s")/" 2>/dev/null
done
echo "模块文件数: $(find "$W/root/usr/lib/modules/$KVER/kernel" -name '*.ko*' 2>/dev/null | wc -l)"

echo "### 4. 求解动态库依赖闭包"
python3 "$CLOSURE" "$W/root" "$R" 2>&1 | tail -20

echo "### 5. 重新打包"
cd "$W/root"
find . -print0 | cpio --null -o -H newc --quiet > "$W/newmain.cpio" 2>/dev/null
zstd -19 -f "$W/newmain.cpio" -o "$W/newmain.zst" 2>/dev/null
cat "$W/early.cpio" "$W/newmain.zst" > "$IR"
echo "新 initrd: $(du -h "$IR" | cut -f1)"

echo "### 6. 校验"
python3 - "$IR" <<'PY'
import sys
d = open(sys.argv[1], 'rb').read()
off = d.find(b'\x28\xb5\x2f\xfd')
open('/tmp/_chk.zst', 'wb').write(d[off:])
PY
zstd -d -f /tmp/_chk.zst -o /tmp/_chk.cpio 2>/dev/null
python3 - <<'PY'
d = open('/tmp/_chk.cpio', 'rb').read()
names = []; i = 0
while i + 110 <= len(d):
    if d[i:i+6] not in (b'070701', b'070702'):
        i += 1; continue
    f = lambda o: int(d[i+o:i+o+8], 16)
    ns, fs = f(94), f(54)
    nm = d[i+110:i+110+ns-1].decode('utf-8', 'replace')
    names.append(nm); i += 110 + ns; i = (i + 3) & ~3; i += (fs + 3) & ~3
    if nm == 'TRAILER!!!': break
ko = [x for x in names if x.endswith(('.ko', '.ko.xz', '.ko.zst'))]
print("条目总数:", len(names), " 模块文件数:", len(ko))
for k in ['init', 'usr/lib/x86_64-linux-gnu/libc.so.6', 'usr/bin/busybox',
          'usr/sbin/losetup', 'usr/lib/x86_64-linux-gnu/libresolv.so.2']:
    print(f"   {k:46s}", "有" if k in names else "缺")
PY
