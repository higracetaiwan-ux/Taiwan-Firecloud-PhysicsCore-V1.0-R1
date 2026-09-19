"""Step 3Q.21 Band25 historical-source / runtime-weight scope qualification.

Evidence-only.  This module records source-domain constraints that narrow the
remaining Band25 reconstruction problem without substituting runtime RRTMG
interpolation/g-point machinery for the unrecovered Fu96 cloud pre-averaging
realization.
"""
from __future__ import annotations

from typing import Any

FU96_LINEAGE_SINGLE_SCATTERING_WAVELENGTH_SAMPLE_COUNT = 200
FU96_LINEAGE_SOLAR_PRIMARY_BAND_COUNT = 6
FU2007_DOI = "https://doi.org/10.1175/2007JAS2289.1"

# Current public AER RRTMG_SW tree pinned only as a runtime-scope witness.
# It is NOT promoted as the historical cloud pre-averaging generator.
AER_RRTMG_SW_RUNTIME_SCOPE_COMMIT = "286e84ed14f61e2279ba819f4ce512a30b48f0b3"
AER_RRTMG_SW_CLDPROP_PATH = "src/rrtmg_sw_cldprop.f90"
AER_RRTMG_SW_CLDPROP_BLOB_SHA = "71a1d4c86a19fe2de1af7e5682562688da25cde0"
AER_RRTMG_SW_INIT_PATH = "src/rrtmg_sw_init.f90"
AER_RRTMG_SW_INIT_BLOB_SHA = "1236caef0b669f96cb0b2405c723dc2664703595"
AER_RRTMG_SW_REPOSITORY = "https://github.com/AER-RC/RRTMG_SW"

RRTMG_FU96_RUNTIME_DGE_MIN_UM = 5.0
RRTMG_FU96_RUNTIME_DGE_MAX_UM = 140.0
RRTMG_FU96_RUNTIME_DGE_STEP_UM = 3.0
RRTMG_BAND25_WAVENUMBER_MIN_CM1 = 16000.0
RRTMG_BAND25_WAVENUMBER_MAX_CM1 = 22650.0


def band25_historical_scope_matrix() -> dict[str, Any]:
    """Return fail-closed Step 3Q.21 historical/runtime scope facts."""
    return {
        "FU96_LINEAGE_200_WAVELENGTH_SAMPLE_COUNT_QUALIFIED": True,
        "FU96_LINEAGE_SOLAR_PRIMARY_BAND_COUNT_QUALIFIED": True,
        "FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED": False,
        "RRTMG_FU96_RUNTIME_DGE_3UM_LINEAR_INTERPOLATION_PINNED": True,
        "RRTMG_RUNTIME_DGE_INTERPOLATION_IS_SPECTRAL_PREAVERAGING_REALIZATION": False,
        "RRTMG_BAND25_RUNTIME_GPOINT_REDUCTION_SCOPE_QUALIFIED": True,
        "RRTMG_BAND25_RUNTIME_RWGT_IS_CLOUD_PREAVERAGING_SOLAR_WEIGHT_VECTOR": False,
        "RRTMG_BAND25_RUNTIME_SFLUXREF_REDUCTION_PROVES_HISTORICAL_CLOUD_WEIGHTING": False,
        "RRTMG_BAND25_HISTORICAL_INTRABAND_INPUT_BUNDLE_COMPLETE": False,
        "RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED": False,
        "RRTMG_BAND25_EXACT_REPRODUCTION_PASS": False,
        "EXACT_FU96_BAND_WEIGHTING_AVAILABLE": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
    }


def pinned_runtime_scope_sources() -> dict[str, Any]:
    return {
        "fu2007_doi": FU2007_DOI,
        "fu96_lineage_single_scattering_wavelength_sample_count": FU96_LINEAGE_SINGLE_SCATTERING_WAVELENGTH_SAMPLE_COUNT,
        "fu96_lineage_solar_primary_band_count": FU96_LINEAGE_SOLAR_PRIMARY_BAND_COUNT,
        "aer_rrtmg_sw_runtime_scope_commit": AER_RRTMG_SW_RUNTIME_SCOPE_COMMIT,
        "aer_rrtmg_sw_cldprop_path": AER_RRTMG_SW_CLDPROP_PATH,
        "aer_rrtmg_sw_cldprop_blob_sha": AER_RRTMG_SW_CLDPROP_BLOB_SHA,
        "aer_rrtmg_sw_init_path": AER_RRTMG_SW_INIT_PATH,
        "aer_rrtmg_sw_init_blob_sha": AER_RRTMG_SW_INIT_BLOB_SHA,
        "rrtmg_fu96_runtime_dge_min_um": RRTMG_FU96_RUNTIME_DGE_MIN_UM,
        "rrtmg_fu96_runtime_dge_max_um": RRTMG_FU96_RUNTIME_DGE_MAX_UM,
        "rrtmg_fu96_runtime_dge_step_um": RRTMG_FU96_RUNTIME_DGE_STEP_UM,
        "rrtmg_band25_wavenumber_min_cm1": RRTMG_BAND25_WAVENUMBER_MIN_CM1,
        "rrtmg_band25_wavenumber_max_cm1": RRTMG_BAND25_WAVENUMBER_MAX_CM1,
    }
