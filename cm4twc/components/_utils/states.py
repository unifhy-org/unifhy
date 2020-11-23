from netCDF4 import Dataset
from datetime import datetime
import cftime
import numpy as np

from ...settings import dtype_float


class State(object):
    """The State class behaves like a list which stores the values of a
    given component state for several consecutive timesteps (in
    chronological order, i.e. the oldest timestep is the first item,
    the most recent is the last item).

    Although, unlike a list, its indexing is shifted so that the last
    item has index 0, and all previous items are accessible via a
    negative integer (e.g. -1 for the 2nd-to-last, -2 for the
    3rd-to-last, etc.). The first item (i.e. the oldest timestep stored)
    is accessible at the index equals to minus the length of the list
    plus one. Since the list always remains in chronological order, it
    means that for a given timestep t, index -1 corresponds to timestep
    t-1, index -2 to timestep t-2, etc. Current timestep t is accessible
    at index 0.
    """
    def __init__(self, array, order='C'):
        self.array = array
        self.slices = [
            np.asfortranarray(array[i, ...]) if order == 'F' else array[i, ...]
            for i in range(array.shape[0])
        ]

    def __getitem__(self, index):
        index = self._shift_index(index)
        return self.slices[index]

    def __setitem__(self, index, item):
        index = self._shift_index(index)
        self.slices[index] = item

    def _shift_index(self, index):
        if isinstance(index, int):
            index = index + len(self) - 1
        elif isinstance(index, slice):
            start, stop = index.start, index.stop
            if start is not None:
                start = start + len(self) - 1
            if stop is not None:
                stop = stop + len(self) - 1
            index = slice(start, stop, index.step)
        return index

    def __delitem__(self, index):
        index = self._shift_index(index)
        del self.slices[index]

    def __len__(self):
        return len(self.slices)

    def __iter__(self):
        return iter(self.slices)

    def __repr__(self):
        return "%r" % self.slices

    def increment(self):
        # determine first index in the State
        # (function of solver's history)
        first_index = -len(self) + 1
        # prepare the left-hand side for the permutation of views
        lhs = [t for t in self]
        # prepare the right-hand side for the permutation of views
        rhs = [t for t in self[first_index + 1:]] + \
              [self[first_index]]
        # carry out the permutation of views
        # to avoid new object creations
        lhs[:] = rhs[:]
        # apply new list of views to the State
        self[:] = lhs

        # re-initialise current timestep of State to zero
        self[0][:] = 0.0


def create_states_dump(filepath, states_info, solver_history,
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
        f.createDimension('nv', 2)

        # coordinate variables
        t = f.createVariable('time', np.float64, ('time',))
        t.standard_name = 'time'
        t.units = timedomain.units
        t.calendar = timedomain.calendar
        h = f.createVariable('history', np.int8, ('history',))
        h[:] = np.arange(-solver_history, 1, 1)
        for axis in axes:
            coord = spacedomain.to_field().construct(axis)
            # (domain coordinate)
            a = f.createVariable(axis, dtype_float(), (axis,))
            a.standard_name = coord.standard_name
            a.units = coord.units
            a.bounds = axis + '_bounds'
            a[:] = coord.data.array
            # (domain coordinate bounds)
            b = f.createVariable(axis + '_bounds', dtype_float(), (axis, 'nv'))
            b.units = coord.units
            b[:] = coord.bounds.data.array

        # state variables
        for var in states_info:
            s = f.createVariable(var, dtype_float(),
                                 ('time', 'history', *axes))
            s.standard_name = var
            s.units = states_info[var]['units']


def update_states_dump(filepath, states, timestamp, solver_history):
    with Dataset(filepath, 'a') as f:
        try:
            # check whether given snapshot already in file
            t = cftime.time2index(timestamp, f.variables['time'])
        # will get a IndexError if time variable is empty
        # will get a ValueError if timestamp not in time variable
        except (IndexError, ValueError):
            # if not, extend time dimension
            t = len(f.variables['time'])
            f.variables['time'][t] = timestamp

        for state in states:
            for i, step in enumerate(range(-solver_history, 1, 1)):
                f.variables[state][t, i, ...] = states[state][step]


def load_states_dump(filepath, datetime_, states_info):
    states = {}

    with Dataset(filepath, 'r') as f:
        f.set_always_mask(False)
        # determine point in time to use from the dump
        if datetime_ is None:
            # if not specified, use the last time index
            t = -1
            datetime_ = cftime.num2date(f.variables['time'][-1],
                                        f.variables['time'].units,
                                        f.variables['time'].calendar)
        else:
            # find the index for the datetime given
            try:
                t = cftime.date2index(datetime_, f.variables['time'])
            except ValueError:
                raise ValueError(
                    '{} not available in dump {}'.format(datetime_, filepath))

        # try to get each of the states, if not in file, carry on anyway
        for state in states_info:
            try:
                states[state] = f.variables[state][t, ...]
            except KeyError:
                pass

    return states, datetime_
