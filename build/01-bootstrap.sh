#!/usr/bin/env bash
# 步骤 1：建立最小根文件系统。
set -euo pipefail
. "$(dirname "$0")/lib.sh"

INCLUDE="$(pkglist)"
rm -rf "$ROOTFS"

if can_use_blockdevices; then
  log "使用 debootstrap（可挂载环境）"
  debootstrap --arch="$JARUNIX_ARCH" --variant=minbase --components=main,contrib,non-free-firmware \
      --include="$INCLUDE" "$JARUNIX_SUITE" "$ROOTFS" "$JARUNIX_MIRROR"
else
  log "检测到受限容器（无 loop 设备），回退到 mmdebstrap chrootless 免挂载模式"
  if [ "$(id -u)" = "0" ]; then
    # chrootless 以 root 直接运行会拒绝，需配合 fakeroot 伪造权限
    fakeroot mmdebstrap --mode=chrootless --arch="$JARUNIX_ARCH" \
        --variant=minbase --components=main,contrib,non-free-firmware \
        --include="$INCLUDE" "$JARUNIX_SUITE" "$ROOTFS" "$JARUNIX_MIRROR"
  else
    mmdebstrap --mode=chrootless --arch="$JARUNIX_ARCH" --variant=minbase \
        --components=main,contrib,non-free-firmware \
        --include="$INCLUDE" "$JARUNIX_SUITE" "$ROOTFS" "$JARUNIX_MIRROR"
  fi
fi

log "根文件系统就绪：$(du -sh "$ROOTFS" | cut -f1)"
