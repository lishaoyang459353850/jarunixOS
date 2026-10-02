# jarunixOS 架构说明

## 分层

```
应用层      jarunix-shell / jarunix-installer / 第三方 Java 应用
会话层      startx -> jarunix-desktop (shell 脚本) -> openbox + java -jar jarunix-shell.jar
图形栈      Xorg (xserver-xorg-core, libinput, vesa/fbdev)
系统层      Debian 13 trixie + systemd + live-boot/live-config
内核        linux-image-amd64 (trixie LTS)
```

## 为什么仍需要 openbox

Java 无法直接实现 X11 的窗口管理器协议（ICCCM/EWMH），因此窗口装饰与焦点
管理交给体积极小的 openbox（约 2 MB），桌面外壳本身、任务栏、开始菜单、
桌面图标、安装器全部由 Java 实现。

## 启动链路

1. systemd 启动 `getty@tty1`，通过 drop-in 覆盖实现 `jarunix` 用户自动登录。
2. `~/.bash_profile` 判断当前 tty 后 `exec startx`。
3. `startx` 调用 `/usr/local/bin/jarunix-desktop`。
4. 会话脚本拉起 openbox，随后启动 `java -jar /opt/jarunix/jarunix-shell.jar`。
5. 外壳退出即会话结束。

## Live 与安装

Live 介质由 `live-boot` 把 squashfs 呈现为只读根。安装器把 squashfs
展开到目标磁盘，写入 fstab、安装 GRUB（BIOS 与 UEFI 双路径），并按所选
版本追加软件包集合。

## 构建期修复

chrootless 构建路径会引入四类缺陷，由 `build/05-fixup.sh` 在打包前统一修复：
Xorg setuid、构建期绝对符号链接重写、initramfs 内核模块补齐、initramfs
动态库依赖闭包。详见 `docs/DEVLOG.md` 第 6 节。
