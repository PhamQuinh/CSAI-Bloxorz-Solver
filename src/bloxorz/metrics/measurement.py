"""Performance measurement for search time, peak RAM, and expanded nodes.

Implemented by TV3, enhanced for R4/R5 robustness. RAM is the peak of
Python allocations traced by ``tracemalloc`` while the ``with`` block runs,
reported in megabytes.
"""
import time
import tracemalloc
from contextlib import contextmanager


@contextmanager
def measure_performance():
    """Measure wall time (seconds) and peak traced memory (MB).

    The yielded dict always has ``search_time``, ``peak_memory_mb`` and
    ``expanded_nodes``. The first two are overwritten on exit. The caller
    sets ``expanded_nodes`` inside the block.
    """
    already_tracing = tracemalloc.is_tracing()
    if already_tracing:
        tracemalloc.reset_peak()
    else:
        tracemalloc.start()

    start_time = time.perf_counter()
    metrics = {"search_time": 0.0, "peak_memory_mb": 0.0, "expanded_nodes": 0}
    try:
        yield metrics
    finally:
        metrics["search_time"] = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
        if not already_tracing:
            tracemalloc.stop()
