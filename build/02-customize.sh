#!/usr/bin/env bash
# 步骤 2：把 jarunixOS 组件与配置植入根文件系统。
set -euo pipefail
. "$(dirname "$0")/lib.sh"

[ -d "$ROOTFS" ] || die "根文件系统不存在，请先运行 01-bootstrap.sh"

log "写入版本标记 /etc/jarunix-edition"
echo "$JARUNIX_EDITION" > "$ROOTFS/etc/jarunix-edition"
echo "$JARUNIX_VERSION" > "$ROOTFS/etc/jarunix-version"

log "叠加系统覆盖层"
cp -a "$BUILD_DIR/overlay/." "$ROOTFS/"

log "创建 jarunix 用户与免密 sudo"
if ! grep -q '^jarunix:' "$ROOTFS/etc/passwd"; then
  chroot "$ROOTFS" useradd -m -s /bin/bash -G sudo,audio,video,plugdev,netdev jarunix 2>/dev/null \
    || echo 'jarunix:x:1000:1000:jarunix:/home/jarunix:/bin/bash' >> "$ROOTFS/etc/passwd"
fi
install -d -m 0755 "$ROOTFS/etc/sudoers.d"
printf 'jarunix ALL=(ALL) NOPASSWD: ALL\n' > "$ROOTFS/etc/sudoers.d/90-jarunix"
chmod 440 "$ROOTFS/etc/sudoers.d/90-jarunix"

log "复制 skel 到用户主目录"
if [ -d "$ROOTFS/home/jarunix" ]; then
  cp -a "$ROOTFS/etc/skel/." "$ROOTFS/home/jarunix/"
  chroot "$ROOTFS" chown -R jarunix:jarunix /home/jarunix || true
fi

log "安装 jarunix 组件"
install -d -m 0755 "$ROOTFS/opt/jarunix"
if [ -f "$WORK_DIR/build/jar/jarunix-shell.jar" ]; then
  install -m 0644 "$WORK_DIR/build/jar/jarunix-shell.jar"     "$ROOTFS/opt/jarunix/"
  install -m 0644 "$WORK_DIR/build/jar/jarunix-installer.jar" "$ROOTFS/opt/jarunix/"
else
  warn "尚未编译 jar，请先执行 03-build-java.sh"
fi

log "启用 tty1 自动登录"
chroot "$ROOTFS" systemctl daemon-reload 2>/dev/null || true

log "生成 initramfs"
chroot "$ROOTFS" update-initramfs -u -k all 2>/dev/null || warn "initramfs 生成跳过"

log "覆盖层完成"
