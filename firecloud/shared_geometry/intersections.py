from __future__ import annotations

"""Reusable lattice / voxel intersection plans for Firecloud Shared Geometry.

This module is geometry-only.  It maps a Sun→target ray onto an existing
(distance, height) lattice and stores segment lengths and nearest-cell indices.
It intentionally carries no cloud fraction, condensate, aerosol, gas, optical
depth, or transmission values.
"""

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import pandas as pd

from ..config import EARTH_RADIUS_KM
from .ray import ray_altitudes_vectorized_km


@dataclass(frozen=True)
class LatticeSignature:
    direction_offset_deg: float
    distances_km: tuple[float, ...]
    heights_km: tuple[float, ...]


@dataclass
class VoxelIntersectionPlan:
    """Angle-specific geometry plan reusable by multiple optical evidence chains."""
    solar_altitude_deg: float
    radius_km: float
    directions: dict[float, dict[str, Any]]
    target_plan_count: int = 0
    segment_count: int = 0
    valid_segment_count: int = 0

    def as_legacy_dict(self) -> dict:
        """Compatibility view used by R5.7.7+ callers and CASE diagnostics."""
        return {
            "solar_altitude_deg": float(self.solar_altitude_deg),
            "radius_km": float(self.radius_km),
            "directions": self.directions,
            "target_plan_count": int(self.target_plan_count),
            "segment_count": int(self.segment_count),
            "valid_segment_count": int(self.valid_segment_count),
            "plan_type": "VOXEL_INTERSECTION_PLAN_V1",
        }


def build_voxel_intersection_plan(
    voxels: pd.DataFrame,
    solar_altitude_deg: float,
    *,
    radius_km: float = EARTH_RADIUS_KM,
    direction_col: str = "direction_offset_deg",
    distance_col: str = "distance_km",
    height_col: str = "voxel_center_km",
) -> VoxelIntersectionPlan:
    """Build one Sun-ray→voxel mapping plan for a complete lattice.

    Nearest-height selection deliberately preserves the legacy rule:
    ``searchsorted(..., side='left')`` with ties resolved toward the lower cell.
    Segment slant length preserves the existing ``dx/cos(|solar altitude|)``
    engineering geometry used by the proxy/native blocking solvers.
    """
    radius = float(radius_km)
    angle = float(solar_altitude_deg)
    if voxels is None or voxels.empty:
        return VoxelIntersectionPlan(angle, radius, {})

    required = {direction_col, distance_col, height_col}
    if not required.issubset(voxels.columns):
        return VoxelIntersectionPlan(angle, radius, {})

    cos_sun = max(0.05, math.cos(math.radians(abs(angle))))
    directions: dict[float, dict[str, Any]] = {}
    target_plan_count = segment_count = valid_segment_count = 0

    for off, gdir0 in voxels.groupby(direction_col, sort=False):
        gdir = gdir0.sort_values([distance_col, height_col])
        distances = np.array(
            sorted(pd.to_numeric(gdir[distance_col], errors="coerce").dropna().unique()),
            dtype=float,
        )
        heights = np.array(
            sorted(pd.to_numeric(gdir[height_col], errors="coerce").dropna().unique()),
            dtype=float,
        )
        if distances.size == 0 or heights.size == 0:
            continue

        di = {float(v): i for i, v in enumerate(distances)}
        targets: dict[tuple[float, float], dict[str, Any]] = {}

        for d_t in distances:
            i0 = di[float(d_t)]
            ds = distances[i0 + 1 :]
            if ds.size:
                prev = np.concatenate(([float(d_t)], ds[:-1]))
                dx = ds - prev
                valid_dx = dx > 0.0
                mids = ds - dx / 2.0
                rows = np.arange(i0 + 1, len(distances), dtype=int)
            else:
                dx = np.empty(0, dtype=float)
                valid_dx = np.empty(0, dtype=bool)
                mids = np.empty(0, dtype=float)
                rows = np.empty(0, dtype=int)

            for z_t in heights:
                if ds.size:
                    ray_h = ray_altitudes_vectorized_km(
                        float(d_t), float(z_t), mids, angle, radius
                    )
                    valid = valid_dx & np.isfinite(ray_h) & (ray_h >= 0.0)
                    idx_hi = np.searchsorted(heights, ray_h, side="left")
                    idx_hi = np.clip(idx_hi, 0, len(heights) - 1)
                    idx_lo = np.clip(idx_hi - 1, 0, len(heights) - 1)
                    choose_hi = np.abs(heights[idx_hi] - ray_h) < np.abs(
                        ray_h - heights[idx_lo]
                    )
                    nearest = np.where(choose_hi, idx_hi, idx_lo)
                    slant_km = np.where(valid, dx / cos_sun, 0.0)
                else:
                    ray_h = np.empty(0, dtype=float)
                    valid = np.empty(0, dtype=bool)
                    nearest = np.empty(0, dtype=int)
                    slant_km = np.empty(0, dtype=float)

                targets[(float(d_t), float(z_t))] = {
                    "i0": int(i0),
                    "ds": ds,
                    "dx": dx,
                    "valid": valid,
                    "ray_height_km": ray_h,
                    "nearest_height_index": nearest,
                    "upstream_row_index": rows,
                    "slant_km": slant_km,
                }
                target_plan_count += 1
                segment_count += int(ds.size)
                valid_segment_count += int(np.sum(valid))

        directions[float(off)] = {
            "distances": distances,
            "heights": heights,
            "di": di,
            "targets": targets,
            "signature": LatticeSignature(
                float(off), tuple(map(float, distances)), tuple(map(float, heights))
            ),
        }

    return VoxelIntersectionPlan(
        angle,
        radius,
        directions,
        target_plan_count=target_plan_count,
        segment_count=segment_count,
        valid_segment_count=valid_segment_count,
    )


def plan_direction_if_compatible(
    plan: VoxelIntersectionPlan | dict | None,
    direction_offset_deg: float,
    distances: np.ndarray,
    heights: np.ndarray,
):
    """Return a direction bucket only when the lattice is exactly identical."""
    if plan is None:
        return None
    directions = plan.directions if isinstance(plan, VoxelIntersectionPlan) else plan.get("directions", {})
    d = directions.get(float(direction_offset_deg))
    if not d:
        return None
    if not np.array_equal(d.get("distances"), distances):
        return None
    if not np.array_equal(d.get("heights"), heights):
        return None
    return d
