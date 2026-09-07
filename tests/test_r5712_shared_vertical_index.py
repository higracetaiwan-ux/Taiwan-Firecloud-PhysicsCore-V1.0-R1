import numpy as np
from firecloud.shared_geometry.vertical import VerticalIndexPlan, nearest_vertical_indices


def test_nearest_vertical_midpoint_tie_chooses_lower():
    h=np.array([0.0,1.0,2.0])
    out=nearest_vertical_indices(h,np.array([0.5,1.5]))
    assert out.tolist()==[0,1]


def test_nearest_vertical_vector_matrix_shape_and_values():
    p=VerticalIndexPlan.from_heights([0.0,1.0,2.0,4.0])
    v=np.array([[0.1,0.9],[1.6,3.4]])
    out=p.nearest_indices(v)
    assert out.shape==v.shape
    assert out.tolist()==[[0,1],[2,3]]


def test_bracket_vertical_indices_preserve_bounds():
    p=VerticalIndexPlan.from_heights([0.0,1.0,2.0])
    lo,hi=p.bracket_indices(np.array([-1.0,0.5,1.0,3.0]))
    assert lo.tolist()==[0,0,0,1]
    assert hi.tolist()==[0,1,1,2]


def test_overlap_indices_closed_interval():
    p=VerticalIndexPlan.from_heights([0.0,0.5,1.0,1.5,2.0])
    assert p.overlap_indices(0.5,1.5).tolist()==[1,2,3]
