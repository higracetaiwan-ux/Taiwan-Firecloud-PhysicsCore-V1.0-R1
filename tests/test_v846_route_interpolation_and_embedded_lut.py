from pathlib import Path
import hashlib, json
import pandas as pd
import numpy as np


def test_embedded_runtime_lut_matches_manifest():
    root=Path(__file__).resolve().parents[1]
    csvp=root/'hitran_runtime'/'firecloud_600_750nm_band_coefficients.csv'
    manp=root/'hitran_runtime'/'firecloud_600_750nm_band_coefficients.manifest.json'
    assert csvp.is_file() and manp.is_file()
    data=csvp.read_bytes(); man=json.loads(manp.read_text())
    assert hashlib.sha256(data).hexdigest()==man['sha256']
    assert len(pd.read_csv(csvp))==288==man['rows']


def test_vectorized_route_interpolation_preserves_nan_and_linear_values():
    from firecloud.providers.openmeteo import interpolate_route_at_time, HOURLY_VARS
    var=HOURLY_VARS[0]
    t0=pd.Timestamp('2026-09-04 10:00:00'); t1=pd.Timestamp('2026-09-04 11:00:00')
    rows=[]
    for pid, a,b in [('a',0.0,10.0),('b',20.0,np.nan)]:
        for t,v in [(t0,a),(t1,b)]:
            r={'time':t,'point_id':pid,'distance_km':0.0,'direction_offset_deg':0.0,'lat':0.0,'lon':0.0}
            for c in HOURLY_VARS:r[c]=np.nan
            r[var]=v; rows.append(r)
    out=interpolate_route_at_time(pd.DataFrame(rows), pd.Timestamp('2026-09-04 10:30:00').to_pydatetime()).set_index('point_id')
    assert abs(float(out.loc['a',var])-5.0)<1e-9
    assert pd.isna(out.loc['b',var])
