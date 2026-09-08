"""Runtime memory containment helpers for long PhysicsCore analysis workers.

R5.7.24 treats memory pressure as a reliability concern.  The helpers here are
engineering-only: they release Python garbage and, on glibc/Linux, ask malloc
to return unused heap pages to the operating system.  They do not change any
physics inputs, thresholds, resolution, or evidence semantics.
"""
from __future__ import annotations

import ctypes
import gc
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def _malloc_trim_function():
    """Return glibc malloc_trim when available, otherwise None."""
    if os.name != "posix":
        return None
    try:
        libc = ctypes.CDLL(None)
        fn = getattr(libc, "malloc_trim", None)
        if fn is None:
            return None
        fn.argtypes = [ctypes.c_size_t]
        fn.restype = ctypes.c_int
        return fn
    except Exception:
        return None


def collect_and_trim() -> dict:
    """Collect cyclic garbage and best-effort trim the native allocator.

    Returns a small diagnostic dictionary so callers/tests can record whether
    the platform exposes ``malloc_trim``.  Failure to trim is never fatal.
    """
    collected = 0
    try:
        collected = int(gc.collect())
    except Exception:
        collected = 0
    trim_available = False
    trim_result = None
    fn = _malloc_trim_function()
    if fn is not None:
        trim_available = True
        try:
            trim_result = int(fn(0))
        except Exception:
            trim_result = None
    return {
        "gc_collected": collected,
        "malloc_trim_available": trim_available,
        "malloc_trim_result": trim_result,
    }
