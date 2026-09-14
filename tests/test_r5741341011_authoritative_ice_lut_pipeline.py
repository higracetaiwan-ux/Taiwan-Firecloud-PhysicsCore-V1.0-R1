from pathlib import Path
import json

import pandas as pd

import firecloud
import firecloud.ice_optics_authoritative as auth


def _write_isca(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 2 wavelengths x 2 particle sizes. Values are synthetic software-fixture
    # data only; tests verify the source gate and unit-preserving pipeline.
    rows = [
        [0.50, 10.0, 100.0, 10.0, 2.0, 0.99, 0.70],
        [0.80, 10.0, 100.0, 10.0, 2.2, 0.995, 0.74],
        [0.50, 20.0, 800.0, 40.0, 2.0, 0.99, 0.72],
        [0.80, 20.0, 800.0, 40.0, 2.2, 0.995, 0.76],
    ]
    pd.DataFrame(rows).to_csv(path, sep=' ', header=False, index=False)


def test_version():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.11'


def test_authoritative_source_manifest_is_explicit_and_non_promoting():
    m = auth.authoritative_source_manifest()
    assert m['zenodo_record'] == '5348402'
    assert m['shortwave_archive']['md5'] == '2fb9bbab2c2c735a869c863a680e2f70'
    assert m['firecloud_target_wavelengths_nm'] == [550,575,600,650,700,750]
    assert len(m['habits']) == 9
    assert m['roughness_states'] == ['Rough000','Rough003','Rough050']
    assert m['physics_promotion_allowed'] is False


def test_missing_source_fails_closed_and_does_not_emit_lut(tmp_path):
    result = auth.build_authoritative_six_band_lut(tmp_path)
    assert result.ready is False
    assert result.qa_summary['overall_status'] == 'FAIL'
    assert result.qa_summary['source_file_fail_count'] == 27
    out = tmp_path / 'out'
    paths = auth.write_authoritative_build_outputs(result, out)
    assert 'ice_optics_lut_v1.csv' not in paths
    assert (out / 'ice_optics_authoritative_build_qa_v1.json').exists()


def test_small_complete_fixture_passes_when_contract_counts_are_monkeypatched(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'HABITS', ('8_columns',))
    monkeypatch.setattr(auth, 'ROUGHNESS_STATES', ('Rough050',))
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_WAVELENGTH_COUNT', 2)
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_SIZE_COUNT', 2)
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_ISCA_ROWS', 4)
    monkeypatch.setattr(auth, 'SOURCE_SHORTWAVE_RANGE_UM', (0.50, 0.80))
    monkeypatch.setattr(auth, 'SOURCE_PARTICLE_SIZE_RANGE_UM', (10.0, 20.0))

    source = tmp_path / 'Data_0.2_15.25' / '8_columns' / 'Rough050' / 'isca.dat'
    _write_isca(source)
    result = auth.build_authoritative_six_band_lut(tmp_path, source_archive_md5_verified=True)
    assert result.ready is True, result.qa_summary
    assert len(result.lut) == 12  # 1 habit * 1 roughness * 2 sizes * six bands
    assert set(result.lut['wavelength_nm'].astype(int)) == {550,575,600,650,700,750}
    assert (result.lut['mass_extinction_coefficient_m2_kg'] > 0).all()
    assert result.qa_summary['lut_qa']['ambiguous_effective_radius_rows'] == 0

    outputs = auth.write_authoritative_build_outputs(result, tmp_path / 'built')
    assert 'ice_optics_lut_v1.csv' in outputs
    manifest = json.loads((tmp_path / 'built' / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['release_ready'] is True
    assert 'ice_optics_lut_v1.csv' in manifest['files']


def test_spectral_grid_audit_never_extrapolates():
    raw = pd.DataFrame({
        'wavelength_um':[0.6,0.7],
        'maximum_dimension_um':[10,10],
        'volume_um3':[100,100],
        'projected_area_um2':[10,10],
        'extinction_efficiency':[2.0,2.1],
        'single_scattering_albedo':[0.99,0.99],
        'asymmetry_parameter':[0.7,0.7],
    })
    audit = auth.spectral_grid_audit(raw, ice_habit='8_columns', surface_roughness='Rough050')
    st = audit.set_index('target_wavelength_nm')['status'].to_dict()
    assert st[550] == 'FAIL'
    assert st[575] == 'FAIL'
    assert st[600] == 'PASS'
    assert st[650] == 'PASS'
    assert st[700] == 'PASS'
    assert st[750] == 'FAIL'
