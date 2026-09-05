from dataclasses import fields
from firecloud.contracts import (
    CORE_FIRECLOUD_ANGLES_DEG, SIX_BAND_WAVELENGTHS_NM, PhysicsCoreResult,
)
from firecloud.config import ModelConfig


def test_v1_core_angle_contract_is_0_to_minus4_half_degree():
    expected=(0.0,-0.5,-1.0,-1.5,-2.0,-2.5,-3.0,-3.5,-4.0)
    assert CORE_FIRECLOUD_ANGLES_DEG == expected
    assert ModelConfig().firecloud_core_angles_deg == expected


def test_v1_six_band_contract():
    assert SIX_BAND_WAVELENGTHS_NM == (550,575,600,650,700,750)


def test_physicscore_result_has_no_decision_score_leakage():
    names={f.name for f in fields(PhysicsCoreResult)}
    forbidden={'physics_score','final_score','outing_score','go_no_go','operational_decision','selected_angle'}
    assert names.isdisjoint(forbidden)
