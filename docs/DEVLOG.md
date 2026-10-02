# jarunixOS 开发日志

> 记录人：库库AI · 起始 2026-10-02

## 1. 目标

按需求交付一款图形化 Linux 发行版：

- 基于 Unix 开源内核（选用 Debian 13 "trixie" 的 LTS 内核）
- 自带图形化安装程序
- 分 **个人版** 与 **专业版**
- 内置 Java 运行库
- ISO 体积 < 800 MB
- 系统层以 Java 为核心，图形界面用 Java 开发
- 以 GPL 协议开源，托管到 GitHub
- 开发日志同步到飞书

## 2. 构建环境与关键约束

构建在云端 Linux 沙箱内完成，环境实测如下：

| 项目 | 实测值 |
| --- | --- |
| 发行版 | Ubuntu 24.04.5 LTS (amd64) |
| 权限 | root，CapEff `00000000a92425fb`，Seccomp 已启用 |
| CPU / 内存 | 2 核 / 3.8 GB |
| 磁盘可用 | 65 GB |
| loop 设备 | **不存在**（`/dev/loop-control` 缺失） |
| 挂载系统调用 | **被禁用**（bind 操作返回失败） |

由此产生两条硬约束，直接决定了构建路线的选择：

1. `debootstrap` 在 `check_sane_mount` 阶段需要把 `/dev/null` 绑定到目标目录做
   可执行性探测，该探测失败后直接报
   `E: Cannot install into target ... mounted with noexec or nodev`，无法继续。
2. `mmdebstrap --mode=root` 需要向目标根目录挂载 `/proc`、`/sys`、`/dev`，
   同样不可用。

## 3. 路线选择：mmdebstrap chrootless

最终采用 **mmdebstrap 的 chrootless 模式**：它用
`dpkg --force-script-chrootless --root=<target>` 在**不进入 chroot、不做任何挂载**
的前提下完成解包与配置，与沙箱约束完全兼容。

调通过程中踩到的三个坑：

1. **chrootless 以 root 直接运行会被拒绝**
   `E: running chrootless mode as root without fakeroot might damage the host system`。
   原因：`--force-script-chrootless` 下维护脚本以当前用户身份运行，若没有 fakeroot
   伪造权限，脚本可能越出目标目录。
2. **改用普通用户运行后 `chown` 失败**
   报错集中在 `base-files` 与 `base-passwd`：
   `chown: changing ownership of '/work/root-personal/mnt': Operation not permitted`
   `fchownat() of /work/root-personal/run/setrans failed: Operation not permitted`
   因为非特权用户无法把文件改为任意属主。
3. **正解：root + fakeroot**
   安装 `fakeroot` 后以 `fakeroot mmdebstrap --mode=chrootless ...` 运行，
   `chown` 由 fakeroot 拦截并伪造成功，dpkg 的 postinst 正常返回 0。

此外，`fakechroot` 收尾阶段必须设置 `FAKECHROOT_EXCLUDE_PATH=/proc:/sys:/dev`，
否则 openjdk 的 postinst 会失败。

### 3.1 镜像源

初次使用 `deb.debian.org`，实测下载速率约 **31 KB/s**，按此速度 400 MB 需要数小时。
对多个镜像做同文件测速（`dists/trixie/main/binary-amd64/Packages.xz`，9.7 MB）：

| 镜像 | 速率 |
| --- | --- |
| deb.debian.org | 超时 / 不可用 |
| **mirrors.ustc.edu.cn** | **28.5 MB/s（采用）** |
| mirrors.aliyun.com | 零传输 / 不可用 |
| mirrors.cloud.tencent.com | 26580 KB/s |
| mirror.nju.edu.cn | 24023 KB/s |
| mirrors.163.com | 1321 KB/s |

切换到 `mirrors.ustc.edu.cn` 后，下载阶段从「数小时」压缩到「数十秒」。
注意 DNS 可能解析到 IPv6 导致 apt 失败，需加 `-o Acquire::ForceIPv4=true`。

## 4. 技术架构

```
应用层      jarunix-shell / jarunix-installer
会话层      startx -> jarunix-desktop -> openbox + java -jar jarunix-shell.jar
图形栈      Xorg (xserver-xorg-core + libinput + vesa/fbdev)
系统层      Debian 13 trixie + systemd + live-boot/live-config
内核        linux-image-amd64 (trixie LTS)
```

