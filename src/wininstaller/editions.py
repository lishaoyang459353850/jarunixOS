# -*- coding: utf-8 -*-
# jarunixOS 安装向导 —— 版本元数据与镜像定位
# Copyright (C) 2026 jarunixOS Project
# SPDX-License-Identifier: GPL-3.0-or-later
#
# 本程序是自由软件：你可以依据自由软件基金会发布的 GNU 通用公共许可证
# （第 3 版或任何更高版本）的条款重新发布和/或修改它。
# 本程序分发时希望有用，但不提供任何担保。

"""版本元数据，以及镜像数据的定位。

镜像有三种来源，按优先级：
  1. 内嵌载荷 —— 镜像数据被追加在 exe 文件尾部（单文件分发）
  2. 随行文件 —— exe 同目录下的 payload/ 目录或同名 .iso 文件
  3. 用户浏览 —— 由用户在向导里手动指定
"""

from __future__ import annotations

import json
import os
import struct
import sys

APP_NAME = "jarunixOS"
APP_VERSION = "1.0"
APP_CODENAME = "trixie"
APP_ARCH = "amd64"
APP_VENDOR = "jarunixOS Project"
APP_HOMEPAGE = "https://github.com/lishaoyang459353850/jarunixOS"
APP_TAGLINE = "以 Java 为核心的图形化 Linux 发行版"

# 追加在 exe 尾部的载荷格式：
#   [可执行文件][镜像A][镜像B]...[索引 JSON][页脚]
# 页脚 40 字节，从文件末尾倒数：
#   magic(8) + index_offset(8) + index_length(8) + payload_total(8) + reserved(8)
PAYLOAD_MAGIC = b"JRNXPAY1"
FOOTER_SIZE = 40
FOOTER_FMT = "<8sQQQQ"

EDITIONS = [
    {
        "key": "personal",
        "name": "个人版",
        "subtitle": "Personal Edition",
        "filename": "jarunixOS-1.0-personal-amd64.iso",
        "size": 463470592,
        "sha256": "1baf91861fc6d4cb0104a282ced000ae5a4139aefa5566e36d5c1663ea615c99",
        "summary": "面向日常使用的轻量桌面",
        "bullets": [
            "Java Swing 图形桌面 + Openbox 窗口管理器",
            "内置 OpenJDK 21 运行库（JRE）",
            "终端、文件管理器、安装程序、关于本机等基础应用",
            "已装软件包约 358 个，镜像约 442 MB",
        ],
    },
    {
        "key": "professional",
        "name": "专业版",
        "subtitle": "Professional Edition",
        "filename": "jarunixOS-1.0-professional-amd64.iso",
        "size": 685768704,
        "sha256": "03fedc6f5b69166d97a7a33151ff440f64f43ea31e6a15e361a748551460bb25",
        "summary": "个人版全部功能 + 完整开发工具链",
        "bullets": [
            "含个人版全部内容",
            "OpenJDK 21 JDK（含 javac、jar、jdb 等）",
            "git、curl、wget、vim、jq、tree、netcat",
            "python3 + pip、build-essential、gdb、cmake",
            "已装软件包约 521 个，镜像约 685 MB",
        ],
    },
]

EDITION_BY_KEY = {e["key"]: e for e in EDITIONS}


# --------------------------------------------------------------------------
# 内嵌载荷
# --------------------------------------------------------------------------

def _exe_path() -> str:
    """返回当前可执行文件路径（打包后为 exe，未打包时为 python 解释器）。"""
    return os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)


def read_embedded_index():
    """读取 exe 尾部内嵌载荷的索引；没有则返回 None。"""
    path = _exe_path()
    try:
        size = os.path.getsize(path)
        if size < FOOTER_SIZE:
            return None
        with open(path, "rb") as fp:
            fp.seek(size - FOOTER_SIZE)
            footer = fp.read(FOOTER_SIZE)
            magic, idx_off, idx_len, total, _ = struct.unpack(FOOTER_FMT, footer)
            if magic != PAYLOAD_MAGIC:
                return None
            if idx_off + idx_len > size or idx_len <= 0:
                return None
            fp.seek(idx_off)
            index = json.loads(fp.read(idx_len).decode("utf-8"))
            index["_payload_total"] = total
            return index
    except Exception:
        return None


