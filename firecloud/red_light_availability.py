"""R5.7.26 Red-Light Availability diagnostics.

This branch answers a Formation prerequisite that exists even when no real
Canvas cloud is present:

    Sun -> forward atmospheric / hypothetical Canvas-region receiver

It never creates a cloud, never fabricates COT, and never claims Firecloud
Formation.  It preserves the frozen separation:

    Red-Light Availability != Effective Canvas != Canvas Optical Response

The reference receivers are sampling surfaces only.  Their purpose is to ask
"if a suitable cloud base existed here, could the six-band direct-solar field
reach it through the resolved atmosphere and upstream blockers?"
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .contracts import (
    SIX_BAND_WAVELENGTHS_NM,
    CanvasCandidate, CanvasDomain, GeometryConfidence,
)
from .geometry import direct_solar_fraction_g0
from .optical_path import build_reference_receiver_cloud_path_evidence
from .precipitation import build_precipitation_path_evidence
from .spectral_rt import build_spectral_rt

REFERENCE_DIRECTIONS_DEG = (-5.0, 0.0, 5.0)
REFERENCE_PRIMARY_DISTANCES_KM = (10.0, 20.0, 30.0, 40.0)
REFERENCE_EXTENDED_DISTANCES_KM = (60.0, 80.0, 100.0)
REFERENCE_CLOUD_BASES_KM = (4.0, 5.0, 8.0, 12.0)
RED_DIAGNOSTIC_BANDS_NM = (600, 650, 700, 750)


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _nearest_row(g: pd.DataFrame, col: str, value: float) -> pd.DataFrame:
    if g.empty or col not in g.columns:
        return pd.DataFrame()
    x = pd.to_numeric(g[col], errors="coerce")
    if not x.notna().any():
        return pd.DataFrame()
    delta = (x - float(value)).abs()
    m = delta == delta.min()
    return g.loc[m].head(1)


def build_reference_receiver_targets(
    native_optical_voxels: pd.DataFrame,
    *,
    solar_altitude_deg: float,
    directions_deg: Iterable[float] = REFERENCE_DIRECTIONS_DEG,
    primary_distances_km: Iterable[float] = REFERENCE_PRIMARY_DISTANCES_KM,
    extended_distances_km: Iterable[float] = REFERENCE_EXTENDED_DISTANCES_KM,
    reference_cloud_bases_km: Iterable[float] = REFERENCE_CLOUD_BASES_KM,
) -> pd.DataFrame:
    """Select small virtual receiving surfaces from the existing native lattice.

    The selected row is only a carrier for route point, native upstream cloud
    ray evidence, gas/aerosol integration coordinates and vertical location.
    `reference_cloud_base_km` records the requested nominal height; the actual
    sampled voxel centre is exported separately and is used for F_sun/RT.
    """
    if native_optical_voxels is None or native_optical_voxels.empty:
        return pd.DataFrame()
    g0 = native_optical_voxels.copy()
    if "solar_altitude_deg" in g0.columns:
        a = pd.to_numeric(g0["solar_altitude_deg"], errors="coerce")
        g0 = g0[(a - float(solar_altitude_deg)).abs() <= 1e-9]
    if g0.empty:
        return pd.DataFrame()

    rows = []
    specs = [
        ("PRIMARY_CANVAS_0_40", d) for d in primary_distances_km
    ] + [
        ("EXTENDED_CANVAS_40_100", d) for d in extended_distances_km
    ]
    for off in directions_deg:
        gd = _nearest_row(g0, "direction_offset_deg", float(off))
        if gd.empty:
            continue
        actual_off = float(pd.to_numeric(gd["direction_offset_deg"], errors="coerce").iloc[0])
        # Re-expand to all rows at the selected exact native direction.
        dirs = pd.to_numeric(g0["direction_offset_deg"], errors="coerce")
        gd = g0[(dirs - actual_off).abs() <= 1e-9]
        for domain, dist_nom in specs:
            gx = _nearest_row(gd, "distance_km", float(dist_nom))
            if gx.empty:
                continue
            actual_dist = float(pd.to_numeric(gx["distance_km"], errors="coerce").iloc[0])
            dist = pd.to_numeric(gd["distance_km"], errors="coerce")
            gx = gd[(dist - actual_dist).abs() <= 1e-9]
            for z_nom in reference_cloud_bases_km:
                gz = _nearest_row(gx, "voxel_center_km", float(z_nom))
                if gz.empty:
                    continue
                r = gz.iloc[0].copy()
                z = float(pd.to_numeric(pd.Series([r.get("voxel_center_km")]), errors="coerce").iloc[0])
                rid = f"redref::dir{actual_off:+.1f}_d{actual_dist:.1f}_z{z:.2f}"
                r["reference_receiver_id"] = rid
                r["reference_domain"] = domain
                r["reference_cloud_base_km"] = float(z_nom)
                r["sampled_receiver_altitude_km"] = z
                r["v1_direct_solar_fraction"] = float(direct_solar_fraction_g0(actual_dist, z, float(solar_altitude_deg)))
                r["red_light_reference_receiver"] = True
                rows.append(r)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).reset_index(drop=True)
    out["solar_altitude_deg"] = float(solar_altitude_deg)
    return out


def _virtual_canvases(receivers: pd.DataFrame) -> list[CanvasCandidate]:
    out: list[CanvasCandidate] = []
    if receivers is None or receivers.empty:
        return out
    for _, r in receivers.iterrows():
        off = float(r["direction_offset_deg"]); dist = float(r["distance_km"])
        domain = CanvasDomain.PRIMARY_CANVAS_0_40 if dist <= 40.0 + 1e-9 else CanvasDomain.EXTENDED_CANVAS_40_100
        out.append(CanvasCandidate(
            canvas_id=str(r["reference_receiver_id"]),
            cloud_layer_id=f"dir{off:+.1f}_d{dist:.1f}_REDREF",
            latitude=float("nan"), longitude=float("nan"),
            cloud_base_altitude_km=float(r["sampled_receiver_altitude_km"]),
            distance_km=dist, azimuth_deg=float("nan"),
            operational_domain=domain,
            geometry_confidence=GeometryConfidence.HIGH,
            provenance=(),
        ))
    return out


def build_red_light_reference_evidence(
    *,
    native_optical_voxels: pd.DataFrame,
    scene,
    route_snapshot: pd.DataFrame,
    aerosol_spectral_snapshot: pd.DataFrame,
    cams_native_aerosol_snapshot: pd.DataFrame,
    gas_profile: pd.DataFrame,
    solar_altitude_deg: float,
    earth_radius_km: float,
    valid_time=None,
    secondary_forecast_optics: pd.DataFrame | None = None,
    cloud_geometry_completeness: float = 1.0,
    gas_prepared_context=None,
) -> pd.DataFrame:
    """Build six-band Red-Light Availability on virtual forward receivers.

    `RED_LIGHT_PATH_OPEN` is intentionally structural, not a new score: it means
    the receiver is geometrically sunlit, all gas/aerosol/cloud/precipitation
    path evidence is resolved, and no upstream cloud/hydrometeor blocker
    intersects the reference ray.  Molecular/aerosol attenuation is retained in
    the six-band availability values and may be strong even on an "open" path.
    """
    receivers = build_reference_receiver_targets(
        native_optical_voxels, solar_altitude_deg=float(solar_altitude_deg)
    )
    if receivers.empty:
        return pd.DataFrame()

    spectral = build_spectral_rt(
        receivers, float(solar_altitude_deg),
        aerosol_snapshot=aerosol_spectral_snapshot,
        cams_native_aerosol_snapshot=cams_native_aerosol_snapshot,
        angstrom_exponent=None,
        earth_radius_km=float(earth_radius_km),
        gas_profile=gas_profile,
        prepared_route_spectral_aod=aerosol_spectral_snapshot,
        gas_prepared_context=gas_prepared_context,
    )
    cloud = build_reference_receiver_cloud_path_evidence(
        scene, receivers,
        solar_altitude_deg=float(solar_altitude_deg),
        earth_radius_km=float(earth_radius_km),
        secondary_forecast_optics=secondary_forecast_optics,
        cloud_geometry_completeness=float(cloud_geometry_completeness),
    )
    virtual = _virtual_canvases(receivers)
    precip = build_precipitation_path_evidence(
        virtual, route_snapshot, valid_time=valid_time,
        solar_altitude_deg=float(solar_altitude_deg), earth_radius_km=float(earth_radius_km),
    )
    if not precip.empty:
        precip = precip.rename(columns={"canvas_id": "reference_receiver_id"})

    base_cols = [
        "reference_receiver_id", "reference_domain", "reference_cloud_base_km",
        "sampled_receiver_altitude_km", "direction_offset_deg", "distance_km",
        "v1_direct_solar_fraction", "point_id",
    ]
    out = spectral.copy()
    out = out.merge(cloud, on=[c for c in ["reference_receiver_id","direction_offset_deg","distance_km","reference_cloud_base_km","sampled_receiver_altitude_km"] if c in out.columns and c in cloud.columns], how="left", suffixes=("", "_cloudref"))
    if not precip.empty:
        keep = [c for c in precip.columns if c == "reference_receiver_id" or c.startswith("tau_precip_") or c in {
            "status","optical_evidence","hydrometeor_intersection_count",
            "hydrometeor_unresolved_intersection_count","native_hydrometeor_field_completeness",
        }]
        p = precip[keep].copy().rename(columns={
            "status":"precipitation_path_status",
            "optical_evidence":"precipitation_optical_evidence",
        })
        out = out.merge(p, on="reference_receiver_id", how="left")

    fsun = pd.to_numeric(out.get("v1_direct_solar_fraction"), errors="coerce").fillna(0.0)
    gas_comp = pd.to_numeric(out.get("gas_path_completeness", pd.Series(0.0, index=out.index)), errors="coerce").fillna(0.0)
    gas_domain = out.get("gas_rt_domain_status", pd.Series("MISSING", index=out.index)).astype(str)
    gas_q = out.get("gas_rt_quality", pd.Series("", index=out.index)).astype(str)
    gas_ready = gas_q.str.startswith("HITRAN_DERIVED_3D_GAS_RT") & (~gas_domain.str.startswith("TRUE_")) & (gas_comp >= 0.999)
    aerosol_ready = out.get("aerosol_rt_path_complete", pd.Series(False, index=out.index)).fillna(False).astype(bool)
    cloud_state = out.get("cloud_path_evidence_state", pd.Series("MISSING", index=out.index)).astype(str)
    cloud_ready = cloud_state.eq("FULL")
    precip_ev = out.get("precipitation_optical_evidence", pd.Series("MISSING", index=out.index)).astype(str)
    precip_ready = precip_ev.eq("FULL")
    cloud_hits = pd.to_numeric(out.get("upstream_cloud_intersection_count", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(0)
    precip_hits = pd.to_numeric(out.get("hydrometeor_intersection_count", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(0)

    total_band_ready = pd.Series(True, index=out.index, dtype=bool)
    for wl in SIX_BAND_WAVELENGTHS_NM:
        ray = pd.to_numeric(out.get(f"rayleigh_transmission_{int(wl)}nm", pd.Series(np.nan, index=out.index)), errors="coerce")
        aer = pd.to_numeric(out.get(f"aerosol_transmission_{int(wl)}nm", pd.Series(np.nan, index=out.index)), errors="coerce")
        gas = pd.to_numeric(out.get(f"gas_transmission_{int(wl)}nm", pd.Series(np.nan, index=out.index)), errors="coerce")
        ctrans = pd.to_numeric(out.get("resolved_upstream_cloud_transmission", pd.Series(np.nan, index=out.index)), errors="coerce")
        ptau = pd.to_numeric(out.get(f"tau_precip_{int(wl)}nm", pd.Series(np.nan, index=out.index)), errors="coerce")
        ptrans = np.exp(-ptau)
        t = ray * aer * gas * ctrans * ptrans
        valid = ray.notna() & aer.notna() & gas.notna() & ctrans.notna() & ptau.notna()
        total_band_ready &= valid
        out[f"reference_total_transmission_{int(wl)}nm"] = t.where(valid, np.nan)
        out[f"red_light_availability_{int(wl)}nm"] = (fsun * t).where(valid, np.nan)

    evidence_ready = gas_ready & aerosol_ready & cloud_ready & precip_ready & total_band_ready
    no_resolved_blocker = cloud_hits.eq(0) & precip_hits.eq(0)
    cloud_conflict = cloud_state.eq("DIRECT_EVIDENCE_CONFLICT")
    path_state = np.select(
        [
            fsun <= 0.0,
            (fsun > 0.0) & cloud_conflict,
            (fsun > 0.0) & (~evidence_ready),
            (fsun > 0.0) & evidence_ready & no_resolved_blocker,
            (fsun > 0.0) & evidence_ready & (~no_resolved_blocker),
        ],
        [
            "NO_DIRECT_RED_ACCESS",
            "RED_LIGHT_PATH_CONFLICT",
            "RED_LIGHT_PATH_UNKNOWN",
            "RED_LIGHT_PATH_OPEN",
            "RED_LIGHT_PATH_ATTENUATED_BY_RESOLVED_BLOCKER",
        ],
        default="RED_LIGHT_PATH_UNKNOWN",
    )
    out["red_light_path_state"] = path_state
    out["red_light_path_evidence_complete"] = evidence_ready
    red_cols = [f"red_light_availability_{w}nm" for w in RED_DIAGNOSTIC_BANDS_NM]
    out["red_band_mean_availability"] = out[red_cols].mean(axis=1, skipna=False)
    out["red_band_min_availability"] = out[red_cols].min(axis=1, skipna=False)
    out["red_light_reference_note"] = (
        "REFERENCE_RECEIVER_IS_NOT_CANVAS;RED_LIGHT_AVAILABILITY_IS_FORMATION_PREREQUISITE_ONLY;"
        "SIX_BANDS_PRESERVED;RED_BAND_MEAN_IS_POST_RT_DIAGNOSTIC_NOT_PHYSICS_SCORE"
    )
    out["time"] = valid_time
    out["solar_altitude_deg"] = float(solar_altitude_deg)
    return out


def summarize_red_light_availability(
    reference_evidence: pd.DataFrame,
    canvas_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Summarize Primary/Extended path state and no-Canvas Formation context."""
    if reference_evidence is None or reference_evidence.empty:
        return pd.DataFrame()
    df = reference_evidence.copy()
    rows = []
    for (t, angle), ga in df.groupby(["time","solar_altitude_deg"], dropna=False, sort=False):
        domain_rows = {}
        for domain in ("PRIMARY_CANVAS_0_40", "EXTENDED_CANVAS_40_100"):
            g = ga[ga["reference_domain"].astype(str).eq(domain)].copy()
            fs = pd.to_numeric(g.get("v1_direct_solar_fraction"), errors="coerce").fillna(0.0)
            sun = g[fs > 0.0]
            st = sun.get("red_light_path_state", pd.Series(dtype=str)).astype(str)
            if sun.empty:
                dstate = "NO_DIRECT_RED_ACCESS"
            elif st.eq("RED_LIGHT_PATH_OPEN").all():
                dstate = "RED_LIGHT_PATH_OPEN"
            elif st.eq("RED_LIGHT_PATH_ATTENUATED_BY_RESOLVED_BLOCKER").all():
                dstate = "RED_LIGHT_PATH_ATTENUATED"
            elif st.isin(["RED_LIGHT_PATH_OPEN","RED_LIGHT_PATH_ATTENUATED_BY_RESOLVED_BLOCKER"]).any():
                dstate = "RED_LIGHT_PATH_PARTIAL"
            elif st.eq("RED_LIGHT_PATH_CONFLICT").any():
                dstate = "RED_LIGHT_PATH_CONFLICT"
            else:
                dstate = "RED_LIGHT_PATH_UNKNOWN"
            avail = pd.to_numeric(sun.get("red_band_mean_availability", pd.Series(dtype=float)), errors="coerce")
            domain_rows[domain] = {
                "state": dstate,
                "reference_count": int(len(g)),
                "sunlit_reference_count": int(len(sun)),
                "open_reference_count": int(st.eq("RED_LIGHT_PATH_OPEN").sum()),
                "attenuated_reference_count": int(st.eq("RED_LIGHT_PATH_ATTENUATED_BY_RESOLVED_BLOCKER").sum()),
                "unknown_reference_count": int(st.isin(["RED_LIGHT_PATH_UNKNOWN","RED_LIGHT_PATH_CONFLICT"]).sum()),
                "mean_availability": float(avail.mean()) if avail.notna().any() else float("nan"),
                "max_availability": float(avail.max()) if avail.notna().any() else float("nan"),
            }

        ps = domain_rows["PRIMARY_CANVAS_0_40"]["state"]
        es = domain_rows["EXTENDED_CANVAS_40_100"]["state"]
        if ps == es == "RED_LIGHT_PATH_OPEN":
            overall = "RED_LIGHT_PATH_OPEN"
        elif ps == es == "NO_DIRECT_RED_ACCESS":
            overall = "NO_DIRECT_RED_ACCESS"
        elif "RED_LIGHT_PATH_CONFLICT" in (ps, es):
            overall = "RED_LIGHT_PATH_CONFLICT"
        elif "RED_LIGHT_PATH_UNKNOWN" in (ps, es):
            overall = "RED_LIGHT_PATH_UNKNOWN"
        elif any(s in {"RED_LIGHT_PATH_OPEN","RED_LIGHT_PATH_PARTIAL"} for s in (ps, es)):
            overall = "RED_LIGHT_PATH_PARTIAL"
        elif ps == es == "RED_LIGHT_PATH_ATTENUATED":
            overall = "RED_LIGHT_PATH_ATTENUATED"
        else:
            overall = "RED_LIGHT_PATH_PARTIAL"

        # Canvas absence is a physical conclusion only when the cloud-geometry
        # dependency is complete. Zero candidates from an incomplete CloudScene
        # are UNKNOWN, not proof of a clear/no-cloud Canvas region.
        geom_vals = pd.to_numeric(
            ga.get("cloud_geometry_completeness", pd.Series(np.nan, index=ga.index)),
            errors="coerce",
        ).dropna()
        canvas_geometry_completeness = float(geom_vals.min()) if len(geom_vals) else float("nan")
        canvas_geometry_resolved = bool(
            _finite(canvas_geometry_completeness) and canvas_geometry_completeness >= 0.999
        )

        c = canvas_candidates if canvas_candidates is not None else pd.DataFrame()
        if not c.empty and "solar_altitude_deg" in c.columns:
            ca = c[(pd.to_numeric(c["solar_altitude_deg"], errors="coerce") - float(angle)).abs() <= 1e-9].copy()
        else:
            ca = pd.DataFrame()
        if not ca.empty and "distance_km" in ca.columns:
            dist = pd.to_numeric(ca["distance_km"], errors="coerce")
            pc = int((dist <= 40.0 + 1e-9).sum())
            ec = int(((dist > 40.0 + 1e-9) & (dist <= 100.0 + 1e-9)).sum())
        else:
            pc = ec = 0
        no_canvas = (pc == 0 and ec == 0 and canvas_geometry_resolved)
        if no_canvas:
            context = {
                "RED_LIGHT_PATH_OPEN": "CLEAR_RED_PATH_NO_CANVAS",
                "RED_LIGHT_PATH_PARTIAL": "PARTIAL_RED_PATH_NO_CANVAS",
                "RED_LIGHT_PATH_ATTENUATED": "RED_PATH_ATTENUATED_NO_CANVAS",
                "NO_DIRECT_RED_ACCESS": "NO_CANVAS_NO_DIRECT_RED_ACCESS",
                "RED_LIGHT_PATH_CONFLICT": "NO_CANVAS_RED_PATH_CONFLICT",
            }.get(overall, "NO_CANVAS_RED_PATH_UNKNOWN")
        elif pc == 0 and ec == 0:
            context = "CANVAS_AVAILABILITY_UNKNOWN"
        else:
            context = "CANVAS_PRESENT_EVALUATE_FORMATION"

        pav = domain_rows["PRIMARY_CANVAS_0_40"]
        eav = domain_rows["EXTENDED_CANVAS_40_100"]
        vals = [x for x in [pav["mean_availability"], eav["mean_availability"]] if _finite(x)]
        vmax = [x for x in [pav["max_availability"], eav["max_availability"]] if _finite(x)]
        rows.append({
            "time": t, "solar_altitude_deg": float(angle),
            "red_light_path_state": overall,
            "primary_red_light_path_state": ps,
            "extended_red_light_path_state": es,
            "primary_canvas_count": pc,
            "extended_canvas_count": ec,
            "primary_canvas_state": ("AVAILABLE" if pc > 0 else ("ABSENT" if canvas_geometry_resolved else "UNKNOWN")),
            "extended_canvas_state": ("AVAILABLE" if ec > 0 else ("ABSENT" if canvas_geometry_resolved else "UNKNOWN")),
            "canvas_geometry_completeness": canvas_geometry_completeness,
            "canvas_geometry_evidence_state": "FULL" if canvas_geometry_resolved else "MISSING_OR_PARTIAL",
            "formation_context_state": context,
            "primary_open_reference_count": pav["open_reference_count"],
            "extended_open_reference_count": eav["open_reference_count"],
            "primary_sunlit_reference_count": pav["sunlit_reference_count"],
            "extended_sunlit_reference_count": eav["sunlit_reference_count"],
            "red_light_availability_mean": float(np.mean(vals)) if vals else float("nan"),
            "red_light_availability_max": float(np.max(vmax)) if vmax else float("nan"),
            "unused_red_light_potential_applicable": bool(no_canvas and len(vals) > 0),
            "unused_red_light_potential": float(np.mean(vals)) if no_canvas and vals else float("nan"),
            "potential_scale_status": "CONTINUOUS_UNCALIBRATED_DIAGNOSTIC",
            "note": "RED_LIGHT_AVAILABILITY_NEQ_FORMATION;NO_CANVAS_NEQ_BAD_RED_LIGHT;GLOW_BRANCH_REMAINS_INDEPENDENT",
        })
    return pd.DataFrame(rows)


