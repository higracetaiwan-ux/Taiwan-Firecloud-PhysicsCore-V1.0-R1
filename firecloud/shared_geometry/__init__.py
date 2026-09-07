"""Firecloud Shared Geometry Core V1.5 Phase-1 completion.

Single-source geometry primitives shared by Formation, Viewing, cloud blocking,
precipitation and spectral RT.  This package contains geometry only; it must not
manufacture optical evidence or collapse Formation and Viewing.
"""
from .earth import (arc_angle_rad, earth_shadow_min_altitude_km, cloud_layer_illuminated_fraction,
                    destination_point, dynamic_rez_entry_distance_km, geometric_illumination_state)
from .ray import (ray_altitude_km_at_surface_distance, ray_altitudes_vectorized_km,
                  observer_los_height_agl_km, observer_los_heights_vectorized_agl_km, sampled_segment_path_km, sample_sun_ray_segment, sample_observer_los_segment)
from .solar import (SOLAR_ANGULAR_DIAMETER_DEG, local_solar_center_clearance_above_earth_limb_deg,
                    circular_disk_visible_fraction, direct_solar_fraction_g0,
                    solar_disk_transition_altitude_km, finite_solar_disk_penumbra_heights_km)
from .context import GeometryIdentity, SharedGeometryContext
from .geodesy import (WGS84_A_M, WGS84_B_M, WGS84_F, WGS84_E2, geodetic_to_ecef, ecef_to_geodetic, ecef_to_enu, enu_to_ecef, ray_sphere_intersections)
from .vertical import VerticalIndexPlan, center_layer_bounds_km

from .intersections import (LatticeSignature, VoxelIntersectionTopology, VoxelIntersectionPlan, build_voxel_intersection_topology, materialize_voxel_intersection_plan, build_voxel_intersection_plan, plan_direction_if_compatible, voxel_lattice_key)
