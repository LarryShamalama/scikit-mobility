from ..utils import gislib, utils, constants
from ..core.trajectorydataframe import *
import numpy as np
import inspect

def compress(tdf, spatial_radius_km=0.2):
    """
    Reduce the number of points in a trajectory.
    All points within a radius of `spatial_radius_km` km from a given initial point are compressed into
    a single point that has the median coordinates of all points and the time of the initial point.

    :param tdf: TrajDataFrame
        the input trajectory

    :param spatial_radius_km: float (default 0.2)
        minimum distance (in km) between points of the compressed trajectory

    :return: TrajDataFrame
        the compressed TrajDataFrame


    References:
        .. [zheng2015trajectory] Zheng, Yu. "Trajectory data mining: an overview." ACM Transactions on Intelligent Systems and Technology (TIST) 6, no. 3 (2015): 29.
    """
    # Sort
    tdf = tdf.sort_by_uid_and_datetime()

    # Save function arguments and values in a dictionary
    frame = inspect.currentframe()
    args, _, _, arg_values = inspect.getargvalues(frame)
    arguments = dict([('function', compress.__name__)]+[(i, arg_values[i]) for i in args[1:]])

    groupby = []

    if utils.is_multi_user(tdf):
        groupby.append(constants.UID)
    if utils.is_multi_trajectory(tdf):
        groupby.append(constants.TID)

    if len(groupby) > 0:
        # Apply simplify trajectory to each group of points
        ctdf = tdf.groupby(groupby, group_keys=False).apply(_compress_trajectory, spatial_radius=spatial_radius_km)

    else:
        ctdf = _compress_trajectory(tdf, spatial_radius=spatial_radius_km)

    ctdf.parameters = tdf.parameters
    ctdf.set_parameter(constants.COMPRESSION_PARAMS, arguments)
    return ctdf


def _compress_trajectory(tdf, spatial_radius):
    # From dataframe convert to numpy matrix
    lat_lng_dtime_other = utils.to_matrix(tdf)
    columns_order = list(tdf.columns)

    compressed_traj = _compress_array(lat_lng_dtime_other, spatial_radius)

    compressed_traj = nparray_to_trajdataframe(compressed_traj, utils.get_columns(tdf), {})
    # Put back to the original order
    compressed_traj = compressed_traj[columns_order]

    return compressed_traj


def _compress_array(lat_lng_dtime_other, spatial_radius):
    # Define the distance function to use
    measure_distance = gislib.getDistance

    compressed_traj = []
    lat_0, lon_0 = lat_lng_dtime_other[0][:2]

    sum_lat, sum_lon = [lat_0], [lon_0]
    t_0 = lat_lng_dtime_other[0][2]
    count = 1
    lendata = len(lat_lng_dtime_other) - 1

    for i in range(lendata):
        lat,lon,t = lat_lng_dtime_other[i+1][:3]

        Dr = measure_distance([lat_0,lon_0],[lat, lon])

        if Dr > spatial_radius:

            extra_cols = list(lat_lng_dtime_other[i][3:])
            compressed_traj += [[np.median(sum_lat), np.median(sum_lon), t_0] + extra_cols]

            t_0 = t
            count = 0
            lat_0, lon_0 = lat, lon
            sum_lat, sum_lon = [], []

        count += 1
        sum_lat += [lat]
        sum_lon += [lon]

    return compressed_traj
