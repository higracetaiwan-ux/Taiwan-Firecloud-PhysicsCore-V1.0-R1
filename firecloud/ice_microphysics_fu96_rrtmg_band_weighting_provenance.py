"""Ice Optics Phase 2 Step 3Q.17 — Fu96-lineage broadband weighting equation transcription correction.

This step corrects the Step3Q diagnostic/provenance transcription of the Fu96-lineage
shortwave broadband averaging equations. The linear and logarithmic single-scattering
co-albedo means are extinction-weighted as well as TOA-solar-irradiance-weighted, and
the band-mean asymmetry factor is scattering-weighted. This is a provenance-contract
correction only; frozen Formation/Viewing/Twilight Glow science is unchanged.

This step pins the public AER-RC rrtmgp-band-generation repository as an imported historical
RRTM_BAND_GEN SVN work tree and qualifies its recovered scope.  The 2014-04-02 AER commit
explicitly describes the imported files as initial band-generation codes from Karen and
original RRTM work, with no modifications yet.  The recovered pipeline operates on LBLRTM
optical depths to generate molecular k-distributions, continuum/minor-gas coefficients and
Planck-related band data.  No Fu96 ice-cloud high-resolution pre-averaging samples or cloud
optics band-averaging generator are promoted from this evidence.

This step refines Step 3Q.1 without promoting exact historical weighting.  It separates
(a) historical Fu96 broadband co-albedo semantics from (b) later RRTMG-band integration
semantics.  Fu-lineage literature states that Fu (1996) used solar-weighted broadband
averaging with a mix of linear and logarithmic co-albedo averages depending on absorption
strength.  Later RRTMG-band ice-optics work provides a solar-spectrum integration formula,
but that later formula is not treated as proof of how the archived default Fu96 tables were
historically generated.

The historical Fu96 -> RRTM/RRTMG default-table transformation remains fail-closed unless
its version-pinned pre-averaging samples, band-specific Fu96 averaging realization, exact
solar spectrum / discrete weights, and reproduction of the archived band-24/25 tables are
recovered.
"""
from __future__ import annotations
from typing import Any
import json
import pandas as pd
from . import __version__ as PHYSICSCORE_VERSION

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3Q_VERSION = "R5.7.41.3.4.10.30.17"
STEP3Q_MODE = "FU96_LINEAGE_BROADBAND_WEIGHTING_EQUATION_TRANSCRIPTION_CORRECTION_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-19"

FU96_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
FU2007_DOI = "https://doi.org/10.1175/2007JAS2289.1"
YI2013_DOI = "https://doi.org/10.1175/JAS-D-13-020.1"
CHOU1998_DOI = "https://doi.org/10.1175/1520-0442(1998)011<0202:PFCOAS>2.0.CO;2"
CHOU2002_DOI = "https://doi.org/10.1029/2002JD002061"
AER_RRTMG_SW_DESCRIPTION = "https://rtweb.aer.com/rrtmg_sw_description.html"
CAM5_DESCRIPTION = "https://www.cesm.ucar.edu/models/cesm1.0/cam/docs/description/cam5_desc.pdf"
BAEK2018_DOI = "https://doi.org/10.1029/2018MS001398"
AER_RRTMG_SW_REPOSITORY = "https://github.com/AER-RC/RRTMG_SW"
AER_RRTMG_SW_README = "https://github.com/AER-RC/RRTMG_SW/blob/master/README.md"
ARM_2002_RRTM_SW_V24_PROCEEDINGS = "https://www.arm.gov/publications/proceedings/conf12/extended_abs/delamere-js.pdf"
MICHALSKY2006_DOI = "https://doi.org/10.1029/2005JD006341"
AER_RRTM_SW_INSTRUCTIONS = "https://github.com/AER-RC/RRTM_SW/blob/master/rrtm_sw_instructions"
AER_RRTM_SW_CLDPROP_PINNED = "https://github.com/AER-RC/RRTM_SW/blob/b1253809ac88ae782964cd030cb202a380032d11/src/cldprop.f"
AER_RRTM_SW_CLDPROP_BLOB_SHA = "8632f7d1940285665b62fdbb30c69861924251da"
AER_RRTM_SW_CODE_PAGE = "https://rtweb.aer.com/rrtm_sw_code.html"
AER_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME = "aer_rrtm_sw_v2.5.tar.gz"
AER_RRTM_SW_V25_EXAMPLES_ARCHIVE_FILENAME = "aer_rrtm_sw_examples_v2.5.tar.gz"
AER_RRTM_SW_V25_SOURCE_ARCHIVE_URL = "https://files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz"
AER_RRTM_SW_V25_HISTORICAL_FTP_SOURCE_PATH = "ftp://ftp.aer.com/pub/downloads/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz"
APPROPEDIA_RRTM_SW_V25_INSTALL_GUIDE = "https://www.appropedia.org/Installing_RTM_Software_on_Linux"
AER_RRTM_SW_RELEASE_BUILD_NOTES_PINNED = (
    "https://github.com/AER-RC/RRTM_SW/blob/"
    "b1253809ac88ae782964cd030cb202a380032d11/README.cvs_checkin_notes"
)
AER_RRTM_SW_RELEASE_BUILD_NOTES_BLOB_SHA = "9304d7bbd17766b48a58fb2c500e8f5f951b557f"
AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_COMMIT = "356609ea083f9684dc83a56e3f5c96515cb25b19"
AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_DATE_UTC = "2004-04-15T18:42:10Z"
AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_BLOB_SHA = "8632f7d1940285665b62fdbb30c69861924251da"
AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004 = (
    "https://github.com/AER-RC/RRTM_SW/blob/"
    "356609ea083f9684dc83a56e3f5c96515cb25b19/src/cldprop.f"
)
AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_COMMIT = "a43212334fd726dec8d69203be0c7d50fd9ce1b0"
AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_DATE_UTC = "2004-04-15T18:50:57Z"
AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_BLOB_SHA = "b2b1080fe51b7c3d512de26b4507314fee17ff58"
AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004 = (
    "https://github.com/AER-RC/RRTM_SW/blob/"
    "a43212334fd726dec8d69203be0c7d50fd9ce1b0/src/taumoldis.f"
)
AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_COMMIT = "a43212334fd726dec8d69203be0c7d50fd9ce1b0"
AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_SHA = "24beb15d868c131b81e354ea34b2b409c4a4062e"
RRTM_SW_V25_EXTERNAL_IMPORT_TREE_SHA = "51b90dfdb83f33f55dc3f23b680af6e327fe1fd8"
RRTM_SW_V25_SCIENTIFIC_SOURCE_FILE_COUNT = 26
RRTM_SW_V25_CVS_NORMALIZED_FULL_FILE_MATCH_COUNT = 24
RRTM_SW_V25_OPERATIONAL_DELTA_FILE_COUNT = 2
RRTM_SW_V25_OPERATIONAL_DELTA_LINE_COUNT = 4
AER_RRTM_SW_V25_OFFICIAL_RRTATM_2004_BLOB_SHA = "74fa6fc4dd352bff71c6f7eafa2ea1b0aa67ee18"
RRTM_SW_V25_EXTERNAL_IMPORT_RRTATM_BLOB_SHA = "6262d3c1e331d237d7dd47520e8f1e5e713fee51"
AER_RRTM_SW_V25_OFFICIAL_RRTM_2004_BLOB_SHA = "d4092d27a1e18b6408c1626617afdd84d88eb0c6"
RRTM_SW_V25_EXTERNAL_IMPORT_RRTM_BLOB_SHA = "c3ef8c054583a9334b32b04261679eab4f704fe3"

PYRRTM_REPOSITORY = "https://github.com/tomflannaghan/pyrrtm"
PYRRTM_SW_2014_COMMIT = "31d776362503c20e84d2a6d78be4a96517f89e49"
PYRRTM_SW_2014_DATE_UTC = "2014-07-14T13:11:02Z"
PYRRTM_SW_2014_TREE_SHA = "e4a56fd0b150b6536e9653c9b4446aa5a0a03d31"
PYRRTM_SW_2014_COMMIT_URL = (
    "https://github.com/tomflannaghan/pyrrtm/commit/"
    "31d776362503c20e84d2a6d78be4a96517f89e49"
)
RRTM_SW_V25_CROSS_REPOSITORY_SCIENTIFIC_FILE_COUNT = 26
RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_COUNT = 22
RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_NONMATCH_COUNT = 4
RRTM_SW_V25_CRITICAL_RAW_BLOB_REPLICATION_FILE_COUNT = 4
PYRRTM_SW_2014_CLDPROP_BLOB_SHA = "d7a2efce33cdf5c1f02a66e598c685ef53b7b8c8"
PYRRTM_SW_2014_TAUMOLDIS_BLOB_SHA = "5111a3bb7d981ea8facb4733c2ebb8d7f1308486"
PYRRTM_SW_2014_KGB24_BLOB_SHA = "7847f1d19a9008137d60db422c623505ebf8835e"
PYRRTM_SW_2014_KGB25_BLOB_SHA = "e3cc504280805b0b2de725d5645334095a92b07e"
RRTM_SW_V25_EXTERNAL_IMPORT_KGB24_BLOB_SHA = "7847f1d19a9008137d60db422c623505ebf8835e"
RRTM_SW_V25_EXTERNAL_IMPORT_KGB25_BLOB_SHA = "e3cc504280805b0b2de725d5645334095a92b07e"

AER_RRTMG_SW_2007_CONTINUITY_COMMIT = "5336e33010ac1a8498a1a66c5ef01fd1199213bf"
AER_RRTMG_SW_2007_CONTINUITY_DATE_UTC = "2007-04-19T22:42:34Z"
AER_RRTMG_SW_2007_CONTINUITY_TREE_SHA = "2ec6d3135d20410d4702f66e2b8ef33aa64da888"
AER_RRTMG_SW_2007_CLDPROP_BLOB_SHA = "0f1df8d16ca6aa2374f4bec1f07567daa57077ab"
AER_RRTMG_SW_2007_CLDPROP = (
    "https://github.com/AER-RC/RRTMG_SW/blob/"
    "5336e33010ac1a8498a1a66c5ef01fd1199213bf/src/rrtmg_sw_cldprop.f90"
)
AER_RRTM_RRTMG_FU96_CONTINUITY_ARRAY_COUNT = 56
AER_RRTM_RRTMG_FU96_CONTINUITY_VALUES_PER_ARRAY = 46
AER_RRTM_RRTMG_FU96_CONTINUITY_VALUE_COUNT = 2576

AER_RRTM_BAND_GEN_REPOSITORY = "https://github.com/AER-RC/rrtmgp-band-generation"
AER_RRTM_BAND_GEN_GITHUB_PUBLIC_CREATED_AT = "2025-01-14T21:14:08Z"
AER_RRTM_BAND_GEN_SVN_PATH = "https://svn.aer.com/svn/aer/project/RD/RRTM_BAND_GEN"
AER_RRTM_BAND_GEN_EARLIEST_GIT_SVN_COMMIT = "b78641520629cf2cca39ee0b6d5fdf99f98ede21"
AER_RRTM_BAND_GEN_EARLIEST_GIT_SVN_DATE_UTC = "2014-03-03T19:13:53Z"
AER_RRTM_BAND_GEN_IMPORTED_HISTORY_COMMIT_COUNT = 176
AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT = "5ce72bd363c993189767f09f1c9fe9bc84b72c56"
AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_DATE_UTC = "2014-04-02T14:35:38Z"
AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_SVN_REVISION = 24171
AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_URL = (
    "https://github.com/AER-RC/rrtmgp-band-generation/commit/"
    "5ce72bd363c993189767f09f1c9fe9bc84b72c56"
)
AER_RRTM_BAND_GEN_INITIAL_SCRIPT_GEN_2BAND = (
    "https://github.com/AER-RC/rrtmgp-band-generation/blob/"
    "5ce72bd363c993189767f09f1c9fe9bc84b72c56/branches/chebyproject/script.gen_2band"
)
AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_FOR = (
    "https://github.com/AER-RC/rrtmgp-band-generation/blob/"
    "5ce72bd363c993189767f09f1c9fe9bc84b72c56/branches/chebyproject/kdis_2sort_for.f"
)
AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_PLANCK = (
    "https://github.com/AER-RC/rrtmgp-band-generation/blob/"
    "5ce72bd363c993189767f09f1c9fe9bc84b72c56/branches/chebyproject/kdis_2sort_planck.f"
)
AER_RRTM_BAND_GEN_INITIAL_COMP_WTAVG_PLANCK = (
    "https://github.com/AER-RC/rrtmgp-band-generation/blob/"
    "5ce72bd363c993189767f09f1c9fe9bc84b72c56/branches/chebyproject/comp_wtavg_planck.f"
)

