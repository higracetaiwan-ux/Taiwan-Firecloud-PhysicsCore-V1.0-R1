from pathlib import Path
import zipfile
import pandas as pd

from tools.aggregate_shadow_validation_cases import aggregate_case_archives


def test_aggregate_multiple_case_archives(tmp_path: Path):
    paths=[]
    for idx, day in enumerate(["2026-09-11","2026-09-12"], start=1):
        p=tmp_path/f"case{idx}.zip"
        frame=pd.DataFrame([{
            "shadow_validation_case_id":f"SV-{idx}","event_date":day,"event":"sunset",
            "site_id":"TWS106","target_count":10+idx,
        }])
        with zipfile.ZipFile(p,"w") as z:
            z.writestr("shadow_validation_cohort_summary.csv", frame.to_csv(index=False))
        paths.append(p)
    out=aggregate_case_archives(paths)
    assert len(out)==2
    assert out["shadow_validation_case_id"].tolist()==["SV-1","SV-2"]
    assert set(out["case_archive_filename"])=={"case1.zip","case2.zip"}