class EmbeddedImage:
    """内嵌镜像的只读视图，支持按块读取并上报进度。"""

    def __init__(self, exe_path: str, offset: int, size: int, sha256: str = ""):
        self._path = exe_path
        self.offset = offset
        self.size = size
        self.sha256 = sha256

    def open(self):
        return _EmbeddedReader(self._path, self.offset, self.size)


class _EmbeddedReader:
    def __init__(self, path: str, offset: int, size: int):
        self._fp = open(path, "rb")
        self._fp.seek(offset)
        self._remaining = size
        self.size = size

    def read(self, n: int = -1) -> bytes:
        if self._remaining <= 0:
            return b""
        if n is None or n < 0:
            n = self._remaining
        n = min(n, self._remaining)
        data = self._fp.read(n)
        self._remaining -= len(data)
        return data

    def close(self):
        try:
            self._fp.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# --------------------------------------------------------------------------
# 随行文件 / 用户指定
# --------------------------------------------------------------------------

def sidecar_dirs() -> list:
    """返回可能存放镜像的目录（exe 所在目录及其 payload 子目录）。"""
    dirs = []
    exe_dir = os.path.dirname(_exe_path())
    dirs.append(exe_dir)
    dirs.append(os.path.join(exe_dir, "payload"))
    cwd = os.getcwd()
    if cwd not in dirs:
        dirs.append(cwd)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dirs.append(sys._MEIPASS)
    return dirs


def find_sidecar(edition: dict):
    """在随行目录里查找该版本的镜像文件，找到返回绝对路径。"""
    for d in sidecar_dirs():
        cand = os.path.join(d, edition["filename"])
        if os.path.isfile(cand):
            return cand
    return None


def find_any_iso(keyword: str):
    """按关键词（如 personal / professional）模糊查找镜像文件。"""
    for d in sidecar_dirs():
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            low = name.lower()
            if low.endswith(".iso") and keyword in low:
                return os.path.join(d, name)
    return None


# --------------------------------------------------------------------------
# 统一入口
# --------------------------------------------------------------------------

class ImageSource:
    """镜像来源。kind 为 embedded / file；size 为字节数。"""

    def __init__(self, kind: str, size: int, path: str = "", offset: int = 0,
                 sha256: str = "", label: str = ""):
        self.kind = kind
        self.size = size
        self.path = path
        self.offset = offset
        self.sha256 = sha256
        self.label = label

    def open(self):
        if self.kind == "embedded":
            return _EmbeddedReader(_exe_path(), self.offset, self.size)
        return open(self.path, "rb")

    def readable(self) -> bool:
        if self.kind == "embedded":
            return True
        return bool(self.path) and os.path.isfile(self.path)


def resolve_source(edition: dict, embedded_index=None, user_path: str = "") -> ImageSource:
    """按 用户指定 → 内嵌载荷 → 随行文件 的顺序解析镜像来源。"""
    if user_path and os.path.isfile(user_path):
        return ImageSource("file", os.path.getsize(user_path), path=user_path,
                           label="用户指定")

    if embedded_index:
        rec = embedded_index.get(edition["key"])
        if rec:
            return ImageSource("embedded", int(rec["size"]), offset=int(rec["offset"]),
                               sha256=rec.get("sha256", ""), label="内嵌于安装程序")

    side = find_sidecar(edition)
    if side:
        return ImageSource("file", os.path.getsize(side), path=side, label="同目录镜像文件")

    return ImageSource("missing", 0)


def embedded_available() -> bool:
    return read_embedded_index() is not None


def format_size(n: int) -> str:
    """把字节数格式化成便于阅读的字符串。"""
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    for u in units:
        if v < 1024 or u == units[-1]:
            if u == "B":
                return "%d %s" % (int(v), u)
            return "%.1f %s" % (v, u)
        v /= 1024.0
    return "%.1f GB" % (n / 1024.0 / 1024.0 / 1024.0)