RRTM_SW_V25_EXTERNAL_MIRROR_REPOSITORY = "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper"
RRTM_SW_V25_EXTERNAL_MIRROR_COMMIT = "a2d974ecefe6f369661bf5a3dfc648f07986ad89"
RRTM_SW_V25_EXTERNAL_IMPORT_COMMIT = "040d18018f553faeeae625fd4ef73d50ba0436fb"
RRTM_SW_V25_EXTERNAL_IMPORT_DATE_UTC = "2020-03-17T22:23:17Z"
RRTM_SW_V25_EXTERNAL_IMPORT_CLDPROP = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "040d18018f553faeeae625fd4ef73d50ba0436fb/SW/src/cldprop.f"
)
RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "040d18018f553faeeae625fd4ef73d50ba0436fb/SW/src/taumoldis.f"
)
RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS_BLOB_SHA = "5111a3bb7d981ea8facb4733c2ebb8d7f1308486"
RRTM_SW_V25_EXTERNAL_CLDPROP = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "a2d974ecefe6f369661bf5a3dfc648f07986ad89/SW/src/cldprop.f"
)
RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA = "d7a2efce33cdf5c1f02a66e598c685ef53b7b8c8"
RRTM_SW_V25_EXTERNAL_UPDATE = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "a2d974ecefe6f369661bf5a3dfc648f07986ad89/SW/update_rrtm_sw_v2.5.txt"
)
RRTM_SW_V25_EXTERNAL_UPDATE_BLOB_SHA = "00ac405ca9805ee9fc4fbaad0f0ce3733a72b67b"
RRTM_SW_V25_EXTERNAL_TAUMOLDIS = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "a2d974ecefe6f369661bf5a3dfc648f07986ad89/SW/src/taumoldis.f"
)
RRTM_SW_V25_EXTERNAL_TAUMOLDIS_BLOB_SHA = "339d64ecb0a4f8fa49938ac4a18ce731e27e34f0"
RRTM_SW_V25_EXTERNAL_MAKEFILE = (
    "https://github.com/nickedkins/RRTM-LWandSW-Python-wrapper/blob/"
    "a2d974ecefe6f369661bf5a3dfc648f07986ad89/SW/makefiles/make_rrtm_sw_linux_pgi"
)
RRTM_SW_V25_EXTERNAL_MAKEFILE_BLOB_SHA = "0baee98667f89d05e46ed6138cde0057c6e07393"
GEOSCHEM_RRTMG_PINNED_SOURCE = (
    "https://github.com/geoschem/geos-chem/blob/"
    "a4551f9442183bb572b23e9c2d362e2d34420d3a/GeosRad/rrtmg_sw_init.F90"
)
GEOSCHEM_RRTMG_SOURCE_SHA = "0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"
RRTMG_BANDS = (24, 25)


def _row(check_id: str, category: str, status: str, observed: str, required: str, notes: str = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "observed": observed,
        "required": required,
        "physics_promotion_allowed": False,
        "notes": notes,
    }


