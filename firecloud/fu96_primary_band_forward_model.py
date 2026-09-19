"""Diagnostic Fu96 primary-solar-band forward model (Step 3Q.19).

This module preserves the six solar-band coefficient sets explicitly labelled in a
legacy Fu radiation implementation as Fu (1996) Eq. 3.9a-d coefficients.  It is a
provenance/reconstruction diagnostic only.  It must not be promoted to production
RRTMG Band 24/25 optics because the historical RRTMG fine-grid interpolation and
solar-weighting realization remain unrecovered.
"""
from __future__ import annotations
from dataclasses import dataclass

SOURCE_REPOSITORY = "XHU-sysu/pyCFRAM"
SOURCE_COMMIT = "3a07581a509936829bca1743e038b0ad9a435ba9"
SOURCE_PATH = "fortran/Fu/cas_fu_radiation.f"
SOURCE_BLOB_SHA = "0711455bbcb94e959c119bcc343db215e1149ecb"
SOURCE_LEGACY_IMPORT_COMMIT = "8da06a2a348babbcdfd588098ed7b5f18cbe6029"
SOURCE_LEGACY_IMPORT_DATE_UTC = "2026-05-10T07:52:23Z"
REPLICATION_REPOSITORY = "DavidEngland/ABL"
REPLICATION_COMMIT = "6813100d1db7f16bdb2340949fd5659ae9604085"
REPLICATION_PATH = "refs/OneDModelRad/misc_subs_flcode.f"
SOLAR_COEFFICIENT_VALUE_COUNT = 90
PRODUCTION_PROMOTION_ALLOWED = False

# Transport-band labels in the recovered Fu radiation code.  The optical-property
# averaging interval provenance is kept separate: published Fu96 lineage documents
# the second primary optical interval as 0.7-1.41 um even though this transport code
# labels its second band 0.7-1.3 um.
TRANSPORT_BANDS_UM = (
    (0.2, 0.7), (0.7, 1.3), (1.3, 1.9),
    (1.9, 2.5), (2.5, 3.5), (3.5, 4.0),
)

AP = (
    (-2.9172062e-05, 2.5192544e+00, 0.0),
    (-2.2948980e-05, 2.5212550e+00, 0.0),
    (-2.9772840e-04, 2.5400320e+00, 0.0),
    ( 4.2668223e-04, 2.4933372e+00, 0.0),
    ( 4.3226531e-04, 2.4642946e+00, 0.0),
    ( 9.5918990e-05, 2.5232218e+00, 0.0),
)
BPS = (
    ( 1.3540265e-07, 9.9282217e-08,-7.3843168e-11, 3.3111862e-13),
    (-2.1458450e-06, 2.1984010e-05,-4.4225520e-09, 1.0711940e-11),
    ( 1.4027890e-04, 1.3919010e-03,-5.1005610e-06, 1.4032930e-08),
    ( 5.7801650e-03, 2.4420420e-03,-1.1985030e-05, 3.3878720e-08),
    ( 2.7122737e-01, 1.9809794e-03,-1.5071269e-05, 5.0103900e-08),
    ( 1.6215025e-01, 6.3734393e-03,-5.7740959e-05, 1.9109300e-07),
)
CP = (
    (7.4812728e-01, 9.5684492e-04,-1.1151708e-06,-8.1557303e-09),
    (7.5212480e-01, 1.1045100e-03,-2.9157100e-06,-1.3429900e-09),
    (7.5320460e-01, 1.8845180e-03,-9.7571460e-06, 2.2428270e-08),
    (7.7381780e-01, 2.2260760e-03,-1.4052790e-05, 3.7896870e-08),
    (8.7020490e-01, 1.6645530e-03,-1.4886030e-05, 4.9867270e-08),
    (7.4212060e-01, 5.2621900e-03,-5.0877550e-05, 1.7307870e-07),
)
DPS = (
    (1.1572963e-01, 2.5648064e-04, 1.9131293e-06,-1.2460341e-08),
    (1.1360752e-01, 2.4156171e-04, 2.0185942e-06,-1.2876106e-08),
    (1.1241170e-01,-1.7635186e-07, 2.1499248e-06,-1.2949304e-08),
    (1.0855775e-01,-3.2496217e-04, 3.4207304e-06,-1.6247759e-08),
    (5.7783360e-02,-4.1158260e-04, 4.2361240e-06,-1.7204950e-08),
    (1.1367129e-01,-1.9711061e-03, 1.6078010e-05,-5.1736898e-08),
)

@dataclass(frozen=True)
class Fu96PrimarySolarOptics:
    band_index: int
    dge_um: float
    mass_extinction_m2_g: float
    single_scattering_albedo: float
    asymmetry_factor: float
    forward_delta_fraction: float


def _poly4(c: tuple[float, float, float, float], x: float) -> float:
    return c[0] + c[1]*x + c[2]*x*x + c[3]*x*x*x


def evaluate_fu96_primary_solar_band(band_index: int, dge_um: float) -> Fu96PrimarySolarOptics:
    """Evaluate recovered Fu Eq. 3.9 primary-band fits; diagnostic only."""
    if not 1 <= int(band_index) <= 6:
        raise ValueError("band_index must be 1..6")
    x=float(dge_um)
    if x <= 0:
        raise ValueError("dge_um must be > 0")
    i=int(band_index)-1
    ext=AP[i][0] + AP[i][1]/x
    ssa=1.0-_poly4(BPS[i],x)
    g=_poly4(CP[i],x)
    fd=_poly4(DPS[i],x)
    return Fu96PrimarySolarOptics(int(band_index),x,ext,ssa,g,fd)


def coefficient_count() -> int:
    return sum(len(x) for x in AP)+sum(len(x) for x in BPS)+sum(len(x) for x in CP)+sum(len(x) for x in DPS)
