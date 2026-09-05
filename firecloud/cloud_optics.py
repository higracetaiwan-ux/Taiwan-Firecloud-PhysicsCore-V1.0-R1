from __future__ import annotations

import math
import numpy as np
import pandas as pd

# Visible-band bulk densities / default effective radii used only when the
# forecast source does not provide particle effective radius. These are explicit
# assumptions, not retrieved microphysics.
RHO_WATER_KGM3 = 1000.0
RHO_ICE_KGM3 = 917.0
DEFAULT_LIQUID_REFF_UM = 10.0
DEFAULT_ICE_REFF_UM = 30.0
DEFAULT_QEXT_VISIBLE = 2.0


def _clip01(v):
    if pd.isna(v):
        return np.nan
    return max(0.0, min(1.0, float(v)))


def condensate_extinction_m1(
    liquid_water_content_gm3: float,
    ice_water_content_gm3: float,
    cloud_fraction: float = 1.0,
    liquid_reff_um: float = DEFAULT_LIQUID_REFF_UM,
    ice_reff_um: float = DEFAULT_ICE_REFF_UM,
    qext: float = DEFAULT_QEXT_VISIBLE,
) -> dict:
    """Estimate visible cloud extinction from condensate content.

    Geometric-optics approximation:
        beta_ext ~= 3 Qext M / (4 rho r_eff)
    which becomes 3 M / (2 rho r_eff) for Qext ~= 2.

    M is condensate mass concentration [kg m-3]. Missing liquid/ice content stays
    missing. Cloud fraction scales grid-cell-mean extinction; it is not a
    sub-grid overlap model.
    """
    if pd.isna(liquid_water_content_gm3) or pd.isna(ice_water_content_gm3):
        return {
            "liquid_extinction_m1": np.nan,
            "ice_extinction_m1": np.nan,
            "total_extinction_m1": np.nan,
            "cloud_fraction_used": np.nan if pd.isna(cloud_fraction) else _clip01(cloud_fraction),
            "optics_quality": "MISSING_NATIVE_CONDENSATE",
        }

    cf = 1.0 if pd.isna(cloud_fraction) else _clip01(cloud_fraction)
    ql = max(0.0, float(liquid_water_content_gm3)) / 1000.0  # g m-3 -> kg m-3
    qi = max(0.0, float(ice_water_content_gm3)) / 1000.0
    rl = max(1e-7, float(liquid_reff_um) * 1e-6)
    ri = max(1e-7, float(ice_reff_um) * 1e-6)

    beta_l = 3.0 * float(qext) * ql / (4.0 * RHO_WATER_KGM3 * rl)
    beta_i = 3.0 * float(qext) * qi / (4.0 * RHO_ICE_KGM3 * ri)
    beta = cf * (beta_l + beta_i)
    return {
        "liquid_extinction_m1": cf * beta_l,
        "ice_extinction_m1": cf * beta_i,
        "total_extinction_m1": beta,
        "cloud_fraction_used": cf,
        "optics_quality": "CONDENSATE_PLUS_ASSUMED_REFF",
    }


def add_native_optical_properties(
    native_voxels: pd.DataFrame,
    liquid_reff_um: float = DEFAULT_LIQUID_REFF_UM,
    ice_reff_um: float = DEFAULT_ICE_REFF_UM,
) -> pd.DataFrame:
    """Add microphysics-based visible extinction/COD for each native voxel.

    COD here is a model estimate based on native LWC/IWC plus assumed effective
    radii. It is more physical than cloud-cover extinction proxy, but it is not a
    retrieved/native model COD and must retain its provenance label.
    """
    if native_voxels.empty:
        return native_voxels.copy()
    rows = []
    for _, r in native_voxels.iterrows():
        ext = condensate_extinction_m1(
            r.get("liquid_water_content_gm3", np.nan),
            r.get("ice_water_content_gm3", np.nan),
            r.get("cloud_fraction", np.nan),
            liquid_reff_um,
            ice_reff_um,
        )
        thickness_m = max(0.0, float(r.get("voxel_top_km", 0.0)) - float(r.get("voxel_bottom_km", 0.0))) * 1000.0
        beta = ext["total_extinction_m1"]
        vertical_cod = np.nan if pd.isna(beta) else max(0.0, float(beta) * thickness_m)
        rec = r.to_dict()
        rec.update(ext)
        rec.update({
            "assumed_liquid_reff_um": float(liquid_reff_um),
            "assumed_ice_reff_um": float(ice_reff_um),
            "vertical_cloud_optical_depth_estimate": vertical_cod,
            "vertical_cloud_transmission_estimate": (math.exp(-vertical_cod) if not pd.isna(vertical_cod) else np.nan),
            "cloud_optical_model": "NATIVE_CONDENSATE_GEOMETRIC_OPTICS_ASSUMED_REFF",
        })
        rows.append(rec)
    return pd.DataFrame(rows)
