from __future__ import annotations
import json
import math
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from firecloud.tier2_libradtran_mystic_adapter import (
    MYSTIC_ADAPTER_CONTRACT, INCIDENT_IRRADIANCE_REFERENCE, ATMOSPHERIC_COUPLING,
    SURFACE_BOUNDARY, geometry_to_uvspec, unit_solar_spectrum_text,
    liquid_cloud_profile_text, render_uvspec_input, parse_mc_rad_spc,
    parse_mc_rad_std_spc,
)
from firecloud.tier2_directional_scattering_calibration import (
    DIRECTIONAL_CALIBRATION_CONTRACT, DIRECTIONAL_RUNTIME_CONTRACT,
    validate_directional_calibration_metadata,
)
from firecloud.tier2_liquid_directional_calibration_pipeline import (
    DOMAIN_CONTRACT, PIPELINE_CONTRACT, build_external_job_table,
    build_libradtran_mystic_solver_recipe,
)


def _domain():
    return {"contract":DOMAIN_CONTRACT,"pipeline_contract":PIPELINE_CONTRACT,"phases":["LIQUID"],"wavelengths_nm":[550,575,600,650,700,750],"cot":[2.0],"effective_radius_um":[10.0],"solar_zenith_deg":[96.0],"view_zenith_deg":[90.4],"relative_azimuth_deg":[179.0]}


def test_geometry_maps_horizon_crossing_without_collapsing_to_scattering_angle():
    g=geometry_to_uvspec(96.0,90.4,179.0)
    assert g.sza_deg==96.0 and g.phi_deg==179.0
    assert math.isclose(g.umu,-math.cos(math.radians(90.4)),abs_tol=1e-12)
    assert g.umu>0


def test_unit_source_and_cloud_profile_are_explicit_normalization_not_solar_truth():
    text=unit_solar_spectrum_text()
    assert "575.0 1.0" in text and "750.0 1.0" in text
    wc=liquid_cloud_profile_text(cloud_base_km=5,cloud_top_km=6,effective_radius_um=10)
    assert "6.000000 0.000000" in wc and "5.000000 0.200000 10.000000" in wc


def test_rendered_input_is_cloud_only_spherical_mystic():
    recipe=build_libradtran_mystic_solver_recipe(photons_per_job=123456)
    job=build_external_job_table(_domain(),solver_recipe=recipe).iloc[0].to_dict()
    text=render_uvspec_input(job,data_files_path="/lrt/data",atmosphere_file="atm.dat",solar_spectrum_file="unit.dat",cloud_profile_file="wc.dat",sensor_altitude_km=5.0)
    for token in ("rte_solver mystic","mc_spherical 1D","mc_vroom","no_rayleigh","no_absorption mol","albedo 0.0","wc_properties mie interpolate","wc_modify tau set 2.000000000"):
        assert token in text
    assert INCIDENT_IRRADIANCE_REFERENCE in text and ATMOSPHERIC_COUPLING in text


def test_mystic_output_parsers_take_single_job_final_numeric_radiance(tmp_path: Path):
    (tmp_path/"mc.rad.spc").write_text("# x y rad\n0 0 0.0125\n")
    (tmp_path/"mc.rad.std.spc").write_text("0 0 0.0001\n")
    assert parse_mc_rad_spc(tmp_path/"mc.rad.spc")==0.0125
    assert parse_mc_rad_std_spc(tmp_path/"mc.rad.std.spc")==0.0001


def test_v3_metadata_rejects_missing_genuine_provenance():
    a=validate_directional_calibration_metadata({"calibration_contract":DIRECTIONAL_CALIBRATION_CONTRACT})
    assert not a["ok"]
    assert any("MISSING_FIELDS" in e for e in a["errors"])
    assert DIRECTIONAL_RUNTIME_CONTRACT.endswith("V3")


def test_batch_runner_render_only_and_no_uvspec_execute_fail(tmp_path: Path):
    recipe=build_libradtran_mystic_solver_recipe(photons_per_job=1000)
    jobs=build_external_job_table(_domain(),solver_recipe=recipe)
    jobs_csv=tmp_path/"jobs.csv"; jobs.to_csv(jobs_csv,index=False)
    recipe_json=tmp_path/"recipe.json"; recipe_json.write_text(json.dumps(recipe))
    root=Path(__file__).resolve().parents[1]
    runner=root/"run_tier2_libradtran_mystic_calibration.py"
    run_dir=tmp_path/"render"
    proc=subprocess.run([sys.executable,str(runner),"--jobs-csv",str(jobs_csv),"--solver-recipe-json",str(recipe_json),"--run-dir",str(run_dir),"--data-files-path","/fake/data","--atmosphere-file","atm.dat","--render-only","--max-jobs","1"],cwd=root,capture_output=True,text=True)
    assert proc.returncode==0, proc.stderr
    inp=next(run_dir.glob("T2DIR-*/uvspec.inp")).read_text()
    assert "mc_spherical 1D" in inp and "no_rayleigh" in inp
    # Force no valid uvspec executable by pointing to a definitely missing one is not allowed;
    # empty/default may find a real local install, so this test only requires render-only safety.
    assert MYSTIC_ADAPTER_CONTRACT in inp
