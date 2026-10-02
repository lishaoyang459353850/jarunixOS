#!/usr/bin/env bash
# 步骤 3：编译 Java 桌面外壳与安装程序，产出可执行 jar。
set -euo pipefail
. "$(dirname "$0")/lib.sh"

command -v javac >/dev/null || die "需要 JDK：apt-get install openjdk-21-jdk-headless"

mkdir -p "$WORK_DIR/build/shell" "$WORK_DIR/build/installer" "$WORK_DIR/build/jar"

log "编译 jarunix-shell"
find "$JARUNIX_ROOT/src/shell" -name '*.java' > "$WORK_DIR/build/shell.srcs"
javac --release 21 -encoding UTF-8 -d "$WORK_DIR/build/shell" @"$WORK_DIR/build/shell.srcs"
jar --create --file "$WORK_DIR/build/jar/jarunix-shell.jar" \
    --main-class os.jarunix.shell.Main -C "$WORK_DIR/build/shell" .

log "编译 jarunix-installer"
find "$JARUNIX_ROOT/src/installer" -name '*.java' > "$WORK_DIR/build/installer.srcs"
javac --release 21 -encoding UTF-8 -d "$WORK_DIR/build/installer" @"$WORK_DIR/build/installer.srcs"
jar --create --file "$WORK_DIR/build/jar/jarunix-installer.jar" \
    --main-class os.jarunix.installer.InstallerMain -C "$WORK_DIR/build/installer" .

log "jar 产物："; ls -l "$WORK_DIR/build/jar"
