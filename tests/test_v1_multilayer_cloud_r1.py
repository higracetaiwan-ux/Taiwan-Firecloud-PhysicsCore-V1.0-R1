from firecloud.cloud_scene import ProviderCloudGeometryConfig, segment_native_levels


def _p(z, q):
    return {'altitude_agl_km':z,'cloud_fraction':1.0 if q else 0.0,
            'cloud_liquid_water_kgkg':q,'cloud_ice_water_kgkg':0.0}


def test_native_clear_gap_splits_layers():
    levels=[_p(1.0,2e-4), _p(2.0,2e-4), _p(3.0,0.0), _p(4.0,2e-4), _p(5.0,2e-4)]
    layers=segment_native_levels(levels,direction_offset_deg=0,distance_km=20)
    assert len(layers)==2
    assert (layers[0].z_base_km,layers[0].z_top_km)==(1.0,2.0)
    assert (layers[1].z_base_km,layers[1].z_top_km)==(4.0,5.0)


def test_unknown_does_not_bridge_native_layers():
    levels=[_p(1.0,2e-4), {'altitude_agl_km':2.0}, _p(3.0,2e-4)]
    layers=segment_native_levels(levels,direction_offset_deg=0,distance_km=20)
    assert len(layers)==2
