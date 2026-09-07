from __future__ import annotations
"""Canonical vertical-index and layer-boundary primitives."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class VerticalIndexPlan:
    centers_km: np.ndarray

    @classmethod
    def from_centers(cls, centers_km):
        a=np.asarray(centers_km,dtype=float)
        if a.ndim != 1 or a.size == 0 or not np.all(np.isfinite(a)):
            raise ValueError("vertical centers must be a finite non-empty 1-D array")
        if np.any(np.diff(a) < 0):
            a=np.sort(a)
        return cls(a)

    def nearest_indices(self, z_km):
        z=np.asarray(z_km,dtype=float)
        h=self.centers_km
        hi=np.searchsorted(h,z,side="left"); hi=np.clip(hi,0,len(h)-1)
        lo=np.clip(hi-1,0,len(h)-1)
        # Strict '<' preserves legacy midpoint tie-to-lower rule.
        choose_hi=np.abs(h[hi]-z) < np.abs(z-h[lo])
        return np.where(choose_hi,hi,lo)

    def bracket_indices(self, z_km: float) -> tuple[int,int,float]:
        h=self.centers_km; z=float(z_km)
        j=int(np.searchsorted(h,z,side="left"))
        if j<=0: return 0,0,0.0
        if j>=len(h): return len(h)-1,len(h)-1,0.0
        lo,hi=j-1,j; den=float(h[hi]-h[lo]); w=0.0 if den==0 else (z-float(h[lo]))/den
        return lo,hi,float(w)


def center_layer_bounds_km(centers_km) -> tuple[np.ndarray,np.ndarray]:
    """Half-level layer bounds from monotonic center heights."""
    h=np.asarray(centers_km,dtype=float)
    if h.ndim!=1 or h.size<2: raise ValueError("at least two centers required")
    if np.any(np.diff(h)<0): h=np.sort(h)
    mid=0.5*(h[:-1]+h[1:])
    lower=np.empty_like(h); upper=np.empty_like(h)
    lower[1:]=mid; upper[:-1]=mid
    lower[0]=max(0.0,float(h[0]-0.5*(h[1]-h[0])))
    upper[-1]=float(h[-1]+0.5*(h[-1]-h[-2]))
    return lower,upper
