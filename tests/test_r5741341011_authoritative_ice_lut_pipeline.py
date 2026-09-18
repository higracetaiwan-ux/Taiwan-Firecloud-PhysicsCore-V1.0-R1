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


def _write_wavelength_dependent_geometry_isca(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Mimics the contract feature observed in authoritative HBR/SBR rows:
    # same Dmax, same projected area, but source-row volume can vary by wavelength.
    rows = [
        [0.50, 10.0, 200.0, 20.0, 2.0, 0.99, 0.70],
        [0.80, 10.0, 100.0, 20.0, 2.2, 0.995, 0.74],
        [0.50, 20.0, 1600.0, 80.0, 2.0, 0.99, 0.72],
        [0.80, 20.0, 800.0, 80.0, 2.2, 0.995, 0.76],
    ]
    pd.DataFrame(rows).to_csv(path, sep=' ', header=False, index=False)


def _patch_small_contract(monkeypatch, habits=('8_columns',), roughness=('Rough050',)):
    monkeypatch.setattr(auth, 'HABITS', tuple(habits))
    monkeypatch.setattr(auth, 'ROUGHNESS_STATES', tuple(roughness))
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_WAVELENGTH_COUNT', 2)
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_SIZE_COUNT', 2)
    monkeypatch.setattr(auth, 'SOURCE_EXPECTED_ISCA_ROWS', 4)
    monkeypatch.setattr(auth, 'SOURCE_SHORTWAVE_RANGE_UM', (0.50, 0.80))
    monkeypatch.setattr(auth, 'SOURCE_PARTICLE_SIZE_RANGE_UM', (10.0, 20.0))


def test_version():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.30.4.1'


def test_authoritative_source_manifest_is_explicit_dmax_first_and_non_promoting():
    m = auth.authoritative_source_manifest()
    assert m['zenodo_record'] == '5348402'
    assert m['shortwave_archive']['md5'] == '2fb9bbab2c2c735a869c863a680e2f70'
    assert m['firecloud_target_wavelengths_nm'] == [550,575,600,650,700,750]
    assert len(m['habits']) == 9
    assert m['roughness_states'] == ['Rough000','Rough003','Rough050']
    assert m['habit_source_directory_aliases']['HC'][0] == 'hollow_column'
    assert m['authoritative_primary_size_coordinate'] == 'maximum_dimension_um'
    assert 'NOT_AUTHORITATIVE_CROSS_BAND_KEY' in m['effective_radius_semantics']
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


def test_hollow_column_source_directory_alias_resolves_to_canonical_hc(tmp_path):
    p = tmp_path / 'Data_0.2_15.25' / 'hollow_column' / 'Rough000' / 'isca.dat'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('dummy', encoding='utf-8')
    got = auth.resolve_isca_path(tmp_path, 'HC', 'Rough000')
    assert got == p


def test_small_complete_fixture_passes_when_contract_counts_are_monkeypatched(tmp_path, monkeypatch):
    _patch_small_contract(monkeypatch)
    source = tmp_path / 'Data_0.2_15.25' / '8_columns' / 'Rough050' / 'isca.dat'
    _write_isca(source)
    result = auth.build_authoritative_six_band_lut(tmp_path, source_archive_md5_verified=True)
    assert result.ready is True, result.qa_summary
    assert len(result.lut) == 12  # 1 habit * 1 roughness * 2 sizes * six bands
    assert set(result.lut['wavelength_nm'].astype(int)) == {550,575,600,650,700,750}
    assert (result.lut['mass_extinction_coefficient_m2_kg'] > 0).all()
    assert result.qa_summary['lut_qa']['primary_size_coordinate'] == 'maximum_dimension_um'
    assert result.qa_summary['lut_qa']['effective_radius_runtime_key'] is False

    outputs = auth.write_authoritative_build_outputs(result, tmp_path / 'built')
    assert 'ice_optics_lut_v1.csv' in outputs
    manifest = json.loads((tmp_path / 'built' / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['release_ready'] is True
    assert 'ice_optics_lut_v1.csv' in manifest['files']


def test_wavelength_dependent_source_geometry_is_accepted_and_preserved_dmax_first(tmp_path, monkeypatch):
    _patch_small_contract(monkeypatch, habits=('HBR',), roughness=('Rough000',))
    source = tmp_path / 'Data_0.2_15.25' / 'HBR' / 'Rough000' / 'isca.dat'
    _write_wavelength_dependent_geometry_isca(source)

    result = auth.build_authoritative_six_band_lut(tmp_path, source_archive_md5_verified=True)
    assert result.ready is True, result.qa_summary
    inv = result.source_inventory.iloc[0]
    assert inv['status'] == 'PASS'
    assert bool(inv['geometry_consistent']) is False
    assert inv['max_volume_relative_spread_across_wavelength'] > 0
    assert 'WAVELENGTH_DEPENDENT_ACCEPTED' in inv['detail']
    assert result.qa_summary['lut_qa']['wavelength_dependent_effective_radius_group_count'] > 0

    d10 = result.lut[result.lut['maximum_dimension_um'].eq(10.0)].sort_values('wavelength_nm')
    assert d10['effective_radius_um'].nunique() > 1
    # Dmax remains the stable six-band grouping key even when source-derived r_eff varies.
    assert set(d10['wavelength_nm'].astype(int)) == {550,575,600,650,700,750}


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
