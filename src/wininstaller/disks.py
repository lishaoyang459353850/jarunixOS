# -*- coding: utf-8 -*-
# jarunixOS 安装向导 —— Windows 存储层
# Copyright (C) 2026 jarunixOS Project
# SPDX-License-Identifier: GPL-3.0-or-later
#
# 本程序是自由软件：你可以依据自由软件基金会发布的 GNU 通用公共许可证
# （第 3 版或任何更高版本）的条款重新发布和/或修改它。

"""通过 Windows 原生 API 枚举可移动磁盘，并把镜像原始字节写入物理磁盘。

全部使用 ctypes 调用 kernel32，不依赖任何第三方库。
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---- 常量 ---------------------------------------------------------------
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
FILE_FLAG_NO_BUFFERING = 0x20000000
FILE_FLAG_WRITE_THROUGH = 0x80000000

DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6

IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x2D1080
IOCTL_STORAGE_QUERY_PROPERTY = 0x2D1400
IOCTL_DISK_UPDATE_PROPERTIES = 0x00070140
FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_DISMOUNT_VOLUME = 0x00090020
FSCTL_ALLOW_EXTENDED_DASD_IO = 0x00090083

# ---- 函数原型（必须显式声明，否则 64 位句柄会被截断）--------------------
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
kernel32.DeviceIoControl.restype = wintypes.BOOL
kernel32.DeviceIoControl.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
    ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.WriteFile.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
]
kernel32.ReadFile.restype = wintypes.BOOL
kernel32.ReadFile.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
]
kernel32.GetLogicalDrives.restype = wintypes.DWORD
kernel32.GetDriveTypeW.restype = wintypes.UINT
kernel32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
kernel32.GetVolumeInformationW.restype = wintypes.BOOL
kernel32.GetVolumeInformationW.argtypes = [
    wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
]
kernel32.GetDiskFreeSpaceExW.restype = wintypes.BOOL
kernel32.GetDiskFreeSpaceExW.argtypes = [
    wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_ulonglong),
    ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong),
]
kernel32.FlushFileBuffers.restype = wintypes.BOOL
kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
kernel32.SetFilePointerEx.restype = wintypes.BOOL
kernel32.SetFilePointerEx.argtypes = [
    wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD,
]


# ---- 结构体 -------------------------------------------------------------
class STORAGE_DEVICE_NUMBER(ctypes.Structure):
    _fields_ = [
        ("DeviceType", wintypes.DWORD),
        ("DeviceNumber", wintypes.DWORD),
        ("PartitionNumber", wintypes.DWORD),
    ]


class STORAGE_PROPERTY_QUERY(ctypes.Structure):
    _fields_ = [
        ("PropertyId", wintypes.DWORD),      # 0 = StorageDeviceProperty
        ("QueryType", wintypes.DWORD),       # 0 = PropertyStandardQuery
        ("AdditionalParameters", ctypes.c_ubyte * 4),
    ]


class STORAGE_DEVICE_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.DWORD),
        ("Size", wintypes.DWORD),
        ("DeviceType", ctypes.c_ubyte),
        ("DeviceTypeModifier", ctypes.c_ubyte),
        ("RemovableMedia", ctypes.c_ubyte),
        ("CommandQueueing", ctypes.c_ubyte),
        ("VendorIdOffset", wintypes.DWORD),
        ("ProductIdOffset", wintypes.DWORD),
        ("ProductRevisionOffset", wintypes.DWORD),
        ("SerialNumberOffset", wintypes.DWORD),
        ("BusType", wintypes.DWORD),
        ("RawPropertiesLength", wintypes.DWORD),
        ("RawDeviceProperties", ctypes.c_ubyte * 1),
    ]


# ---- 权限 ---------------------------------------------------------------
def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(argv=None) -> bool:
    """以管理员身份重启自身（触发 UAC）。返回 True 表示已发起提权。"""
    if argv is None:
        if getattr(sys, "frozen", False):
            argv = sys.argv
        else:
            argv = [sys.executable] + sys.argv
    exe = argv[0]
    params = " ".join('"%s"' % a for a in argv[1:])
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return int(rc) > 32
    except Exception:
        return False


# ---- 设备访问小工具 ------------------------------------------------------
def _open_device(path: str, write: bool = False, share: bool = True):
    access = GENERIC_READ | (GENERIC_WRITE if write else 0)
    flags = FILE_ATTRIBUTE_NORMAL
    sh = (FILE_SHARE_READ | FILE_SHARE_WRITE) if share else 0
    h = kernel32.CreateFileW(path, access, sh, None, OPEN_EXISTING, flags, None)
    if h == INVALID_HANDLE_VALUE or h is None:
        return None
    return h


def _ioctl(h, code, in_buf=None, in_size=0, out_buf=None, out_size=0):
    returned = wintypes.DWORD(0)
    ok = kernel32.DeviceIoControl(
        h, code,
        ctypes.cast(in_buf, ctypes.c_void_p) if in_buf is not None else None, in_size,
        ctypes.cast(out_buf, ctypes.c_void_p) if out_buf is not None else None, out_size,
        ctypes.byref(returned), None,
    )
    return bool(ok), returned.value


def physical_drive_of_letter(letter: str):
    """把盘符映射到物理磁盘号；失败返回 None。"""
    h = _open_device("\\\\.\\%s:" % letter, write=False)
    if h is None:
        return None
    try:
        sdn = STORAGE_DEVICE_NUMBER()
        ok, _ = _ioctl(h, IOCTL_STORAGE_GET_DEVICE_NUMBER, None, 0,
                       ctypes.byref(sdn), ctypes.sizeof(sdn))
        if ok:
            return int(sdn.DeviceNumber)
        return None
    finally:
        kernel32.CloseHandle(h)


def _device_text(buf, offset, size=128):
    if not offset or offset >= size:
        return ""
    end = buf.find(b"\x00", offset)
    raw = buf[offset:end if end > 0 else size]
    return raw.decode("ascii", "replace").strip()


def drive_model(disk_number: int) -> dict:
    """查询物理磁盘的厂商/型号/总线类型/是否可移动。"""
    info = {"vendor": "", "model": "", "serial": "", "bus": 0, "removable": False}
    h = _open_device("\\\\.\\PhysicalDrive%d" % disk_number, write=False)
    if h is None:
        return info
    try:
        q = STORAGE_PROPERTY_QUERY()
        q.PropertyId = 0
        q.QueryType = 0
        buf = ctypes.create_string_buffer(1024)
        ok, _ = _ioctl(h, IOCTL_STORAGE_QUERY_PROPERTY, ctypes.byref(q),
                       ctypes.sizeof(q), buf, len(buf))
        if ok:
            raw = buf.raw
            desc = STORAGE_DEVICE_DESCRIPTOR.from_buffer_copy(raw)
            info["removable"] = bool(desc.RemovableMedia)
            info["bus"] = int(desc.BusType)
            info["vendor"] = _device_text(raw, desc.VendorIdOffset)
            info["model"] = _device_text(raw, desc.ProductIdOffset)
            info["serial"] = _device_text(raw, desc.SerialNumberOffset)
        return info
    finally:
        kernel32.CloseHandle(h)


# ---- 枚举可移动磁盘 ------------------------------------------------------
BUS_NAMES = {1: "SCSI", 2: "ATAPI", 3: "ATA", 7: "USB", 8: "RAID", 9: "iSCSI",
             10: "SAS", 11: "SATA", 12: "SD", 13: "MMC", 17: "NVMe", 18: "SCM"}


def list_removable_disks():
    """返回所有可移动磁盘（U 盘/SD 卡）。

    每项字段：letter, root, label, fs, total, free, disk, model, vendor, bus。
    同一物理磁盘上的多个分区会合并为一条记录。
    """
    mask = kernel32.GetLogicalDrives()
    seen = {}
    for i in range(26):
        if not (mask & (1 << i)):
            continue
        letter = chr(ord("A") + i)
        root = "%s:\\" % letter
        try:
            dtype = kernel32.GetDriveTypeW(root)
        except Exception:
            continue
        if dtype != DRIVE_REMOVABLE:
            continue

        label_buf = ctypes.create_unicode_buffer(261)
        fs_buf = ctypes.create_unicode_buffer(261)
        serial = wintypes.DWORD(0)
        maxlen = wintypes.DWORD(0)
        flags = wintypes.DWORD(0)
        label, fs = "", ""
        try:
            if kernel32.GetVolumeInformationW(root, label_buf, 261, ctypes.byref(serial),
                                              ctypes.byref(maxlen), ctypes.byref(flags),
                                              fs_buf, 261):
                label = label_buf.value
                fs = fs_buf.value
        except Exception:
            pass

        free_avail = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        total_free = ctypes.c_ulonglong(0)
        try:
            kernel32.GetDiskFreeSpaceExW(root, ctypes.byref(free_avail),
                                         ctypes.byref(total), ctypes.byref(total_free))
        except Exception:
            pass

        disk = physical_drive_of_letter(letter)
        if disk is None:
            continue
        if disk in seen:
            seen[disk]["letters"].append(letter)
            continue
        info = drive_model(disk)
        seen[disk] = {
            "disk": disk,
            "letters": [letter],
            "letter": letter,
            "root": root,
            "label": label,
            "fs": fs,
            "total": int(total.value),
            "free": int(free_avail.value),
            "model": info["model"] or info["vendor"] or "未知设备",
            "vendor": info["vendor"],
            "bus": BUS_NAMES.get(info["bus"], "总线%d" % info["bus"]),
        }
    out = []
    for rec in seen.values():
        rec["display_letter"] = ",".join("%s:" % x for x in rec["letters"])
        out.append(rec)
    out.sort(key=lambda r: r["disk"])
    return out


def letters_on_disk(disk_number: int):
    """列出某个物理磁盘上所有已挂载的盘符。"""
    mask = kernel32.GetLogicalDrives()
    letters = []
    for i in range(26):
        if not (mask & (1 << i)):
            continue
        letter = chr(ord("A") + i)
        if physical_drive_of_letter(letter) == disk_number:
            letters.append(letter)
    return letters


# ---- 写入 ---------------------------------------------------------------
class WriteError(Exception):
    pass


def _lock_and_dismount(disk_number: int):
    """锁定并卸载该磁盘上的所有卷，返回保持打开的句柄列表。"""
    handles = []
    for letter in letters_on_disk(disk_number):
        h = _open_device("\\\\.\\%s:" % letter, write=True)
        if h is None:
            continue
        _ioctl(h, FSCTL_ALLOW_EXTENDED_DASD_IO)
        locked = False
        for _ in range(20):
            ok, _ = _ioctl(h, FSCTL_LOCK_VOLUME)
            if ok:
                locked = True
                break
            time.sleep(0.25)
        _ioctl(h, FSCTL_DISMOUNT_VOLUME)
        handles.append(h)
    return handles


def write_image(disk_number: int, source, progress_cb=None, cancel_cb=None,
                verify: bool = False):
    """把镜像原始字节写入物理磁盘。

    source 需提供 open()/size；progress_cb(done, total, bps, eta) 会被周期性调用；
    cancel_cb() 返回真值时中止（会抛出 WriteError('cancelled')）。
    """
    path = "\\\\.\\PhysicalDrive%d" % disk_number
    total = int(source.size)
    if total <= 0:
        raise WriteError("镜像大小无效")

    locked = _lock_and_dismount(disk_number)
    h = _open_device(path, write=True, share=False)
    if h is None:
        for lh in locked:
            kernel32.CloseHandle(lh)
        err = ctypes.get_last_error()
        raise WriteError("无法打开 %s（错误码 %d）。请确认已用管理员身份运行，"
                         "且该磁盘未被其他程序占用。" % (path, err))

    done = 0
    started = time.time()
    try:
        src = source.open()
        buf = ctypes.create_string_buffer(4 * 1024 * 1024)
        mv = memoryview(buf)
        while done < total:
            if cancel_cb is not None and cancel_cb():
                raise WriteError("cancelled")
            chunk = src.read(len(buf))
            if not chunk:
                break
            written = wintypes.DWORD(0)
            ok = kernel32.WriteFile(h, chunk, len(chunk), ctypes.byref(written), None)
            if not ok:
                err = ctypes.get_last_error()
                raise WriteError("写入失败（错误码 %d）。请检查 U 盘是否处于写保护状态，"
                                 "或换一个 USB 接口重试。" % err)
            done += int(written.value)
            if progress_cb is not None:
                elapsed = max(time.time() - started, 1e-6)
                bps = done / elapsed
                eta = (total - done) / bps if bps > 0 else 0
                progress_cb(done, total, bps, eta)
        try:
            kernel32.FlushFileBuffers(h)
        except Exception:
            pass
    finally:
        try:
            src.close()
        except Exception:
            pass
        kernel32.CloseHandle(h)
        for lh in locked:
            kernel32.CloseHandle(lh)

    # 通知系统刷新分区表
    h2 = _open_device(path, write=True)
    if h2 is not None:
        _ioctl(h2, IOCTL_DISK_UPDATE_PROPERTIES)
        kernel32.CloseHandle(h2)
    return done


def extract_image(source, dest_path: str, progress_cb=None, cancel_cb=None):
    """把镜像释放成磁盘上的一个 .iso 文件。"""
    total = int(source.size)
    done = 0
    started = time.time()
    src = source.open()
    try:
        with open(dest_path, "wb") as fp:
            while True:
                if cancel_cb is not None and cancel_cb():
                    raise WriteError("cancelled")
                chunk = src.read(4 * 1024 * 1024)
                if not chunk:
                    break
                fp.write(chunk)
                done += len(chunk)
                if progress_cb is not None:
                    elapsed = max(time.time() - started, 1e-6)
                    bps = done / elapsed
                    eta = (total - done) / bps if bps > 0 else 0
                    progress_cb(done, total, bps, eta)
    finally:
        try:
            src.close()
        except Exception:
            pass
    return done


def flush_volume_cache(disk_number: int):
    for letter in letters_on_disk(disk_number):
        h = _open_device("\\\\.\\%s:" % letter, write=True)
        if h is not None:
            try:
                kernel32.FlushFileBuffers(h)
            finally:
                kernel32.CloseHandle(h)