**为什么保留 openbox**：Java 无法直接实现 X11 的窗口管理器协议（ICCCM/EWMH），
因此窗口装饰与焦点管理交给体积约 2 MB 的 openbox；桌面外壳、任务栏、开始菜单、
桌面图标、文件浏览器、安装程序全部由 Java 实现。

**为什么用 `startx` 而非显示管理器**：省掉 LightDM/GDM 的依赖体积（约 15–40 MB），
同时避免显示管理器与自动登录的耦合。

## 5. 自研 Java 组件

| 组件 | 源文件数 | 说明 |
| --- | --- | --- |
| `jarunix-shell` | 12 | 桌面外壳：任务栏、开始菜单、桌面图标、文件浏览器、关于本机 |
| `jarunix-installer` | 5 | 图形化安装向导：版本选择、磁盘选择、账户设置、确认、执行、完成 |

编译验证：`javac --release 21 -encoding UTF-8`，两个模块均 **0 error** 通过。

外壳与安装器的图标全部由 Java2D 矢量绘制，不依赖任何图片资源文件。

## 6. 首次实机启动：四个致命故障与修复

个人版 ISO 首次打包完成后，在 QEMU 中启动失败。逐个定位并修复：

| # | 故障 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | 内核 panic，找不到根文件系统 | initramfs 内 **0 个 `.ko`**（仅 454 个条目），initramfs-tools 在 fakechroot 下写不进暂存目录 | 手工补入 21 个模块子树（squashfs/overlayfs/isofs/ext4/ata/virtio/usb…），约 420 个 `.ko`、11 MB |
| 2 | `/init` 以 127 退出 | initramfs 缺动态库：busybox 需 `libresolv.so.2`，systemd-udevd 需 `libsystemd-shared-257.so`（藏在 `usr/lib/x86_64-linux-gnu/systemd/`） | 新增依赖闭包求解器，用 `readelf -d` 解析 `NEEDED` 迭代补齐 |
| 3 | Xorg 启动被拒 | `/usr/lib/xorg/Xorg` 无 setuid 位，且缺 `Xwrapper.config` | `chmod 4755` + 写 `allowed_users=anybody` / `needs_root_rights=yes` |
| 4 | **`java: command not found`，桌面永远起不来** | chrootless 构建把 `/usr/bin/java` 等 36+ 个 alternatives 符号链接写成了构建期绝对路径（`/work/root-personal/...`），装进 ISO 后全部悬空 | 批量重写为相对根路径的链接，残留 0 条 |

排查手段上，**串口调试**最有效：给 QEMU 加 `-serial unix:...,server,nowait`，
在 `APPEND` 行加 `console=ttyS0,115200`，即可用 socket 连入交互式排障；
图形会话的输出**不能**重定向到 ttyS0（会 Permission denied 导致整段
`.bash_profile` 失败），改为写 `/tmp/desktop.log`。

这四项修复已固化为 `build/05-fixup.sh` 与 `build/tools/`（`fix-initrd.sh`、
`lib-closure.py`），并接入 `build.sh` 主流程，重跑构建可自动复现。

## 7. 实机验证结果

个人版 ISO 在 QEMU 中完成全链路启动：

```
ISOLINUX 菜单 → linux 6.12.107+deb13-amd64 → live-boot → tty1 自动登录 jarunix
→ X.Org 1.21.1.16 → java -jar /opt/jarunix/jarunix-shell.jar
```

**自研 Java Swing 桌面外壳正常显示**，截图确认的界面元素：

- 深蓝渐变壁纸（Java2D 绘制）
- 底部任务栏：`jarunix` 标识 + 终端 / 文件 / 安装程序 / 关于本机 + 实时时钟
- 左侧图标栏：4 个 Java2D 自绘图标
- 右下角 `jarunixOS` 水印

体积：rootfs 1.2 GB → squashfs 366 MB → **ISO 434 MB**，满足 < 800 MB 要求。

## 8. 开源托管

- 仓库：https://github.com/lishaoyang459353850/jarunixOS （公开，`main` 分支）
- 许可：GNU GPL v3.0（`LICENSE` 全文 35 KB），README 声明 GPL-3.0-or-later
- 已推送：`src/` 全部 17 个 Java 源文件、`build/` 全部构建脚本与配置、
  `build/overlay/` 覆盖层、`build/packages/` 包清单、`docs/` 文档

## 9. 待续

- 专业版 ISO 重建（套用个人版的四项修复后重新打包与实机验证）
- 源码包与 GitHub 仓库内容随最新修复保持同步
