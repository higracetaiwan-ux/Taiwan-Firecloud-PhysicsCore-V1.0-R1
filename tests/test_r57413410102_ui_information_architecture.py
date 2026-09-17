from pathlib import Path

import firecloud


def test_release_version_matches_current_release():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.21"


def test_main_ui_exposes_current_state_without_wall_of_history():
    src = Path("app.py").read_text(encoding="utf-8")
    assert 'SCIENCE_BASELINE_FROZEN = "R5.7.41.2_SHADOW_COT_AB_FROZEN"' in src
    assert 'CURRENT_MILESTONE = "Ice Optics Phase 2 Step 3H — Wyser→Yang/Bi Dmax Coordinate Qualification + Shape Compatibility Gate"' in src
    assert 'with st.expander("本版更新與版本歷史", expanded=False)' in src
    assert 'with st.expander("現行 Science Baseline（Frozen）", expanded=False)' in src
    assert 'with st.expander("歷史科學改版", expanded=False)' in src
    assert 'with st.expander("Runtime / Provider / Hotfix 歷史", expanded=False)' in src


def test_three_physics_tracks_and_windy_decoupling_are_visible():
    src = Path("app.py").read_text(encoding="utf-8")
    assert "Formation｜火燒雲形成" in src
    assert "Viewing｜觀測者是否看得到" in src
    assert "Twilight Glow｜晨昏霞光" in src
    assert "FIRECLOUD_ICE_OPTICS_PORTABLE_V1" in src
    assert "不依賴 PhysicsCore、Python 或 Streamlit runtime" in src


def test_source_and_missing_semantics_are_structured():
    src = Path("app.py").read_text(encoding="utf-8")
    assert "**預報與物理資料來源**" in src
    assert "NOAA GFS" in src
    assert "DWD ICON" in src
    assert "CAMS" in src
    assert "Missing ≠ Clear ≠ Zero" in src
