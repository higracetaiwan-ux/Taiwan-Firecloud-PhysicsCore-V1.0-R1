import json
from pathlib import Path
from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck import (
    fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload,
    serialize_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_json_bytes,
)

def test_step3o_contract_bytes_are_canonical_across_insertion_order():
    payload = fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.30.15"
    )
    reordered = dict(reversed(list(payload.items())))
    a = serialize_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_json_bytes(payload)
    b = serialize_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_json_bytes(reordered)
    assert a == b
    assert a == json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")


def test_step3o_case_export_uses_canonical_contract_serializer():
    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "serialize_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_json_bytes(_obj)" in app
