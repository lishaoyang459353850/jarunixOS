# -*- coding: utf-8 -*-
# jarunixOS 安装向导 —— 界面
# Copyright (C) 2026 jarunixOS Project
# SPDX-License-Identifier: GPL-3.0-or-later
#
# 本程序是自由软件：你可以依据自由软件基金会发布的 GNU 通用公共许可证
# （第 3 版或任何更高版本）的条款重新发布和/或修改它。

"""Windows 安装程序风格的向导界面。

流程：欢迎 → 选择版本 → 选择释放位置 → 确认 → 写入 → 完成
"""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import disks
import editions as ed

# ---- 视觉常量 ------------------------------------------------------------
SIDEBAR_W = 190
WIN_W, WIN_H = 880, 600

C_SIDEBAR_TOP = (10, 32, 74)
C_SIDEBAR_BOT = (18, 78, 140)
C_BG = "#ffffff"
C_TITLE = "#101418"
C_TEXT = "#2b3138"
C_MUTED = "#6b7480"
C_ACCENT = "#0a63c9"
C_ACCENT_DK = "#084f9f"
C_CARD = "#f4f7fb"
C_CARD_SEL = "#e3efff"
C_BORDER = "#d5dde6"
C_BORDER_SEL = "#0a63c9"
C_DANGER = "#b42318"
C_OK = "#067647"

FONT = "Microsoft YaHei UI"
F_UI = (FONT, 10)
F_SMALL = (FONT, 9)
F_TITLE = (FONT, 18, "bold")
F_H2 = (FONT, 12, "bold")
F_MONO = ("Consolas", 9)


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


