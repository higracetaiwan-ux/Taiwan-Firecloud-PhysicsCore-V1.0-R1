from pathlib import Path


def test_no_candidate_does_not_stop_ui():
    app = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    anchor = 'if selected is None:'
    i = app.index(anchor)
    window = app[i:i+2200]
    assert 'st.stop()' not in window
    assert 'diagnostic_angle' in window
    assert '正式選定核心角度' in window
    assert '以下仍完整顯示所有診斷' in window


def test_cross_section_uses_diagnostic_detail_angle():
    app = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'detail_angle = matrix_angle' in app
    assert 'cross_section_figure(detail["snapshot"], direction, detail_angle, detail["voxels"])' in app
