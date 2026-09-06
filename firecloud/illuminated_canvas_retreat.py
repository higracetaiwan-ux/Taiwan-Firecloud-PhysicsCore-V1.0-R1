"""PhysicsCore V1.0-R5.3 illuminated-canvas retreat diagnostics.

Geometry and spectral RT remain separate:
- Geometry track: finite-solar-disk F_sun only, indicating where direct sunlight is geometrically accessible.
- Physical-red track: only canvases with resolved Sun->CloudBase spectral RT and positive red-band base illumination.

The module never turns geometric access into a firecloud claim.
"""
from __future__ import annotations

import math
import pandas as pd

from .geometry import direct_solar_fraction_g0
from .penumbra_red import CORE_DISTANCES_KM

REFERENCE_CLOUD_BASE_HEIGHTS_KM = (4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0)


def _finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def _weighted_centroid(distance: pd.Series, weight: pd.Series) -> float:
    d = pd.to_numeric(distance, errors="coerce")
    w = pd.to_numeric(weight, errors="coerce")
    m = d.notna() & w.notna() & (w > 0)
    if not bool(m.any()):
        return float("nan")
    return float((d[m] * w[m]).sum() / w[m].sum())


def build_illuminated_canvas_retreat(canvas_penumbra: pd.DataFrame) -> pd.DataFrame:
    """Summarize outward retreat of actual Canvas illumination by solar altitude.

    `GEOMETRY_*` fields use only F_sun. `PHYSICAL_RED_*` fields require the
    already-resolved spectral RT / CloudBase illumination result. Missing RT
    remains Missing and does not contaminate the geometry track.
    """
    if canvas_penumbra is None or canvas_penumbra.empty:
        return pd.DataFrame()

    df = canvas_penumbra.copy()
    df["solar_altitude_deg"] = pd.to_numeric(df.get("solar_altitude_deg"), errors="coerce")
    df["distance_km"] = pd.to_numeric(df.get("distance_km"), errors="coerce")
    df["direct_solar_fraction"] = pd.to_numeric(df.get("direct_solar_fraction"), errors="coerce")
    df["cloud_base_altitude_km"] = pd.to_numeric(df.get("cloud_base_altitude_km"), errors="coerce")

    rows = []
    for angle, g in df.dropna(subset=["solar_altitude_deg"]).groupby("solar_altitude_deg", sort=False):
        geom = g[g["direct_solar_fraction"].fillna(0.0) > 0.0].copy()
        full = g[g["direct_solar_fraction"].fillna(0.0) >= 1.0 - 1e-12].copy()
        red_resolved = g[g.get("red_base_illumination_resolved", pd.Series(False, index=g.index)).fillna(False).astype(bool)].copy()
        red_lit = g[g.get("red_light_reaches_cloudbase", pd.Series(False, index=g.index)).fillna(False).astype(bool)].copy()

        def mm(x):
            if x.empty:
                return (float("nan"), float("nan"))
            s = pd.to_numeric(x["distance_km"], errors="coerce").dropna()
            return (float(s.min()), float(s.max())) if not s.empty else (float("nan"), float("nan"))

        gn, gf = mm(geom)
        fn, ff = mm(full)
        rn, rf = mm(red_lit)
        rows.append({
            "solar_altitude_deg": float(angle),
            "canvas_count": int(len(g)),
            "geometry_any_sun_canvas_count": int(len(geom)),
            "geometry_nearest_any_sun_km": gn,
            "geometry_farthest_any_sun_km": gf,
            "geometry_fsun_weighted_centroid_km": _weighted_centroid(g["distance_km"], g["direct_solar_fraction"]),
            "geometry_full_sun_canvas_count": int(len(full)),
            "geometry_nearest_full_sun_km": fn,
            "geometry_farthest_full_sun_km": ff,
            "geometry_mean_cloud_base_km": float(pd.to_numeric(geom.get("cloud_base_altitude_km"), errors="coerce").mean()) if not geom.empty else float("nan"),
            "physical_red_rt_resolved_canvas_count": int(len(red_resolved)),
            "physical_red_illuminated_canvas_count": int(len(red_lit)),
            "physical_red_nearest_illuminated_km": rn,
            "physical_red_farthest_illuminated_km": rf,
            "physical_red_distance_centroid_km": float(pd.to_numeric(red_lit.get("distance_km"), errors="coerce").mean()) if not red_lit.empty else float("nan"),
            "geometry_track_state": "RESOLVED" if bool(g["direct_solar_fraction"].notna().all()) else "PARTIAL",
            "physical_red_track_state": "RESOLVED" if len(red_resolved) == len(g) else ("PARTIAL" if len(red_resolved) else "MISSING_RT"),
            "note": "GEOMETRY_RETREAT_USES_F_SUN_ONLY;PHYSICAL_RED_RETREAT_REQUIRES_RESOLVED_SPECTRAL_RT;NO_GEOMETRY_TO_FIRECLOUD_PROMOTION",
        })

    out = pd.DataFrame(rows).sort_values("solar_altitude_deg", ascending=False).reset_index(drop=True)
    # Positive delta means the illuminated envelope moved outward as the Sun descended.
    for col in ("geometry_nearest_any_sun_km", "geometry_fsun_weighted_centroid_km", "physical_red_nearest_illuminated_km", "physical_red_distance_centroid_km"):
        out[f"{col}_delta_from_previous_angle_km"] = pd.to_numeric(out[col], errors="coerce").diff()
    return out


def build_reference_canvas_retreat_matrix(
    solar_altitudes_deg,
    *,
    distances_km=CORE_DISTANCES_KM,
    cloud_base_heights_km=REFERENCE_CLOUD_BASE_HEIGHTS_KM,
) -> pd.DataFrame:
    """Geometry-only reference matrix for fixed cloud-base heights.

    This table lets a CASE diagnose how 4–8 km medium/high clouds geometrically
    retreat outward even when the forecast happens not to contain such clouds.
    It is explicitly NOT spectral RT and NOT a firecloud forecast.
    """
    rows = []
    for angle in solar_altitudes_deg:
        a = float(angle)
        for z in cloud_base_heights_km:
            fs = [(float(d), float(direct_solar_fraction_g0(float(d), float(z), a))) for d in distances_km]
            any_sun = [d for d, f in fs if f > 0.0]
            full_sun = [d for d, f in fs if f >= 1.0 - 1e-12]
            partial = [d for d, f in fs if 0.0 < f < 1.0]
            rows.append({
                "solar_altitude_deg": a,
                "reference_cloud_base_km": float(z),
                "nearest_any_sun_km": min(any_sun) if any_sun else float("nan"),
                "farthest_any_sun_km": max(any_sun) if any_sun else float("nan"),
                "nearest_full_sun_km": min(full_sun) if full_sun else float("nan"),
                "farthest_full_sun_km": max(full_sun) if full_sun else float("nan"),
                "partial_penumbra_distance_count": int(len(partial)),
                "any_sun_distance_count": int(len(any_sun)),
                "full_sun_distance_count": int(len(full_sun)),
                "distance_grid_km": ";".join(str(int(d)) if float(d).is_integer() else str(d) for d in distances_km),
                "geometry_only": True,
                "spectral_rt_included": False,
                "note": "REFERENCE_GEOMETRY_ONLY;USE_TO_DIAGNOSE_OUTWARD_RETREAT_OF_FIXED_CLOUD_HEIGHTS;NOT_A_FIRECLOUD_CLAIM",
            })
    return pd.DataFrame(rows)
