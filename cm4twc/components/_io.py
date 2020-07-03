from netCDF4 import Dataset
from datetime import datetime
import cftime
import numpy as np


def create_dump_file(filepath, states_info, solver_history,
                     timedomain, spacedomain):
    with Dataset(filepath, 'w') as f:
        axes = spacedomain.axes

        # description
        f.description = "Dump file created on {}".format(
            datetime.now().strftime('%Y-%m-%d at %H:%M:%S'))

        # dimensions
        f.createDimension('time', None)
        f.createDimension('history', solver_history + 1)
        for axis in axes:
            f.createDimension(axis, len(getattr(spacedomain, axis)))

        # coordinate variables
        t = f.createVariable('time', np.float64, ('time',))
        t.units = timedomain.units
        t.calendar = timedomain.calendar
        h = f.createVariable('history', np.int8, ('history',))
        h[:] = np.arange(-solver_history, 1, 1)
        for axis in axes:
            a = f.createVariable(axis, np.float64, (axis,))
            a[:] = getattr(spacedomain, axis).array

        # state variables
        for state in states_info:
            s = f.createVariable(state, np.float64, ('time', 'history', *axes))
            s.units = states_info[state]


def update_dump_file(filepath, states, timestamp, solver_history):
    with Dataset(filepath, 'a') as f:
        t = len(f.variables['time'])
        f.variables['time'][t] = timestamp
        for state in states:
            for i, step in enumerate(range(-solver_history, 1, 1)):
                f.variables[state][t, i, ...] = states[state][step]


def load_dump_file(filepath, datetime_, states_info):
    states = {}

    with Dataset(filepath, 'r') as f:
        # determine point in time to use from the dump
        if datetime_ is None:
            # if not specified, use the last time index
            t = -1
        else:
            # find the index for the datetime given
            try:
                t = cftime.date2index(datetime_, f.variable['time'])
            except ValueError:
                raise ValueError(
                    '{} not available in dump {}'.format(datetime_, filepath))

        # try to get each of the states, if not in file, carry on anyway
        for state in states_info:
            try:
                states[state] = f.variables[state][t, ...]
            except KeyError:
                pass

    return states
