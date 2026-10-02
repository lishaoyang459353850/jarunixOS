#!/usr/bin/env bash
# jarunixOS 构建入口。
#
#   sudo ./build/build.sh --edition personal
#   sudo ./build/build.sh --edition professional
#
set -euo pipefail
cd "$(dirname "$0")/.."

while [ $# -gt 0 ]; do
  case "$1" in
    --edition) JARUNIX_EDITION="$2"; shift 2 ;;
    --version) JARUNIX_VERSION="$2"; shift 2 ;;
    --suite)   JARUNIX_SUITE="$2";   shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：$1"; exit 2 ;;
  esac
done

export JARUNIX_EDITION JARUNIX_VERSION
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

need_root
mkdir -p "$WORK_DIR" "$OUT_DIR"

log "构建 jarunixOS $JARUNIX_VERSION / $JARUNIX_EDITION / $JARUNIX_ARCH (Debian $JARUNIX_SUITE)"
"$BUILD_DIR/01-bootstrap.sh"
"$BUILD_DIR/02-customize.sh"
"$BUILD_DIR/03-build-java.sh"
"$BUILD_DIR/04-make-iso.sh"
log "完成：$OUT_DIR/$ISO_NAME"
