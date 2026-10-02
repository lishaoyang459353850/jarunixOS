#!/usr/bin/env bash
# 步骤 4：生成 squashfs 并制作 BIOS + UEFI 双引导 ISO。
set -euo pipefail
. "$(dirname "$0")/lib.sh"

ISO_TREE="$WORK_DIR/iso-tree"
rm -rf "$ISO_TREE"
mkdir -p "$ISO_TREE"/{live,isolinux,boot/grub}

log "查找内核与 initrd"
KERNEL="$(ls -1 "$ROOTFS"/boot/vmlinuz-* 2>/dev/null | sort -V | tail -1)"
INITRD="$(ls -1 "$ROOTFS"/boot/initrd.img-* 2>/dev/null | sort -V | tail -1)"
[ -n "$KERNEL" ] || die "根文件系统中找不到内核"
[ -n "$INITRD" ] || die "根文件系统中找不到 initrd"

cp "$KERNEL" "$ISO_TREE/live/vmlinuz"
cp "$INITRD" "$ISO_TREE/live/initrd.img"

log "生成 squashfs（xz 压缩）"
mksquashfs "$ROOTFS" "$ISO_TREE/live/filesystem.squashfs" \
    -comp xz -b 1M -noappend -e boot >/dev/null

log "装配 BIOS 引导（isolinux）"
cp /usr/lib/ISOLINUX/isolinux.bin "$ISO_TREE/isolinux/"
cp /usr/lib/syslinux/modules/bios/*.c32 "$ISO_TREE/isolinux/" 2>/dev/null || true
cp "$BUILD_DIR/config/isolinux/isolinux.cfg" "$ISO_TREE/isolinux/"

log "装配 UEFI 引导（GRUB EFI 镜像）"
grub-mkimage -O x86_64-efi -o "$WORK_DIR/BOOTX64.EFI" -p /boot/grub \
    part_gpt part_msdos fat iso9660 normal linux configfile loopback chain \
    efi_gop efi_uga ls search search_label search_fs_uuid all_video gfxterm font serial
[ -s "$WORK_DIR/BOOTX64.EFI" ] || die "grub-mkimage 未生成 BOOTX64.EFI"
# 注意：EFI 分区必须格式化为 FAT12/FAT16。16 MB 的小卷若强行为 FAT32，
# 簇数低于 FAT32 规范下限（约 65525 簇），UEFI 固件会判其为无效卷，
# 表现为固件报 "Not Found" 并转去网络启动（PXE）。故由 mkfs.vfat 自动选 FAT16。
dd if=/dev/zero of="$ISO_TREE/boot/grub/efi.img" bs=1M count=16 status=none
mkfs.vfat -F 16 -n JRNXEFI "$ISO_TREE/boot/grub/efi.img" >/dev/null
mmd -i "$ISO_TREE/boot/grub/efi.img" ::/EFI ::/EFI/BOOT ::/boot ::/boot/grub ::/boot/grub/fonts
mcopy -i "$ISO_TREE/boot/grub/efi.img" "$WORK_DIR/BOOTX64.EFI" ::/EFI/BOOT/BOOTX64.EFI
mcopy -i "$ISO_TREE/boot/grub/efi.img" "$BUILD_DIR/config/grub/grub.cfg" ::/EFI/BOOT/grub.cfg
mcopy -i "$ISO_TREE/boot/grub/efi.img" "$BUILD_DIR/config/grub/grub.cfg" ::/boot/grub/grub.cfg
# GRUB 的 gfxterm 必须加载位图字体才能渲染菜单文字，缺字体会导致菜单一片空白
mcopy -i "$ISO_TREE/boot/grub/efi.img" /usr/share/grub/unicode.pf2 ::/boot/grub/fonts/unicode.pf2
cp "$BUILD_DIR/config/grub/grub.cfg" "$ISO_TREE/boot/grub/grub.cfg"
mkdir -p "$ISO_TREE/boot/grub/fonts"
cp /usr/share/grub/unicode.pf2 "$ISO_TREE/boot/grub/fonts/unicode.pf2"

log "用 xorriso 打包 ISO"
mkdir -p "$OUT_DIR"
xorriso -as mkisofs \
    -iso-level 3 -full-iso9660-filenames -volid "JARUNIXOS" \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat \
    -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat \
    -o "$OUT_DIR/$ISO_NAME" "$ISO_TREE" >/dev/null

SIZE_MB=$(( $(stat -c%s "$OUT_DIR/$ISO_NAME") / 1000000 ))
log "ISO 已生成：$OUT_DIR/$ISO_NAME  (${SIZE_MB} MB)"
[ "$SIZE_MB" -lt 800 ] || warn "体积超过 800 MB 目标，请精简包清单"
