# ◢◤ SYSMON — 系统遥测终端（Sci-Fi System Monitor）

基于 **Python + psutil + Tkinter** 的科幻风系统监控程序，覆盖五大指标：**CPU 占用率、网络收发速率、磁盘 IO 读写速率、磁盘使用率、进程信息（TOP CPU/内存）**。

![主界面](docs/screenshots/01_main_interface.png)

---

## 一、开发框架与技术

| 类别 | 技术 | 版本 | 说明 |
| --- | --- | --- | --- |
| 语言 | Python | ≥ 3.8 | CPython |
| 系统库 | [psutil](https://pypi.org/project/psutil/) | ≥ 5.9.0 | 跨平台系统信息采集 |
| GUI | Tkinter / ttk | 标准库内置 | 深色科幻主题（霓虹配色 + 等宽字体） |
| 图形 | tk.Canvas | 标准库内置 | CPU 折线图 + 迷你进度条，零第三方绘图依赖 |

### psutil API 与指标映射

| 指标 | API |
| --- | --- |
| CPU 占用率（整体/每核） | `psutil.cpu_percent(percpu=True)` |
| 网络收发速率 | `psutil.net_io_counters()` 两次采样差值 ÷ 间隔 |
| 磁盘 IO 读写速率 | `psutil.disk_io_counters()` 两次采样差值 ÷ 间隔 |
| 磁盘使用率 | `psutil.disk_partitions()` + `psutil.disk_usage()` |
| 进程信息 | `psutil.process_iter()` + `cpu_percent()` / `memory_percent()` / `memory_info()` |

### 目录结构

```
SystemMonitor/
├── gui.py                    # 科幻风主界面（面板 + 折线图 + 进程表）
├── requirements.txt          # 仅 psutil
├── README.md                 # 本文件
├── OPERATING_MANUAL.md       # 详细操作手册（含运行截图）
├── monitor/
│   ├── __init__.py
│   └── sampler.py            # psutil 采样封装（五大指标 + 速率差值）
└── docs/
    └── screenshots/          # 运行截图（全屏 2560×1600 物理像素）
```

---

## 二、主要功能

| 模块 | 功能 |
| --- | --- |
| ◢ CPU | 整体占用率大号数值 + 霓虹进度条 + 60 秒遥测折线图 + 每核心矩阵 |
| ◢ NET | 实时上行/下行速率（KB/s、MB/s 自动换算）+ 量程进度条 |
| ◢ I/O | 磁盘读/写速率（MB/s）+ 量程进度条 |
| ◢ DSK | 磁盘分区使用率 + 已用/总量 GB，下拉切换分区 |
| ◢ PROC | **进程总数统计 + TOP 12 进程实时表**（PID / 进程名 / CPU% / 内存 MB），CPU ≥ 20% 高亮红色告警 |
| 工具栏 | 暂停/恢复（ONLINE/HOLD 状态灯）、采样周期 200ms~10s 可调 |

### 科幻风设计

- **配色**：深空黑底 `#05080f` + 霓虹青/绿/紫/琥珀四色通道
- **字体**：全界面等宽 Consolas，角标装饰 `◢ ⟨ ⟩ ▸ │`
- **动效**：折线图末端光点、进度条末端亮斑模拟"发光"
- **告警**：进程 CPU ≥ 20% 红色高亮，暂停时状态灯由 ONLINE(绿) 变 HOLD(红)

---

## 三、快速开始

```bash
git clone https://github.com/klsjSDE6/SystemMonitor.git
cd SystemMonitor
pip install -r requirements.txt
python gui.py
```

详细操作说明（含截图）见 [OPERATING_MANUAL.md](OPERATING_MANUAL.md)。

---

## 四、运行截图

| 主界面（运行中） | 暂停状态 |
| --- | --- |
| ![运行中](docs/screenshots/01_main_interface.png) | ![已暂停](docs/screenshots/02_paused_state.png) |

---

## 五、代码库地址

**https://github.com/klsjSDE6/SystemMonitor**
