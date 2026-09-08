from __future__ import annotations
"""R5.7.23 libRadtran/MYSTIC adapter for genuine liquid-cloud calibration.

This adapter is deliberately cloud-only.  Gas absorption, Rayleigh scattering,
aerosol extinction, Earth shadow and the Sun->CloudBase path remain in the
PhysicsCore incident-irradiance chain and must not be counted again here.
"""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .contracts import SIX_BAND_WAVELENGTHS_NM

MYSTIC_ADAPTER_CONTRACT = "R5.7.23_LIBRADTRAN_MYSTIC_ADAPTER_V1"
INCIDENT_IRRADIANCE_REFERENCE = "UNIT_EXTRATERRESTRIAL_COLLIMATED_BEAM_NORMAL_IRRADIANCE"
ATMOSPHERIC_COUPLING = "CLOUD_ONLY_NO_GAS_NO_RAYLEIGH_NO_AEROSOL_NO_EARTH_SHADOW"
SURFACE_BOUNDARY = "BLACK_SURFACE_ALBEDO_0"
CALIBRATION_SCOPE = "LIQUID_CLOUD_FULL_DIRECTIONAL_SIX_BAND"


@dataclass(frozen=True)
class MysticGeometry:
    sza_deg: float
    phi0_deg: float
    umu: float
    phi_deg: float


def geometry_to_uvspec(solar_zenith_deg: float, view_zenith_deg: float, relative_azimuth_deg: float) -> MysticGeometry:
    """Map target-local propagation geometry to uvspec/MYSTIC sensor geometry.

    PhysicsCore theta_v is the propagation direction Cloud->Observer measured
    from local upward zenith.  uvspec ``umu`` is the cosine of the detector
    look direction, hence the sign reversal: umu=-cos(theta_v).
    """
    t0 = float(solar_zenith_deg)
    tv = float(view_zenith_deg)
    daz = float(relative_azimuth_deg)
    if not (0.0 <= t0 <= 180.0 and 0.0 <= tv <= 180.0 and 0.0 <= daz <= 180.0):
        raise ValueError("MYSTIC_GEOMETRY_OUT_OF_RANGE")
    return MysticGeometry(t0, 0.0, float(-math.cos(math.radians(tv))), daz)


def unit_solar_spectrum_text(wavelengths_nm: Iterable[int] = SIX_BAND_WAVELENGTHS_NM) -> str:
    """Return a unit extraterrestrial spectrum used only for normalization.

    A constant value of one makes the returned cloud radiance numerically equal
    to the directional response factor in sr^-1 for the chosen input-unit
    convention.  It is not a physical solar spectrum and must not be used in
    production Formation RT.
    """
    rows = ["# wavelength_nm  unit_normal_irradiance"]
    for wl in sorted({int(x) for x in wavelengths_nm}):
        rows.append(f"{wl:.1f} 1.0")
    return "\n".join(rows) + "\n"


def liquid_cloud_profile_text(*, cloud_base_km: float, cloud_top_km: float, effective_radius_um: float, lwc_g_m3: float = 0.2) -> str:
    """Return a minimal 1D liquid-water cloud profile for ``wc_file 1D``.

    ``wc_modify tau set`` in the rendered input controls the integrated optical
    depth; this file therefore supplies only a reproducible vertical shape and
    droplet effective radius.  Cloud thickness remains validation evidence, not
    a production LUT interpolation axis.
    """
    base = float(cloud_base_km)
    top = float(cloud_top_km)
    reff = float(effective_radius_um)
    lwc = float(lwc_g_m3)
    if not (math.isfinite(base) and math.isfinite(top) and top > base >= 0):
        raise ValueError("REFERENCE_CLOUD_VERTICAL_GEOMETRY_INVALID")
    if not (math.isfinite(reff) and reff > 0 and math.isfinite(lwc) and lwc > 0):
        raise ValueError("REFERENCE_CLOUD_MICROPHYSICS_INVALID")
    # libRadtran 1D water-cloud files are altitude / LWC / r_eff level tables.
    # A zero-LWC top boundary prevents cloud material above the requested top.
    return (
        "# altitude_km  LWC_g_m-3  reff_um\n"
        f"{top:.6f} 0.000000 {reff:.6f}\n"
        f"{base:.6f} {lwc:.6f} {reff:.6f}\n"
    )


