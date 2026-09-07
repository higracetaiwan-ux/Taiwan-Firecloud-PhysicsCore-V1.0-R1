from __future__ import annotations

"""Reusable lattice / voxel intersection plans for Firecloud Shared Geometry.

This module is geometry-only. It separates angle-independent lattice topology
from angle-dependent Sun→target ray materialization so the same forecast/model
lattice can be reused across multiple solar-altitude candidates.

It intentionally carries no cloud fraction, condensate, aerosol, gas, optical
depth, or transmission values.
"""

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import pandas as pd

from ..config import EARTH_RADIUS_KM
from .ray import ray_altitudes_vectorized_km, ray_altitude_matrix_km
from .vertical import VerticalIndexPlan


@dataclass(frozen=True)
class LatticeSignature:
    direction_offset_deg: float
    distances_km: tuple[float, ...]
    heights_km: tuple[float, ...]


@dataclass
class VoxelIntersectionTopology:
    """Angle-independent distance/height lattice topology.

    Each target stores only the upstream distance rows, segment widths and
    segment midpoints. No Sun angle, ray height, validity, nearest-height index,
    or optical evidence is stored here.
    """
    directions: dict[float, dict[str, Any]]
    target_plan_count: int = 0
    segment_count: int = 0


@dataclass
class VoxelIntersectionPlan:
    """Angle-specific geometry plan reusable by multiple optical evidence chains."""
    solar_altitude_deg: float
    radius_km: float
    directions: dict[float, dict[str, Any]]
    target_plan_count: int = 0
    segment_count: int = 0
    valid_segment_count: int = 0
    topology_cache_status: str = "BUILT"

    def as_legacy_dict(self) -> dict:
        """Compatibility view used by R5.7.7+ callers and CASE diagnostics."""
        return {
            "solar_altitude_deg": float(self.solar_altitude_deg),
            "radius_km": float(self.radius_km),
            "directions": self.directions,
            "target_plan_count": int(self.target_plan_count),
            "segment_count": int(self.segment_count),
            "valid_segment_count": int(self.valid_segment_count),
            "topology_cache_status": str(self.topology_cache_status),
            "plan_type": "VOXEL_INTERSECTION_PLAN_V1",
            "topology_version": "VOXEL_INTERSECTION_TOPOLOGY_V1_CROSS_ANGLE",
        }


def voxel_lattice_key(
    voxels: pd.DataFrame,
    *,
    direction_col: str = "direction_offset_deg",
    distance_col: str = "distance_km",
    height_col: str = "voxel_center_km",
) -> tuple:
    """Return a deterministic geometry-only lattice identity.

    The key contains no cloud/optical values and is safe to reuse across times
    and solar angles only when direction, distance and height coordinates are
    exactly identical.
    """
    if voxels is None or voxels.empty:
        return tuple()
    required = {direction_col, distance_col, height_col}
    if not required.issubset(voxels.columns):
        return tuple()
    out = []
    for off, g in voxels.groupby(direction_col, sort=True):
        d = tuple(map(float, sorted(pd.to_numeric(g[distance_col], errors="coerce").dropna().unique())))
        h = tuple(map(float, sorted(pd.to_numeric(g[height_col], errors="coerce").dropna().unique())))
        out.append((float(off), d, h))
    return tuple(out)


def build_voxel_intersection_topology(
    voxels: pd.DataFrame,
    *,
    direction_col: str = "direction_offset_deg",
    distance_col: str = "distance_km",
    height_col: str = "voxel_center_km",
) -> VoxelIntersectionTopology:
    """Build angle-independent upstream segment topology once per lattice."""
    if voxels is None or voxels.empty:
        return VoxelIntersectionTopology({})
    required = {direction_col, distance_col, height_col}
    if not required.issubset(voxels.columns):
        return VoxelIntersectionTopology({})

    directions: dict[float, dict[str, Any]] = {}
    target_plan_count = segment_count = 0

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

            # All height targets at the same distance share this exact topology.
            for z_t in heights:
                targets[(float(d_t), float(z_t))] = {
                    "i0": int(i0),
                    "ds": ds,
                    "dx": dx,
                    "valid_dx": valid_dx,
                    "mids": mids,
                    "upstream_row_index": rows,
                }
                target_plan_count += 1
                segment_count += int(ds.size)

        directions[float(off)] = {
            "distances": distances,
            "heights": heights,
            "di": di,
            "targets": targets,
            "signature": LatticeSignature(
                float(off), tuple(map(float, distances)), tuple(map(float, heights))
            ),
        }

    return VoxelIntersectionTopology(
        directions,
        target_plan_count=target_plan_count,
        segment_count=segment_count,
    )


