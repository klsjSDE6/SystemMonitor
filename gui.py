"""SystemMonitor GUI - 科幻风系统监控终端.

- 近黑深蓝底 + 霓虹青/绿/紫/琥珀配色，等宽字体 + 角标装饰
- 4 个指标面板（CPU / 网络 / 磁盘IO / 磁盘使用率），各带迷你进度条
- 左侧 CPU 60s 折线图，右侧 TOP 进程实时表
- 支持暂停/恢复、采样周期可调、磁盘分区下拉切换
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections import deque

from monitor.sampler import SystemSampler, Sample


# ------------------------------------------------------------------ 科幻配色

COLOR_BG = "#05080f"          # 深空黑
COLOR_PANEL = "#0b1120"       # 面板底
COLOR_EDGE = "#1b2b47"        # 面板描边
COLOR_GRID = "#122036"        # 网格线
COLOR_TEXT = "#d8f4ff"        # 主文字（冰蓝白）
COLOR_MUTED = "#5b7392"       # 次要文字
COLOR_CPU = "#00e5ff"         # 霓虹青
COLOR_NET = "#39ff88"         # 霓虹绿
COLOR_IO = "#b366ff"          # 霓虹紫
COLOR_DISK = "#ffb454"        # 琥珀
COLOR_DANGER = "#ff3d71"      # 警戒红

FONT_NUM = ("Consolas", 26, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_S = ("Consolas", 9)
FONT_UI = ("Microsoft YaHei", 10)

GRAPH_SECONDS = 60
SAMPLE_INTERVAL_MS = 1000


# ------------------------------------------------------------------ 迷你进度条

class NeonBar(tk.Canvas):
    """单条霓虹进度条：暗色轨道 + 亮色填充 + 末端亮点."""

    def __init__(self, master, color: str, height: int = 6) -> None:
        super().__init__(master, height=height, bg=COLOR_PANEL,
                         highlightthickness=0)
        self.color = color
        self._track = "#0f1a2e"
        self.value = 0.0
        self.bind("<Configure>", lambda _e: self._draw())

    def set(self, v: float) -> None:
        self.value = min(max(v, 0.0), 100.0)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        self.create_rectangle(0, 0, w, h, fill=self._track, outline="")
        fw = int(w * self.value / 100)
        if fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=self.color, outline="")
            # 末端亮点模拟"发光"
            self.create_rectangle(fw - 2, 0, fw, h, fill=COLOR_TEXT, outline="")


# ------------------------------------------------------------------ 指标面板

class MetricPanel(tk.Frame):
    """科幻指标面板：角标标题 + 大号霓虹数值 + 迷你进度条 + 副信息."""

    def __init__(self, master, code: str, title: str, accent: str) -> None:
        super().__init__(master, bg=COLOR_PANEL,
                         highlightbackground=COLOR_EDGE, highlightthickness=1)
        self.accent = accent

        # 顶部装饰条
        tk.Frame(self, bg=accent, height=2).pack(fill="x")

        head = tk.Frame(self, bg=COLOR_PANEL)
        head.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(head, text=f"◢ {code}", fg=accent, bg=COLOR_PANEL,
                 font=FONT_MONO_S).pack(side="left")
        tk.Label(head, text=title, fg=COLOR_MUTED, bg=COLOR_PANEL,
                 font=FONT_MONO_S).pack(side="right")

        self.value_lbl = tk.Label(self, text="--", fg=accent, bg=COLOR_PANEL,
                                  font=FONT_NUM)
        self.value_lbl.pack(anchor="w", padx=10, pady=(6, 0))

        self.bar = NeonBar(self, accent)
        self.bar.pack(fill="x", padx=10, pady=(6, 0))

        self.sub_lbl = tk.Label(self, text="", fg=COLOR_MUTED, bg=COLOR_PANEL,
                                font=FONT_MONO_S, anchor="w", justify="left")
        self.sub_lbl.pack(fill="x", padx=10, pady=(4, 8))

    def update(self, value: str, sub: str = "", bar: float | None = None) -> None:
        self.value_lbl.configure(text=value)
        self.sub_lbl.configure(text=sub)
        if bar is not None:
            self.bar.set(bar)


# ------------------------------------------------------------------ 折线图

class Graph(tk.Canvas):
    """霓虹折线图：最近 N 秒 CPU 使用率."""

    def __init__(self, master) -> None:
        super().__init__(master, height=200, bg=COLOR_PANEL,
                         highlightthickness=1, highlightbackground=COLOR_EDGE)
        self.data: deque[float] = deque(maxlen=GRAPH_SECONDS)
        self.bind("<Configure>", lambda _e: self._draw())

    def push(self, value: float) -> None:
        self.data.append(min(max(value, 0.0), 100.0))
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return

        # 横向网格
        for y in (0.0, 25.0, 50.0, 75.0, 100.0):
            yp = h - 14 - (y / 100.0) * (h - 30)
            self.create_line(30, yp, w - 6, yp, fill=COLOR_GRID, dash=(2, 4))
            self.create_text(6, yp, anchor="w", text=f"{int(y):3d}%",
                             fill=COLOR_MUTED, font=FONT_MONO_S)
        # 纵向网格（每 10s 一根）
        step10 = (w - 40) / max(GRAPH_SECONDS - 1, 1) * 10
        x = 34
        while x < w - 6:
            self.create_line(x, 12, x, h - 14, fill=COLOR_GRID, dash=(1, 6))
            x += step10

        if len(self.data) >= 2:
            step_x = (w - 40) / max(GRAPH_SECONDS - 1, 1)
            points = []
            for i, v in enumerate(self.data):
                points.extend((34 + i * step_x, h - 14 - (v / 100.0) * (h - 30)))

            fill = list(points)
            fill.extend([points[-2], h - 14, points[0], h - 14])
            self.create_polygon(*fill, fill="#062a33", outline="")
            self.create_line(*points, fill=COLOR_CPU, width=2, smooth=True)
            # 末端光点
            self.create_oval(points[-2] - 3, points[-1] - 3,
                             points[-2] + 3, points[-1] + 3,
                             fill=COLOR_CPU, outline=COLOR_TEXT)

        self.create_text(w - 8, 16, anchor="e",
                         text="⟨ CPU TELEMETRY // 60s WINDOW ⟩",
                         fill=COLOR_MUTED, font=FONT_MONO_S)


# ------------------------------------------------------------------ 主窗口

class MonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.sampler = SystemSampler()
        self.running = True

        self._build_styles()
        self._build_ui()

        self.sampler.take_sample()   # 基准采样
        self._tick()

    # --------------------------------------------------------------- 样式

    def _build_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                        font=FONT_UI)
        style.configure("TButton", padding=6)
        style.configure("TCombobox", padding=3)
        style.configure("Treeview",
                        background=COLOR_PANEL, foreground=COLOR_TEXT,
                        fieldbackground=COLOR_PANEL, rowheight=22,
                        font=FONT_MONO_S, borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#101a2e", foreground=COLOR_CPU,
                        font=("Consolas", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", "#16324a")],
                  foreground=[("selected", COLOR_CPU)])

    # --------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        self.root.title("SYSMON // SYSTEM TELEMETRY TERMINAL")
        self.root.configure(bg=COLOR_BG)
        self.root.geometry("1100x680")
        self.root.minsize(980, 620)

        # ── 顶部标题条 ──
        topbar = tk.Frame(self.root, bg=COLOR_BG)
        topbar.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(topbar, text="◢◤ SYSMON", fg=COLOR_CPU, bg=COLOR_BG,
                 font=("Consolas", 16, "bold")).pack(side="left")
        tk.Label(topbar, text="  // SYSTEM TELEMETRY TERMINAL v2.0",
                 fg=COLOR_MUTED, bg=COLOR_BG, font=FONT_MONO).pack(side="left")

        self.status_lbl = tk.Label(topbar, text="● ONLINE", fg=COLOR_NET,
                                   bg=COLOR_BG, font=("Consolas", 10, "bold"))
        self.status_lbl.pack(side="right")

        # ── 工具栏 ──
        bar = tk.Frame(self.root, bg=COLOR_BG)
        bar.pack(fill="x", padx=14, pady=(2, 6))

        self.pause_btn = tk.Button(
            bar, text="⟨ PAUSE ⟩", command=self._toggle_pause,
            bg="#101a2e", fg=COLOR_CPU, activebackground="#16324a",
            activeforeground=COLOR_CPU, relief="flat",
            font=("Consolas", 10, "bold"), padx=12, cursor="hand2",
        )
        self.pause_btn.pack(side="left")

        tk.Label(bar, text="  DISK:", fg=COLOR_MUTED, bg=COLOR_BG,
                 font=FONT_MONO_S).pack(side="left")
        self.partition_var = tk.StringVar()
        self.partition_combo = ttk.Combobox(
            bar, textvariable=self.partition_var, state="readonly", width=22,
        )
        self.partition_combo.pack(side="left")

        tk.Label(bar, text="  CYCLE(ms):", fg=COLOR_MUTED, bg=COLOR_BG,
                 font=FONT_MONO_S).pack(side="left")
        self.interval_var = tk.StringVar(value="1000")
        tk.Spinbox(bar, from_=200, to=10000, increment=100, width=6,
                   textvariable=self.interval_var,
                   bg="#101a2e", fg=COLOR_TEXT, buttonbackground="#101a2e",
                   insertbackground=COLOR_CPU, relief="flat",
                   font=FONT_MONO_S).pack(side="left")

        # ── 指标面板 ──
        grid = tk.Frame(self.root, bg=COLOR_BG)
        grid.pack(fill="x", padx=14, pady=4)

        self.cpu_panel = MetricPanel(grid, "CPU", "处理器占用", COLOR_CPU)
        self.net_panel = MetricPanel(grid, "NET", "网络速率", COLOR_NET)
        self.io_panel = MetricPanel(grid, "I/O", "磁盘读写", COLOR_IO)
        self.disk_panel = MetricPanel(grid, "DSK", "磁盘使用率", COLOR_DISK)

        for i, p in enumerate((self.cpu_panel, self.net_panel,
                               self.io_panel, self.disk_panel)):
            p.grid(row=0, column=i, padx=4, sticky="nsew")
            grid.columnconfigure(i, weight=1)

        # ── 中部：左折线图 + 右进程表 ──
        mid = tk.Frame(self.root, bg=COLOR_BG)
        mid.pack(fill="both", expand=True, padx=14, pady=6)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        self.graph = Graph(mid)
        self.graph.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # 进程表容器
        proc_frame = tk.Frame(mid, bg=COLOR_PANEL,
                              highlightbackground=COLOR_EDGE,
                              highlightthickness=1)
        proc_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        phead = tk.Frame(proc_frame, bg=COLOR_PANEL)
        phead.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(phead, text="◢ PROC", fg=COLOR_DISK, bg=COLOR_PANEL,
                 font=FONT_MONO_S).pack(side="left")
        self.proc_count_lbl = tk.Label(phead, text="", fg=COLOR_MUTED,
                                       bg=COLOR_PANEL, font=FONT_MONO_S)
        self.proc_count_lbl.pack(side="right")

        cols = ("pid", "name", "cpu", "mem")
        self.proc_tree = ttk.Treeview(proc_frame, columns=cols,
                                      show="headings", height=14)
        self.proc_tree.heading("pid", text="PID")
        self.proc_tree.heading("name", text="PROCESS")
        self.proc_tree.heading("cpu", text="CPU%")
        self.proc_tree.heading("mem", text="MEM")
        self.proc_tree.column("pid", width=60, anchor="e")
        self.proc_tree.column("name", width=170, anchor="w")
        self.proc_tree.column("cpu", width=60, anchor="e")
        self.proc_tree.column("mem", width=80, anchor="e")
        vsb = ttk.Scrollbar(proc_frame, orient="vertical",
                            command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=vsb.set)
        self.proc_tree.pack(side="left", fill="both", expand=True,
                            padx=(8, 0), pady=(0, 8))
        vsb.pack(side="right", fill="y", pady=(0, 8), padx=(0, 4))

        # ── 底部状态行 ──
        self.detail = tk.Label(
            self.root, text="", fg=COLOR_MUTED, bg=COLOR_BG,
            anchor="w", justify="left", font=FONT_MONO_S,
        )
        self.detail.pack(fill="x", padx=14, pady=(2, 10))

    # --------------------------------------------------------------- 刷新

    def _toggle_pause(self) -> None:
        self.running = not self.running
        if self.running:
            self.pause_btn.configure(text="⟨ PAUSE ⟩")
            self.status_lbl.configure(text="● ONLINE", fg=COLOR_NET)
        else:
            self.pause_btn.configure(text="⟨ RESUME ⟩")
            self.status_lbl.configure(text="◌ HOLD", fg=COLOR_DANGER)

    def _tick(self) -> None:
        try:
            interval = max(200, int(self.interval_var.get() or SAMPLE_INTERVAL_MS))
        except ValueError:
            interval = SAMPLE_INTERVAL_MS
        if self.running:
            self._update()
        self.root.after(interval, self._tick)

    def _update(self) -> None:
        sample = self.sampler.take_sample()
        self._refresh_partitions(sample)
        self._refresh_panels(sample)
        self._refresh_processes(sample)
        self._refresh_detail(sample)
        self.graph.push(sample.cpu_percent)

    def _refresh_partitions(self, s: Sample) -> None:
        current = self.partition_var.get()
        values = [f"{p.mountpoint} ({p.percent:.0f}%)" for p in s.partitions]
        self.partition_combo["values"] = values
        if current not in values and values:
            self.partition_var.set(values[0])

    @staticmethod
    def _net_bar(recv: float, sent: float) -> float:
        """网络面板进度条：按 50MB/s 满量程估算."""
        return min(max(recv, sent) / 1024 / 50 * 100, 100)

    @staticmethod
    def _io_bar(r: float, w: float) -> float:
        return min(max(r, w) / 200 * 100, 100)

    def _refresh_panels(self, s: Sample) -> None:
        self.cpu_panel.update(
            f"{s.cpu_percent:.1f}%",
            f"CORES {len(s.cpu_percpu)}  PROC {s.proc_total}",
            bar=s.cpu_percent,
        )

        peak = max(s.net_recv_kbps, s.net_sent_kbps)
        if peak > 1024:
            net_val = f"↓{s.net_recv_kbps/1024:.2f} ↑{s.net_sent_kbps/1024:.2f} MB/s"
        else:
            net_val = f"↓{s.net_recv_kbps:.1f} ↑{s.net_sent_kbps:.1f} KB/s"
        self.net_panel.update(net_val, "RX / TX RATE",
                              bar=self._net_bar(s.net_recv_kbps, s.net_sent_kbps))

        self.io_panel.update(
            f"R {s.disk_read_mbps:.1f}  W {s.disk_write_mbps:.1f}",
            "READ / WRITE  MB/s",
            bar=self._io_bar(s.disk_read_mbps, s.disk_write_mbps),
        )

        selected = self.partition_var.get()
        pct, used, total = 0.0, 0.0, 0.0
        for p in s.partitions:
            if f"{p.mountpoint} ({p.percent:.0f}%)" == selected or (
                not selected and s.partitions
                and p.mountpoint == s.partitions[0].mountpoint
            ):
                pct, used, total = p.percent, p.used_gb, p.total_gb
                break
        self.disk_panel.update(
            f"{pct:.1f}%",
            f"{used:.0f} / {total:.0f} GB USED",
            bar=pct,
        )

    def _refresh_processes(self, s: Sample) -> None:
        self.proc_count_lbl.configure(text=f"TOTAL {s.proc_total}")
        for iid in self.proc_tree.get_children():
            self.proc_tree.delete(iid)
        for p in s.processes:
            tag = "hot" if p.cpu_percent >= 20 else ""
            self.proc_tree.insert(
                "", "end",
                values=(p.pid, p.name[:24], f"{p.cpu_percent:.1f}",
                        f"{p.mem_mb:.0f}MB"),
                tags=(tag,),
            )
        self.proc_tree.tag_configure("hot", foreground=COLOR_DANGER)

    def _refresh_detail(self, s: Sample) -> None:
        cores = " ".join(f"{c:5.1f}" for c in s.cpu_percpu[:16])
        parts = "  │  ".join(
            f"{p.mountpoint} {p.used_gb:.0f}/{p.total_gb:.0f}GB {p.percent:.0f}%"
            for p in s.partitions
        )
        self.detail.configure(
            text=f"▸ CORE MATRIX [ {cores} ]\n▸ VOLUMES     {parts}",
        )


def main() -> None:
    root = tk.Tk()
    MonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
