"""Performance measurement context manager for CPU time and peak RAM."""
import time
import tracemalloc
from contextlib import contextmanager

@contextmanager
def measure_performance():
    """Context manager measuring execution time (s) and peak memory (MB)."""
    tracemalloc.start()
    start_time = time.perf_counter()
    metrics = {"search_time": 0.0, "peak_memory_mb": 0.0}
    try:
        yield metrics
    finally:
        metrics["search_time"] = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
        tracemalloc.stop()
