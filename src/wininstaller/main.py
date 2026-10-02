# -*- coding: utf-8 -*-
# jarunixOS 安装向导 —— 程序入口
# Copyright (C) 2026 jarunixOS Project
# SPDX-License-Identifier: GPL-3.0-or-later
#
# 本程序是自由软件：你可以依据自由软件基金会发布的 GNU 通用公共许可证
# （第 3 版或任何更高版本）的条款重新发布和/或修改它。

"""jarunixOS 安装向导（Windows）。

用法：
    jarunixOS-USB-Setup.exe             启动图形向导
    jarunixOS-USB-Setup.exe --version      显示版本
    jarunixOS-USB-Setup.exe --help         显示帮助
    jarunixOS-USB-Setup.exe --no-elevate   跳过启动时的管理员提权提示
                                           （此时只能使用「释放镜像到文件夹」）
"""

from __future__ import annotations

import ctypes
import os
import sys
import traceback

MB_YESNO = 0x00000004
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010
IDYES = 6


def enable_dpi_awareness():
    """让界面在高分屏上不发虚。"""
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def msgbox(text, flags=MB_ICONERROR):
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(None, text, "jarunixOS 安装向导", flags)
            return
        except Exception:
            pass
    sys.stderr.write(text + "\n")


def _ensure_path():
    """把脚本所在目录加入模块搜索路径（源码直接运行时需要）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        if sys._MEIPASS not in sys.path:
            sys.path.insert(0, sys._MEIPASS)


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)

    if "--version" in argv or "-v" in argv:
        import editions as ed
        print("%s %s (%s, %s)" % (ed.APP_NAME, ed.APP_VERSION,
                                  ed.APP_CODENAME, ed.APP_ARCH))
        return 0

    if "--help" in argv or "-h" in argv or "/?" in argv:
        print(__doc__)
        return 0

    if os.name != "nt":
        msgbox("本安装向导仅支持 Windows。")
        return 2

    enable_dpi_awareness()
    _ensure_path()

    import disks
    import editions as ed
    import wizard

    if not disks.is_admin() and "--no-elevate" not in argv:
        r = ctypes.windll.user32.MessageBoxW(
            None,
            "制作 USB 启动盘需要管理员权限。\n\n"
            "是否以管理员身份重新启动本程序？\n\n"
            "选择「否」仍可继续使用，但只能执行"
            "「释放镜像文件到文件夹」，无法写入 U 盘。",
            "jarunixOS 安装向导 —— 权限提示",
            MB_YESNO | MB_ICONWARNING)
        if r == IDYES:
            if disks.relaunch_as_admin(argv):
                return 0
            msgbox("提权失败。请右键本程序，选择「以管理员身份运行」。")

    root = wizard.Wizard()
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        msgbox("程序启动失败：\n\n" + traceback.format_exc())
        sys.exit(1)
