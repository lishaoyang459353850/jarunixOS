# jarunixOS

一个以 **Java 为系统层核心** 的 Linux 桌面发行版。基于 Debian 13 "trixie" 与其 LTS 内核构建，内置 Java 运行时、Java 编写的桌面外壳（Shell）与 Java 编写的图形化安装程序。提供 **个人版（Personal）** 与 **专业版（Professional）** 两个版本，ISO 体积控制在 800 MB 以内。

## 特性

| 项目 | 说明 |
| --- | --- |
| 基础系统 | Debian 13 trixie (amd64)，LTS 内核 |
| 图形会话 | Xorg + openbox，会话层为自研 Java Swing 桌面外壳 |
| 桌面外壳 | `jarunix-shell`，纯 Java，负责任务栏、开始菜单、桌面图标、应用启动 |
| 安装程序 | `jarunix-installer`，纯 Java Swing 向导，分区/格式化/部署/引导全流程 |
| 运行时 | OpenJDK 21 (LTS) |
| 版本 | Personal / Professional |
| 许可 | GPL-3.0-or-later |

## 构建

```bash
sudo apt-get install debootstrap mmdebstrap squashfs-tools xorriso \
     isolinux syslinux-common syslinux-efi grub-pc-bin grub-efi-amd64-bin \
     grub-common mtools dosfstools rsync openjdk-21-jdk-headless
./build/build.sh --edition personal
```

产物位于 `build/out/jarunixOS-<version>-<edition>-amd64.iso`。

> 构建容器若禁用挂载系统调用与 loop 设备，`build.sh` 会自动回退到 mmdebstrap 的 `chrootless` 免挂载模式。

## 目录结构

```
build/        构建脚本、包清单、配置与 rootfs 覆盖层
src/shell/    Java 桌面外壳
src/installer/ Java 图形化安装程序
docs/         开发日志与架构说明
```

## 许可

本项目遵循 GNU General Public License v3.0 或更高版本，见 `LICENSE`。
