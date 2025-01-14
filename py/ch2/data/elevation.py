from logging import getLogger

import numpy as np
from scipy.interpolate import UnivariateSpline

from .frame import present
from ..names import N

log = getLogger(__name__)


def smooth_elevation(df, smooth=4):
    if not present(df, N.ELEVATION):
        log.debug(f'Smoothing {N.SRTM1_ELEVATION} to get {N.ELEVATION}')
        unique = df.loc[~df[N.DISTANCE].isna() & ~df[N.SRTM1_ELEVATION].isna(),
                        [N.DISTANCE, N.SRTM1_ELEVATION]].drop_duplicates(N.DISTANCE)
        # the smoothing factor is from eyeballing results only.  maybe it should be a parameter.
        # it seems better to smooth along the route rather that smooth the terrain model since
        # 1 - we expect the route to be smoother than the terrain in general (roads / tracks)
        # 2 - smoothing the 2d terrain is difficult to control and can give spikes
        # 3 - we better handle errors from mismatches between terrain model and position
        #     (think hairpin bends going up a mountainside)
        # the main drawbacks are
        # 1 - speed on loading
        # 2 - no guarantee of consistency between routes (or even on the same routine retracing a path)
        spline = UnivariateSpline(unique[N.DISTANCE], unique[N.SRTM1_ELEVATION], s=len(unique) * smooth)
        df[N.ELEVATION] = spline(df[N.DISTANCE])
        df[N.GRADE] = (spline.derivative()(df[N.DISTANCE]) / 10)  # distance in km, but percentage
        df[N.GRADE] = df[N.GRADE].rolling(5, center=True).median().ffill().bfill()
        # avoid extrapolation / interpolation
        df.loc[df[N.SRTM1_ELEVATION].isna(), [N.ELEVATION]] = None
    return df


def add_gradient(df):
    # not used above, but used for barometer based data
    df[N.GRADE] = df[N.ELEVATION].rolling(3, center=True).mean().diff() / (10 * df[N.DISTANCE].diff())
    df[N.GRADE].replace([np.inf, -np.inf], np.nan, inplace=True)
