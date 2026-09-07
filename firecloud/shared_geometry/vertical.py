from __future__ import annotations

"""Shared vertical indexing primitives.

Geometry-only utilities for mapping arbitrary ray/model heights onto sorted
vertical lattices.  Tie behavior is explicit and stable so all Firecloud
modules assign the same physical height to the same vertical cell.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class VerticalIndexPlan:
    heights_km: np.ndarray

    @classmethod
    def from_heights(cls, heights_km) -> "VerticalIndexPlan":
        h = np.asarray(heights_km, dtype=float)
        if h.ndim != 1 or h.size == 0:
            raise ValueError("heights_km must be a non-empty 1-D array")
        if np.any(~np.isfinite(h)) or np.any(np.diff(h) < 0):
            raise ValueError("heights_km must be finite and sorted ascending")
        return cls(h)

    def nearest_indices(self, values_km) -> np.ndarray:
        """Nearest vertical-cell index; exact midpoint ties choose lower cell.

        This preserves the existing Firecloud rule used by the R5.7.7+
        VoxelIntersectionPlan implementation (strict '<' when choosing upper).
        """
        v = np.asarray(values_km, dtype=float)
        h = self.heights_km
        idx_hi = np.searchsorted(h, v, side="left")
        idx_hi = np.clip(idx_hi, 0, h.size - 1)
        idx_lo = np.clip(idx_hi - 1, 0, h.size - 1)
        choose_hi = np.abs(h[idx_hi] - v) < np.abs(v - h[idx_lo])
        return np.where(choose_hi, idx_hi, idx_lo).astype(int, copy=False)

    def bracket_indices(self, values_km) -> tuple[np.ndarray, np.ndarray]:
        """Return lower/upper bracketing indices, clipped to lattice bounds."""
        v = np.asarray(values_km, dtype=float)
        h = self.heights_km
        hi = np.searchsorted(h, v, side="left")
        hi = np.clip(hi, 0, h.size - 1)
        lo = np.clip(hi - 1, 0, h.size - 1)
        return lo.astype(int, copy=False), hi.astype(int, copy=False)

    def overlap_indices(self, z0_km: float, z1_km: float) -> np.ndarray:
        """Indices whose center heights lie within the closed vertical interval."""
        lo, hi = sorted((float(z0_km), float(z1_km)))
        h = self.heights_km
        i0 = int(np.searchsorted(h, lo, side="left"))
        i1 = int(np.searchsorted(h, hi, side="right"))
        return np.arange(i0, i1, dtype=int)


def nearest_vertical_indices(heights_km, values_km) -> np.ndarray:
    return VerticalIndexPlan.from_heights(heights_km).nearest_indices(values_km)


def bracket_vertical_indices(heights_km, values_km) -> tuple[np.ndarray, np.ndarray]:
    return VerticalIndexPlan.from_heights(heights_km).bracket_indices(values_km)
