#!/usr/bin/env bash
# 步骤 5：收尾修复。
#
# 本步骤固化 jarunixOS 在 chrootless（mmdebstrap --mode=chrootless + fakechroot）
# 构建路径下必须做的四项修复。缺任何一项，产出的 ISO 都无法启动或无法进入图形界面：
#
#   1. Xorg setuid —— 普通用户 jarunix 必须能启动 X 服务器；
#   2. 符号链接修正 —— chrootless 构建会把 alternatives 链接写成构建期绝对路径，
#      装进 ISO 后全部失效（典型症状：java: command not found）；
#   3. initramfs 内核模块补齐 —— initramfs-tools 在 fakechroot 下拿不到模块，
#      必须手工补入挂载根文件系统所需的模块子树；
#   4. initramfs 动态库依赖闭包 —— busybox 需要 libresolv.so.2、
#      systemd-udevd 需要 libsystemd-shared-257.so 等，缺一个 init 就退 127 导致内核 panic。
set -euo pipefail
. "$(dirname "$0")/lib.sh"

[ -d "$ROOTFS" ] || die "根文件系统不存在，请先运行 01-bootstrap.sh"

TOOLS="$(dirname "$0")/tools"

# ---------- 1. Xorg setuid ----------
log "修复 1/4：为 Xorg 加 setuid 位"
if [ -f "$ROOTFS/usr/lib/xorg/Xorg" ]; then
  chmod 4755 "$ROOTFS/usr/lib/xorg/Xorg"
  install -d -m 0755 "$ROOTFS/etc/X11"
  printf 'allowed_users=anybody\nneeds_root_rights=yes\n' > "$ROOTFS/etc/X11/Xwrapper.config"
else
  warn "未找到 /usr/lib/xorg/Xorg，跳过"
fi

# ---------- 2. 符号链接修正 ----------
log "修复 2/4：重写指向构建根目录的绝对符号链接"
BUILD_ROOT_ABS="$(cd "$ROOTFS" && pwd)"
FIXED=0
while IFS= read -r -d '' l; do
  t="$(readlink "$l" 2>/dev/null || true)"
  case "$t" in
    "$BUILD_ROOT_ABS"/*)
      ln -sfn "${t#"$BUILD_ROOT_ABS"}" "$l"
      FIXED=$((FIXED + 1))
      ;;
  esac
done < <(find "$ROOTFS" -type l -print0 2>/dev/null)
log "  已修正 $FIXED 个符号链接"
[ "$FIXED" -gt 0 ] || warn "未发现需修正的符号链接，请确认构建方式"

# ---------- 3 + 4. initramfs 模块与库闭包 ----------
log "修复 3-4/4：重建 initramfs（补内核模块 + 动态库依赖闭包）"
KVER="$(ls -1 "$ROOTFS/lib/modules" 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$KVER" ]; then
  warn "找不到内核模块目录，跳过 initramfs 修复"
else
  if [ -f "$ROOTFS/boot/initrd.img-$KVER" ]; then
    bash "$TOOLS/fix-initrd.sh" "$ROOTFS" "$KVER" "$TOOLS/lib-closure.py"
  else
    warn "找不到 initrd.img-$KVER，请先运行 02-customize.sh"
  fi
fi

log "收尾修复完成"
