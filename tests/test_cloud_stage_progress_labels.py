from pathlib import Path

def test_3d_cloud_stage_has_granular_progress_labels():
    text = (Path(__file__).parents[1] / 'firecloud' / 'model.py').read_text(encoding='utf-8')
    for label in [
        '建立粗層雲體照明格點',
        '重建 0.5 km 垂直雲柱',
        '建立氣壓層 3D 雲體',
        '建立 GFS 原生雲微物理體積',
    ]:
        assert label in text
