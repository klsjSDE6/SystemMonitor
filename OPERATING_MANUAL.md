# SystemMonitor 系统监控程序 —— 操作手册

> **版本**：v1.0  **更新时间**：2026-10-30  **代码库**：https://github.com/klsjSDE6/SystemMonitor

---

## 一、项目概述

基于 **Python + psutil + Tkinter** 实现的桌面端系统实时监控工具，覆盖课程作业要求的全部四项指标：

| 指标 | 说明 | psutil API |
| --- | --- | --- |
| 磁盘使用率 | 各分区总容量、已用、剩余、使用率 | `psutil.disk_usage()` |
| CPU 占用率 | 整体 + 每核心实时占用（折线图展示） | `psutil.cpu_percent(percpu=True)` |
| 网络收发速率 | 所有网卡的实时上行/下行速率 | `psutil.net_io_counters(pernic=True)` + 差值计算 |
| 磁盘 IO 读写速率 | 磁盘读/写字节数、速率 | `psutil.disk_io_counters(perdisk=True)` + 差值计算 |

### 技术栈

```
Python ≥ 3.8  ·  psutil ≥ 5.9.0（系统信息采集）  ·  Tkinter（Python 标准库 GUI）
```

### 功能特点

- ✅ **深色主题**，护眼、信息层次清晰
- ✅ **实时折线图**（CPU 最近 60 秒趋势）
- ✅ **可调节采样周期**（默认 1000ms，最快 200ms）
- ✅ **暂停/恢复** 实时刷新（方便截图、对比数据）
- ✅ **多分区支持**（自动枚举所有磁盘，可下拉切换）
- ✅ **跨平台**（Windows / macOS / Linux 均支持，psutil 提供平台适配）

---

## 二、环境要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10/11、macOS 12+、Linux（主流发行版） |
| Python 版本 | 3.8 ~ 3.12（推荐 3.10+） |
| 依赖库 | 仅 `psutil`（其他均为 Python 标准库） |
| 屏幕分辨率 | 最低 1024×768（推荐 1280×800 以上） |

### 安装 Python（Windows）

