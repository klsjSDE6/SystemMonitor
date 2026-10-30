"""系统资源采样器：基于 psutil 封装 CPU / 磁盘 / 网络 / IO 指标.

网络速率与磁盘 IO 速率为「两次采样的差值 / 时间间隔」，因此需要先调用
一次 take_sample() 作为基准，后续再采样时才会给出真实速率。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

import psutil


@dataclass
class DiskPartition:
    """单个磁盘分区的使用率信息."""
    mountpoint: str
    device: str
    total_gb: float
    used_gb: float
    percent: float


@dataclass
class ProcessInfo:
    """单个进程的资源占用信息."""
    pid: int
    name: str
    cpu_percent: float            # 自上次采样以来的 CPU 占用 %
    mem_percent: float            # 内存占用 %
    mem_mb: float                 # 常驻内存 MB


@dataclass
class Sample:
    """一次完整的系统状态采样."""
    timestamp: float
    cpu_percent: float
    cpu_percpu: List[float]
    partitions: List[DiskPartition]
    net_recv_kbps: float          # 网络接收速率 KB/s
    net_sent_kbps: float          # 网络发送速率 KB/s
    disk_read_mbps: float         # 磁盘读取速率 MB/s
    disk_write_mbps: float        # 磁盘写入速率 MB/s
    processes: List[ProcessInfo] = field(default_factory=list)   # TOP 进程（按 CPU 排序）
    proc_total: int = 0           # 进程总数


class SystemSampler:
    """系统采样器，维护采样基准并计算速率差值."""

    def __init__(self) -> None:
        self._last_net = psutil.net_io_counters()
        self._last_disk = psutil.disk_io_counters()
        self._last_ts = time.monotonic()
        # 预热：进程级 cpu_percent 首次调用恒为 0，先调用一次建立基准
        for p in psutil.process_iter():
            try:
                p.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    # ------------------------------------------------------------------ 工具

    @staticmethod
    def _gb(bytes_: int) -> float:
        return bytes_ / (1024 ** 3)

    @staticmethod
    def _kbps(delta_bytes: int, delta_sec: float) -> float:
        if delta_sec <= 0:
            return 0.0
        return delta_bytes / delta_sec / 1024

    @staticmethod
    def _mbps(delta_bytes: int, delta_sec: float) -> float:
        if delta_sec <= 0:
            return 0.0
        return delta_bytes / delta_sec / (1024 ** 2)

    # ------------------------------------------------------------------ 采样

    def take_sample(self) -> Sample:
        """立即采样一次，返回当前系统状态."""
        now = time.monotonic()
        dt = now - self._last_ts
        self._last_ts = now

        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_percpu = psutil.cpu_percent(interval=None, percpu=True)

        # 磁盘分区
        partitions: List[DiskPartition] = []
        for p in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(p.mountpoint)
            except PermissionError:
                continue
            partitions.append(DiskPartition(
                mountpoint=p.mountpoint,
                device=p.device,
                total_gb=round(self._gb(u.total), 2),
                used_gb=round(self._gb(u.used), 2),
                percent=u.percent,
            ))

        # 网络速率（差值）
        cur_net = psutil.net_io_counters()
        net_recv_kbps = self._kbps(cur_net.bytes_recv - self._last_net.bytes_recv, dt)
        net_sent_kbps = self._kbps(cur_net.bytes_sent - self._last_net.bytes_sent, dt)
        self._last_net = cur_net

        # 磁盘 IO 速率（差值）
        cur_disk = psutil.disk_io_counters()
        if cur_disk and self._last_disk:
            disk_read_mbps = self._mbps(cur_disk.read_bytes - self._last_disk.read_bytes, dt)
            disk_write_mbps = self._mbps(cur_disk.write_bytes - self._last_disk.write_bytes, dt)
            self._last_disk = cur_disk
        else:
            disk_read_mbps = 0.0
            disk_write_mbps = 0.0

        # 进程信息（按 CPU 占用降序取 TOP N）
        procs: List[ProcessInfo] = []
        proc_total = 0
        for p in psutil.process_iter():
            try:
                if p.pid == 0:        # System Idle Process 无意义，剔除
                    continue
                cpu_p = p.cpu_percent(None)
                mem_p = p.memory_percent()
                mem_mb = p.memory_info().rss / (1024 ** 2)
                procs.append(ProcessInfo(
                    pid=p.pid,
                    name=p.name(),
                    cpu_percent=round(cpu_p, 1),
                    mem_percent=round(mem_p, 2),
                    mem_mb=round(mem_mb, 1),
                ))
                proc_total += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        procs.sort(key=lambda x: x.cpu_percent, reverse=True)

        return Sample(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            cpu_percpu=cpu_percpu,
            partitions=partitions,
            net_recv_kbps=round(net_recv_kbps, 2),
            net_sent_kbps=round(net_sent_kbps, 2),
            disk_read_mbps=round(disk_read_mbps, 2),
            disk_write_mbps=round(disk_write_mbps, 2),
            processes=procs[:12],   # TOP 12 进程
            proc_total=proc_total,
        )
