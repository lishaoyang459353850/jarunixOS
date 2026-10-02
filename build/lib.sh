#!/usr/bin/env bash
# jarunixOS 构建公共变量与函数。

set -euo pipefail

export JARUNIX_VERSION="${JARUNIX_VERSION:-1.0}"
export JARUNIX_EDITION="${JARUNIX_EDITION:-personal}"
export JARUNIX_SUITE="${JARUNIX_SUITE:-trixie}"
export JARUNIX_MIRROR="${JARUNIX_MIRROR:-http://deb.debian.org/debian}"
export JARUNIX_ARCH="${JARUNIX_ARCH:-amd64}"

JARUNIX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JARUNIX_ROOT
export BUILD_DIR="$JARUNIX_ROOT/build"
export WORK_DIR="$BUILD_DIR/work"
export OUT_DIR="$BUILD_DIR/out"
export ROOTFS="$WORK_DIR/rootfs-$JARUNIX_EDITION"
export ISO_NAME="jarunixOS-${JARUNIX_VERSION}-${JARUNIX_EDITION}-${JARUNIX_ARCH}.iso"

log()  { printf '\033[1;34m[jarunix]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

need_root() {
  [ "$(id -u)" = "0" ] || die "请以 root 运行（sudo ./build/build.sh）"
}

# 判断当前环境是否允许使用 loop 设备（受限容器里通常不允许）
can_use_blockdevices() {
  [ -e /dev/loop-control ] && return 0
  return 1
}

pkglist() {
  local f="$BUILD_DIR/packages/${JARUNIX_EDITION}.list"
  [ -f "$f" ] || die "找不到包清单：$f"
  grep -v '^#' "$f" | grep -v '^$' | paste -sd,
}
