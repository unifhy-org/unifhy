import sys
import cf


# SETTINGS FOR PRECISION OF NUMERICAL OPERATIONS
# WHERE FLOATING POINT ISSUES CAN ARISE
PRECISION = {}


def ATOL(atol=None):
    """TODO: DOCSTRING REQUIRED"""
    # absolute numerical tolerance parameter for equality
    if atol is not None:
        PRECISION['ATOL'] = float(atol)
        cf.ATOL(atol)
    return PRECISION['ATOL']


def RTOL(rtol=None):
    """TODO: DOCSTRING REQUIRED"""
    # relative numerical tolerance parameter for equality
    if rtol is not None:
        PRECISION['RTOL'] = float(rtol)
        cf.RTOL(rtol)
    return PRECISION['RTOL']


def DECR(decr=None):
    """TODO: DOCSTRING REQUIRED"""
    # number of decimals for rounding floating point numbers
    if decr is not None:
        PRECISION['DECR'] = int(decr)
    return PRECISION['DECR']


ATOL(sys.float_info.epsilon)
RTOL(sys.float_info.epsilon)
DECR(12)
