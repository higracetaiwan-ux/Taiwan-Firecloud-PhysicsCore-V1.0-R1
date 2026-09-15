import io
import json
import shutil
import subprocess
import tempfile
import zipfile

import pandas as pd
import pytest

import firecloud
from firecloud.ice_cloud_spectral_optics import ICE_OPTICS_WAVELENGTHS_NM, IceOpticsLUTStatus, validate_ice_optics_lut
from firecloud.ice_optics_portable import (
    PORTABLE_PACKAGE_CONTRACT_VERSION,
    build_portable_package_files,
    build_portable_package_zip_bytes,
    evaluate_portable_ice_optics,
    portable_contract_payload,
)


def _fake_lut():
    rows=[]
    for habit in ['8_columns']:
        for rough in ['Rough050']:
            for r,dmax in [(20.0,40.0),(40.0,80.0)]:
                for wl in ICE_OPTICS_WAVELENGTHS_NM:
                    rows.append({
                        'wavelength_nm':wl,
                        'maximum_dimension_um':dmax,
                        'effective_diameter_um':2*r,
                        'effective_radius_um':r,
                        'ice_habit':habit,
                        'surface_roughness':rough,
                        'mass_extinction_coefficient_m2_kg':100.0 + r + wl/1000.0,
                        'single_scattering_albedo':0.999 - (wl-550)*1e-6,
                        'asymmetry_parameter':0.74 + (wl-550)*1e-5,
                        'source_dataset':'TEST_CALIBRATED_LUT',
                        'source_version':'v1',
                        'source_record_provenance':'TEST_ONLY',
                    })
    return validate_ice_optics_lut(pd.DataFrame(rows))


