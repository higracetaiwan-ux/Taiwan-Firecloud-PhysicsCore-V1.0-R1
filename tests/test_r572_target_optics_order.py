from pathlib import Path


def test_target_optical_evidence_is_aggregated_before_viewing_spectral_use():
    src = (Path(__file__).resolve().parents[1] / 'firecloud' / 'model.py').read_text()
    assign = src.index('v1_target_canvas_optical_evidence = pd.concat')
    use = src.index('v1_viewing_spectral_extinction = build_viewing_spectral_extinction')
    assert assign < use