def apply_red_light_context_to_formation(formation: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Promote only the *reason for no Formation*; never create Formation."""
    if formation is None or formation.empty or summary is None or summary.empty:
        return formation if isinstance(formation, pd.DataFrame) else pd.DataFrame()
    out = formation.copy()
    out["formation_state_base"] = out.get("formation_state")
    add_cols = [
        "red_light_path_state","primary_canvas_state","extended_canvas_state",
        "formation_context_state","unused_red_light_potential","potential_scale_status",
    ]
    s = summary[[c for c in ["time","solar_altitude_deg",*add_cols] if c in summary.columns]].copy()
    out = out.merge(s, on=[c for c in ["time","solar_altitude_deg"] if c in out.columns and c in s.columns], how="left")
    m = out["formation_state_base"].astype(str).eq("NO_CANVAS_EVIDENCE") & out["formation_context_state"].notna()
    out.loc[m, "formation_state"] = out.loc[m, "formation_context_state"].astype(str)
    hi = m & out["formation_state"].astype(str).isin(["CLEAR_RED_PATH_NO_CANVAS","NO_CANVAS_NO_DIRECT_RED_ACCESS"])
    if "formation_confidence" in out.columns:
        out.loc[hi, "formation_confidence"] = "HIGH"
    return out


def apply_red_light_context_to_headline_summary(summary: pd.DataFrame, red_summary: pd.DataFrame) -> pd.DataFrame:
    """Bridge Red-Light/Canvas context into the legacy headline table.

    The inherited ``physics_score`` column is retained only for archive/backward
    compatibility.  When there is no effective Canvas it is explicitly marked
    inapplicable and cannot participate in operational angle selection.  A
    resolved no-Canvas context may replace an earlier legacy
    ``UNKNOWN / DATA INCOMPLETE`` headline, but this helper never creates a
    Firecloud Formation score or Glow result.
    """
    if summary is None or summary.empty:
        return summary if isinstance(summary, pd.DataFrame) else pd.DataFrame()
    out = summary.copy()
    for c in [
        "red_light_path_state", "primary_red_light_path_state",
        "extended_red_light_path_state", "formation_context_state",
        "primary_canvas_state", "extended_canvas_state",
        "unused_red_light_potential", "potential_scale_status",
        "legacy_physics_score_applicable",
    ]:
        if c not in out.columns:
            if c == "unused_red_light_potential":
                out[c] = np.nan
            elif c == "legacy_physics_score_applicable":
                out[c] = True
            else:
                out[c] = ""
    if red_summary is None or red_summary.empty:
        return out

    no_canvas_contexts = {
        "CLEAR_RED_PATH_NO_CANVAS",
        "PARTIAL_RED_PATH_NO_CANVAS",
        "RED_PATH_ATTENUATED_NO_CANVAS",
        "NO_CANVAS_NO_DIRECT_RED_ACCESS",
        "NO_CANVAS_RED_PATH_CONFLICT",
        "NO_CANVAS_RED_PATH_UNKNOWN",
    }
    for _, rr in red_summary.iterrows():
        try:
            angle = float(rr.get("solar_altitude_deg"))
        except Exception:
            continue
        mask = np.isclose(pd.to_numeric(out.get("solar_altitude_deg"), errors="coerce"), angle)
        for c in [
            "red_light_path_state", "primary_red_light_path_state",
            "extended_red_light_path_state", "formation_context_state",
            "primary_canvas_state", "extended_canvas_state",
            "unused_red_light_potential", "potential_scale_status",
        ]:
            if c in rr.index:
                out.loc[mask, c] = rr.get(c)
        ctx = str(rr.get("formation_context_state", ""))
        if ctx in no_canvas_contexts:
            out.loc[mask, "legacy_physics_score_applicable"] = False
            if "core_score_eligible" in out.columns:
                out.loc[mask, "core_score_eligible"] = False
            # The absence of an effective Canvas is already a resolved
            # Formation outcome.  Red-Light UNKNOWN/CONFLICT describes the
            # independent illumination prerequisite and must not resurrect a
            # legacy score or generic DATA INCOMPLETE headline.
            if "operational_decision" in out.columns:
                out.loc[mask, "operational_decision"] = ctx
    return out