def build_fu96_rrtmg_band_weighting_provenance_evidence() -> pd.DataFrame:
    rows = [
        _row(
            "FU96_PRIMARY_SOLAR_ICE_PARAMETERIZATION_PINNED", "PRIMARY_SCIENCE_SOURCE", "PASS_PINNED",
            "Fu 1996 solar cirrus parameterization; Dge-based extinction/SSA framework; spectral averaging is scientifically material",
            "PRIMARY_FU96_SOURCE_PINNED", FU96_DOI,
        ),
        _row(
            "FU96_SSA_SPECTRAL_AVERAGING_SIGNIFICANCE", "PRIMARY_SCIENCE_SOURCE", "PASS_CONFIRMED",
            "Fu 1996 identifies SSA averaging technique in absorption-band spectral intervals as important",
            "AVERAGING_SEMANTICS_MUST_NOT_BE_REPLACED_BY_ARBITRARY_MEAN",
            "Primary source establishes materiality but not the later historical RRTM_SW discrete weight vector.",
        ),
        _row(
            "FU96_HISTORICAL_COALBEDO_MIXED_LINEAR_LOG_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_CONFIRMED",
            "Fu-lineage documentation states Fu (1996) used a mix of solar-weighted linear and logarithmic averaging for single-scattering coalbedo depending on absorption strength",
            "HISTORICAL_FU96_SSA_COALBEDO_MUST_NOT_BE_REPLACED_BY_SIMPLE_LINEAR_OR_MODERN_RATIO_FORMULA", CHOU1998_DOI,
        ),

        _row(
            "FU96_LINEAGE_LINEAR_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "alpha_linear = sum(alpha_lambda * beta_lambda * S_lambda * dLambda) / sum(beta_lambda * S_lambda * dLambda), where alpha=1-SSA and beta is extinction coefficient",
            "SOLAR_WEIGHTED_LINEAR_COALBEDO_EQUATION_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_LOG_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "ln(alpha_log) = sum(ln(alpha_lambda) * beta_lambda * S_lambda * dLambda) / sum(beta_lambda * S_lambda * dLambda)",
            "SOLAR_WEIGHTED_LOG_COALBEDO_EQUATION_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_MIXED_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "alpha_eff = h*alpha_linear + (1-h)*alpha_log; h in [0,1]; h near 1 for weak absorption and decreases as absorption strengthens",
            "LINEAR_LOG_MIXING_EQUATION_FAMILY_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_COALBEDO_EXTINCTION_WEIGHTING_TRANSCRIPTION_CORRECTED", "PROVENANCE_CONTRACT_CORRECTION", "PASS_CORRECTED",
            "Step3Q linear/log coalbedo equations now retain beta_lambda extinction weighting in numerator and denominator in addition to TOA solar irradiance and spectral-interval weighting",
            "FU96_LINEAGE_COALBEDO_EQUATIONS_MUST_USE_BETA_TIMES_SOLAR_WEIGHTING", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTED_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "g_eff = sum(g_lambda * omega_lambda * beta_lambda * S_lambda * dLambda) / sum(omega_lambda * beta_lambda * S_lambda * dLambda)",
            "FU96_LINEAGE_BAND_MEAN_G_MUST_BE_SCATTERING_WEIGHTED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_SIMPLE_SOLAR_ONLY_COALBEDO_AVERAGE", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "MUST_NOT_DROP_BETA_LAMBDA_EXTINCTION_WEIGHTING_FROM_LINEAR_OR_LOG_COALBEDO_AVERAGES", CHOU1998_DOI,
        ),

        _row(
            "FU96_LINEAGE_H_EMPIRICAL_SELECTION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "Chou et al. 1998 determines optimal h empirically by trial and error to minimize TOA/surface flux differences against high-resolution calculations",
            "H_IS_EMPIRICAL_FLUX_CALIBRATION_PARAMETER_NOT_DERIVABLE_FROM_ABSORPTION_STRENGTH_ALONE", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU1998", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "For ice clouds Chou et al. 1998 Table 1 gives h=1 for 0.18-0.70 um and h=2/3 for 0.70-1.22 um",
            "FU_LINEAGE_H_DOMAIN_VALUES_PINNED_AS_CONSTRAINT_NOT_RRTM_GENERATOR", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU2002", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "Chou et al. 2002 explicitly gives h=1 for bands 1-8 (0.175-0.700 um) and h=2/3 for band 9 (0.700-1.220 um)",
            "FU_LINEAGE_H_DOMAIN_VALUES_INDEPENDENTLY_RESTATED", CHOU2002_DOI,
        ),
        _row(
            "RRTMG_BAND25_H_DOMAIN_CONSTRAINT", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "RRTMG band 25 is 16000-22650 cm-1 = 0.441501-0.625000 um, entirely inside the Fu-lineage weak-absorption h=1 domain below 0.700 um",
            "BAND25_H1_DOMAIN_CONSTRAINT_QUALIFIED_BUT_ARCHIVED_RRTMG_GENERATOR_IDENTITY_NOT_PROVEN",
            f"{AER_RRTMG_SW_REPOSITORY}; {CHOU1998_DOI}; {CHOU2002_DOI}",
        ),
        _row(
            "RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "RRTMG band 24 is 12850-16000 cm-1 = 0.625000-0.778210 um and crosses the 0.700 um Fu-lineage h-domain boundary: 0.625-0.700 lies in h=1 domain while 0.700-0.778210 lies in h=2/3 domain",
            "BAND24_CANNOT_BE_ASSIGNED_ONE_H_FROM_CHOU_DOMAIN_VALUES_WITHOUT_HISTORICAL_RRTM_GENERATOR_RULE",
            f"{AER_RRTMG_SW_REPOSITORY}; {CHOU1998_DOI}; {CHOU2002_DOI}",
        ),
        _row(
            "RRTMG_BAND25_EXACT_H_FOR_ARCHIVED_TABLE", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PROVEN",
            "Fu-lineage domain evidence constrains all band-25 wavelengths to h=1, but no source ties that Chou/Fu-lineage h realization byte-for-byte to the archived RRTM/RRTMG Fu96 band-25 table generator",
            "ARCHIVED_RRTM_GENERATOR_IDENTITY_OR_NUMERIC_REPRODUCTION_REQUIRED_BEFORE_EXACT_H_CLAIM",
        ),
        _row(
            "FU96_RRTMG_BAND24_25_H_VALUES", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "Fu-lineage h domains are now constrained; however no authoritative RRTM/RRTMG-specific band-24 historical mixing realization, nor a fully provenance-linked band-25 generator, has been recovered",
            "BAND24_HISTORICAL_MIXING_OR_EQUIVALENT_GENERATOR_AND_BAND25_GENERATOR_IDENTITY_REQUIRED",
        ),
        _row(
            "FU96_HISTORICAL_BAND_SPECIFIC_MIXING_REALIZATION", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "The exact band-specific linear/log mixing realization used for the archived RRTM/RRTMG Fu96 tables has not been recovered",
            "BAND_SPECIFIC_FU96_LINEAR_LOG_MIXING_RULE_OR_EQUIVALENT_GENERATOR_REQUIRED",
        ),
        _row(
            "FU96_LINEAGE_SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_CONFIRMED",
            "Fu 2007 states that calculations following Fu 1996 divide the solar spectrum into Fu96 bands and weight data with solar irradiance to obtain band averages",
            "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_CLASS_SUPPORTED", FU2007_DOI,
        ),
        _row(
            "RRTMG_SW_BAND_INTEGRATION_FORMULA_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_QUALIFIED",
            "Yi 2013 later RRTMG-band ice optics integrates SW properties over wavelength with solar spectrum S(lambda); SSA is derived from integrated scattering/extinction and g is scattering-weighted",
            "LATER_RRTMG_BAND_INTEGRATION_SEMANTIC_QUALIFIED_BUT_NOT_HISTORICAL_FU96_DEFAULT_TABLE_PROVENANCE", YI2013_DOI,
        ),
        _row(
            "RRTMG_SW_BAND_LIMITS_24_25_PINNED", "SPECTRAL_DOMAIN", "PASS_PINNED",
            "RRTMG band 24 = 0.63-0.78 um; band 25 = 0.44-0.63 um in Yi 2013; Baek 2018 independently documents RRTMG spectral-band averaging and band 25 near 0.44-0.63 um",
            "BAND_24_25_LIMITS_PINNED", f"{YI2013_DOI}; {BAEK2018_DOI}",
        ),
        _row(
            "RRTMG_ICEFLAG3_FU96_DGE_LINEAGE", "MODEL_LINEAGE", "PASS_PINNED",
            "RRTM/RRTMG SW ICEFLAG=3 uses Fu (1996) generalized effective size Dge; valid 5-140 um",
            "FU96_DGE_LINEAGE_PINNED", AER_RRTM_SW_INSTRUCTIONS,
        ),
        _row(
            "RRTMG_FU96_FINAL_BAND_TABLES_PINNED", "MODEL_REFERENCE_TABLE", "PASS_PINNED",
            "Final band-24/band-25 Fu96 extice3/ssaice3/asyice3 reference tables are available in pinned RRTMG implementation source",
            "FINAL_REFERENCE_TABLES_PINNED", f"{GEOSCHEM_RRTMG_PINNED_SOURCE}; source_sha={GEOSCHEM_RRTMG_SOURCE_SHA}",
        ),
        _row(
            "RRTM_SW_FU96_POST_AVERAGED_ARCHIVE_PINNED", "ARCHIVE_BOUNDARY", "PASS_QUALIFIED",
            "Pinned AER RRTM_SW cldprop.f states that Q. Fu provided high-resolution tables which were appropriately averaged for RRTM_SW bands, and the archived runtime contains the resulting EXTICE3/SSAICE3/ASYICE3/FDLICE3 arrays",
            "POST_AVERAGED_RUNTIME_TABLE_ARCHIVE_BOUNDARY_PINNED",
            f"{AER_RRTM_SW_CLDPROP_PINNED}; blob_sha={AER_RRTM_SW_CLDPROP_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_FU96_46_NODE_DGE_RUNTIME_GRID", "ARCHIVE_BOUNDARY", "PASS_QUALIFIED",
            "ICEFLAG=3 runtime interpolation uses 46 stored nodes on the Dge grid 5,8,...,140 um (3 um spacing), confirming the archived object is a compact band table rather than the pre-averaging spectral sample set",
            "POST_AVERAGED_46_NODE_RUNTIME_GRID_PINNED", AER_RRTM_SW_CLDPROP_PINNED,
        ),
        _row(
            "RRTM_SW_PREAVERAGING_FU96_GENERATOR_PRESENT_IN_PINNED_ARCHIVE", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PRESENT",
            "The pinned AER RRTM_SW runtime source contains the post-averaged Fu96 band tables and interpolation logic but does not contain the Q. Fu high-resolution pre-averaging spectral tables or the historical band-averaging generator",
            "AUTHORITATIVE_PREAVERAGING_SOURCE_OR_GENERATOR_REQUIRED", AER_RRTM_SW_CLDPROP_PINNED,
        ),
        _row(
            "RRTMG_SW_CURRENT_PRE_V5_PUBLIC_RELEASE_AVAILABILITY", "PUBLIC_ARCHIVE_BOUNDARY", "PASS_QUALIFIED",
            "Current AER RRTMG_SW README states Version 5.0 is the latest release and releases before Version 5.0 are not publicly available in the present public release archive",
            "CURRENT_PUBLIC_RELEASE_AVAILABILITY_BOUNDARY_PINNED; CURRENT_UNAVAILABILITY_MUST_NOT_BE_MISSTATED_AS_HISTORICAL_NONPUBLICATION", AER_RRTMG_SW_README,
        ),
        _row(
            "RRTM_SW_V24_HISTORICALLY_PUBLIC_2002", "HISTORICAL_RELEASE_EXISTENCE", "PASS_PINNED",
            "ARM 2002 proceedings state RRTM_SW v2.4 had just been publicly released and was available on the AER web site",
            "HISTORICAL_PUBLIC_RELEASE_EXISTENCE_PINNED_SEPARATELY_FROM_CURRENT_ARCHIVE_AVAILABILITY", ARM_2002_RRTM_SW_V24_PROCEEDINGS,
        ),
        _row(
            "RRTM_SW_V25_HISTORICAL_USE_2006", "HISTORICAL_RELEASE_EXISTENCE", "PASS_PINNED",
            "A 2006 JGR radiative-closure study documents use of RRTM_SW version 2.5 and cites the AER web site",
            "HISTORICAL_V25_EXISTENCE_AND_USE_PINNED_WITHOUT_CLAIMING_CURRENT_DOWNLOAD_AVAILABILITY", MICHALSKY2006_DOI,
        ),
        _row(
            "RRTM_SW_V25_EXTERNAL_DISTRIBUTION_MIRROR_PINNED", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_PINNED",
            "A third-party GitHub archive preserves an RRTM_SW v2.5-style SW distribution tree with AER update notes, v2.5 makefile identity, source tree, instructions, and examples at a pinned commit",
            "EXTERNAL_MIRROR_PINNED_AS_LINEAGE_EVIDENCE_NOT_AS_BYTE_PROOF_OF_ORIGINAL_AER_TARBALL",
            f"{RRTM_SW_V25_EXTERNAL_MIRROR_REPOSITORY}; commit={RRTM_SW_V25_EXTERNAL_MIRROR_COMMIT}",
        ),
        _row(
            "RRTM_SW_V25_UPDATE_NOTE_IDENTITY", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_PINNED",
            "Pinned update_rrtm_sw_v2.5.txt states in April 2004 that RRTM_SW v2.4.1 was updated to RRTM_SW v2.5 and directs users to AER web/FTP distribution paths",
            "V25_DISTRIBUTION_IDENTITY_PINNED_FROM_EXTERNAL_MIRROR",
            f"{RRTM_SW_V25_EXTERNAL_UPDATE}; blob_sha={RRTM_SW_V25_EXTERNAL_UPDATE_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_MAKEFILE_VERSION_IDENTITY", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_PINNED",
            "Pinned make_rrtm_sw_linux_pgi contains VERSION = v2.5 and CVS Id dated 2004-04-16",
            "V25_BUILD_IDENTITY_PINNED",
            f"{RRTM_SW_V25_EXTERNAL_MAKEFILE}; blob_sha={RRTM_SW_V25_EXTERNAL_MAKEFILE_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_CLDPROP_CVS_PROVENANCE", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_PINNED",
            "External mirror cldprop.f retains CVS provenance: source /storm/rc1/cvsroot/rc/rrtm_sw/src/cldprop.f,v; author jdelamer; revision 2.7; date 2004-04-15 18:42:10",
            "V25_CLOUD_RUNTIME_CVS_PROVENANCE_PINNED",
            f"{RRTM_SW_V25_EXTERNAL_CLDPROP}; blob_sha={RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_CLDPROP_SCIENCE_CONTENT_EQUIVALENCE_TO_AER_ARCHIVE", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_QUALIFIED",
            "Line comparison of the pinned 2080-line external v2.5 cldprop.f against pinned AER RRTM_SW cldprop.f found only five differing lines, all CVS keyword expansion/stripping; executable and table content are otherwise line-identical",
            "V25_EXTERNAL_CLOUD_RUNTIME_LINEAGE_MATCH_QUALIFIED_WITHOUT_CLAIMING_ORIGINAL_TARBALL_BYTE_IDENTITY",
            f"external_blob={RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA}; aer_blob={AER_RRTM_SW_CLDPROP_BLOB_SHA}",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_PINNED",
            "AER-RC/RRTM_SW records src/cldprop.f commit 356609ea083f9684dc83a56e3f5c96515cb25b19 by jdelamer at 2004-04-15T18:42:10Z; the official blob is 8632f7d1940285665b62fdbb30c69861924251da",
            "OFFICIAL_2004_CLDPROP_HISTORY_AND_BLOB_PINNED",
            f"{AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004}; commit={AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_COMMIT}; blob_sha={AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_BLOB_SHA}",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_PINNED",
            "AER-RC/RRTM_SW records src/taumoldis.f commit a43212334fd726dec8d69203be0c7d50fd9ce1b0 by jdelamer at 2004-04-15T18:50:57Z; the official blob is b2b1080fe51b7c3d512de26b4507314fee17ff58",
            "OFFICIAL_2004_TAUMOLDIS_HISTORY_AND_BLOB_PINNED",
            f"{AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004}; commit={AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_COMMIT}; blob_sha={AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_QUALIFIED",
            "Official AER 2004 cldprop.f and the external mirror import both contain 2080 lines; the only raw differences are CVS keyword collapse/expansion ($Source/$Author/$Revision/$Date and the runtime HVRCLD revision string). After canonical CVS-keyword normalization the complete files are identical",
            "FULL_FILE_EQUIVALENCE_AFTER_CVS_KEYWORD_NORMALIZATION_REQUIRED",
            f"official_blob={AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_BLOB_SHA}; mirror_blob={RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA}; official_commit={AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_COMMIT}; mirror_import_commit={RRTM_SW_V25_EXTERNAL_IMPORT_COMMIT}",
        ),
        _row(
            "RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_QUALIFIED",
            "Official AER 2004 taumoldis.f and the external mirror import both contain 2054 lines; after canonical CVS-keyword normalization ($Source/$Author/$Revision/$Date) the complete files are identical. The mirror expansion identifies revision 2.5 dated 2004-04-15 18:50:57",
            "FULL_FILE_EQUIVALENCE_AFTER_CVS_KEYWORD_NORMALIZATION_REQUIRED",
            f"official_blob={AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_BLOB_SHA}; mirror_blob={RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS_BLOB_SHA}; official_commit={AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_COMMIT}; mirror_import_commit={RRTM_SW_V25_EXTERNAL_IMPORT_COMMIT}",
        ),
        _row(
            "RRTM_SW_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_QUALIFIED",
            "The two critical v2.5 provenance anchors used by this qualification (cldprop.f cloud tables/runtime and taumoldis.f solar-source context) are full-file equivalent between AER official 2004 history and the external mirror after removing CVS keyword expansion as a non-science checkout artifact",
            "CRITICAL_SOURCE_TREE_EQUIVALENCE_QUALIFIED_WITHOUT_PROMOTING_ORIGINAL_TARBALL_BYTE_IDENTITY",
            "This is source-tree equivalence for pinned critical files, not proof that the external repository tree or archive bytes are byte-identical to aer_rrtm_sw_v2.5.tar.gz.",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_PINNED",
            "AER official 2004 release tree at commit a43212334fd726dec8d69203be0c7d50fd9ce1b0 / tree 24beb15d868c131b81e354ea34b2b409c4a4062e contains 26 Fortran scientific-source files under src/",
            "OFFICIAL_2004_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED",
            f"official_commit={AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_COMMIT}; official_tree={AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_SHA}",
        ),
        _row(
            "RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_QUALIFIED",
            "24 of 26 common Fortran scientific-source files are complete-file identical between AER official 2004 history and the external v2.5 import after generic CVS keyword collapse/expansion normalization",
            "FULL_FILE_EQUIVALENCE_FOR_NON_OPERATIONAL_DELTA_SOURCE_SET_REQUIRED",
            f"official_tree={AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_SHA}; mirror_tree={RRTM_SW_V25_EXTERNAL_IMPORT_TREE_SHA}; matched=24/26",
        ),
        _row(
            "RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED", "DOCUMENTED_OPERATIONAL_DELTA", "PASS_QUALIFIED",
            "rrtatm.f has identical line count and, after CVS normalization, differs only at three adjacent lines where the mirror comments out LBLDAT/FTIME/date-time header output calls; no radiative-transfer equation, coefficient table, cloud-optics table, gas-optics table, or spectral-band definition is changed",
            "ONLY_NON_PHYSICS_DATE_TIME_OUTPUT_DELTA_ALLOWED",
            f"official_blob={AER_RRTM_SW_V25_OFFICIAL_RRTATM_2004_BLOB_SHA}; mirror_blob={RRTM_SW_V25_EXTERNAL_IMPORT_RRTATM_BLOB_SHA}; delta_lines=3",
        ),
        _row(
            "RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED", "DOCUMENTED_OPERATIONAL_DELTA", "PASS_QUALIFIED",
            "rrtm.f has identical line count and, after CVS normalization, differs only at one OPEN statement filename literal: official INPUT_RRTM versus mirror input_rrtm_MLS; the computation path and scientific equations are otherwise unchanged",
            "ONLY_INPUT_FILENAME_LITERAL_DELTA_ALLOWED",
            f"official_blob={AER_RRTM_SW_V25_OFFICIAL_RRTM_2004_BLOB_SHA}; mirror_blob={RRTM_SW_V25_EXTERNAL_IMPORT_RRTM_BLOB_SHA}; delta_lines=1",
        ),
        _row(
            "RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE", "OFFICIAL_HISTORICAL_SOURCE_TREE", "PASS_QUALIFIED",
            "Across the 26-file Fortran scientific-source set, 24 files are full-file identical after generic CVS-keyword normalization and the remaining two files contain exactly four documented operational-only deltas (three date/time-output comments and one input-filename literal); no scientific source delta was identified",
            "SCIENTIFIC_SEMANTIC_EQUIVALENCE_MAY_BE_QUALIFIED_ONLY_WITH_OPERATIONAL_DELTAS_EXPLICITLY_PRESERVED_AND_RAW_BYTE_IDENTITY_FORBIDDEN",
            "This qualifies scientific-source semantic equivalence for the pinned source set, not whole-repository equality, release-package equality, original tarball identity, or historical pre-averaging generator recovery.",
        ),
        _row(
            "RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_IS_RAW_BYTE_IDENTITY", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_MUST_NOT_BE_RELABELED_AS_RAW_BYTE_IDENTITY_OR_ORIGINAL_TARBALL_IDENTITY",
        ),
        _row(
            "PYRRTM_SW_2014_PRE2020_HISTORY_PINNED", "CROSS_REPOSITORY_REPLICATION", "PASS_PINNED",
            "tomflannaghan/pyrrtm is a non-fork GitHub repository whose commit 31d776362503c20e84d2a6d78be4a96517f89e49 added the shortwave code on 2014-07-14T13:11:02Z, predating the 2020 nickedkins mirror import by more than five years",
            "SEPARATE_PRE2020_REPOSITORY_HISTORY_WITH_PINNED_COMMIT_DATE_AND_TREE_REQUIRED",
            f"{PYRRTM_SW_2014_COMMIT_URL}; tree={PYRRTM_SW_2014_TREE_SHA}",
        ),
        _row(
            "RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26", "CROSS_REPOSITORY_REPLICATION", "PASS_QUALIFIED",
            "Comparing the 26-file Fortran scientific-source set between pyrrtm's pinned 2014 SW-addition tree and the nickedkins pinned 2020 v2.5 import gives 22 of 26 exact Git-blob SHA matches; the four nonmatching files are RDI1MACH.f, disort.f, rrtatm.f, and rrtm.f",
            "RAW_BLOB_REPLICATION_COUNT_MUST_BE_EXPLICIT_AND_NONMATCHES_MUST_NOT_BE_SILENTLY_NORMALIZED",
            f"pyrrtm_tree={PYRRTM_SW_2014_TREE_SHA}; mirror_tree={RRTM_SW_V25_EXTERNAL_IMPORT_TREE_SHA}; raw_blob_match=22/26",
        ),
        _row(
            "RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION", "CROSS_REPOSITORY_REPLICATION", "PASS_QUALIFIED",
            "The four provenance-critical files cldprop.f, taumoldis.f, k_gB24.f, and k_gB25.f are exact raw Git-blob matches between the pinned 2014 pyrrtm history and the pinned 2020 v2.5 import",
            "CRITICAL_FU96_CLOUD_TABLE_RUNTIME_SOLAR_CONTEXT_AND_BAND24_25_FILES_MUST_MATCH_RAW_BLOBS_ACROSS_PINNED_REPOSITORY_HISTORIES",
            f"cldprop={PYRRTM_SW_2014_CLDPROP_BLOB_SHA}; taumoldis={PYRRTM_SW_2014_TAUMOLDIS_BLOB_SHA}; k_gB24={PYRRTM_SW_2014_KGB24_BLOB_SHA}; k_gB25={PYRRTM_SW_2014_KGB25_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "CROSS_REPOSITORY_RAW_BLOB_REPLICATION_MUST_NOT_BE_RELABELED_AS_ORIGINAL_AER_TARBALL_BYTE_IDENTITY_OR_AUTHORITATIVE_ARCHIVE_HASH",
            "Separate repository replication strengthens source-lineage confidence but both histories may derive from the same historical AER distribution; original aer_rrtm_sw_v2.5.tar.gz bytes/hash remain unrecovered.",
        ),
        _row(
            "AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED", "OFFICIAL_AER_CROSS_GENERATION_CONTINUITY", "PASS_PINNED",
            "AER official RRTMG_SW commit 5336e33010ac1a8498a1a66c5ef01fd1199213bf dated 2007-04-19 preserves the Fu96 cloud tables in rrtmg_sw_cldprop.f90",
            "OFFICIAL_AER_RRTMG_SW_2007_HISTORY_AND_CLOUD_TABLE_SOURCE_PINNED",
            f"{AER_RRTMG_SW_2007_CLDPROP}; tree={AER_RRTMG_SW_2007_CONTINUITY_TREE_SHA}; blob={AER_RRTMG_SW_2007_CLDPROP_BLOB_SHA}",
        ),
        _row(
            "AER_RRTM_SW_2004_TO_RRTMG_SW_2007_FU96_FINAL_TABLE_VALUE_CONTINUITY", "OFFICIAL_AER_CROSS_GENERATION_CONTINUITY", "PASS_QUALIFIED",
            "EXTICE3, SSAICE3, ASYICE3, and FDLICE3 were compared for all RRTM_SW bands 16-29: 56 of 56 arrays and 2576 of 2576 numeric values are identical between AER official 2004 RRTM_SW v2.5 source and AER official 2007 RRTMG_SW source",
            "ALL_4_FU96_TABLE_FAMILIES_X_14_BANDS_X_46_VALUES_MUST_MATCH_NUMERICALLY",
            "This qualifies authoritative final-table continuity across AER model generations; it does not recover the pre-averaging spectral samples, generator, exact historical solar weights, or original v2.5 tarball hash.",
        ),
        _row(
            "AER_RRTM_RRTMG_FU96_FINAL_TABLE_CONTINUITY_IS_PREAVERAGING_GENERATOR_RECOVERY", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "FINAL_TABLE_CONTINUITY_MUST_NOT_BE_RELABELED_AS_PREAVERAGING_GENERATOR_OR_EXACT_WEIGHTING_RECOVERY",
        ),
        _row(
            "AER_RRTM_BAND_GEN_IMPORTED_SVN_HISTORY_PINNED", "HISTORICAL_AER_BAND_GENERATION_PIPELINE", "PASS_PINNED",
            "AER-RC/rrtmgp-band-generation is a 2025 public GitHub repository carrying 176 imported git-svn commits from AER RRTM_BAND_GEN history; the imported history begins 2014-03-03 and commit messages retain the private SVN path/revision provenance",
            "PUBLIC_REPOSITORY_DATE_MUST_BE_SEPARATED_FROM_IMPORTED_AER_SVN_HISTORY_DATE",
            f"repo={AER_RRTM_BAND_GEN_REPOSITORY}; public_created={AER_RRTM_BAND_GEN_GITHUB_PUBLIC_CREATED_AT}; earliest={AER_RRTM_BAND_GEN_EARLIEST_GIT_SVN_COMMIT}; svn={AER_RRTM_BAND_GEN_SVN_PATH}",
        ),
        _row(
            "AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT_PINNED", "HISTORICAL_AER_BAND_GENERATION_PIPELINE", "PASS_PINNED",
            "AER commit 5ce72bd363c993189767f09f1c9fe9bc84b72c56 dated 2014-04-02 states: Adding initial band generation codes from Karen and original RRTM work. No modifications yet.",
            "AER_SELF_DESCRIBED_ORIGINAL_RRTM_BAND_GENERATION_IMPORT_COMMIT_PINNED",
            f"{AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_URL}; svn_revision={AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_SVN_REVISION}",
        ),
        _row(
            "AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_SCOPE", "HISTORICAL_AER_BAND_GENERATION_PIPELINE", "PASS_QUALIFIED",
            "The pinned initial pipeline drives LBLRTM optical-depth runs and kdis_2sort programs to generate molecular absorption k-distributions, continuum/minor-gas coefficients, g-band data, and Planck-related band information; write_data_* and write_tape5* tools serialize those products",
            "RECOVERED_PIPELINE_SCOPE_MUST_BE_QUALIFIED_FROM_PINNED_CODE_BEHAVIOR_NOT_FROM_REPOSITORY_NAME_ALONE",
            f"{AER_RRTM_BAND_GEN_INITIAL_SCRIPT_GEN_2BAND}; {AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_FOR}; {AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_PLANCK}; {AER_RRTM_BAND_GEN_INITIAL_COMP_WTAVG_PLANCK}",
        ),
        _row(
            "AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "MOLECULAR_K_DISTRIBUTION_PLANCK_CONTINUUM_PIPELINE_MUST_NOT_BE_RELABELED_AS_FU96_ICE_CLOUD_HIGH_RESOLUTION_PREAVERAGING_GENERATOR",
            "The pinned initial-file set contains k-distribution/Planck/continuum/minor-gas generation tools, but no provenance-linked Fu96 high-resolution ice-cloud spectral samples or Fu96 cloud-optics band-averaging generator was identified.",
        ),
        _row(
            "RRTM_SW_V25_RUNTIME_KURUCZ_LOW_HIGH_RESOLUTION_DISTINCTION", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_QUALIFIED",
            "Pinned v2.5 taumoldis.f explicitly distinguishes a low-resolution Kurucz solar source from a high-resolution version and notes a band-total irradiance discrepancy handled by SCALEKUR",
            "RUNTIME_SFLUXREF_MUST_NOT_BE_EQUATED_TO_UNRECOVERED_HIGH_RESOLUTION_CLOUD_TABLE_WEIGHT_VECTOR",
            f"{RRTM_SW_V25_EXTERNAL_TAUMOLDIS}; blob_sha={RRTM_SW_V25_EXTERNAL_TAUMOLDIS_BLOB_SHA}",
        ),
        _row(
            "RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME", "EXTERNAL_ARCHIVAL_LINEAGE", "PASS_QUALIFIED",
            "The GitHub history shows the mirrored v2.5 file tree was imported into the wrapper repository in 2020, while the preserved AER CVS metadata inside cldprop.f and makefiles dates the source lineage to April 2004",
            "GITHUB_IMPORT_TIMESTAMP_MUST_NOT_BE_USED_AS_THE_HISTORICAL_SOURCE_DATE_OR_AS_PROOF_OF_ORIGINAL_AER_ARCHIVE_IDENTITY",
            f"import_commit={RRTM_SW_V25_EXTERNAL_IMPORT_COMMIT}; import_date_utc={RRTM_SW_V25_EXTERNAL_IMPORT_DATE_UTC}; source_cvs_date=2004-04-15/16",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_PINNED_RUNTIME_CONTEXT",
            "Current AER RRTMG_SW description states RRTM_SW uses the Kurucz solar source with fixed solar constant 1368.22 W m-2 and that RRTMG_SW absorption data are consistent with RRTM_SW_v2.5",
            "OFFICIAL_V25_RUNTIME_SOLAR_CONTEXT_PINNED_WITHOUT_EQUATING_RUNTIME_SOURCE_TO_FU_CLOUD_TABLE_PREAVERAGING_WEIGHTS",
            AER_RRTMG_SW_DESCRIPTION,
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PUBLISHED", "OFFICIAL_ARCHIVE_PUBLICATION_CHAIN", "PASS_PINNED",
            "AER RRTM_SW Code and Examples identifies the source package as aer_rrtm_sw_v2.5.tar.gz",
            "OFFICIAL_V25_SOURCE_ARCHIVE_FILENAME_PINNED_WITHOUT_CLAIMING_ARCHIVE_BYTES_OR_HASH_RECOVERY",
            AER_RRTM_SW_CODE_PAGE,
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED", "OFFICIAL_ARCHIVE_ACQUISITION", "PASS_PINNED",
            "The current AER RRTM_SW Code and Examples page links aer_rrtm_sw_v2.5.tar.gz directly to files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz",
            "OFFICIAL_AER_BINARY_ENDPOINT_PINNED_WITHOUT_CLAIMING_SUCCESSFUL_ARCHIVE_RETRIEVAL_OR_HASH",
            AER_RRTM_SW_V25_SOURCE_ARCHIVE_URL,
        ),
        _row(
            "AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED", "OFFICIAL_ARCHIVE_ACQUISITION", "PASS_PINNED",
            "The v2.5 update notice documents anonymous FTP distribution at ftp.aer.com/pub/downloads/aer_rrtm_sw and explicitly instructs get aer_rrtm_sw_v2.5.tar.gz",
            "HISTORICAL_AER_FTP_DISTRIBUTION_PATH_PINNED_AS_LINEAGE_EVIDENCE_NOT_AS_CURRENT_ARCHIVE_BYTES",
            RRTM_SW_V25_EXTERNAL_UPDATE,
        ),
        _row(
            "RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT", "SECONDARY_ARCHIVAL_OBSERVATION", "PASS_SECONDARY_QUALIFIED",
            "An independent RRTM_SW v2.5 installation record describes obtaining the source package from AER and, after extraction, shows src/, makefiles/, rrtm_sw_instructions, update_rrtm_sw_v2.5.txt and a linux_pgi build object; the shown makefile declares VERSION = v2.5",
            "SECONDARY_EXTRACTED_DISTRIBUTION_FOOTPRINT_MAY_CORROBORATE_PACKAGING_ONLY_AND_MUST_NOT_ESTABLISH_ORIGINAL_TARBALL_HASH_OR_BYTE_IDENTITY",
            APPROPEDIA_RRTM_SW_V25_INSTALL_GUIDE,
        ),
        _row(
            "AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY", "LOCAL_ARCHIVE_VERIFICATION_TOOLING", "PASS_TOOLING",
            "tools/verify_aer_rrtm_sw_v25_archive.py can hash a locally acquired tar.gz, enumerate its tar manifest, check expected v2.5 footprint anchors, and optionally fetch the pinned official endpoint; it never upgrades archive authenticity without actual local bytes",
            "LOCAL_ARCHIVE_BYTES_REQUIRED_BEFORE_HASH_AND_MANIFEST_CAN_BE_RECORDED",
            "tools/verify_aer_rrtm_sw_v25_archive.py",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_WEB_TAR_BUILD_PROCEDURE", "OFFICIAL_ARCHIVE_PUBLICATION_CHAIN", "PASS_PINNED",
            "Pinned AER README.cvs_checkin_notes documents the April 2004 public-release procedure: update release files, then run script_build_rrtm_sw.pl to build source-code and example tar files for the web-site, with the proper version number",
            "OFFICIAL_WEB_TARBALL_RELEASE_BUILD_CHAIN_PINNED",
            f"{AER_RRTM_SW_RELEASE_BUILD_NOTES_PINNED}; blob_sha={AER_RRTM_SW_RELEASE_BUILD_NOTES_BLOB_SHA}",
        ),
        _row(
            "AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_AND_HASH_RECOVERED", "ARCHIVAL_AUTHENTICITY", "BLOCKED_NOT_RECOVERED",
            "The official v2.5 source-archive filename and website build procedure are now pinned, but the original aer_rrtm_sw_v2.5.tar.gz bytes and a provenance-qualified cryptographic hash are not present in the qualified evidence set",
            "ORIGINAL_AER_V25_ARCHIVE_BYTES_PLUS_HASH_OR_EQUIVALENT_AUTHENTICITY_CHAIN_REQUIRED_FOR_BYTE_IDENTITY",
            AER_RRTM_SW_CODE_PAGE,
        ),
        _row(
            "RRTM_SW_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN", "OFFICIAL_ARCHIVE_PUBLICATION_CHAIN", "PASS_QUALIFIED",
            "Official AER evidence now links the v2.5 source-archive filename to AER's documented website tar-build release process; this qualifies publication lineage but not original-tarball byte identity",
            "PUBLICATION_CHAIN_MAY_STRENGTHEN_LINEAGE_ONLY; BYTE_IDENTITY_REMAINS_FAIL_CLOSED_UNTIL_ARCHIVE_BYTES_HASH_RECOVERED",
            f"{AER_RRTM_SW_CODE_PAGE}; {AER_RRTM_SW_RELEASE_BUILD_NOTES_PINNED}",
        ),
        _row(
            "RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT_EQUALS_FU_CLOUD_TABLE_WEIGHT_VECTOR", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "RUNTIME_KURUCZ_CONTEXT_AND_SFLUXREF_DO_NOT_ESTABLISH_THE_UNRECOVERED_HIGH_RESOLUTION_CLOUD_TABLE_WEIGHT_VECTOR",
            f"{AER_RRTMG_SW_DESCRIPTION}; {RRTM_SW_V25_EXTERNAL_TAUMOLDIS}",
        ),
        _row(
            "RRTM_SW_V25_EXTERNAL_DISTRIBUTION_PREAVERAGING_GENERATOR_RECOVERY", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PRESENT",
            "The pinned external v2.5 distribution mirror preserves runtime cloud tables and runtime solar-source code but no Q. Fu high-resolution pre-averaging cloud table source or band-averaging generator was identified",
            "AUTHORITATIVE_OR_PROVENANCE_LINKED_PREAVERAGING_GENERATOR_STILL_REQUIRED",
            RRTM_SW_V25_EXTERNAL_MIRROR_REPOSITORY,
        ),
        _row(
            "RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY", "ARCHIVAL_AUTHENTICITY", "BLOCKED_NOT_PROVEN",
            "No original AER v2.5 tarball hash has been recovered, so the external mirror is qualified for source lineage evidence but not promoted to byte-identical authoritative AER distribution status",
            "ORIGINAL_AER_ARCHIVE_HASH_OR_EQUIVALENT_AUTHENTICITY_CHAIN_REQUIRED_FOR_BYTE_IDENTITY_CLAIM",
        ),
        _row(
            "PUBLIC_RUNTIME_ARCHIVE_SUFFICIENT_FOR_EXACT_HISTORICAL_GENERATOR", "PUBLIC_ARCHIVE_BOUNDARY", "PASS_FAIL_CLOSED",
            "false",
            "POST_AVERAGED_RRTM_SW_RUNTIME_TABLES_PLUS_CURRENT_PUBLIC_RRTMG_SW_RELEASE_DO_NOT_ESTABLISH_THE_HISTORICAL_PREAVERAGING_GENERATOR",
            f"{AER_RRTM_SW_CLDPROP_PINNED}; {AER_RRTMG_SW_README}",
        ),
        _row(
            "FINAL_TABLE_INVERSE_IDENTIFICATION_OF_H_OR_WEIGHTS", "SCOPE_GUARD", "PASS_FORBIDDEN",
            "false",
            "FINAL_EXTICE3_SSAICE3_ASYICE3_TABLES_ARE_OUTPUTS_AND_MUST_NOT_BE_INVERTED_TO_CLAIM_UNIQUE_H_SOLAR_GRID_OR_DISCRETE_WEIGHTS",
        ),
        _row(
            "RRTMG_HIGH_RES_TO_BAND_LINEAGE_STATEMENT", "MODEL_LINEAGE", "PASS_LINEAGE_ONLY",
            "RRTMG lineage documents that Fu high-resolution ice optical tables were averaged for RRTM_SW",
            "LINEAGE_STATEMENT_IS_NOT_EQUIVALENT_TO_REPRODUCIBLE_WEIGHT_VECTOR",
            "The final tables and semantic class are known; the exact historical transformation remains unrecovered.",
        ),
        _row(
            "RRTMG_PRE_V4_RUNTIME_SOLAR_SOURCE_KURUCZ", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_PINNED_RUNTIME_CONTEXT",
            "RRTMG_SW documentation states versions prior to v4.0 used the Kurucz solar source with total solar irradiance 1368.22 W m-2",
            "RUNTIME_SOLAR_SOURCE_CONTEXT_PINNED_BUT_NOT_EQUATED_TO_CLOUD_TABLE_GENERATOR", AER_RRTMG_SW_DESCRIPTION,
        ),
        _row(
            "RRTMG_PRE_V4_BAND24_25_SOLAR_IRRADIANCE_TOTALS", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_PINNED_BAND_TOTALS",
            "Documented RRTMG_SW band-integrated solar irradiance: band 24 (0.625-0.778 um) about 218.19 W m-2; band 25 (0.442-0.625 um) about 347.20 W m-2",
            "BAND_TOTALS_ARE_CONTEXT_ONLY_AND_DO_NOT_DEFINE_WITHIN_BAND_DISCRETE_WEIGHTS", CAM5_DESCRIPTION,
        ),
        _row(
            "RRTMG_RUNTIME_SOLAR_SOURCE_EQUALS_FU96_TABLE_GENERATION_SOURCE", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PROVEN",
            "No authoritative source recovered that proves the runtime Kurucz solar spectrum realization is exactly the spectrum/grid/weights used when Q. Fu high-resolution tables were averaged into the archived default RRTM_SW cloud tables",
            "EXACT_GENERATOR_SOLAR_SOURCE_IDENTITY_MUST_BE_PROVEN_BEFORE_REUSE",
        ),
        _row(
            "FU96_RRTMG_PREAVERAGING_SPECTRAL_SAMPLE_SET", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "No version-pinned authoritative pre-averaging spectral sample set tied to the archived default RRTMG band-24/25 Fu96 tables has been recovered",
            "EXACT_PREAVERAGING_SPECTRAL_SAMPLES_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_EXACT_SOLAR_SPECTRUM_AND_DISCRETE_WEIGHTS", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "Solar-irradiance weighting is supported as the semantic class, but the exact historical solar spectrum version, sampling grid, and discrete weights used to generate the archived default Fu96 RRTMG tables are not recovered",
            "VERSION_PINNED_SOLAR_SPECTRUM_PLUS_DISCRETE_WEIGHT_VECTOR_OR_EXACTLY_EQUIVALENT_ALGORITHM_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_WEIGHTING_SEMANTICS_CLASS", "EXACT_WEIGHTING_PREREQUISITE", "PASS_NARROWED_NOT_EXACT",
            "Qualified constraints: solar irradiance is a weighting basis; historical Fu96 coalbedo used absorption-dependent linear/log averaging; later RRTMG-band schemes may use integrated scattering/extinction SSA and scattering-weighted g. These are not interchangeable provenance claims",
            "HISTORICAL_FU96_AND_LATER_RRTMG_SEMANTICS_SEPARATED; EXACT_HISTORICAL_REALIZATION_STILL_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_BAND24_EXACT_REPRODUCTION", "NUMERIC_REPRODUCTION", "BLOCKED_NO_EXACT_WEIGHT_VECTOR",
            "not executed", "REPRODUCE_PINNED_RRTMG_BAND24_REFERENCE_FROM_AUTHORITATIVE_HISTORICAL_INPUTS",
        ),
        _row(
            "FU96_RRTMG_BAND25_EXACT_REPRODUCTION", "NUMERIC_REPRODUCTION", "BLOCKED_NO_EXACT_WEIGHT_VECTOR",
            "not executed", "REPRODUCE_PINNED_RRTMG_BAND25_REFERENCE_FROM_AUTHORITATIVE_HISTORICAL_INPUTS",
        ),
        _row("ARBITRARY_EQUAL_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "MUST_NOT_SUBSTITUTE_FOR_EXACT_FU96_RRTMG_WEIGHTING"),
        _row("UNVERSIONED_OR_ASSUMED_SOLAR_SPECTRUM_WEIGHTS", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "SOLAR_WEIGHTING_CLASS_IS_SUPPORTED_BUT_EXACT_HISTORICAL_SPECTRUM_AND_WEIGHTS_MUST_BE_PINNED"),
        _row("GPOINT_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "MUST_NOT_BE_ASSUMED_AS_THE_CLOUD_OPTICS_BAND_AVERAGING_RULE"),
        _row("AD_HOC_EXTINCTION_OR_SCATTERING_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "NO_AD_HOC_REWEIGHTING"),
        _row("YI2013_FORMULA_AS_HISTORICAL_FU96_DEFAULT_TABLE_GENERATOR", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "LATER_RRTMG_BAND_FORMULA_MUST_NOT_BE_SUBSTITUTED_FOR_UNRECOVERED_HISTORICAL_FU96_AVERAGING"),
        _row(
            "EXACT_FU96_RRTMG_BAND_WEIGHTING", "QUALIFICATION_RESULT", "BLOCKED_NOT_PROVEN", "false",
            "PREAVERAGING_SAMPLES_PLUS_VERSION_PINNED_SOLAR_SPECTRUM_AND_DISCRETE_WEIGHTS_PLUS_NUMERIC_REPRODUCTION_REQUIRED",
        ),
        _row(
            "YANG_FULL_SPECTRAL_BAND_INTEGRATION_VALIDATION", "DOWNSTREAM_BLOCKER", "BLOCKED", "false",
            "EXACT_FU96_RRTMG_BAND_WEIGHTING_REQUIRED_BEFORE_LIKE_FOR_LIKE_YANG_INTEGRATION",
        ),
        _row(
            "PRODUCTION_PROMOTION_GUARD", "PRODUCTION_GUARD", "PASS_FAIL_CLOSED",
            "independent_ssa=false; independent_g=false; tau_ice=false; production_ice_optics=false; physics_promotion=false",
            "NO_STEP3Q2_PRODUCTION_PROMOTION",
        ),
    ]
    return pd.DataFrame(rows)


def build_fu96_rrtmg_band_weighting_provenance_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    evidence = evidence if evidence is not None else build_fu96_rrtmg_band_weighting_provenance_evidence()
    status = {str(r.check_id): str(r.status) for r in evidence.itertuples(index=False)}
    primary = status.get("FU96_PRIMARY_SOLAR_ICE_PARAMETERIZATION_PINNED") == "PASS_PINNED"
    lineage = status.get("RRTMG_ICEFLAG3_FU96_DGE_LINEAGE") == "PASS_PINNED"
    tables = status.get("RRTMG_FU96_FINAL_BAND_TABLES_PINNED") == "PASS_PINNED"
    semantic = status.get("FU96_RRTMG_WEIGHTING_SEMANTICS_CLASS") == "PASS_NARROWED_NOT_EXACT"
    band_limits = status.get("RRTMG_SW_BAND_LIMITS_24_25_PINNED") == "PASS_PINNED"
    equation_family = all(status.get(k) == "PASS_QUALIFIED" for k in ["FU96_LINEAGE_LINEAR_COALBEDO_EQUATION","FU96_LINEAGE_LOG_COALBEDO_EQUATION","FU96_LINEAGE_MIXED_COALBEDO_EQUATION","FU96_LINEAGE_H_EMPIRICAL_SELECTION"])
    h_domain_constraints = all(status.get(k) == "PASS_QUALIFIED" for k in [
        "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU1998",
        "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU2002",
        "RRTMG_BAND25_H_DOMAIN_CONSTRAINT",
        "RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING",
    ])
    archive_boundary = all(status.get(k) == "PASS_QUALIFIED" for k in [
        "RRTM_SW_FU96_POST_AVERAGED_ARCHIVE_PINNED",
        "RRTM_SW_FU96_46_NODE_DGE_RUNTIME_GRID",
    ]) and status.get("RRTM_SW_PREAVERAGING_FU96_GENERATOR_PRESENT_IN_PINNED_ARCHIVE") == "BLOCKED_NOT_PRESENT"
    public_archive_boundary = (
        status.get("RRTMG_SW_CURRENT_PRE_V5_PUBLIC_RELEASE_AVAILABILITY") == "PASS_QUALIFIED"
        and status.get("PUBLIC_RUNTIME_ARCHIVE_SUFFICIENT_FOR_EXACT_HISTORICAL_GENERATOR") == "PASS_FAIL_CLOSED"
    )
    official_archive_publication_chain = (
        status.get("AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PUBLISHED") == "PASS_PINNED"
        and status.get("AER_OFFICIAL_RRTM_SW_WEB_TAR_BUILD_PROCEDURE") == "PASS_PINNED"
        and status.get("RRTM_SW_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN") == "PASS_QUALIFIED"
        and status.get("AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_AND_HASH_RECOVERED") == "BLOCKED_NOT_RECOVERED"
    )
    official_source_tree_equivalence = (
        status.get("AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED") == "PASS_PINNED"
        and status.get("AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED") == "PASS_PINNED"
        and status.get("RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE") == "PASS_QUALIFIED"
    )
    official_scientific_source_semantic_equivalence = (
        status.get("AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED") == "PASS_PINNED"
        and status.get("RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_IS_RAW_BYTE_IDENTITY") == "PASS_FORBIDDEN"
    )
    official_download_distribution_footprint = (
        status.get("AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED") == "PASS_PINNED"
        and status.get("AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED") == "PASS_PINNED"
        and status.get("RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT") == "PASS_SECONDARY_QUALIFIED"
        and status.get("AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY") == "PASS_TOOLING"
    )
    pre2020_cross_repository_raw_blob_replication = (
        status.get("PYRRTM_SW_2014_PRE2020_HISTORY_PINNED") == "PASS_PINNED"
        and status.get("RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION") == "PASS_QUALIFIED"
        and status.get("RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY") == "PASS_FORBIDDEN"
    )
    official_aer_cross_generation_fu96_final_table_continuity = (
        status.get("AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED") == "PASS_PINNED"
        and status.get("AER_RRTM_SW_2004_TO_RRTMG_SW_2007_FU96_FINAL_TABLE_VALUE_CONTINUITY") == "PASS_QUALIFIED"
        and status.get("AER_RRTM_RRTMG_FU96_FINAL_TABLE_CONTINUITY_IS_PREAVERAGING_GENERATOR_RECOVERY") == "PASS_FORBIDDEN"
    )
    historical_aer_rrtm_band_generation_scope = (
        status.get("AER_RRTM_BAND_GEN_IMPORTED_SVN_HISTORY_PINNED") == "PASS_PINNED"
        and status.get("AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT_PINNED") == "PASS_PINNED"
        and status.get("AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_SCOPE") == "PASS_QUALIFIED"
        and status.get("AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR") == "PASS_FORBIDDEN"
    )
    exact = status.get("EXACT_FU96_RRTMG_BAND_WEIGHTING") == "PASS"
    state = (
        "PASS_EXACT_WEIGHTING_PROVENANCE_QUALIFIED" if primary and lineage and tables and semantic and exact
        else "PASS_FAIL_CLOSED_FU96_LINEAGE_BROADBAND_WEIGHTING_EQUATION_TRANSCRIPTION_CORRECTED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED"
    )
    return pd.DataFrame([{
        "qualification_state": state,
        "FU96_PRIMARY_SOURCE_PINNED": bool(primary),
        "RRTMG_FU96_DGE_LINEAGE_PINNED": bool(lineage),
        "RRTMG_FINAL_FU96_BAND_TABLES_PINNED": bool(tables),
        "RRTMG_BAND24_25_LIMITS_PINNED": bool(band_limits),
        "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_SUPPORTED": True,
        "FU96_HISTORICAL_MIXED_LINEAR_LOG_COALBEDO_SEMANTIC_PINNED": True,
        "FU96_HISTORICAL_COALBEDO_EQUATION_FAMILY_QUALIFIED": bool(equation_family),
        "FU96_LINEAGE_COALBEDO_BETA_WEIGHTING_TRANSCRIPTION_CORRECTED": bool(status.get("FU96_LINEAGE_COALBEDO_EXTINCTION_WEIGHTING_TRANSCRIPTION_CORRECTED") == "PASS_CORRECTED"),
        "FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTING_QUALIFIED": bool(status.get("FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTED_EQUATION") == "PASS_QUALIFIED"),
        "FU96_LINEAGE_SIMPLE_SOLAR_ONLY_COALBEDO_WEIGHTING_FORBIDDEN": bool(status.get("FU96_LINEAGE_SIMPLE_SOLAR_ONLY_COALBEDO_AVERAGE") == "PASS_FORBIDDEN"),
        "FU96_HISTORICAL_H_DOMAIN_CONSTRAINTS_QUALIFIED": bool(h_domain_constraints),
        "RRTM_SW_POST_AVERAGED_ARCHIVE_BOUNDARY_QUALIFIED": bool(archive_boundary),
        "RRTMG_SW_PUBLIC_RELEASE_AVAILABILITY_BOUNDARY_QUALIFIED": bool(public_archive_boundary),
        "RRTMG_SW_PRE_V5_CURRENT_PUBLIC_RELEASES_AVAILABLE": False,
        "RRTM_SW_V24_HISTORICALLY_PUBLIC_2002": bool(status.get("RRTM_SW_V24_HISTORICALLY_PUBLIC_2002") == "PASS_PINNED"),
        "RRTM_SW_V25_HISTORICAL_USE_2006": bool(status.get("RRTM_SW_V25_HISTORICAL_USE_2006") == "PASS_PINNED"),
        "RRTM_SW_V25_EXTERNAL_DISTRIBUTION_MIRROR_PINNED": bool(status.get("RRTM_SW_V25_EXTERNAL_DISTRIBUTION_MIRROR_PINNED") == "PASS_PINNED"),
        "RRTM_SW_V25_UPDATE_NOTE_IDENTITY_PINNED": bool(status.get("RRTM_SW_V25_UPDATE_NOTE_IDENTITY") == "PASS_PINNED"),
        "RRTM_SW_V25_MAKEFILE_VERSION_IDENTITY_PINNED": bool(status.get("RRTM_SW_V25_MAKEFILE_VERSION_IDENTITY") == "PASS_PINNED"),
        "RRTM_SW_V25_CLDPROP_CVS_PROVENANCE_PINNED": bool(status.get("RRTM_SW_V25_CLDPROP_CVS_PROVENANCE") == "PASS_PINNED"),
        "RRTM_SW_V25_CLDPROP_SCIENCE_CONTENT_EQUIVALENCE_QUALIFIED": bool(status.get("RRTM_SW_V25_CLDPROP_SCIENCE_CONTENT_EQUIVALENCE_TO_AER_ARCHIVE") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_RUNTIME_KURUCZ_LOW_HIGH_RESOLUTION_DISTINCTION_QUALIFIED": bool(status.get("RRTM_SW_V25_RUNTIME_KURUCZ_LOW_HIGH_RESOLUTION_DISTINCTION") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME": bool(status.get("RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME") == "PASS_QUALIFIED"),
        "AER_OFFICIAL_RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT") == "PASS_PINNED_RUNTIME_CONTEXT"),
        "AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PUBLISHED") == "PASS_PINNED"),
        "AER_RRTM_SW_WEB_TAR_BUILD_PROCEDURE_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_WEB_TAR_BUILD_PROCEDURE") == "PASS_PINNED"),
        "RRTM_SW_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED": bool(official_archive_publication_chain),
        "RRTM_SW_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED": bool(official_source_tree_equivalence),
        "AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED") == "PASS_PINNED"),
        "RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH_24_OF_26_QUALIFIED": bool(status.get("RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED": bool(status.get("RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED": bool(status.get("RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED": bool(official_scientific_source_semantic_equivalence),
        "RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_IS_FULL_RAW_BYTE_IDENTITY": False,
        "PYRRTM_SW_2014_PRE2020_HISTORY_PINNED": bool(status.get("PYRRTM_SW_2014_PRE2020_HISTORY_PINNED") == "PASS_PINNED"),
        "RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26_QUALIFIED": bool(status.get("RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION_QUALIFIED": bool(pre2020_cross_repository_raw_blob_replication),
        "RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY": False,
        "AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED": bool(status.get("AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED") == "PASS_PINNED"),
        "AER_RRTM_SW_TO_RRTMG_SW_FU96_FINAL_TABLE_CONTINUITY_56_OF_56_ARRAYS_2576_OF_2576_VALUES_QUALIFIED": bool(official_aer_cross_generation_fu96_final_table_continuity),
        "AER_RRTM_RRTMG_FU96_FINAL_TABLE_CONTINUITY_IS_PREAVERAGING_GENERATOR_RECOVERY": False,
        "AER_RRTM_BAND_GEN_IMPORTED_SVN_HISTORY_PINNED": bool(status.get("AER_RRTM_BAND_GEN_IMPORTED_SVN_HISTORY_PINNED") == "PASS_PINNED"),
        "AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT_PINNED": bool(status.get("AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT_PINNED") == "PASS_PINNED"),
        "AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_RECOVERED": bool(historical_aer_rrtm_band_generation_scope),
        "AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR": False,
        "FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED": False,
        "AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED") == "PASS_PINNED"),
        "AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED": bool(status.get("AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED") == "PASS_PINNED"),
        "RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT_QUALIFIED": bool(status.get("RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT") == "PASS_SECONDARY_QUALIFIED"),
        "AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY": bool(status.get("AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY") == "PASS_TOOLING"),
        "RRTM_SW_V25_OFFICIAL_DOWNLOAD_AND_EXTRACTED_FOOTPRINT_QUALIFIED": bool(official_download_distribution_footprint),
        "AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED") == "PASS_PINNED"),
        "AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED": bool(status.get("AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED") == "PASS_PINNED"),
        "RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE_QUALIFIED": bool(status.get("RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE") == "PASS_QUALIFIED"),
        "RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE_QUALIFIED": bool(status.get("RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE") == "PASS_QUALIFIED"),
        "AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED": False,
        "AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED": False,
        "RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT_EQUALS_FU_CLOUD_TABLE_WEIGHT_VECTOR": False,
        "RRTM_SW_V25_EXTERNAL_DISTRIBUTION_CONTAINS_PREAVERAGING_GENERATOR": False,
        "RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY_PROVEN": False,
        "PUBLIC_RUNTIME_ARCHIVE_SUFFICIENT_FOR_EXACT_HISTORICAL_GENERATOR": False,
        "RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED": False,
        "FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED": False,
        "RRTMG_BAND25_FULLY_WITHIN_FU_LINEAGE_H1_DOMAIN": bool(status.get("RRTMG_BAND25_H_DOMAIN_CONSTRAINT") == "PASS_QUALIFIED"),
        "RRTMG_BAND24_CROSSES_FU_LINEAGE_H_DOMAIN_BOUNDARY": bool(status.get("RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING") == "PASS_QUALIFIED"),
        "RRTMG_BAND24_SINGLE_H_ASSIGNMENT_JUSTIFIED": False,
        "RRTMG_BAND25_EXACT_ARCHIVED_GENERATOR_H_PROVEN": False,
        "FU96_HISTORICAL_BAND24_25_H_VALUES_RECOVERED": False,
        "LATER_RRTMG_BAND_INTEGRATION_SEMANTIC_CLASS_QUALIFIED": bool(semantic),
        "YI2013_FORMULA_PROVEN_AS_HISTORICAL_FU96_TABLE_GENERATOR": False,
        "RRTMG_PRE_V4_KURUCZ_RUNTIME_SOLAR_SOURCE_PINNED": True,
        "RRTMG_BAND24_25_SOLAR_IRRADIANCE_TOTALS_PINNED": True,
        "RUNTIME_SOLAR_SOURCE_IDENTITY_WITH_FU96_TABLE_GENERATOR_PROVEN": False,
        "FU96_HISTORICAL_BAND_SPECIFIC_LINEAR_LOG_MIXING_RECOVERED": False,
        "PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED": False,
        "EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED": False,
        "HISTORICAL_EXACT_WEIGHTING_REALIZATION_UNAMBIGUOUS": False,
        "RRTMG_BAND24_EXACT_REPRODUCTION_PASS": False,
        "RRTMG_BAND25_EXACT_REPRODUCTION_PASS": False,
        "EXACT_FU96_BAND_WEIGHTING_AVAILABLE": False,
        "BAND_INTEGRATED_OPTICAL_VALIDATION_READY": False,
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
    }])


def fu96_rrtmg_band_weighting_provenance_contract_payload(*, evidence: pd.DataFrame | None = None, gate: pd.DataFrame | None = None, physicscore_version: str = PHYSICSCORE_VERSION) -> dict[str, Any]:
    evidence = evidence if evidence is not None else build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = gate if gate is not None else build_fu96_rrtmg_band_weighting_provenance_gate(evidence)
    g = gate.iloc[0].to_dict()
    return {
        "contract_version": "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_17",
        "physicscore_version": str(physicscore_version),
        "step_version": STEP3Q_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3Q_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "sources": {
            "fu96_doi": FU96_DOI,
            "fu2007_doi": FU2007_DOI,
            "yi2013_doi": YI2013_DOI,
            "chou1998_doi": CHOU1998_DOI,
            "chou2002_doi": CHOU2002_DOI,
            "baek2018_doi": BAEK2018_DOI,
            "aer_rrtmg_sw_description": AER_RRTMG_SW_DESCRIPTION,
            "cam5_description": CAM5_DESCRIPTION,
            "aer_rrtmg_sw_repository": AER_RRTMG_SW_REPOSITORY,
            "aer_rrtm_band_gen_repository": AER_RRTM_BAND_GEN_REPOSITORY,
            "aer_rrtm_band_gen_initial_original_rrtm_work_commit": AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_URL,
            "aer_rrtm_band_gen_initial_script_gen_2band": AER_RRTM_BAND_GEN_INITIAL_SCRIPT_GEN_2BAND,
            "aer_rrtm_band_gen_initial_kdis_2sort_for": AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_FOR,
            "aer_rrtm_band_gen_initial_kdis_2sort_planck": AER_RRTM_BAND_GEN_INITIAL_KDIS_2SORT_PLANCK,
            "aer_rrtm_band_gen_initial_comp_wtavg_planck": AER_RRTM_BAND_GEN_INITIAL_COMP_WTAVG_PLANCK,
            "aer_rrtmg_sw_readme": AER_RRTMG_SW_README,
            "arm_2002_rrtm_sw_v24_proceedings": ARM_2002_RRTM_SW_V24_PROCEEDINGS,
            "michalsky2006_doi": MICHALSKY2006_DOI,
            "aer_rrtm_sw_instructions": AER_RRTM_SW_INSTRUCTIONS,
            "aer_rrtm_sw_cldprop_pinned": AER_RRTM_SW_CLDPROP_PINNED,
            "aer_rrtm_sw_cldprop_blob_sha": AER_RRTM_SW_CLDPROP_BLOB_SHA,
            "aer_rrtm_sw_code_page": AER_RRTM_SW_CODE_PAGE,
            "aer_rrtm_sw_v25_source_archive_filename": AER_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME,
            "aer_rrtm_sw_v25_examples_archive_filename": AER_RRTM_SW_V25_EXAMPLES_ARCHIVE_FILENAME,
            "aer_rrtm_sw_v25_source_archive_url": AER_RRTM_SW_V25_SOURCE_ARCHIVE_URL,
            "aer_rrtm_sw_v25_historical_ftp_source_path": AER_RRTM_SW_V25_HISTORICAL_FTP_SOURCE_PATH,
            "appropedia_rrtm_sw_v25_install_guide": APPROPEDIA_RRTM_SW_V25_INSTALL_GUIDE,
            "aer_rrtm_sw_release_build_notes_pinned": AER_RRTM_SW_RELEASE_BUILD_NOTES_PINNED,
            "aer_rrtm_sw_release_build_notes_blob_sha": AER_RRTM_SW_RELEASE_BUILD_NOTES_BLOB_SHA,
            "aer_rrtm_sw_v25_official_cldprop_2004": AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004,
            "aer_rrtm_sw_v25_official_cldprop_2004_commit": AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_COMMIT,
            "aer_rrtm_sw_v25_official_cldprop_2004_date_utc": AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_DATE_UTC,
            "aer_rrtm_sw_v25_official_cldprop_2004_blob_sha": AER_RRTM_SW_V25_OFFICIAL_CLDPROP_2004_BLOB_SHA,
            "aer_rrtm_sw_v25_official_taumoldis_2004": AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004,
            "aer_rrtm_sw_v25_official_taumoldis_2004_commit": AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_COMMIT,
            "aer_rrtm_sw_v25_official_taumoldis_2004_date_utc": AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_DATE_UTC,
            "aer_rrtm_sw_v25_official_taumoldis_2004_blob_sha": AER_RRTM_SW_V25_OFFICIAL_TAUMOLDIS_2004_BLOB_SHA,
            "aer_rrtm_sw_v25_official_release_tree_commit": AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_COMMIT,
            "aer_rrtm_sw_v25_official_release_tree_sha": AER_RRTM_SW_V25_OFFICIAL_RELEASE_TREE_SHA,
            "rrtm_sw_v25_external_import_tree_sha": RRTM_SW_V25_EXTERNAL_IMPORT_TREE_SHA,
            "aer_rrtmg_sw_2007_continuity_commit": AER_RRTMG_SW_2007_CONTINUITY_COMMIT,
            "aer_rrtmg_sw_2007_continuity_date_utc": AER_RRTMG_SW_2007_CONTINUITY_DATE_UTC,
            "aer_rrtmg_sw_2007_continuity_tree_sha": AER_RRTMG_SW_2007_CONTINUITY_TREE_SHA,
            "aer_rrtmg_sw_2007_cldprop": AER_RRTMG_SW_2007_CLDPROP,
            "aer_rrtmg_sw_2007_cldprop_blob_sha": AER_RRTMG_SW_2007_CLDPROP_BLOB_SHA,
            "pyrrtm_repository": PYRRTM_REPOSITORY,
            "pyrrtm_sw_2014_commit": PYRRTM_SW_2014_COMMIT,
            "pyrrtm_sw_2014_date_utc": PYRRTM_SW_2014_DATE_UTC,
            "pyrrtm_sw_2014_tree_sha": PYRRTM_SW_2014_TREE_SHA,
            "pyrrtm_sw_2014_commit_url": PYRRTM_SW_2014_COMMIT_URL,
            "pyrrtm_sw_2014_cldprop_blob_sha": PYRRTM_SW_2014_CLDPROP_BLOB_SHA,
            "pyrrtm_sw_2014_taumoldis_blob_sha": PYRRTM_SW_2014_TAUMOLDIS_BLOB_SHA,
            "pyrrtm_sw_2014_k_gB24_blob_sha": PYRRTM_SW_2014_KGB24_BLOB_SHA,
            "pyrrtm_sw_2014_k_gB25_blob_sha": PYRRTM_SW_2014_KGB25_BLOB_SHA,
            "rrtm_sw_v25_scientific_source_file_count": RRTM_SW_V25_SCIENTIFIC_SOURCE_FILE_COUNT,
            "rrtm_sw_v25_cvs_normalized_full_file_match_count": RRTM_SW_V25_CVS_NORMALIZED_FULL_FILE_MATCH_COUNT,
            "rrtm_sw_v25_operational_delta_file_count": RRTM_SW_V25_OPERATIONAL_DELTA_FILE_COUNT,
            "rrtm_sw_v25_operational_delta_line_count": RRTM_SW_V25_OPERATIONAL_DELTA_LINE_COUNT,
            "aer_rrtm_sw_v25_official_rrtatm_2004_blob_sha": AER_RRTM_SW_V25_OFFICIAL_RRTATM_2004_BLOB_SHA,
            "rrtm_sw_v25_external_import_rrtatm_blob_sha": RRTM_SW_V25_EXTERNAL_IMPORT_RRTATM_BLOB_SHA,
            "aer_rrtm_sw_v25_official_rrtm_2004_blob_sha": AER_RRTM_SW_V25_OFFICIAL_RRTM_2004_BLOB_SHA,
            "rrtm_sw_v25_external_import_rrtm_blob_sha": RRTM_SW_V25_EXTERNAL_IMPORT_RRTM_BLOB_SHA,
            "rrtm_sw_v25_external_mirror_repository": RRTM_SW_V25_EXTERNAL_MIRROR_REPOSITORY,
            "rrtm_sw_v25_external_mirror_commit": RRTM_SW_V25_EXTERNAL_MIRROR_COMMIT,
            "rrtm_sw_v25_external_import_commit": RRTM_SW_V25_EXTERNAL_IMPORT_COMMIT,
            "rrtm_sw_v25_external_import_date_utc": RRTM_SW_V25_EXTERNAL_IMPORT_DATE_UTC,
            "rrtm_sw_v25_external_import_cldprop": RRTM_SW_V25_EXTERNAL_IMPORT_CLDPROP,
            "rrtm_sw_v25_external_import_taumoldis": RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS,
            "rrtm_sw_v25_external_import_taumoldis_blob_sha": RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS_BLOB_SHA,
            "rrtm_sw_v25_external_cldprop": RRTM_SW_V25_EXTERNAL_CLDPROP,
            "rrtm_sw_v25_external_cldprop_blob_sha": RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA,
            "rrtm_sw_v25_external_update": RRTM_SW_V25_EXTERNAL_UPDATE,
            "rrtm_sw_v25_external_update_blob_sha": RRTM_SW_V25_EXTERNAL_UPDATE_BLOB_SHA,
            "rrtm_sw_v25_external_taumoldis": RRTM_SW_V25_EXTERNAL_TAUMOLDIS,
            "rrtm_sw_v25_external_taumoldis_blob_sha": RRTM_SW_V25_EXTERNAL_TAUMOLDIS_BLOB_SHA,
            "rrtm_sw_v25_external_makefile": RRTM_SW_V25_EXTERNAL_MAKEFILE,
            "rrtm_sw_v25_external_makefile_blob_sha": RRTM_SW_V25_EXTERNAL_MAKEFILE_BLOB_SHA,
            "pinned_rrtmg_reference_source": GEOSCHEM_RRTMG_PINNED_SOURCE,
            "pinned_rrtmg_reference_source_sha": GEOSCHEM_RRTMG_SOURCE_SHA,
        },
        "bands": list(RRTMG_BANDS),
        "qualified_weighting_semantic_class": {
            "shortwave_weighting_basis": "solar_irradiance",
            "historical_fu96_coalbedo": "absorption_dependent_mix_of_solar_weighted_linear_and_logarithmic_averages",
            "historical_fu96_alpha_linear": "sum(alpha_lambda*S_lambda*dLambda)/sum(S_lambda*dLambda)",
            "historical_fu96_alpha_log": "exp(sum(ln(alpha_lambda)*S_lambda*dLambda)/sum(S_lambda*dLambda))",
            "historical_fu96_h_semantic": "empirical flux-calibration parameter; h near 1 for weak absorption and decreases with stronger absorption",
            "historical_fu96_band24_25_h_values_recovered": False,
            "fu_lineage_h_domains": {
                "0.175_to_0.700_um": 1.0,
                "0.700_to_1.220_um": "2/3",
            },
            "rrtmg_band25_domain_constraint": "0.441501-0.625000 um lies entirely inside Fu-lineage h=1 domain; exact archived-generator identity still unproven",
            "rrtmg_band24_domain_constraint": "0.625000-0.778210 um crosses 0.700 um h-domain boundary; no single h may be assigned without historical generator proof",
            "rrtmg_band24_single_h_assignment_allowed": False,
            "rrtmg_band25_exact_archived_generator_h_proven": False,
            "rrtm_sw_archive_boundary": "pinned runtime archive contains post-averaged EXTICE3/SSAICE3/ASYICE3/FDLICE3 tables plus interpolation, not the Q. Fu high-resolution pre-averaging sample set or averaging generator",
            "rrtm_sw_preaveraging_generator_recovered": False,
            "rrtmg_sw_pre_v5_current_public_releases_available": False,
            "rrtm_sw_v24_historically_public_2002": True,
            "rrtm_sw_v25_historical_use_2006": True,
            "public_runtime_archive_sufficient_for_exact_historical_generator": False,
            "v25_external_distribution_lineage_qualified": True,
            "v25_external_mirror_original_aer_tarball_byte_identity_proven": False,
            "v25_official_source_archive_filename_pinned": True,
            "v25_official_web_tar_build_procedure_pinned": True,
            "v25_official_archive_publication_chain_qualified": True,
            "v25_official_source_tree_cvs_normalized_equivalence_qualified": True,
            "v25_official_scientific_source_set_manifest_pinned": True,
            "v25_scientific_source_cvs_normalized_full_file_match_count": 24,
            "v25_scientific_source_operational_delta_file_count": 2,
            "v25_scientific_source_operational_delta_line_count": 4,
            "v25_scientific_source_semantic_equivalence_qualified": True,
            "v25_scientific_source_semantic_equivalence_is_full_raw_byte_identity": False,
            "v25_pre2020_pyrrtm_history_pinned": True,
            "v25_cross_repository_scientific_source_file_count": 26,
            "v25_cross_repository_raw_blob_match_count": 22,
            "v25_cross_repository_raw_blob_nonmatch_count": 4,
            "v25_critical_fu96_band24_25_raw_blob_replication_qualified": True,
            "v25_cross_repository_raw_blob_replication_is_original_aer_tarball_identity": False,
            "aer_rrtm_sw_to_rrtmg_sw_fu96_final_table_continuity_qualified": True,
            "aer_rrtm_rrtmg_fu96_continuity_array_count": 56,
            "aer_rrtm_rrtmg_fu96_continuity_value_count": 2576,
            "aer_rrtm_rrtmg_fu96_final_table_continuity_is_preaveraging_generator_recovery": False,
            "aer_historical_rrtm_band_generation_svn_history_pinned": True,
            "aer_historical_rrtm_band_generation_initial_original_rrtm_work_commit_pinned": True,
            "aer_historical_rrtm_molecular_band_generation_pipeline_recovered": True,
            "aer_historical_rrtm_band_generation_pipeline_is_fu96_cloud_preaveraging_generator": False,
            "fu96_cloud_preaveraging_generator_recovered": False,
            "v25_official_binary_download_endpoint_pinned": True,
            "v25_historical_ftp_distribution_path_pinned": True,
            "v25_independent_extracted_distribution_footprint_qualified": True,
            "v25_archive_acquisition_verifier_ready": True,
            "v25_official_download_and_extracted_footprint_qualified": True,
            "v25_cldprop_official_mirror_cvs_normalized_equivalence": True,
            "v25_taumoldis_official_mirror_cvs_normalized_equivalence": True,
            "v25_official_source_tree_equivalence_is_original_tarball_byte_identity": False,
            "v25_original_aer_archive_bytes_recovered": False,
            "v25_original_aer_archive_hash_recovered": False,
            "v25_runtime_kurucz_low_high_resolution_distinction_qualified": True,
            "v25_runtime_sfluxref_equated_to_cloud_table_high_resolution_weights": False,
            "final_table_inverse_identification_allowed": False,
            "later_rrtmg_band_ssa_example": "band_integrated_scattering_divided_by_band_integrated_extinction",
            "later_rrtmg_band_g_example": "scattering_cross_section_weighted_with_solar_spectrum",
            "later_formula_is_historical_fu96_generator": False,
            "historical_exact_solar_spectrum_and_discrete_weights_recovered": False,
            "historical_band_specific_linear_log_mixing_recovered": False,
        },
        "qualification_state": str(g["qualification_state"]),
        "capabilities": {k: bool(v) for k, v in g.items() if k != "qualification_state"},
        "forbidden_substitutes": [
            "equal_weighting",
            "unversioned_or_assumed_solar_spectrum_weights",
            "assumed_gpoint_weighting_for_cloud_optics_band_average",
            "ad_hoc_extinction_or_scattering_reweighting",
            "yi2013_formula_substituted_as_historical_fu96_generator",
            "inverse_identification_of_unique_h_or_weights_from_final_rrtm_tables",
            "treating_public_release_absence_as_generator_identity_evidence",
            "treating_v25_runtime_low_resolution_kurucz_sfluxref_as_exact_cloud_table_high_resolution_weights",
            "treating_external_v25_mirror_as_byte_identical_original_aer_tarball_without_original_archive_hash",
            "treating_official_archive_filename_or_web_build_procedure_as_equivalent_to_recovered_original_tarball_bytes_or_hash",
            "treating_cvs_normalized_source_tree_equivalence_as_proof_of_original_tarball_byte_identity_or_original_tarball_hash",
            "treating_scientific_source_semantic_equivalence_with_documented_operational_deltas_as_full_raw_byte_identity_or_original_tarball_identity",
            "treating_pre2020_cross_repository_raw_blob_replication_as_original_aer_tarball_byte_identity_or_authoritative_archive_hash",
            "treating_official_aer_rrtm_sw_to_rrtmg_sw_final_table_continuity_as_recovered_preaveraging_generator_exact_weighting_or_original_v25_tarball_hash",
            "treating_historical_aer_rrtm_molecular_kdistribution_planck_band_generation_pipeline_as_the_fu96_ice_cloud_high_resolution_preaveraging_generator",
            "dropping_beta_lambda_extinction_weighting_and_using_solar_irradiance_only_for_fu96_lineage_coalbedo_band_averages",
            "treating_live_official_download_endpoint_or_secondary_extracted_distribution_footprint_as_recovered_original_tarball_bytes_or_hash",
            "treating_2020_github_mirror_import_timestamp_as_the_2004_aer_source_date",
        ],
        "production_guards": {"tau_ice_production_allowed": False, "production_ice_optics_ready": False, "physics_promotion_allowed": False},
        "scope_note": (
            "Step 3Q.17 corrects the Fu96-lineage broadband-weighting equation transcription used by Step3Q diagnostics: linear/log single-scattering coalbedo means retain beta_lambda extinction weighting together with TOA solar irradiance and spectral interval, while asymmetry factor is weighted by omega_lambda*beta_lambda scattering. This is a provenance-contract correction only; it does not alter frozen Formation/Viewing/Twilight Glow science. "
            "Step 3Q.16 remains valid: the public AER-RC rrtmgp-band-generation repository is an imported historical AER RRTM_BAND_GEN SVN work tree whose qualified scope is molecular/k-distribution/continuum/minor-gas/Planck band generation, not the Fu96 ice-cloud pre-averaging generator. "
            "The 2014-04-02 AER commit explicitly describes the added files as initial band-generation codes from Karen and original RRTM work with no modifications yet. The pinned script.gen_2band and kdis_2sort sources operate on LBLRTM optical depths to generate molecular absorption k-distributions, continuum/minor-gas coefficients, g-band data and Planck-related products. "
            "This release also corrects the diagnostic Fu96-lineage broadband equations: single-scattering coalbedo linear/log means retain extinction coefficient beta_lambda weighting together with TOA solar irradiance, and asymmetry factor is scattering-weighted. This corrects provenance transcription only and does not recover the exact archived RRTM band-24/25 realization. A historical AER molecular/k-distribution/Planck band-generation pipeline is recovered, but no provenance-linked Q. Fu high-resolution ice-cloud spectral sample set or Fu96 cloud-optics band-averaging generator is present in the qualified initial file set. Therefore AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_RECOVERED may be true while FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED remains false. "
            "Step 3Q.15 official AER 2004-to-2007 Fu96 final-table continuity, Step 3Q.14 pre-2020 cross-repository raw-blob replication, Step 3Q.13 scientific-source semantic equivalence, and Step 3Q.12 archive-endpoint/footprint qualifications remain valid. Original AER v2.5 tarball bytes/hash, exact historical Fu96 solar/discrete weighting, pre-averaging spectral samples, and deterministic Band 24/25 reproduction remain unrecovered. Production Ice Optics and Step 3R remain fail-closed."
        )
    }


def serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
