from __future__ import annotations

from pathlib import Path

from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
    serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes,
)


def main() -> int:
    root=Path(__file__).resolve().parents[1]
    out=root/'release_artifacts'
    out.mkdir(parents=True,exist_ok=True)
    evidence=build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate=build_fu96_rrtmg_band_weighting_provenance_gate(evidence)
    contract=fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=evidence,gate=gate)
    (out/'ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence.csv').write_bytes(
        evidence.to_csv(index=False,lineterminator='\n').encode('utf-8')
    )
    (out/'ice_microphysics_fu96_rrtmg_band_weighting_provenance_gate.csv').write_bytes(
        gate.to_csv(index=False,lineterminator='\n').encode('utf-8')
    )
    (out/'ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract.json').write_bytes(
        serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(contract)
    )
    print(f'evidence rows={len(evidence)}')
    print(f'gate rows={len(gate)}')
    print(f'contract={contract["contract_version"]}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