若未安装 Python 3.8+：
1. 访问 [Python 官网](https://www.python.org/downloads/) 下载最新稳定版（如 3.12.x）；
2. 运行安装包时**务必勾选「Add Python to PATH」**；
3. 安装完成后，`Win + R` → 输入 `python --version` 应能看到版本号。

---

## 三、安装与启动

### 步骤 1：克隆仓库

```bash
git clone https://github.com/klsjSDE6/SystemMonitor.git
cd SystemMonitor
```

**若没有 git**：直接在 GitHub 仓库页面点击 `Code` → `Download ZIP` → 解压到任意目录。

### 步骤 2：安装依赖

```bash
pip install -r requirements.txt
```

> 💡 依赖只有 `psutil` 一个，若网络慢可加国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 步骤 3：启动程序

```bash
python gui.py
```

启动后应弹出标题为 **「SystemMonitor 系统监控」** 的深色窗口，约 1 秒后数据开始刷新。

---

## 四、界面详解

启动后的主界面如下图所示：

![SystemMonitor 主界面](screenshots/01_main_interface.png)

### 4.1 顶部工具栏（左 → 右）

| 控件 | 功能 |
| --- | --- |
| **⏸ 暂停** 按钮 | 暂停/恢复所有数据的实时刷新。暂停后按钮变为 `▶ 继续`，所有指标保持最后一次采样值不变 |
| **磁盘分区** 下拉框 | 默认显示系统盘（Windows 上为 `C:`），可下拉切换查看其他分区的使用率 |
| **采样周期** 下拉框 | 可选 `200ms / 500ms / 1s / 2s / 5s`，默认 1 秒。采样越密数据越实时，但占用更多 CPU |
| **右上角数值** | 实时显示当前采样周期下的核心指标摘要（可选扩展位） |

### 4.2 四个核心指标面板（上半部分，左 → 右）

| 面板 | 显示内容 | 数据来源 |
| --- | --- | --- |
| **💻 CPU 占用率** | 整体占用百分比 + 每核心小柱状图（核心数随 CPU 自动适配） | `psutil.cpu_percent(percpu=True)` |
| **🌐 网络速率** | 实时上行/下行速率（单位 KB/s 或 MB/s，自动换算） | 连续两次 `net_io_counters()` 差值 ÷ 采样间隔 |
| **💾 磁盘 IO** | 磁盘读/写速率（MB/s） + 累计读写量 | 连续两次 `disk_io_counters()` 差值 |
| **📀 磁盘使用率** | 当前选中分区的容量环 + 百分比 + 已用/剩余 GB 数 | `psutil.disk_usage(path)` |

### 4.3 下半部分：CPU 趋势折线图

- **横轴**：最近 60 秒的时间窗口（左旧右新）
- **纵轴**：0% ~ 100% CPU 占用
- **刷新逻辑**：每次采样都把当前值推入队列，超过 60 个点则丢弃最早的
- **暂停时**：折线图停止滚动，保持暂停瞬间的 60 秒趋势线

### 4.4 底部详细信息区

展开后显示：
- **每核心 CPU 占用**：单独列出每个逻辑核心的实时百分比（方便观察多核负载是否均衡）
- **所有磁盘分区列表**：枚举所有已挂载分区的总容量、已用、剩余、使用率

---

## 五、操作指南

### 5.1 基本操作流程

```mermaid
graph LR
A[启动程序 python gui.py] --> B{是否正常显示?}
B -->|是| C[观察实时数据]
B -->|否| D[查常见问题章节]
C --> E[需要截图/对比?]
E -->|是| F[点击「⏸ 暂停」]
F --> G[截图 / 记录数据]
G --> H[点击「▶ 继续」恢复刷新]
E -->|否| I[调整采样周期]
I --> J[切换磁盘分区查看]
J --> K[关闭程序 或 继续观察]
```

### 5.2 暂停/恢复数据刷新

**操作**：点击顶部工具栏左侧的 `⏸ 暂停` 按钮

**效果**：
- 所有四个指标面板停止刷新，保持最后一次采样值
- CPU 折线图停止滚动
- 按钮文字变为 `▶ 继续`，再次点击恢复实时刷新

**适用场景**：
- 截作业报告里的运行截图（避免数据变化导致截图模糊）
- 对比同一时刻不同指标之间的相关性
- 做演示时让观众看清数值

![暂停状态截图](screenshots/02_paused_state.png)

### 5.3 切换磁盘分区

**操作**：点击顶部「磁盘分区」下拉框 → 选择目标分区（如 `D:`、`E:`）

**效果**：`📀 磁盘使用率` 面板立刻显示新分区的容量和使用率，其他面板（CPU/网络/IO）不受影响。

### 5.4 调整采样周期

**操作**：点击顶部「采样周期」下拉框 → 选择新周期

| 周期选项 | 适用场景 | CPU 占用影响 |
| --- | --- | --- |
| 200ms | 高速网络/磁盘速率监控 | 略高（<5%） |
| 500ms | 平衡方案（推荐日常用） | 低（<2%） |
| **1s（默认）** | 常规系统监控 | 极低（<1%） |
| 2s / 5s | 低功耗场景、远程服务器 | 几乎为零 |

---

## 六、作业要求对应说明

| 作业要求 | 本程序实现位置 | 说明 |
| --- | --- | --- |
| ① 图形用户界面 | `gui.py`（Tkinter，380+ 行） | 深色主题 + Tab 式布局 + 实时折线图 |
| ② 代码提交到 GitHub | https://github.com/klsjSDE6/SystemMonitor | 公开仓库，main 分支，2 次提交 |
| ③ 系统文档 | 本文件 + `README.md` | 框架/技术选型 + 主要功能 + 用户手册 + 代码库地址 |
| ④ 源码 + 文档压缩提交 | `SystemMonitor_submit.zip` | 包含：源码、README、本手册、运行截图 |

---

## 七、常见问题

### Q1：启动时报 `ModuleNotFoundError: No module named 'psutil'`

→ 执行 `pip install psutil` 或 `pip install -r requirements.txt`

### Q2：程序启动后窗口空白或闪退

→ 检查 Python 版本是否 ≥ 3.8：`python --version`
→ 若为 Windows：确认 `tkinter` 已安装（Tkinter 随 Python 一起安装，若缺失需重装 Python 并勾选「tcl/tk and IDLE」）

### Q3：磁盘使用率面板显示「找不到分区」

→ Windows 上某些移动硬盘、U 盘未挂载盘符时不会出现在下拉框；
→ 若为 macOS/Linux：分区路径可能是 `/dev/sda1`、`/mnt/data` 等，程序自动枚举所有 `disk_usage()` 可访问的路径。

### Q4：网络速率显示为 0 KB/s

→ 刚启动时的前 1~2 秒会为 0（需要两次采样才能算差值）；
→ 若持续为 0：检查是否有活动网络连接（打开浏览器访问任意网站）；
→ VMware / Hyper-V 虚拟网卡可能干扰：程序已自动过滤 down 状态的接口。

### Q5：CPU 折线图出现尖峰或骤降

→ 采样间隔内的瞬时峰值被捕捉到是正常现象；
→ 若频繁尖峰：适当调大采样周期（如从 1s 改为 2s）；
→ 若持续 100%：检查是否有高负载进程（任务管理器 → 详细信息 → 按 CPU 排序）。

### Q6：在远程桌面 / 虚拟机中运行

→ 完全支持：`psutil` 是跨平台系统 API 封装，不依赖本地显示器；
→ 图形界面在无显示器环境下需要虚拟帧缓冲（Linux 上可装 `xvfb` 后用 `xvfb-run python gui.py` 启动）。

---

## 八、扩展建议（供后续迭代）

| 扩展方向 | 实现难度 | 说明 |
| --- | --- | --- |
| **CSV 导出** | ⭐⭐ | 加一个「导出历史数据」按钮，把 60 秒的采样数据存为 CSV，方便 Excel 分析 |
| **多指标折线图** | ⭐⭐⭐ | 把网络速率、磁盘 IO 也画成折线图，三条线叠加对比 |
| **系统托盘常驻** | ⭐⭐ | 缩小到托盘区，右键菜单恢复主窗口、一键暂停、退出 |
| **阈值告警** | ⭐⭐⭐ | CPU > 90% 时弹窗或闪烁托盘图标，磁盘使用率 > 95% 预警 |
| **历史趋势归档** | ⭐⭐⭐⭐ | 每小时存一份快照到 SQLite，加一个「查看历史」Tab 拉取 24h/7d 趋势 |
| **PyInstaller 打包** | ⭐⭐ | `pyinstaller -F -w gui.py` 生成单文件 `.exe`，双击即用 |

---

## 九、代码库地址

| 平台 | 地址 |
| --- | --- |
| GitHub | **https://github.com/klsjSDE6/SystemMonitor** |

### 快速上手 3 行

```bash
git clone https://github.com/klsjSDE6/SystemMonitor.git
cd SystemMonitor && pip install -r requirements.txt
python gui.py
```
