import numpy as np


# dictionary to store package-wide settings
settings_ = {}


# functions to set and get a particular package-wide setting
def atol(value=None):
    """TODO: DOCSTRING REQUIRED"""
    # absolute numerical tolerance parameter for equality
    if value is not None:
        settings_['ATOL'] = float(value)
    return settings_['ATOL']


def rtol(value=None):
    """TODO: DOCSTRING REQUIRED"""
    # relative numerical tolerance parameter for equality
    if value is not None:
        settings_['RTOL'] = float(value)
    return settings_['RTOL']


def decr(value=None):
    """TODO: DOCSTRING REQUIRED"""
    # number of decimals for rounding floating point numbers
    if value is not None:
        settings_['DECR'] = int(value)
    return settings_['DECR']


def dtype_float(value=None):
    """TODO: DOCSTRING REQUIRED"""
    # data type (i.e. precision) for floating point numbers
    if value is not None:
        settings_['DTYPE_FLOAT'] = np.dtype(value)
    return settings_['DTYPE_FLOAT']


def array_order(value=None):
    """TODO: DOCSTRING REQUIRED"""
    # contiguity for arrays ('C' is row-major, 'F' is column-major)
    if value is not None:
        settings_['ORDER'] = str(value)
    return settings_['ORDER']


# configuring default values
atol(1e-8)
rtol(1e-5)
decr(12)
dtype_float(np.float64)
array_order('C')
