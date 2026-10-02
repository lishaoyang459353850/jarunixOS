# jarunixOS 1.0 开发日志

**项目**：jarunixOS —— 以 Java 为核心的图形化 Linux 发行版  
**版本**：1.0（代号 trixie） · **架构**：amd64  
**协议**：GNU General Public License v3.0  
**记录时间**：2026-10-02

---

## 一、项目目标

| 需求 | 设计决策 |
| --- | --- |
| 基于 Unix 开源内核 | Debian 13（trixie）+ 6.12 LTS 内核 |
| 内置图形化安装程序 | 完全自研 Java Swing 向导，7 步流程 |
| 个人版 / 专业版 | 个人版=桌面+JRE；专业版=个人版+开发工具链 |
| 内置 Java 运行库 | openjdk-21-jre-headless / openjdk-21-jdk |
| ISO < 800 MB | squashfs xz 压缩 + 精简包清单 |
| 系统一切基于 Java | 桌面外壳、任务栏、文件管理器、安装器全部 Java Swing |
| GPL 开源 + GitHub 托管 | GPL-3.0，公开仓库 |

## 二、系统架构

### 启动链路

1. 引导：BIOS 走 isolinux，UEFI 走 GRUB EFI 镜像（同一 ISO 双引导）
2. 内核：`/live/vmlinuz` + `/live/initrd.img`，由 live-boot 将 squashfs 挂为可写 overlay
3. 会话：`getty@tty1` 自动登录 jarunix → `.bash_profile` → `startx` → `jarunix-desktop`
4. 桌面：openbox 提供窗口装饰（EWMH 协议层），Java Swing 外壳提供其余全部界面

> 为何保留 openbox：Java/Swing 无法实现 EWMH 窗口管理协议，窗口装饰与任务切换必须由 X11 窗口管理器承担。桌面外壳、任务栏、图标、文件管理器、安装器均为 Java 实现。

### Java 组件

**桌面外壳 `os.jarunix.shell`（12 类）**：Main、DesktopFrame、WallpaperPanel、Taskbar、DesktopIcon、Icons、Theme、AppEntry、Launcher、ShellActions、FileBrowser、About

**图形化安装器 `os.jarunix.installer`（5 类）**：InstallerMain、Pages、InstallTask、DiskUtil、WizardModel

安装器 7 步向导：欢迎 → 版本选择 → 磁盘分区 → 账户设置 → 确认 → 安装进度 → 完成。后端调用 sfdisk / mkfs / unsquashfs / grub-install 完成实际写入。

## 三、关键技术问题

### 1. Java 组件编译验证

`javac --release 21 -encoding UTF-8` 两个模块均 0 error 通过，产出 `jarunix-shell.jar`（22850 字节）与 `jarunix-installer.jar`（30727 字节）。

### 2. 构建环境限制与应对

| 限制 | 现象 | 应对 |
| --- | --- | --- |
| 无 loop 设备 | `/dev/loop-control` 不存在 | 改用免挂载的 mmdebstrap |
| 无特权挂载 | debootstrap 报 `mounted with noexec or nodev` | 放弃 debootstrap |
| chroot 系统调用被禁 | `cannot change root directory` | 改用 chrootless 模式 |
| chrootless 下 systemd 配置失败 | `Unknown modifier 'u!'` | 宿主与目标 systemd 版本不一致，需兼容处理 |
| 镜像源不稳 | aliyun 连接建立但零传输 | 切换至 USTC（28.5 MB/s） |

构建脚本 `01-bootstrap.sh` 已内置环境自适应：检测到 loop 设备则用 debootstrap，否则自动回退 mmdebstrap chrootless。

### 3. 图形栈决策

Xorg + openbox + 自研 Java Swing 外壳。不使用显示管理器以压缩体积，改由 getty 自动登录直接拉起 X 会话。

## 四、交付物

| 交付物 | 说明 |
| --- | --- |
| jarunixOS-1.0-personal-amd64.iso | 个人版安装镜像 |
| jarunixOS-1.0-professional-amd64.iso | 专业版安装镜像 |
| GitHub 仓库 | GPL-3.0 全量源码 |
| `.github/workflows/build-iso.yml` | CI 矩阵构建两个版本并上传产物 |
| 开发日志 | 本文档（同步至飞书） |

## 五、后续工作

1. 在具备完整权限的构建机上执行 `sudo ./build/build.sh --edition personal`，产出最终 ISO
2. 用 QEMU 启动验证 Java 桌面外壳与图形化安装器
3. 补充 GRUB 主题与安装器多语言资源
4. 建立发布流程：打 tag 自动构建并附加 ISO 到 Release
