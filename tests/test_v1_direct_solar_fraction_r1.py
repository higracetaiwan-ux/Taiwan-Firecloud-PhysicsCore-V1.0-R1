from firecloud.geometry import circular_disk_visible_fraction, direct_solar_fraction_g0


def test_finite_disk_half_visible_at_limb():
    assert abs(circular_disk_visible_fraction(0.0)-0.5) < 1e-12


def test_direct_solar_fraction_is_bounded():
    for d in (0,100,300,440):
        for z in (0,2,5,12):
            for a in (0,-1,-4,-6):
                f=direct_solar_fraction_g0(d,z,a)
                assert 0.0 <= f <= 1.0


def test_ground_at_geometric_horizon_sees_half_disk_in_g0():
    assert abs(direct_solar_fraction_g0(0,0,0)-0.5) < 1e-12
