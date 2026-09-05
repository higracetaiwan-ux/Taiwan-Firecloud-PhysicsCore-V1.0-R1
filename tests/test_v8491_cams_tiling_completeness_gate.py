import pandas as pd
from firecloud.providers.cams_native import split_cams_route_tiles, _merge_tile_frames


def test_long_dynamic_route_is_tiled_without_dropping_or_duplicating_points():
    pts=[]
    for d in range(0,1041,20):
        for off in (-5.0,0.0,5.0):
            pts.append({'point_id':f'{off}:{d}','distance_km':float(d),'direction_offset_deg':off,'lat':24.0,'lon':120.0-d/100.0})
    tiles=split_cams_route_tiles(pts, max_distance_span_km=320)
    assert len(tiles) >= 4
    ids=[p['point_id'] for tile in tiles for p in tile]
    assert len(ids)==len(set(ids))==len(pts)
    assert max(max(p['distance_km'] for p in tile)-min(p['distance_km'] for p in tile) for tile in tiles) <= 320.0001


def test_tile_frame_merge_preserves_unique_point_ids():
    a=pd.DataFrame({'point_id':['a','b'],'distance_km':[0,20],'direction_offset_deg':[0,0],'x':[1,2]})
    b=pd.DataFrame({'point_id':['c'],'distance_km':[340],'direction_offset_deg':[0],'x':[3]})
    out=_merge_tile_frames([a,b])
    assert list(out['point_id'])==['a','b','c']