class Wizard(tk.Tk):
    PAGE_NAMES = ["欢迎", "选择版本", "选择释放位置", "确认", "写入", "完成"]

    def __init__(self):
        super().__init__()
        self.title("jarunixOS 安装向导")
        self.configure(bg=C_BG)
        self.resizable(False, False)
        self._center(WIN_W, WIN_H)
        setup_styles(self)

        # 状态
        self.embedded_index = ed.read_embedded_index()
        self.edition = ed.EDITION_BY_KEY["personal"]
        self.mode = tk.StringVar(value="usb")          # usb | folder
        self.disk_choice = tk.StringVar(value="")
        self.folder_path = tk.StringVar(value="")
        self.user_image = tk.StringVar(value="")
        self.confirm_ok = tk.BooleanVar(value=False)
        self.disks_cache = []

        self.worker = None
        self.q = queue.Queue()
        self.cancel_flag = threading.Event()
        self.writing = False
        self.result = {}

        self._build_layout()
        self.show_page(0)
        self.after(80, self._drain_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, max(0, (sh - h) // 2 - 20)))

    def _build_layout(self):
        self.sidebar = tk.Canvas(self, width=SIDEBAR_W, height=WIN_H,
                                 highlightthickness=0, bd=0)
        self.sidebar.place(x=0, y=0, width=SIDEBAR_W, height=WIN_H)
        self._paint_sidebar()

        self.body = tk.Frame(self, bg=C_BG)
        self.body.place(x=SIDEBAR_W, y=0, width=WIN_W - SIDEBAR_W, height=WIN_H)

        # 底部按钮栏
        self.nav = tk.Frame(self.body, bg="#f0f3f7", height=62)
        self.nav.pack(side="bottom", fill="x")
        self.nav.pack_propagate(False)
        tk.Frame(self.nav, bg=C_BORDER, height=1).pack(side="top", fill="x")

        self.btn_cancel = ttk.Button(self.nav, text="取消", width=11,
                                     command=self._on_close, style="Nav.TButton")
        self.btn_cancel.pack(side="right", padx=(6, 14), pady=14)
        self.btn_next = ttk.Button(self.nav, text="下一步 >", width=13,
                                   command=self._next, style="Accent.TButton")
        self.btn_next.pack(side="right", padx=6, pady=14)
        self.btn_back = ttk.Button(self.nav, text="< 上一步", width=11,
                                   command=self._back, style="Nav.TButton")
        self.btn_back.pack(side="right", padx=6, pady=14)

        # 页面容器
        self.stage = tk.Frame(self.body, bg=C_BG)
        self.stage.pack(side="top", fill="both", expand=True)

        self.pages = [
            self._page_welcome(),
            self._page_edition(),
            self._page_target(),
            self._page_confirm(),
            self._page_progress(),
            self._page_done(),
        ]

    def _paint_sidebar(self):
        cv = self.sidebar
        for y in range(WIN_H):
            cv.create_line(0, y, SIDEBAR_W, y,
                           fill=_hex(_lerp(C_SIDEBAR_TOP, C_SIDEBAR_BOT, y / float(WIN_H))))
        # 品牌区
        cv.create_oval(28, 40, 88, 100, fill="#1f6fd0", outline="")
        cv.create_text(58, 70, text="J", fill="white",
                       font=("Segoe UI", 26, "bold"))
        cv.create_text(28, 118, text="jarunixOS", anchor="w", fill="white",
                       font=("Segoe UI", 15, "bold"))
        cv.create_text(28, 140, text="%s · %s" % (ed.APP_VERSION, ed.APP_CODENAME),
                       anchor="w", fill="#9dc4ee", font=("Segoe UI", 9))

        steps = ["欢迎", "选择版本", "选择释放位置", "确认设置", "写入", "完成"]
        self._side_items = []
        y = 200
        for i, s in enumerate(steps):
            dot = cv.create_oval(28, y - 5, 38, y + 5, fill="#2d4a72", outline="")
            txt = cv.create_text(50, y, text=s, anchor="w", fill="#8fa8c6",
                                 font=(FONT, 10))
            self._side_items.append((dot, txt))
            y += 34
        cv.create_text(28, WIN_H - 30, text="GPL-3.0 开源", anchor="w",
                       fill="#7f9cc0", font=(FONT, 8))

    def _paint_steps(self, current):
        for i, (dot, txt) in enumerate(self._side_items):
            if i < current:
                self.sidebar.itemconfig(dot, fill="#4fae6a")
                self.sidebar.itemconfig(txt, fill="#c8dbf0")
            elif i == current:
                self.sidebar.itemconfig(dot, fill="#ffffff")
                self.sidebar.itemconfig(txt, fill="#ffffff")
            else:
                self.sidebar.itemconfig(dot, fill="#2d4a72")
                self.sidebar.itemconfig(txt, fill="#8fa8c6")

    # ------------------------------------------------------------------
    def _new_page(self):
        f = tk.Frame(self.stage, bg=C_BG)
        f.place(x=0, y=0, relwidth=1, relheight=1)
        return f

    def _head(self, page, title, desc):
        tk.Label(page, text=title, bg=C_BG, fg=C_TITLE, font=F_TITLE,
                 anchor="w").pack(fill="x", padx=30, pady=(26, 4))
        tk.Label(page, text=desc, bg=C_BG, fg=C_MUTED, font=F_UI,
                 anchor="w", justify="left", wraplength=WIN_W - SIDEBAR_W - 70
                 ).pack(fill="x", padx=30)
        tk.Frame(page, bg=C_BORDER, height=1).pack(fill="x", padx=30, pady=(16, 0))

    # ---- 第 1 页：欢迎 --------------------------------------------------
    def _page_welcome(self):
        p = self._new_page()
        self._head(p, "欢迎使用 jarunixOS 安装向导",
                   "本向导将把 %s 的镜像释放到您指定的位置。" % ed.APP_NAME)

        box = tk.Frame(p, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1)
        box.pack(fill="x", padx=30, pady=18)
        tk.Label(box, text="您可以选择两种释放方式", bg=C_CARD, fg=C_TITLE,
                 font=F_H2, anchor="w").pack(fill="x", padx=16, pady=(12, 6))
        for t, d in [
            ("制作 USB 启动盘",
             "把镜像原始写入 U 盘，做成可直接开机启动的安装盘。U 盘上的原有数据将被全部清空。"),
            ("释放镜像文件到文件夹",
             "把所选版本的 .iso 文件复制到您指定的文件夹，供虚拟机、光盘刻录或其他工具使用。"),
        ]:
            row = tk.Frame(box, bg=C_CARD)
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text="·", bg=C_CARD, fg=C_ACCENT, font=(FONT, 11, "bold")
                     ).pack(side="left", anchor="n")
            tk.Label(row, text=t, bg=C_CARD, fg=C_TITLE, font=(FONT, 10, "bold"),
                     anchor="w").pack(side="left", anchor="n")
            tk.Label(row, text=" " + d, bg=C_CARD, fg=C_MUTED, font=F_SMALL,
                     anchor="w", justify="left",
                     wraplength=WIN_W - SIDEBAR_W - 120).pack(side="left", anchor="n")

        tk.Label(box, text="", bg=C_CARD).pack(pady=4)

        foot = tk.Frame(p, bg=C_BG)
        foot.pack(fill="x", padx=30)
        tk.Label(foot, text="继续之前，请关闭所有正在使用目标 U 盘的程序。",
                 bg=C_BG, fg=C_DANGER, font=F_SMALL, anchor="w").pack(fill="x")
        tk.Label(foot, text="本程序为自由软件，以 GPL-3.0 许可发布，不提供任何担保。",
                 bg=C_BG, fg=C_MUTED, font=F_SMALL, anchor="w").pack(fill="x", pady=(4, 0))
        return p

    # ---- 第 2 页：选择版本 ----------------------------------------------
    def _page_edition(self):
        p = self._new_page()
        self._head(p, "选择要释放的版本",
                   "两个版本都基于 Debian 13（trixie）与 Linux 6.12 LTS 内核，"
                   "并且都内置 Java 运行库与图形化桌面。")

        self.edition_cards = {}
        wrap = tk.Frame(p, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=30, pady=16)

        for e in ed.EDITIONS:
            card = tk.Frame(wrap, bg=C_CARD, highlightbackground=C_BORDER,
                            highlightthickness=1, cursor="hand2")
            card.pack(fill="x", pady=(0, 12))

            top = tk.Frame(card, bg=C_CARD)
            top.pack(fill="x", padx=16, pady=(12, 2))
            rb = tk.Radiobutton(top, variable=self._edition_var_holder(),
                                value=e["key"], command=self._on_edition,
                                bg=C_CARD, activebackground=C_CARD, bd=0,
                                highlightthickness=0)
            rb.pack(side="left")
            name = tk.Label(top, text=e["name"], bg=C_CARD, fg=C_TITLE,
                            font=(FONT, 13, "bold"))
            name.pack(side="left")
            tk.Label(top, text="  " + e["subtitle"], bg=C_CARD, fg=C_MUTED,
                     font=F_SMALL).pack(side="left")
            tk.Label(top, text=ed.format_size(e["size"]) + "  ", bg=C_CARD,
                     fg=C_ACCENT, font=(FONT, 10, "bold")).pack(side="right")

            tk.Label(card, text=e["summary"], bg=C_CARD, fg=C_TEXT, font=F_UI,
                     anchor="w").pack(fill="x", padx=16)
            for b in e["bullets"]:
                tk.Label(card, text="· " + b, bg=C_CARD, fg=C_MUTED, font=F_SMALL,
                         anchor="w").pack(fill="x", padx=30)

            tk.Label(card, text="文件名：%s" % e["filename"], bg=C_CARD, fg=C_MUTED,
                     font=F_MONO, anchor="w").pack(fill="x", padx=16, pady=(4, 12))

            self.edition_cards[e["key"]] = (card, rb, name)
            for w in (card, top, name):
                w.bind("<Button-1>", lambda ev, k=e["key"]: self._pick_edition(k))

        # 镜像来源提示
        self.src_hint = tk.Label(p, text="", bg=C_BG, fg=C_MUTED, font=F_SMALL,
                                 anchor="w")
        self.src_hint.pack(fill="x", padx=30, pady=(0, 8))
        return p

    def _edition_var_holder(self):
        if not hasattr(self, "_ed_var"):
            self._ed_var = tk.StringVar(value=self.edition["key"])
        return self._ed_var

    def _pick_edition(self, key):
        self._ed_var.set(key)
        self._on_edition()

    def _on_edition(self):
        self.edition = ed.EDITION_BY_KEY[self._ed_var.get()]
        for k, (card, rb, name) in self.edition_cards.items():
            sel = (k == self.edition["key"])
            bg = C_CARD_SEL if sel else C_CARD
            card.configure(bg=bg, highlightbackground=C_BORDER_SEL if sel else C_BORDER,
                           highlightthickness=2 if sel else 1)
            for w in card.winfo_children():
                try:
                    w.configure(bg=bg)
                    for c in w.winfo_children():
                        c.configure(bg=bg)
                except Exception:
                    pass
            rb.configure(bg=bg, activebackground=bg)
        self._refresh_source_hint()
        self._refresh_disks_if_needed()

    def _refresh_source_hint(self):
        src = self._current_source()
        if src.kind == "missing":
            self.src_hint.configure(
                text="⚠ 未找到 %s 的镜像数据，请在下一步手动指定 .iso 文件。" %
                     self.edition["name"], fg=C_DANGER)
        else:
            self.src_hint.configure(
                text="镜像来源：%s（%s）" % (src.label, ed.format_size(src.size)),
                fg=C_OK)

    # ---- 第 3 页：选择释放位置 ------------------------------------------
    def _page_target(self):
        p = self._new_page()
        self._head(p, "选择释放位置",
                   "请选择要把所选版本释放到哪里。")

        modebox = tk.Frame(p, bg=C_BG)
        modebox.pack(fill="x", padx=30, pady=(14, 4))
        for val, text, sub in [
            ("usb", "制作 USB 启动盘", "写入 U 盘，做成可开机启动的安装盘"),
            ("folder", "释放镜像文件到文件夹", "导出 .iso 文件到指定目录"),
        ]:
            row = tk.Frame(modebox, bg=C_BG)
            row.pack(fill="x", pady=2)
            rb = tk.Radiobutton(row, text=text, variable=self.mode, value=val,
                                command=self._on_mode, bg=C_BG, fg=C_TITLE,
                                activebackground=C_BG, font=(FONT, 10, "bold"),
                                bd=0, highlightthickness=0, anchor="w")
            rb.pack(side="left")
            tk.Label(row, text="   " + sub, bg=C_BG, fg=C_MUTED,
                     font=F_SMALL).pack(side="left")

        tk.Frame(p, bg=C_BORDER, height=1).pack(fill="x", padx=30, pady=(12, 0))

        # ---- U 盘面板 ----
        self.panel_usb = tk.Frame(p, bg=C_BG)
        self.panel_usb.pack(fill="both", expand=True, padx=30, pady=12)
        bar = tk.Frame(self.panel_usb, bg=C_BG)
        bar.pack(fill="x")
        tk.Label(bar, text="检测到的可移动磁盘", bg=C_BG, fg=C_TITLE,
                 font=F_H2).pack(side="left")
        ttk.Button(bar, text="刷新", width=8, command=self._refresh_disks,
                   style="Nav.TButton").pack(side="right")

        cols = ("letter", "label", "size", "model")
        self.disk_tree = ttk.Treeview(self.panel_usb, columns=cols, show="headings",
                                      height=6, selectmode="browse")
        for c, t, w in [("letter", "盘符", 90), ("label", "卷标", 130),
                        ("size", "容量", 110), ("model", "设备型号", 300)]:
            self.disk_tree.heading(c, text=t)
            self.disk_tree.column(c, width=w, anchor="w")
        self.disk_tree.pack(fill="both", expand=True, pady=(8, 0))
        self.disk_tree.bind("<<TreeviewSelect>>", self._on_disk_select)

        self.usb_msg = tk.Label(self.panel_usb, text="", bg=C_BG, fg=C_MUTED,
                                font=F_SMALL, anchor="w", justify="left",
                                wraplength=WIN_W - SIDEBAR_W - 70)
        self.usb_msg.pack(fill="x", pady=(8, 0))

        # ---- 文件夹面板 ----
        self.panel_folder = tk.Frame(p, bg=C_BG)
        tk.Label(self.panel_folder, text="目标文件夹", bg=C_BG, fg=C_TITLE,
                 font=F_H2, anchor="w").pack(fill="x")
        row = tk.Frame(self.panel_folder, bg=C_BG)
        row.pack(fill="x", pady=(8, 0))
        ent = tk.Entry(row, textvariable=self.folder_path, font=F_UI,
                       relief="solid", bd=1, bg="white")
        ent.pack(side="left", fill="x", expand=True, ipady=5)
        ttk.Button(row, text="浏览...", width=9, command=self._choose_folder,
                   style="Nav.TButton").pack(side="left", padx=(8, 0))
        self.folder_msg = tk.Label(self.panel_folder, text="", bg=C_BG, fg=C_MUTED,
                                   font=F_SMALL, anchor="w", justify="left",
                                   wraplength=WIN_W - SIDEBAR_W - 70)
        self.folder_msg.pack(fill="x", pady=(10, 0))

        # ---- 高级：手动指定镜像 ----
        adv = tk.Frame(p, bg=C_BG)
        adv.pack(fill="x", padx=30, pady=(0, 10))
        r2 = tk.Frame(adv, bg=C_BG)
        r2.pack(fill="x")
        tk.Label(r2, text="镜像文件", bg=C_BG, fg=C_MUTED,
                 font=F_SMALL).pack(side="left")
        e2 = tk.Entry(r2, textvariable=self.user_image, font=F_MONO,
                      relief="solid", bd=1, bg="white")
        e2.pack(side="left", fill="x", expand=True, padx=8, ipady=3)
        ttk.Button(r2, text="浏览...", width=9, command=self._choose_image,
                   style="Nav.TButton").pack(side="left")
        self.img_msg = tk.Label(adv, text="", bg=C_BG, fg=C_MUTED, font=F_SMALL,
                                anchor="w")
        self.img_msg.pack(fill="x", pady=(6, 0))
        return p

    def _on_mode(self):
        if self.mode.get() == "usb":
            self.panel_folder.pack_forget()
            self.panel_usb.pack(fill="both", expand=True, padx=30, pady=12)
            if not self.disks_cache:
                self._refresh_disks()
        else:
            self.panel_usb.pack_forget()
            self.panel_folder.pack(fill="both", expand=True, padx=30, pady=12)
            if not self.folder_path.get():
                self.folder_path.set(os.path.join(
                    os.path.expanduser("~"), "Desktop"))
            self._on_folder_change()

    def _choose_folder(self):
        d = filedialog.askdirectory(title="选择释放镜像的文件夹", mustexist=True)
        if d:
            self.folder_path.set(os.path.normpath(d))
            self._on_folder_change()

    def _on_folder_change(self):
        d = self.folder_path.get()
        target = os.path.join(d, self.edition["filename"])
        if not d:
            self.folder_msg.configure(text="", fg=C_MUTED)
        elif not os.path.isdir(d):
            self.folder_msg.configure(text="⚠ 文件夹不存在", fg=C_DANGER)
        else:
            try:
                free = _free_space(d)
                need = self._current_source().size or self.edition["size"]
                if free and free < need:
                    self.folder_msg.configure(
                        text="⚠ 空间不足：需要 %s，可用 %s" %
                             (ed.format_size(need), ed.format_size(free)), fg=C_DANGER)
                else:
                    self.folder_msg.configure(
                        text="将写入：%s" % target, fg=C_MUTED)
            except Exception:
                self.folder_msg.configure(text="将写入：%s" % target, fg=C_MUTED)

    def _choose_image(self):
        f = filedialog.askopenfilename(
            title="选择 %s 的镜像文件" % self.edition["name"],
            filetypes=[("光盘镜像", "*.iso"), ("全部文件", "*.*")])
        if f:
            self.user_image.set(os.path.normpath(f))
            self._on_image_change()

    def _on_image_change(self):
        f = self.user_image.get()
        if f and os.path.isfile(f):
            self.img_msg.configure(text="已指定：%s" % ed.format_size(os.path.getsize(f)),
                                   fg=C_OK)
        elif f:
            self.img_msg.configure(text="⚠ 文件不存在", fg=C_DANGER)
        else:
            self.img_msg.configure(text="留空则使用安装程序内置的镜像。", fg=C_MUTED)
        self._refresh_source_hint()
        self._refresh_disks_if_needed()

    def _refresh_disks_if_needed(self):
        if self.mode.get() == "usb" and not self.disks_cache:
            self._refresh_disks()

    def _refresh_disks(self):
        self.disk_tree.delete(*self.disk_tree.get_children())
        self.disks_cache = disks.list_removable_disks()
        need = self._current_source().size or self.edition["size"]
        for d in self.disks_cache:
            iid = "disk%d" % d["disk"]
            self.disk_tree.insert("", "end", iid=iid, values=(
                d["display_letter"], d["label"] or "(无卷标)",
                ed.format_size(d["total"]), d["model"]))
            if d["total"] < need:
                self.disk_tree.item(iid, tags=("small",))
        self.disk_tree.tag_configure("small", foreground="#a0a6ad")
        if not self.disks_cache:
            self.usb_msg.configure(
                text="⚠ 没有检测到可移动磁盘。请插入 U 盘后点击「刷新」。"
                     "若已插入仍看不到，请尝试换一个 USB 接口。", fg=C_DANGER)
        else:
            self.usb_msg.configure(
                text="共检测到 %d 个可移动磁盘。灰色条目容量小于所选镜像，无法使用。"
                     % len(self.disks_cache), fg=C_MUTED)
        if self.disk_choice.get() and self.disk_choice.get() not in \
                ["disk%d" % d["disk"] for d in self.disks_cache]:
            self.disk_choice.set("")

    def _on_disk_select(self, _ev=None):
        sel = self.disk_tree.selection()
        self.disk_choice.set(sel[0] if sel else "")
        self._validate_target()

    def _validate_target(self):
        if self.mode.get() == "usb":
            iid = self.disk_choice.get()
            if not iid:
                return False, "请选择一个目标 U 盘。"
            rec = self._disk_by_iid(iid)
            if rec is None:
                return False, "所选磁盘已不可用，请刷新后重试。"
            need = self._current_source().size or self.edition["size"]
            if rec["total"] < need:
                return False, "该磁盘容量 %s，小于镜像所需的 %s。" % (
                    ed.format_size(rec["total"]), ed.format_size(need))
            return True, ""
        d = self.folder_path.get()
        if not d:
            return False, "请选择目标文件夹。"
        if not os.path.isdir(d):
            return False, "目标文件夹不存在。"
        return True, ""

    def _disk_by_iid(self, iid):
        for d in self.disks_cache:
            if "disk%d" % d["disk"] == iid:
                return d
        return None

    # ---- 第 4 页：确认 --------------------------------------------------
    def _page_confirm(self):
        p = self._new_page()
        self._head(p, "确认设置", "请核对以下信息，然后点击「开始」。")

        box = tk.Frame(p, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1)
        box.pack(fill="x", padx=30, pady=16)
        self.summary = tk.Label(box, text="", bg=C_CARD, fg=C_TEXT, font=F_UI,
                                anchor="w", justify="left",
                                wraplength=WIN_W - SIDEBAR_W - 100)
        self.summary.pack(fill="x", padx=18, pady=16)

        warn = tk.Frame(p, bg=C_BG)
        warn.pack(fill="x", padx=30)
        self.warn_label = tk.Label(warn, text="", bg=C_BG, fg=C_DANGER,
                                   font=(FONT, 10, "bold"), anchor="w",
                                   justify="left",
                                   wraplength=WIN_W - SIDEBAR_W - 70)
        self.warn_label.pack(fill="x")

        self.chk = tk.Checkbutton(
            p, text="我已知悉：目标 U 盘上的全部数据将被永久清除，且无法恢复。",
            variable=self.confirm_ok, command=self._update_nav,
            bg=C_BG, fg=C_TEXT, activebackground=C_BG, font=F_UI,
            anchor="w", justify="left", bd=0, highlightthickness=0)
        self.chk.pack(fill="x", padx=28, pady=(14, 0))
        self.chk_folder = tk.Label(p, text="", bg=C_BG, fg=C_MUTED, font=F_SMALL,
                                   anchor="w")
        return p

    def _refresh_confirm(self):
        e = self.edition
        src = self._current_source()
        lines = [
            "版本：%s（%s）" % (e["name"], e["subtitle"]),
            "镜像文件：%s" % e["filename"],
            "镜像大小：%s" % ed.format_size(src.size or e["size"]),
            "镜像来源：%s" % src.label,
        ]
        if self.mode.get() == "usb":
            rec = self._disk_by_iid(self.disk_choice.get())
            if rec:
                lines += [
                    "",
                    "释放方式：制作 USB 启动盘",
                    "目标磁盘：物理磁盘 %d（%s）" % (rec["disk"], rec["model"]),
                    "目标盘符：%s    容量：%s" % (rec["display_letter"],
                                                 ed.format_size(rec["total"])),
                ]
            self.warn_label.configure(
                text="⚠ 即将清空 物理磁盘 %d（%s）上的全部数据，请再次确认这是您的 U 盘。" %
                     (rec["disk"], rec["display_letter"]) if rec else "")
            self.chk.pack(fill="x", padx=28, pady=(14, 0))
            self.chk_folder.pack_forget()
        else:
            lines += [
                "",
                "释放方式：释放镜像文件到文件夹",
                "目标文件夹：%s" % self.folder_path.get(),
                "生成文件：%s" % os.path.join(self.folder_path.get(),
                                              e["filename"]),
            ]
            self.warn_label.configure(text="")
            self.chk.pack_forget()
            self.chk_folder.pack(fill="x", padx=30, pady=(16, 0))
            self.chk_folder.configure(
                text="如果目标文件夹里已有同名文件，将被覆盖。", fg=C_MUTED)
        self.summary.configure(text="\n".join(lines))

    # ---- 第 5 页：写入 --------------------------------------------------
    def _page_progress(self):
        p = self._new_page()
        self._head(p, "正在释放镜像", "请不要拔出设备或关闭本窗口。")

        self.pbar = ttk.Progressbar(p, mode="determinate", maximum=1000,
                                    style="Wiz.Horizontal.TProgressbar")
        self.pbar.pack(fill="x", padx=30, pady=(24, 8))

        row = tk.Frame(p, bg=C_BG)
        row.pack(fill="x", padx=30)
        self.lb_pct = tk.Label(row, text="0%", bg=C_BG, fg=C_ACCENT,
                               font=(FONT, 14, "bold"), anchor="w")
        self.lb_pct.pack(side="left")
        self.lb_stat = tk.Label(row, text="", bg=C_BG, fg=C_MUTED, font=F_SMALL,
                                anchor="e")
        self.lb_stat.pack(side="right")

        self.log = tk.Text(p, height=9, font=F_MONO, bg="#0f1a26", fg="#c8e1ff",
                           relief="flat", wrap="none")
        self.log.pack(fill="both", expand=True, padx=30, pady=(14, 18))
        self.log.configure(state="disabled")
        return p

    # ---- 第 6 页：完成 --------------------------------------------------
    def _page_done(self):
        p = self._new_page()
        self._head(p, "完成", "所选版本已经释放到您指定的位置。")
        self.done_label = tk.Label(p, text="", bg=C_BG, fg=C_TEXT, font=F_UI,
                                   anchor="w", justify="left",
                                   wraplength=WIN_W - SIDEBAR_W - 70)
        self.done_label.pack(fill="x", padx=30, pady=20)
        self.done_extra = tk.Label(p, text="", bg=C_BG, fg=C_MUTED, font=F_SMALL,
                                   anchor="w", justify="left",
                                   wraplength=WIN_W - SIDEBAR_W - 70)
        self.done_extra.pack(fill="x", padx=30)
        return p

    # ------------------------------------------------------------------
    def _current_source(self):
        return ed.resolve_source(self.edition, self.embedded_index,
                                 self.user_image.get())

    def show_page(self, i):
        self.page_index = i
        for j, pg in enumerate(self.pages):
            if j == i:
                pg.tkraise()
            pg.lower() if j != i else None
        self.pages[i].tkraise()
        self._paint_steps(i)
        if i == 2:
            self._on_mode()
        if i == 3:
            self.confirm_ok.set(False)
            self._refresh_confirm()
        self._update_nav()

    def _update_nav(self):
        i = self.page_index
        self.btn_back.configure(state="normal" if 0 < i < 4 else "disabled")
        self.btn_cancel.configure(text="取消" if i != 4 else "中止")

        if i == 0:
            self.btn_next.configure(text="下一步 >", state="normal")
        elif i == 1:
            ok = self._current_source().kind != "missing"
            self.btn_next.configure(text="下一步 >", state="normal" if ok else "disabled")
        elif i == 2:
            ok, _ = self._validate_target()
            self.btn_next.configure(text="下一步 >", state="normal" if ok else "disabled")
        elif i == 3:
            need = (self.mode.get() == "folder") or self.confirm_ok.get()
            self.btn_next.configure(text="开始", state="normal" if need else "disabled")
        elif i == 4:
            self.btn_next.configure(text="开始", state="disabled")
        else:
            self.btn_next.configure(text="完成", state="normal")

    def _next(self):
        i = self.page_index
        if i == 0:
            self.show_page(1)
        elif i == 1:
            self.show_page(2)
        elif i == 2:
            ok, msg = self._validate_target()
            if not ok:
                messagebox.showwarning("无法继续", msg, parent=self)
                return
            self.show_page(3)
        elif i == 3:
            self._start()
        elif i == 5:
            self._on_close()

    def _back(self):
        if self.page_index in (2, 3):
            self.show_page(self.page_index - 1)

    # ------------------------------------------------------------------
    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self):
        src = self._current_source()
        if not src.readable():
            messagebox.showerror("镜像不可用",
                                 "没有找到可用的镜像数据，请返回上一步指定 .iso 文件。",
                                 parent=self)
            self.show_page(2)
            return

        self.writing = True
        self.cancel_flag.clear()
        self.pbar.configure(value=0)
        self.lb_pct.configure(text="0%")
        self.lb_stat.configure(text="")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.show_page(4)

        if self.mode.get() == "usb":
            rec = self._disk_by_iid(self.disk_choice.get())
            self._log("目标：物理磁盘 %d（%s）%s" %
                      (rec["disk"], rec["model"], rec["display_letter"]))
            self._log("镜像：%s  %s" % (self.edition["filename"],
                                       ed.format_size(src.size)))
            self._log("开始写入…")
            self.worker = threading.Thread(target=self._run_usb, args=(rec, src),
                                           daemon=True)
        else:
            dest = os.path.join(self.folder_path.get(), self.edition["filename"])
            self._log("目标：%s" % dest)
            self._log("镜像：%s  %s" % (self.edition["filename"],
                                       ed.format_size(src.size)))
            self._log("开始释放…")
            self.worker = threading.Thread(target=self._run_folder, args=(src, dest),
                                           daemon=True)
        self.worker.start()

    def _progress(self, done, total, bps, eta):
        self.q.put(("progress", done, total, bps, eta))

    def _run_usb(self, rec, src):
        try:
            disks.write_image(rec["disk"], src,
                              progress_cb=self._progress,
                              cancel_cb=self.cancel_flag.is_set)
            self.q.put(("done", "usb", rec))
        except disks.WriteError as ex:
            self.q.put(("error", str(ex)))
        except Exception as ex:  # noqa: BLE001
            self.q.put(("error", "%s: %s" % (type(ex).__name__, ex)))

    def _run_folder(self, src, dest):
        try:
            disks.extract_image(src, dest, progress_cb=self._progress,
                                cancel_cb=self.cancel_flag.is_set)
            self.q.put(("done", "folder", dest))
        except disks.WriteError as ex:
            self.q.put(("error", str(ex)))
        except Exception as ex:  # noqa: BLE001
            self.q.put(("error", "%s: %s" % (type(ex).__name__, ex)))

    def _drain_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    _, done, total, bps, eta = msg
                    pct = done * 100.0 / total if total else 0
                    self.pbar.configure(value=pct * 10)
                    self.lb_pct.configure(text="%.1f%%" % pct)
                    self.lb_stat.configure(
                        text="%s / %s   %.1f MB/s   剩余约 %s" % (
                            ed.format_size(done), ed.format_size(total),
                            bps / 1048576.0, _fmt_eta(eta)))
                    if int(pct) % 10 == 0 and int(pct) != getattr(self, "_last_pct", -1):
                        self._last_pct = int(pct)
                        self._log("已完成 %d%%" % int(pct))
                elif kind == "done":
                    self._finish(msg[1], msg[2])
                elif kind == "error":
                    self._fail(msg[1])
        except queue.Empty:
            pass
        if not self.writing or self.page_index != 4:
            pass
        self.after(80, self._drain_queue)

    def _finish(self, mode, payload):
        self.writing = False
        self.pbar.configure(value=1000)
        self.lb_pct.configure(text="100%")
        self.lb_stat.configure(text="完成")
        if mode == "usb":
            self._log("写入完成，已通知系统刷新分区表。")
            self.done_label.configure(
                text="已完成：%s 的镜像已写入 物理磁盘 %d（%s）。" %
                     (self.edition["name"], payload["disk"], payload["display_letter"]))
            self.done_extra.configure(
                text="请安全弹出 U 盘后再拔出：\n"
                     "  1. 打开「此电脑」，右键该 U 盘 → 弹出；\n"
                     "  2. 或使用任务栏的「安全删除硬件并弹出媒体」。\n\n"
                     "开机启动：插入 U 盘，开机时按启动菜单键（常见为 F12 / F11 / ESC / F8），"
                     "选择该 U 盘即可进入 jarunixOS。")
        else:
            self._log("释放完成：%s" % payload)
            self.done_label.configure(
                text="已完成：%s 的镜像已释放到\n%s" % (self.edition["name"], payload))
            self.done_extra.configure(
                text="该 .iso 可用于虚拟机（如 VirtualBox / VMware）、光盘刻录工具"
                     "（如 Rufus / balenaEtcher），或直接在支持 ISO 引导的环境中使用。")
        self.show_page(5)

    def _fail(self, msg):
        self.writing = False
        if msg == "cancelled":
            self._log("已被用户中止。")
            self.show_page(3)
            self._update_nav()
            return
        self._log("错误：%s" % msg)
        messagebox.showerror("操作失败", msg, parent=self)
        self.show_page(3)
        self._update_nav()

    def _on_close(self):
        if self.writing:
            if not messagebox.askyesno(
                    "确认中止", "正在写入镜像，中止可能导致目标设备数据不完整。\n"
                                "确定要中止吗？", parent=self):
                return
            self.cancel_flag.set()
            return
        self.destroy()


def _fmt_eta(sec):
    try:
        sec = int(sec)
    except Exception:
        return "—"
    if sec < 60:
        return "%d 秒" % sec
    if sec < 3600:
        return "%d 分 %d 秒" % (sec // 60, sec % 60)
    return "%d 小时 %d 分" % (sec // 3600, (sec % 3600) // 60)


def _free_space(path):
    try:
        import ctypes
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        totalfree = ctypes.c_ulonglong(0)
        ok = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), ctypes.byref(free), ctypes.byref(total),
            ctypes.byref(totalfree))
        return int(free.value) if ok else 0
    except Exception:
        return 0


def setup_styles(root):
    st = ttk.Style(root)
    try:
        st.theme_use("vista")
    except Exception:
        pass
    st.configure("Nav.TButton", font=(FONT, 10), padding=(12, 6))
    st.configure("Accent.TButton", font=(FONT, 10, "bold"), padding=(14, 6))
    st.configure("Wiz.Horizontal.TProgressbar", thickness=22)
    return st
