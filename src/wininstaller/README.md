# jarunixOS 安装向导（Windows）

把 jarunixOS 的镜像释放到 U 盘或文件夹的图形化向导，Windows 安装程序风格，纯 Python 标准库实现（tkinter），可编译成单个 `.exe`。

## 功能

向导共六步：**欢迎 → 选择版本 → 选择释放位置 → 确认 → 写入 → 完成**。

- **选择版本**：个人版（约 445 MiB）或专业版（约 656 MiB），界面里显示每个版本的说明与已装组件。
- **选择释放位置**，两种方式：
  - **制作 USB 启动盘** —— 把镜像原始字节写入 U 盘，做成可直接开机启动的安装盘。
  - **释放镜像文件到文件夹** —— 导出 `.iso` 文件，供虚拟机、刻录工具等使用。
- **安全保护**：只列出可移动磁盘（不显示本机硬盘）；校验目标容量是否装得下；确认页需勾选确认才能开始；写入过程中可中止。
- **内嵌镜像**：编译时可以先把两个版本的镜像追加进 exe，得到一个自带镜像的单文件安装程序，用户无需另外准备 `.iso`。

## 源码结构

| 文件 | 作用 |
| --- | --- |
| `main.py` | 程序入口、DPI 适配、管理员权限检测与 UAC 提权 |
| `editions.py` | 版本元数据、镜像定位（内嵌载荷 / 同目录文件 / 用户指定） |
| `disks.py` | 通过 ctypes 调用 Windows API：枚举可移动磁盘、锁定卷、原始写盘、释放文件 |
| `wizard.py` | 向导界面（六个页面、左侧步骤栏、底部导航按钮） |
| `pack_payload.py` | 构建期工具：把镜像追加到 exe 尾部，生成单文件安装程序 |
| `build_exe.bat` | 一键构建脚本 |

## 构建

需要 Windows + Python 3.9 或更高版本（tkinter 随官方安装包提供）。

```bat
build_exe.bat
```

脚本会：

1. 检查并按需安装 PyInstaller；
2. 编译出独立安装器 `dist\jarunixOS-USB-Setup.exe`；
3. 如果当前目录（或 `payload\` 子目录）里有
   `jarunixOS-1.0-personal-amd64.iso` 与 `jarunixOS-1.0-professional-amd64.iso`，
   再合成内嵌双版本镜像的 `dist\jarunixOS-USB-Setup-2in1.exe`。

也可以手动执行：

```bat
python -m PyInstaller --onefile --noconsole --name jarunixOS-USB-Setup main.py
python pack_payload.py dist\jarunixOS-USB-Setup.exe dist\jarunixOS-USB-Setup-2in1.exe ^
    jarunixOS-1.0-personal-amd64.iso jarunixOS-1.0-professional-amd64.iso
```

### 单文件是怎么做出来的

`pack_payload.py` 把镜像字节直接追加在 exe 尾部，再写一段索引 JSON 和 40 字节页脚：

```
[安装器 exe][个人版镜像][专业版镜像][索引 JSON][页脚 40B]
```

页脚记录了索引的偏移与长度，索引里记录了每个镜像的偏移、大小和 SHA-256。
运行时程序读自己的尾部就能找到镜像，**不需要解包到临时目录**，因此启动很快、也不占用额外磁盘空间。

## 使用

1. 插入 U 盘（制作启动盘时，U 盘上的数据会被清空）。
2. 双击 `jarunixOS-USB-Setup-2in1.exe`。制作 U 盘需要管理员权限，程序会提示是否提权。
3. 依次选择版本、目标 U 盘，确认后点击「开始」。
4. 完成后安全弹出 U 盘。开机时按启动菜单键（常见为 `F12` / `F11` / `ESC` / `F8`）选择该 U 盘。

如果只想导出 `.iso` 文件，选择「释放镜像文件到文件夹」即可，这种方式不需要管理员权限。

## 引导菜单

镜像同时支持 BIOS（syslinux）和 UEFI（GRUB）引导，菜单提供四个入口：

| 入口 | 说明 |
| --- | --- |
| Live desktop | 正常启动，进入 Java 图形桌面 |
| safe graphics (VESA) | 正常入口黑屏时使用（虚拟机、老旧显卡） |
| text mode | 只启动文本控制台，用于排错 |
| serial console | 把内核日志同时输出到 ttyS0，仅调试用 |

引导菜单文字使用英文：syslinux 与 GRUB 的图形菜单都使用内置位图字体，无法显示中文，写中文会变成乱码。

UEFI 侧 GRUB 的位图字体（`unicode.pf2`）会随 EFI 分区一起写入镜像，缺失它会导致菜单一片空白；
EFI 分区固定为 16 MB 并格式化为 FAT16 —— 小容量卷若强用 FAT32，会因簇数低于规范下限而被 UEFI 固件判为无效。

## 许可

GPL-3.0-or-later，与 jarunixOS 主体一致。