def render_uvspec_input(
    job: dict[str, Any],
    *,
    data_files_path: str,
    atmosphere_file: str,
    solar_spectrum_file: str,
    cloud_profile_file: str,
    sensor_altitude_km: float,
) -> str:
    """Render one genuine MYSTIC calibration job.

    The atmosphere file is still required by uvspec for geometry/pressure-grid
    bookkeeping, but molecular absorption and Rayleigh are explicitly disabled.
    """
    geom = geometry_to_uvspec(job["solar_zenith_deg"], job["view_zenith_deg"], job["relative_azimuth_deg"])
    wl = int(job["wavelength_nm"])
    if wl not in {int(x) for x in SIX_BAND_WAVELENGTHS_NM}:
        raise ValueError("MYSTIC_WAVELENGTH_OUTSIDE_FROZEN_SIX_BANDS")
    cot = float(job["cot"])
    photons = int(job.get("mc_photons", job.get("photon_count", 0)))
    if cot < 0 or photons <= 0:
        raise ValueError("MYSTIC_JOB_PHYSICS_INVALID")
    return f"""# Taiwan Firecloud PhysicsCore R5.7.23 genuine calibration job
# adapter_contract: {MYSTIC_ADAPTER_CONTRACT}
# incident_irradiance_reference: {INCIDENT_IRRADIANCE_REFERENCE}
# atmospheric_coupling: {ATMOSPHERIC_COUPLING}

data_files_path {data_files_path}
atmosphere_file {atmosphere_file}
source solar {solar_spectrum_file} per_nm
wavelength {wl:.1f} {wl:.1f}

# Cloud-only calibration: do not double-count Formation-path atmosphere.
no_rayleigh
no_absorption mol
albedo 0.0

sza {geom.sza_deg:.9f}
phi0 {geom.phi0_deg:.9f}
umu {geom.umu:.12f}
phi {geom.phi_deg:.9f}

rte_solver mystic
mc_spherical 1D
mc_vroom
mc_photons {photons}
mc_escape

wc_file 1D {cloud_profile_file}
wc_properties mie interpolate
wc_modify tau set {cot:.9f}

zout {float(sensor_altitude_km):.6f}
quiet
"""


def _numeric_rows(path: str | Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        vals: list[float] = []
        ok = True
        for tok in s.replace(",", " ").split():
            try:
                vals.append(float(tok))
            except Exception:
                ok = False
                break
        if ok and vals:
            rows.append(vals)
    return rows


def parse_mc_rad_spc(path: str | Path) -> float:
    """Parse MYSTIC directional radiance from ``mc.rad.spc``.

    libRadtran output layouts can contain coordinate columns before radiance;
    for a single-pixel/single-wavelength calibration job the final numeric
    column is the radiance value.  Ambiguous or non-finite files are rejected.
    """
    rows = _numeric_rows(path)
    if not rows:
        raise ValueError("MYSTIC_MC_RAD_SPC_EMPTY")
    value = float(rows[-1][-1])
    if not math.isfinite(value) or value < 0:
        raise ValueError("MYSTIC_MC_RAD_SPC_INVALID_RADIANCE")
    return value


def parse_mc_rad_std_spc(path: str | Path) -> float:
    rows = _numeric_rows(path)
    if not rows:
        raise ValueError("MYSTIC_MC_RAD_STD_SPC_EMPTY")
    value = float(rows[-1][-1])
    if not math.isfinite(value) or value < 0:
        raise ValueError("MYSTIC_MC_RAD_STD_SPC_INVALID")
    return value


def external_result_row(
    *,
    job: dict[str, Any],
    response_factor: float,
    response_factor_std: float,
    solver_exit_code: int,
    solver_version: str,
    solver_run_id: str,
    result_contract: str,
) -> dict[str, Any]:
    response = float(response_factor)
    std = float(response_factor_std)
    photons = int(job.get("mc_photons", 0))
    if response < 0 or std < 0 or photons <= 0:
        raise ValueError("MYSTIC_EXTERNAL_RESULT_NUMERIC_INVALID")
    rel = 0.0 if response == 0 and std == 0 else (math.inf if response == 0 else std / response)
    return {
        "job_id": str(job["job_id"]),
        "response_factor": response,
        "response_factor_std": std,
        "mc_absolute_sigma": std,
        "mc_relative_sigma": float(rel),
        "photon_count": photons,
        "sample_qc_state": "UNASSESSED_EXTERNAL_RESULT",
        "solver_run_id": str(solver_run_id),
        "solver_exit_code": int(solver_exit_code),
        "solver_family": "LIBRADTRAN_UVSPEC_MYSTIC",
        "solver_version": str(solver_version),
        "result_contract": str(result_contract),
        "adapter_contract": MYSTIC_ADAPTER_CONTRACT,
    }
