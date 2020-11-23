import numpy as np
from netCDF4 import Dataset

import cm4twc
from tests.test_time import get_dummy_output_time_and_bounds
from tests.test_component import time_resolutions

# expected raw values for states/transfers/outputs after main run
# (null initial conditions, no spinup run, 12-day period)
exp_outputs_raw = {
    'sync': {
        'surfacelayer': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
            'transfer_i': [6, 10, 20, 40, 56, 84, 132, 172, 236, 340, 428, 564],
            'transfer_j': [8, 12, 15, 42, 57, 69, 153, 201, 240, 495, 642, 762],
            'output_x': [5, 6, 6, 30, 42, 51, 132, 177, 213, 465, 609, 726]
        },
        'subsurface': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
            'transfer_k': [2, 3, 28, 41, 51, 133, 179, 216, 469, 614, 732, 1498],
            'transfer_m': [3, 11, 17, 29, 51, 69, 99, 149, 191, 257, 363, 453],
            'output_x': [0, -1, 22, 33, 41, 121, 165, 200, 451, 594, 710, 1474]
        },
        'openwater': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'transfer_l': [1, 8, 25, 38, 63, 108, 145, 206, 307, 392, 525, 738],
            'transfer_n': [0, 24, 36, 45, 126, 171, 207, 459, 603, 720, 1485, 1926],
            'transfer_o': [3, 11, 15, 18, 45, 60, 72, 156, 204, 243, 498, 645],
            'output_x': [3, 27, 39, 48, 129, 174, 210, 462, 606, 723, 1488, 1929],
            'output_y': [-1, 4, 19, 30, 53, 96, 131, 190, 289, 372, 503, 714]
        }
    },
    'async': {
        'surfacelayer': {
            'state_a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'state_b': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
            'transfer_i': [6, 9, 13, 16, 28, 31, 43, 46, 82, 85, 112, 115],
            'transfer_j': [8, 10, 12, 20, 22, 24, 49, 51, 53, 108.5, 110.5, 112.5],
            'output_x': [5, 4, 3, 8, 7, 6, 28, 27, 26, 78.5, 77.5, 76.5]
        },
        'subsurface': {
            'state_a': [1, 2, 3, 4],
            'state_b': [2, 4, 6, 8],
            'transfer_k': [6, 29, 82.5, 145.5],
            'transfer_m': [8, 24, 47, 102],
            'output_x': [4, 25, 76.5, 137.5]
        },
        'openwater': {
            'state_a': [1, 2, 3, 4, 5, 6],
            'transfer_l': [1, 10, 19, 52, 76, 100],
            'transfer_n': [12, 33, 63, 109.5, 156, 328.5],
            'transfer_o': [7, 14, 24, 39.5, 55, 112.5],
            'output_x': [15, 36, 66, 112.5, 159, 331.5],
            'output_y': [-1, 6, 13, 44, 66, 88]
        }
    }
}


def aggregate_raw_output(values, method, slice_):
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


def get_expected_output(time_, component, name, delta, method):
    category = component.category

    # map to default for alias methods
    method = cm4twc.components._utils.outputs._methods_map[method]

    # aggregate raw output using method and relevant slices
    expected_output = aggregate_raw_output(
        exp_outputs_raw[time_][category][name],
        method,
        delta // component.timedomain.timedelta
    )

    # get expected temporal dimensions
    expected_time, expected_bounds = get_dummy_output_time_and_bounds(
        time_resolutions[category][time_], delta
    )

    return expected_time, expected_bounds, expected_output


def get_produced_output(component, name, delta, method):
    rtol, atol = cm4twc.rtol(), cm4twc.atol()

    # map to default for alias methods
    method = cm4twc.components._utils.outputs._methods_map[method]

    # load output from stream file
    with Dataset(component._output_streams[delta].file, 'r') as f:
        values = f.variables['_'.join([name, method])][:]
        time = f.variables['time'][:]
        bounds = f.variables['time_bounds'][:]

    # check that array is homogeneous (i.e. min = max)
    axis = tuple(range(1, values.ndim))
    min_ = np.amin(values, axis=axis)
    max_ = np.amax(values, axis=axis)
    np.testing.assert_allclose(min_, max_, atol, rtol)

    return time, bounds, min_
