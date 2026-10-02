# jarunixOS

一个以 **Java 为系统层核心** 的 Linux 桌面发行版。基于 Debian 13 "trixie" 与
其 LTS 内核构建，内置 Java 运行时、Java 编写的桌面外壳（Shell）与 Java 编写的
图形化安装程序。提供 **个人版（Personal）** 与 **专业版（Professional）** 两个版本，
ISO 体积控制在 800 MB 以内。

## 状态

- ✅ **个人版 ISO 已在 QEMU 实机启动验证通过**：ISOLINUX 菜单 → 内核
  `6.12.107+deb13-amd64` → live-boot → tty1 自动登录 → Xorg → **自研 Java Swing
  桌面外壳正常显示**（任务栏、开始菜单、桌面图标、时钟、壁纸）。
- 个人版镜像体积 **434 MB**，满足 < 800 MB 的体积要求。
- 桌面外壳与安装程序全部源码位于本仓库 `src/`，以 GPL-3.0-or-later 开源。

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

## 版本差异

| 组件 | 个人版 | 专业版 |
| --- | --- | --- |
| 图形桌面 + Java 运行时 + 图形化安装器 | ✅ | ✅ |
| JDK / Git / GCC / Python / CMake 开发工具链 | — | ✅ |

## 构建

```bash
sudo apt-get install mmdebstrap squashfs-tools xorriso fakeroot fakechroot \
     isolinux syslinux-common syslinux-efi grub-pc-bin grub-efi-amd64-bin \
     grub-common mtools dosfstools rsync openjdk-21-jdk-headless cpio zstd
./build/build.sh --edition personal
```

产物位于 `build/out/jarunixOS-<version>-<edition>-amd64.iso`。

构建容器若禁用挂载系统调用与 loop 设备，`build.sh` 会走 mmdebstrap 的
`chrootless` 免挂载模式（配合 `fakeroot` / `fakechroot`）。

### 收尾修复（`build/05-fixup.sh`）

chrootless 构建会引入四类只有实机启动才会暴露的缺陷，`build.sh` 在打包前自动修复：

| 修复 | 未修复时的症状 | 处理方式 |
| --- | --- | --- |
| Xorg setuid | 普通用户无法启动 X 服务器 | `chmod 4755 /usr/lib/xorg/Xorg`，并写 `Xwrapper.config` |
| 符号链接重写 | `java: command not found`，桌面永远起不来 | 重写指向构建期绝对路径的链接 |
| initramfs 内核模块 | 内核 panic（找不到根文件系统） | 手工补入挂载根文件系统所需的模块子树 |
| initramfs 动态库 | `/init` 以 127 退出、内核 panic | 解析 ELF `NEEDED` 迭代补齐依赖闭包 |

## 目录结构

```
build/         构建脚本、包清单、配置与 rootfs 覆盖层
build/tools/   initramfs 重建与动态库闭包求解工具
src/shell/     Java 桌面外壳
src/installer/ Java 图形化安装程序
docs/          开发日志与架构说明
```

## 许可

本项目遵循 **GNU General Public License v3.0 或更高版本**（GPL-3.0-or-later），
完整文本见 [LICENSE](LICENSE)。
