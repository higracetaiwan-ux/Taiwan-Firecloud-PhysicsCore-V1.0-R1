"""PhysicsCore V1.0-R4.4 six-band spectral-colour diagnostics.

This module does *not* invent blue/blue-green channels.  It integrates only the
retained 550/575/600/650/700/750 nm radiance samples against sampled CIE 1931
2-degree colour-matching functions.  The resulting XYZ/x/y values are therefore
explicitly a *truncated retained-band diagnostic*, not a complete reconstruction
of a broadband human-visible spectrum.

No photography thresholds, colour-name boundaries, or outing decisions are
encoded here.  Those remain Ground Truth calibration / Decision Layer concerns.
"""
from __future__ import annotations

import math
from typing import Mapping, Optional

from .contracts import SIX_BAND_WAVELENGTHS_NM

# Approximate CIE 1931 2-degree colour matching samples at the retained bands.
# Values are dimensionless standard-observer samples.  zbar is essentially zero
# in the deep-red tail.  We deliberately do not add wavelengths < 550 nm.
_CIE1931_2DEG = {
    550: (0.43345, 0.99495, 0.00875),
    575: (0.84250, 0.91540, 0.00180),
    600: (1.06220, 0.63100, 0.00080),
    650: (0.28350, 0.10700, 0.00000),
    700: (0.01136, 0.00410, 0.00000),
    750: (0.00033, 0.00012, 0.00000),
}

# Trapezoidal integration support weights for the irregular retained wavelength
# grid.  These are spectral-integration widths, not empirical firecloud weights.
_INTEGRATION_WIDTH_NM = {
    550: 12.5,
    575: 25.0,
    600: 37.5,
    650: 50.0,
    700: 50.0,
    750: 25.0,
}


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def reconstruct_six_band_colour(radiance: Mapping[int, Optional[float]]) -> dict:
    """Return source-faithful colour diagnostics from the six retained bands.

    The method is intentionally fail-closed: all six channels must be finite.
    Missing 550 nm is not back-filled from 575/600 nm and no blue channel is
    synthesized.  Chromaticity is undefined for zero total radiance.
    """
    vals = {int(w): radiance.get(int(w)) for w in SIX_BAND_WAVELENGTHS_NM}
    if any(not _finite(vals[w]) for w in vals):
        return {
            "spectral_colour_status": "MISSING_SIX_BAND_RADIANCE",
            "cie_X_truncated": None,
            "cie_Y_truncated": None,
            "cie_Z_truncated": None,
            "cie_x_truncated": None,
            "cie_y_truncated": None,
            "deep_red_tail_fraction_750": None,
            "warm_red_fraction_650_750": None,
            "spectral_centroid_nm": None,
            "spectral_peak_wavelength_nm_diagnostic": None,
            "colour_reconstruction_method": "CIE1931_2DEG_RETAINED_550_750NM_NO_BLUE_EXTRAPOLATION",
        }

    rr = {w: max(0.0, float(vals[w])) for w in vals}
    X = Y = Z = 0.0
    spectral_energy = 0.0
    weighted_lambda = 0.0
    for w in SIX_BAND_WAVELENGTHS_NM:
        wi = int(w)
        width = _INTEGRATION_WIDTH_NM[wi]
        xbar, ybar, zbar = _CIE1931_2DEG[wi]
        e = rr[wi] * width
        X += e * xbar
        Y += e * ybar
        Z += e * zbar
        spectral_energy += e
        weighted_lambda += e * wi

    xyz_sum = X + Y + Z
    if spectral_energy <= 0.0:
        status = "ZERO_RADIANCE"
        cx = cy = None
        centroid = None
        tail = warm = 0.0
        peak = None
    else:
        status = "READY_TRUNCATED_SIX_BAND_CIE_DIAGNOSTIC"
        cx = (X / xyz_sum) if xyz_sum > 0 else None
        cy = (Y / xyz_sum) if xyz_sum > 0 else None
        centroid = weighted_lambda / spectral_energy
        raw_sum = sum(rr.values())
        tail = rr[750] / raw_sum if raw_sum > 0 else 0.0
        warm = (rr[650] + rr[700] + rr[750]) / raw_sum if raw_sum > 0 else 0.0
        # Retained only as a diagnostic; colour classification must not use the
        # maximum channel as a substitute for spectral-shape reconstruction.
        peak = max(rr, key=rr.get) if raw_sum > 0 else None

    return {
        "spectral_colour_status": status,
        "cie_X_truncated": X,
        "cie_Y_truncated": Y,
        "cie_Z_truncated": Z,
        "cie_x_truncated": cx,
        "cie_y_truncated": cy,
        "deep_red_tail_fraction_750": tail,
        "warm_red_fraction_650_750": warm,
        "spectral_centroid_nm": centroid,
        "spectral_peak_wavelength_nm_diagnostic": peak,
        "colour_reconstruction_method": "CIE1931_2DEG_RETAINED_550_750NM_NO_BLUE_EXTRAPOLATION",
    }
