from firecloud.model import _audit_dataframe_dedup

def test_nested_audit_cells_can_be_deduplicated():
    rows=[{"tile_index":1,"bbox_nwse":[25.0,120.0,24.0,117.0],"meta":{"roles":["O3","AER"]}},
          {"tile_index":1,"bbox_nwse":[25.0,120.0,24.0,117.0],"meta":{"roles":["O3","AER"]}}]
    df=_audit_dataframe_dedup(rows)
    assert len(df)==1
    assert isinstance(df.loc[0,"bbox_nwse"],str)
    assert isinstance(df.loc[0,"meta"],str)
