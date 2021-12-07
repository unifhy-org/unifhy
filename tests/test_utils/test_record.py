import numpy as np
from netCDF4 import Dataset

import unifhy
from tests.test_time import get_dummy_output_time_and_bounds
from tests.test_component import time_resolutions

# expected raw values for states/transfers/outputs after main run
# (null initial conditions, no spinup run, 12-day period)
exp_records_raw = {
    'same_t': {
        'surfacelayer': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32],
            'transfer_i': [6, 10, 20, 40, 56, 84, 132, 172, 236, 340, 428, 564, 780, 964, 1244, 1684],
            'transfer_j': [8, 12, 15, 42, 57, 69, 153, 201, 240, 495, 642, 762, 1530, 1974, 2337, 4644],
            'output_x': [5, 4, 27, 38, 46, 126, 170, 205, 456, 599, 715, 1479, 1919, 2278, 4581, 5912]
        },
        'subsurface': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32],
            'transfer_k': [2, 3, 28, 41, 51, 133, 179, 216, 469, 614, 732, 1498, 1940, 2301, 4606, 5939],
            'transfer_m': [3, 11, 17, 29, 51, 69, 99, 149, 191, 257, 363, 453, 591, 809, 995, 1277],
            'output_x': [0, -1, 22, 33, 41, 121, 165, 200, 451, 594, 710, 1474, 1914, 2273, 4576, 5907]
        },
        'openwater': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            'transfer_l': [1, 8, 25, 38, 63, 108, 145, 206, 307, 392, 525, 738, 919, 1196, 1633, 2006],
            'transfer_n': [0, 24, 36, 45, 126, 171, 207, 459, 603, 720, 1485, 1926, 2286, 4590, 5922, 7011],
            'transfer_o': [3, 11, 15, 18, 45, 60, 72, 156, 204, 243, 498, 645, 765, 1533, 1977, 2340],
            'output_x': [3, 27, 39, 48, 129, 174, 210, 462, 606, 723, 1488, 1929, 2289, 4593, 5925, 7014],
            'output_y': [-1, 4, 19, 30, 53, 96, 131, 190, 289, 372, 503, 714, 893, 1168, 1603, 1974]
        }
    },
    'diff_t': {
        'surfacelayer': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32],
            'transfer_i': [6, 9, 13, 16, 20, 23, 47, 50, 54, 57, 104, 107, 111, 114, 201.5, 204.5],
            'transfer_j': [8, 10, 12, 14, 24, 26, 28, 30, 72, 74, 76, 78, 153, 155, 157, 159],
            'output_x': [5, 4, 15, 14, 34, 33, 56, 55, 78, 77, 148, 147, 218, 217, 337.5, 336.5]
        },
        'subsurface': {
            'state_a': [1, 2, 3, 4],
            'state_b': [2, 4, 6, 8],
            'transfer_k': [8, 48, 121, 290.75],
            'transfer_m': [10, 31.5, 73.25, 142.375],
            'output_x': [6, 44, 115, 282.75]
        },
        'openwater': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8],
            'transfer_l': [1, 2, 23, 24, 68, 69, 153.5, 154.5],
            'transfer_n': [12, 33, 57, 81, 153, 225, 346.5, 468],
            'transfer_o': [7, 14, 22, 30, 54, 78, 118.5, 159],
            'output_x': [15, 36, 60, 84, 156, 228, 349.5, 471],
            'output_y': [-1, -2, 17, 16, 58, 57, 139.5, 138.5]
        }
    }
}


def aggregate_raw_record(values, method, slice_):
    length = len(values)

    if method == 'sum':
        result = [sum(values[slice_ * i:(slice_ * (i + 1))])
                  for i in range(0, length // slice_)]
    elif method == 'mean':
        result = [sum(values[slice_ * i:(slice_ * (i + 1))]) / slice_
                  for i in range(0, length // slice_)]
    elif method == 'minimum':
        result = [min(values[slice_ * i:(slice_ * (i + 1))])
                  for i in range(0, length // slice_)]
    elif method == 'maximum':
        result = [max(values[slice_ * i:(slice_ * (i + 1))])
                  for i in range(0, length // slice_)]
    else:  # method == 'point'
        result = [values[slice_ * (i + 1) - 1]
                  for i in range(0, length // slice_)]

    return np.array(result)


def get_expected_record(time_, component, name, delta, method):
    category = component.category

    # map to default for alias methods
    method = unifhy._utils.record._methods_map[method]

    # aggregate raw record using method and relevant slices
    expected_record = aggregate_raw_record(
        exp_records_raw[time_][category][name],
        method,
        delta // component.timedomain.timedelta
    )

    # get expected temporal dimensions
    expected_time, expected_bounds = get_dummy_output_time_and_bounds(
        time_resolutions[category][time_], delta
    )

    return expected_time, expected_bounds, expected_record


def get_produced_record(component, name, delta, method):
    rtol, atol = unifhy.rtol(), unifhy.atol()

    # map to default for alias methods
    method = unifhy._utils.record._methods_map[method]

    # load record from stream file
    with Dataset(component._record_streams[delta].file, 'r') as f:
        values = f.variables['_'.join([name, method])][:]
        time = f.variables['time'][:]
        bounds = f.variables['time_bounds'][:]

    # check that array is homogeneous (i.e. min = max)
    axis = tuple(range(1, values.ndim))
    min_ = np.amin(values, axis=axis)
    max_ = np.amax(values, axis=axis)
    np.testing.assert_allclose(min_, max_, atol, rtol)

    return time, bounds, min_