def test_version_and_portable_contract_runtime_decoupling():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.11.2'
    c=portable_contract_payload(physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    assert c['portable_package_contract_version']==PORTABLE_PACKAGE_CONTRACT_VERSION
    assert c['runtime_dependency_on_physicscore']=='NONE'
    assert c['runtime_dependency_on_python']=='NONE'
    assert c['runtime_dependency_on_streamlit']=='NONE'
    assert c['consumer']=='WINDY_FIRECLOUD_OBSERVER'
    assert c['wavelengths_nm']==list(ICE_OPTICS_WAVELENGTHS_NM)
    assert c['primary_size_coordinate']=='maximum_dimension_um'
    assert c['interpolation']['maximum_dimension']=='LINEAR_WITHIN_SAME_HABIT_AND_ROUGHNESS_ONLY'
    assert c['interpolation']['effective_radius']=='DIAGNOSTIC_ONLY_NOT_RUNTIME_LOOKUP_AXIS'



def test_portable_evaluator_is_dmax_first_even_when_reff_varies_by_wavelength():
    lut=_fake_lut().copy()
    # Make source-derived r_eff wavelength-dependent while Dmax remains stable.
    mask=lut['maximum_dimension_um'].eq(40.0)
    lut.loc[mask,'effective_radius_um']=lut.loc[mask,'wavelength_nm'].map({550:18.0,575:18.5,600:19.0,650:19.5,700:20.0,750:20.5})
    lut.loc[mask,'effective_diameter_um']=2*lut.loc[mask,'effective_radius_um']
    lut=validate_ice_optics_lut(lut)
    got=evaluate_portable_ice_optics(
        lut, iwp_kg_m2=0.01, native_vertical_completeness=1.0,
        maximum_dimension_um=40.0, ice_habit='8_columns', surface_roughness='Rough050'
    )
    assert got['state']=='ICE_SIX_BAND_OPTICS_READY'
    assert got['lookup_state']=='EXACT_DMAX_LUT_ROW'
    assert set(map(int,got['bands'].keys()))==set(ICE_OPTICS_WAVELENGTHS_NM)
    assert len({v['source_effective_radius_um'] for v in got['bands'].values()})>1


def test_positive_iwp_without_dmax_fails_closed_no_reff_substitution():
    got=evaluate_portable_ice_optics(
        _fake_lut(), iwp_kg_m2=0.01, native_vertical_completeness=1.0,
        maximum_dimension_um=None, ice_habit='8_columns', surface_roughness='Rough050'
    )
    assert got['state']=='ICE_MAXIMUM_DIMENSION_MISSING'
    assert got['missing_reason']=='NO_NATIVE_OR_CALIBRATED_ICE_DMAX'

def test_portable_package_contains_lut_evaluator_contract_and_vectors():
    lut=_fake_lut()
    status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    files=build_portable_package_files(lut, physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN', lut_status=status, source_manifest={'source':'TEST'})
    required={
        'manifest.json','contract.json','ice_optics_lut_v1.csv','ice_optics_lut_v1.json',
        'windy/iceOpticsEvaluator.mjs','windy/iceOpticsEvaluator.ts',
        'validation/reference_vectors.json','validation/validatePackage.mjs','README_WINDY.md','source/source_manifest.json',
    }
    assert required.issubset(files)
    manifest=json.loads(files['manifest.json'])
    assert manifest['runtime_dependency_on_physicscore']=='NONE'
    assert manifest['runtime_dependency_on_python']=='NONE'
    assert manifest['runtime_dependency_on_streamlit']=='NONE'
    assert manifest['lut_status']['state']=='ICE_OPTICS_LUT_READY'
    for name,meta in manifest['files'].items():
        assert name in files
        import hashlib
        assert hashlib.sha256(files[name]).hexdigest()==meta['sha256']
        assert len(files[name])==meta['byte_size']


def test_portable_package_refuses_empty_lut():
    cols=['wavelength_nm','maximum_dimension_um','effective_diameter_um','effective_radius_um','ice_habit','surface_roughness','mass_extinction_coefficient_m2_kg','single_scattering_albedo','asymmetry_parameter','source_dataset','source_version','source_record_provenance']
    with pytest.raises(ValueError, match='non-empty'):
        build_portable_package_files(pd.DataFrame(columns=cols), physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')


def test_portable_zip_is_self_contained_and_has_no_physicscore_runtime_files():
    payload=build_portable_package_zip_bytes(_fake_lut(), physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names=set(zf.namelist())
        assert 'windy/iceOpticsEvaluator.mjs' in names
        assert 'ice_optics_lut_v1.json' in names
        assert not any(n.endswith('.py') for n in names)
        contract=json.loads(zf.read('contract.json'))
        assert contract['runtime_dependency_on_physicscore']=='NONE'


def test_node_reference_evaluator_passes_generated_validation_vectors():
    if shutil.which('node') is None:
        pytest.skip('node not installed')
    payload=build_portable_package_zip_bytes(_fake_lut(), physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            zf.extractall(td)
        proc=subprocess.run(['node','validation/validatePackage.mjs'],cwd=td,capture_output=True,text=True,timeout=20)
        assert proc.returncode==0, proc.stderr
        assert proc.stdout.startswith('PASS ')


def test_integrity_requires_portable_runtime_decoupling_contract():
    from firecloud.case_integrity import build_analysis_integrity_audit
    audit=build_analysis_integrity_audit({
        'ice_cloud_spectral_optics_phase1_required':True,
        'ice_cloud_spectral_optics_contract':{
            'contract_version':'FIRECLOUD_ICE_OPTICS_V1',
            'wavelengths_nm':list(ICE_OPTICS_WAVELENGTHS_NM),
            'tau_definition':'tau_ice_lambda = IWP_kg_m2 * k_ext_ice_lambda_m2_kg',
        },
        'ice_optics_portable_consumer_contract':portable_contract_payload(physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN'),
        'windy_firecloud_ice_optics_summary_v1':{
            'ice_optics_contract_version':'FIRECLOUD_ICE_OPTICS_V1',
            'wavelengths_nm':list(ICE_OPTICS_WAVELENGTHS_NM),
            'physics_promotion_allowed':False,
            'records':[],
        },
    })
    checks=audit.set_index('check_id')['status'].to_dict()
    assert checks['ICE_OPTICS_PORTABLE_WINDY_RUNTIME_DECOUPLING']=='PASS'

def test_typescript_reference_evaluator_compiles_standalone():
    if shutil.which('tsc') is None:
        pytest.skip('tsc not installed')
    files=build_portable_package_files(_fake_lut(), physicscore_version=firecloud.__version__, science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    with tempfile.TemporaryDirectory() as td:
        from pathlib import Path
        src=Path(td)/'iceOpticsEvaluator.ts'
        src.write_bytes(files['windy/iceOpticsEvaluator.ts'])
        proc=subprocess.run(['tsc','--strict','--target','ES2020','--module','ES2020','--noEmit',str(src)],capture_output=True,text=True,timeout=20)
        assert proc.returncode==0, proc.stdout+proc.stderr
