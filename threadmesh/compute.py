# ThreadMesh - Compute backend detection and configuration
# AGPL-3.0-or-later
#
# On startup: benchmarks GPU vs CPU on a synthetic workload.
# Selects GPU if faster; otherwise uses n-1 CPU cores capped at 40% RAM.
# GPU packages (cupy, pyopencl) are optional — graceful fallback always.

import os
import psutil
from threadmesh.config import RAM_MAX_FRACTION, CPU_RESERVE_CORES

# Optional GPU imports — never raise on missing packages
try:
    import cupy as cp
    _CUPY_AVAILABLE = True
except ImportError:
    _CUPY_AVAILABLE = False

try:
    import GPUtil
    _GPUTIL_AVAILABLE = True
except ImportError:
    _GPUTIL_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    _PYNVML_AVAILABLE = True
except Exception:
    _PYNVML_AVAILABLE = False

try:
    import pyopencl as cl
    _OPENCL_AVAILABLE = True
except ImportError:
    _OPENCL_AVAILABLE = False


class ComputeBackend:
    CPU  = "cpu"
    CUDA = "cuda"
    OCL  = "opencl"


class ComputeConfig:
    def __init__(self):
        self.backend      = ComputeBackend.CPU
        self.cpu_cores    = max(1, os.cpu_count() - CPU_RESERVE_CORES)
        self.ram_limit_gb = psutil.virtual_memory().total * RAM_MAX_FRACTION / (1024 ** 3)
        self.gpu_name     = None
        self.gpu_vram_gb  = None


def _detect_nvidia_gpu():
    if not _GPUTIL_AVAILABLE:
        return None
    gpus = GPUtil.getGPUs()
    return gpus[0] if gpus else None


def _benchmark_cpu(size=500_000):
    import numpy as np
    import time
    a = np.random.rand(size, 3).astype(np.float64)
    b = np.random.rand(size, 3).astype(np.float64)
    t0 = time.perf_counter()
    _ = np.linalg.norm(a - b, axis=1)
    return time.perf_counter() - t0


def _benchmark_cuda(size=500_000):
    if not _CUPY_AVAILABLE:
        return float("inf")
    import cupy as cp
    import time
    a = cp.random.rand(size, 3, dtype=cp.float64)
    b = cp.random.rand(size, 3, dtype=cp.float64)
    cp.cuda.Stream.null.synchronize()
    t0 = time.perf_counter()
    _ = cp.linalg.norm(a - b, axis=1)
    cp.cuda.Stream.null.synchronize()
    return time.perf_counter() - t0


def detect_and_configure() -> ComputeConfig:
    cfg = ComputeConfig()

    gpu = _detect_nvidia_gpu()
    if gpu is None or not _CUPY_AVAILABLE:
        # No NVIDIA GPU or CuPy — stay on CPU
        return cfg

    try:
        cpu_time  = _benchmark_cpu()
        cuda_time = _benchmark_cuda()

        if cuda_time < cpu_time:
            cfg.backend     = ComputeBackend.CUDA
            cfg.gpu_name    = gpu.name
            cfg.gpu_vram_gb = gpu.memoryTotal / 1024
    except Exception:
        # Any GPU error → fall back to CPU silently
        pass

    return cfg


# Module-level singleton — populated once at app startup
_config: ComputeConfig | None = None


def get_config() -> ComputeConfig:
    global _config
    if _config is None:
        _config = detect_and_configure()
    return _config


def backend_label() -> str:
    cfg = get_config()
    if cfg.backend == ComputeBackend.CUDA:
        return f"GPU · {cfg.gpu_name}"
    return f"CPU · {cfg.cpu_cores} cores · {cfg.ram_limit_gb:.1f} GB RAM"