def materialize_voxel_intersection_plan(
    topology: VoxelIntersectionTopology,
    solar_altitude_deg: float,
    *,
    radius_km: float = EARTH_RADIUS_KM,
    topology_cache_status: str = "HIT",
) -> VoxelIntersectionPlan:
    """Materialize angle-dependent geometry in distance-batched matrices.

    All target heights sharing the same target distance are evaluated in one
    broadcast ray matrix. Target dictionaries are retained only as a compact
    compatibility view for existing cloud-blocking consumers.
    """
    radius = float(radius_km)
    angle = float(solar_altitude_deg)
    cos_sun = max(0.05, math.cos(math.radians(abs(angle))))
    directions: dict[float, dict[str, Any]] = {}
    valid_segment_count = 0

    for off, topo_dir in topology.directions.items():
        distances = topo_dir["distances"]
        heights = topo_dir["heights"]
        targets: dict[tuple[float, float], dict[str, Any]] = {}

        # One ray matrix per target distance instead of one ray call per
        # (distance,height) target. The topology object guarantees all heights
        # at this distance share ds/dx/mids/upstream rows.
        for d_t in distances:
            first = topo_dir["targets"].get((float(d_t), float(heights[0])))
            if first is None:
                continue
            ds = first["ds"]
            dx = first["dx"]
            if ds.size:
                ray_matrix = ray_altitude_matrix_km(
                    float(d_t), heights, first["mids"], angle, radius
                )
                valid_matrix = first["valid_dx"][None,:] & np.isfinite(ray_matrix) & (ray_matrix >= 0.0)
                nearest_matrix = VerticalIndexPlan.from_centers(heights).nearest_indices(ray_matrix)
                slant_matrix = np.where(valid_matrix, dx[None,:]/cos_sun, 0.0)
            else:
                ray_matrix=np.empty((len(heights),0),dtype=float)
                valid_matrix=np.empty((len(heights),0),dtype=bool)
                nearest_matrix=np.empty((len(heights),0),dtype=int)
                slant_matrix=np.empty((len(heights),0),dtype=float)

            for zi,z_t in enumerate(heights):
                t=topo_dir["targets"][(float(d_t),float(z_t))]
                valid=valid_matrix[zi]
                targets[(float(d_t),float(z_t))]={
                    "i0":t["i0"], "ds":ds, "dx":dx, "valid":valid,
                    "ray_height_km":ray_matrix[zi],
                    "nearest_height_index":nearest_matrix[zi],
                    "upstream_row_index":t["upstream_row_index"],
                    "slant_km":slant_matrix[zi],
                }
                valid_segment_count += int(np.sum(valid))

        directions[float(off)]={
            "distances":distances, "heights":heights, "di":topo_dir["di"],
            "targets":targets, "signature":topo_dir["signature"],
        }

    return VoxelIntersectionPlan(
        angle, radius, directions,
        target_plan_count=int(topology.target_plan_count),
        segment_count=int(topology.segment_count),
        valid_segment_count=int(valid_segment_count),
        topology_cache_status=str(topology_cache_status),
    )


def build_voxel_intersection_plan(
    voxels: pd.DataFrame,
    solar_altitude_deg: float,
    *,
    radius_km: float = EARTH_RADIUS_KM,
    direction_col: str = "direction_offset_deg",
    distance_col: str = "distance_km",
    height_col: str = "voxel_center_km",
) -> VoxelIntersectionPlan:
    """Compatibility constructor: build topology then materialize one angle."""
    topology = build_voxel_intersection_topology(
        voxels,
        direction_col=direction_col,
        distance_col=distance_col,
        height_col=height_col,
    )
    return materialize_voxel_intersection_plan(
        topology,
        solar_altitude_deg,
        radius_km=radius_km,
        topology_cache_status="BUILT",
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
