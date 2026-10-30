"""SystemMonitor GUI - Tkinter 图形界面.

- 每 1 秒刷新一次所有指标
- 顶部显示 4 个面板（CPU / 磁盘 / 网络 / IO）
- 下部 Canvas 绘制最近 60 秒 CPU 使用率折线图
- 支持「启动 / 暂停」按钮、采样周期可调、分区下拉切换
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections import deque

from monitor.sampler import SystemSampler, Sample


# ------------------------------------------------------------------ 样式常量

COLOR_BG = "#1e1f29"
COLOR_PANEL = "#2a2c3a"
COLOR_TEXT = "#f0f0f5"
COLOR_MUTED = "#8a8ca0"
COLOR_CPU = "#ff7a59"
COLOR_NET = "#58c4dc"
COLOR_IO = "#9d8fff"
COLOR_DISK = "#49d28c"

GRAPH_SECONDS = 60       # 折线图窗口秒数
SAMPLE_INTERVAL_MS = 1000  # 默认刷新间隔


class MetricPanel(ttk.Frame):
    """单个指标面板：标题 + 大号数值 + 底部小字."""

    def __init__(self, master, title: str, accent: str) -> None:
        super().__init__(master, style="Panel.TFrame", padding=12)
        self.title_lbl = ttk.Label(self, text=title, style="Muted.TLabel")
        self.title_lbl.pack(anchor="w")

        self.value_lbl = tk.Label(
            self, text="--", fg=accent, bg=COLOR_PANEL,
            font=("Consolas", 28, "bold"),
        )
        self.value_lbl.pack(anchor="w", pady=(4, 0))

        self.sub_lbl = ttk.Label(self, text="", style="Muted.TLabel")
        self.sub_lbl.pack(anchor="w")

    def update(self, value: str, sub: str = "") -> None:
        self.value_lbl.configure(text=value)
        self.sub_lbl.configure(text=sub)


class Graph(tk.Canvas):
    """简易折线图 Canvas：最近 N 秒的 CPU 使用率."""

    def __init__(self, master) -> None:
        super().__init__(
            master, height=180, bg=COLOR_PANEL,
            highlightthickness=0,
        )
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

        # 网格
        for y in (0.0, 25.0, 50.0, 75.0, 100.0):
            yp = h - 12 - (y / 100.0) * (h - 24)
            self.create_line(24, yp, w - 4, yp, fill="#3a3c4e", dash=(2, 4))
            self.create_text(6, yp, anchor="w", text=f"{int(y)}%",
                             fill=COLOR_MUTED, font=("Consolas", 9))

        if len(self.data) < 2:
            return

        step_x = (w - 32) / max(GRAPH_SECONDS - 1, 1)
        points = []
        for i, v in enumerate(self.data):
            x = 28 + i * step_x
            y = h - 12 - (v / 100.0) * (h - 24)
            points.extend((x, y))

        # 填充
        fill = list(points)
        fill.extend([points[-2], h - 12, points[0], h - 12])
        self.create_polygon(*fill, fill="#ff7a5933", outline="")

        # 折线
        self.create_line(*points, fill=COLOR_CPU, width=2, smooth=True)

        # 标签
        self.create_text(w - 4, 14, anchor="e", text="CPU 使用率 (%)  最近 60s",
                         fill=COLOR_MUTED, font=("Microsoft YaHei", 9))


# ------------------------------------------------------------------ 主窗口

class MonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.sampler = SystemSampler()
        self.running = True

        self._build_styles()
        self._build_ui()

        # 基准采样：第一次采样用来初始化计数器基准，不计入显示
        self.sampler.take_sample()
        self._tick()

    # --------------------------------------------------------------- UI 构建

    def _build_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                        font=("Microsoft YaHei", 10))
        style.configure("Muted.TLabel", background=COLOR_PANEL,
                        foreground=COLOR_MUTED, font=("Microsoft YaHei", 9))
        style.configure("TMenubutton", background=COLOR_PANEL,
                        foreground=COLOR_TEXT, padding=4)
        style.configure("TButton", padding=6)

    def _build_ui(self) -> None:
        self.root.title("SystemMonitor 系统监控")
        self.root.configure(bg=COLOR_BG)
        self.root.geometry("820x560")
        self.root.minsize(720, 480)

        # 顶部工具栏
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=12, pady=(10, 6))

        self.pause_btn = ttk.Button(bar, text="暂停", command=self._toggle_pause)
        self.pause_btn.pack(side="left")

        ttk.Label(bar, text="磁盘分区:").pack(side="left", padx=(16, 4))
        self.partition_var = tk.StringVar()
        self.partition_combo = ttk.Combobox(
            bar, textvariable=self.partition_var, state="readonly", width=20,
        )
        self.partition_combo.pack(side="left")

        ttk.Label(bar, text="采样周期(ms):").pack(side="left", padx=(16, 4))
        self.interval_var = tk.StringVar(value="1000")
        ttk.Spinbox(bar, from_=200, to=10000, increment=100, width=6,
                    textvariable=self.interval_var).pack(side="left")

        self.status_lbl = ttk.Label(bar, text="● 运行中",
                                    style="Muted.TLabel")
        self.status_lbl.pack(side="right")

        # 指标面板区
        grid = ttk.Frame(self.root)
        grid.pack(fill="x", padx=12, pady=6)

        self.cpu_panel = MetricPanel(grid, "CPU 占用率", COLOR_CPU)
        self.net_panel = MetricPanel(grid, "网络收发速率", COLOR_NET)
        self.io_panel = MetricPanel(grid, "磁盘读写速率", COLOR_IO)
        self.disk_panel = MetricPanel(grid, "磁盘使用率", COLOR_DISK)

        for i, p in enumerate((self.cpu_panel, self.net_panel,
                               self.io_panel, self.disk_panel)):
            p.grid(row=0, column=i, padx=4, sticky="nsew")
            grid.columnconfigure(i, weight=1)

        # 折线图
        ttk.Label(self.root, text="CPU 使用率趋势").pack(anchor="w", padx=12, pady=(10, 2))
        self.graph = Graph(self.root)
        self.graph.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # 底部详细信息
        self.detail = tk.Label(
            self.root, text="", fg=COLOR_MUTED, bg=COLOR_BG,
            anchor="w", justify="left", font=("Consolas", 9),
        )
        self.detail.pack(fill="x", padx=12, pady=(0, 10))

    # --------------------------------------------------------------- 刷新逻辑

    def _toggle_pause(self) -> None:
        self.running = not self.running
        self.pause_btn.configure(text="继续" if not self.running else "暂停")
        self.status_lbl.configure(
            text=("● 已暂停" if not self.running else "● 运行中"))

    def _tick(self) -> None:
        interval = max(200, int(self.interval_var.get() or SAMPLE_INTERVAL_MS))
        if self.running:
            self._update()
        self.root.after(interval, self._tick)

    def _update(self) -> None:
        sample = self.sampler.take_sample()
        self._refresh_partitions(sample)
        self._refresh_panels(sample)
        self._refresh_detail(sample)
        self.graph.push(sample.cpu_percent)

    def _refresh_partitions(self, s: Sample) -> None:
        current = self.partition_var.get()
        values = [f"{p.mountpoint} ({p.percent:.0f}%)" for p in s.partitions]
        self.partition_combo["values"] = values
        if current not in values and values:
            self.partition_var.set(values[0])

    def _refresh_panels(self, s: Sample) -> None:
        self.cpu_panel.update(
            f"{s.cpu_percent:.1f}%",
            f"核心数: {len(s.cpu_percpu)}   {s.cpu_percpu[:4]}...",
        )
        net_speed = max(s.net_recv_kbps, s.net_sent_kbps)
        net_unit = "MB/s" if net_speed > 1024 else "KB/s"
        if net_unit == "MB/s":
            r = s.net_recv_kbps / 1024; t = s.net_sent_kbps / 1024
        else:
            r, t = s.net_recv_kbps, s.net_sent_kbps
        self.net_panel.update(
            f"↓ {r:.2f}  ↑ {t:.2f} {net_unit}",
            "接收 / 发送",
        )
        self.io_panel.update(
            f"读 {s.disk_read_mbps:.2f}  写 {s.disk_write_mbps:.2f} MB/s",
            "磁盘 I/O 速率",
        )
        # 选中分区的使用率
        selected = self.partition_var.get()
        pct, used, total = 0.0, 0.0, 0.0
        for p in s.partitions:
            if f"{p.mountpoint} ({p.percent:.0f}%)" == selected or (
                not selected and p.mountpoint == s.partitions[0].mountpoint
            ):
                pct, used, total = p.percent, p.used_gb, p.total_gb
                break
        self.disk_panel.update(
            f"{pct:.1f}%",
            f"{used:.1f} / {total:.1f} GB",
        )

    def _refresh_detail(self, s: Sample) -> None:
        cores = " ".join(f"{c:4.1f}" for c in s.cpu_percpu)
        parts = "  |  ".join(
            f"{p.mountpoint}: {p.used_gb:.1f}/{p.total_gb:.1f}GB ({p.percent:.0f}%)"
            for p in s.partitions
        )
        text = (
            f"每核心 CPU %: [ {cores} ]\n"
            f"磁盘分区:     {parts}"
        )
        self.detail.configure(text=text)


def main() -> None:
    root = tk.Tk()
    MonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
