from collections.abc import MutableMapping
from os import path, sep
from netCDF4 import Dataset
from datetime import datetime
import cftime
import numpy as np

from ..settings import dtype_float


class Interface(MutableMapping):

    def __init__(self, components, clock, compass,
                 identifier, output_directory):
        # transfers that are both inwards and outwards will exist
        # only once because dictionary keys are unique
        transfers = {}
        for c in components:
            for i in [components[c].inwards_info, components[c].outwards_info]:
                for t in i:
                    if t not in transfers:
                        transfers[t] = {}
                    transfers[t].update(i[t])
        self.transfers = transfers
        # set up transfers according to components' time-/spacedomains
        self.set_up(components, clock, compass)

        # assign identifier
        self.identifier = identifier

        # directories and files
        self.output_directory = output_directory
        self.dump_file = None

    def set_up(self, components, clock, compass, overwrite=False):
        # determine how many iterations of the clock
        # each component covers (i.e. steps)
        steps = {
            c: components[c].timedomain.timedelta // clock.timedelta
            for c in components
        }

        # set up each transfer
        for t in self.transfers:
            # special case for transfers towards a DataComponent or
            # a NullComponent (or towards outside framework which will
            # remain possible until Ocean and Atmosphere components are
            # implemented in the framework)
            if self.transfers[t].get('from') is None:
                # in this case only __setitem__ will be called
                continue

            to_ = steps[self.transfers[t]['to']]
            from_ = steps[self.transfers[t]['from']]

            # determine the weights that will be used by the interface
            # on the stored timesteps when a transfer is asked (i.e.
            # when __getitem__ is called)
            self.transfers[t]['weights'] = self._calculate_weights(
                from_, to_, clock.length
            )
            if self.transfers[t]['method'] == 'sum':
                # need to add dimensions of size 1 for numpy broadcasting
                self.transfers[t]['weights'] = np.expand_dims(
                    self.transfers[t]['weights'],
                    axis=[-(i+1) for i in range(len(compass.shape))]
                )

            # history is the number of timesteps that are stored
            self.transfers[t]['history'] = (
                self.transfers[t]['weights'].shape[-1]
            )

            # initialise iterator that allows the interface to know
            # which weights to use
            self.transfers[t]['iter'] = 0

            # if required or requested, initialise array to store
            # required timesteps
            if (
                    overwrite
                    or ('array' not in self.transfers[t])
                    or ('array' in self.transfers[t]
                        and (self.transfers[t]['array'].shape
                             != ((self.transfers[t]['history'],)
                                 + compass.shape)))
            ):
                arr = np.zeros((self.transfers[t]['history'],) + compass.shape,
                               dtype_float())
                self.transfers[t]['array'] = arr
                # set up slices that are views of the array that is be
                # rolled out each time a transfer is asked
                self.transfers[t]['slices'] = [
                    arr[i] for i in range(self.transfers[t]['history'])
                ]

    @staticmethod
    def _calculate_weights(from_, to_, length):
        weights = []

        if to_ == from_:
            # need to keep only one step with full weight
            keep = 1
            for i in range(length // to_):
                weights.append((to_,))
        elif to_ > from_:
            if to_ % from_ == 0:
                # need to keep several steps with equal weights
                keep = to_ // from_
                for i in range(length // to_):
                    weights.append(
                        (from_,) * (to_ // from_)
                    )
            else:
                # need to keep several steps with varying weights
                keep = (to_ // from_) + 1
                previous = 0
                for i in range(length // to_):
                    start = from_ - previous
                    middle = ((to_ - start) // from_)
                    end = to_ - start - (middle * from_)
                    weights.append(
                        (start,
                         *((from_,) * middle),
                         *((end,) if end > 0 else ()))
                    )
                    previous = end
        else:
            if from_ % to_ == 0:
                # need to keep only one step with full weight
                keep = 1
                for i in range(length // to_):
                    weights.append(
                        (to_,)
                    )
            else:
                # need to keep two steps with varying weights
                keep = 2
                from_hits = 1
                for i in range(length // to_):
                    from_tracker = from_ * from_hits
                    if ((i * to_) < from_tracker) and (from_tracker < ((i + 1) * to_)):
                        # from_ falls in-between two consecutive steps of to_
                        # spread weight across from_ kept values
                        # and update from_ hits
                        discard = (from_tracker // to_) * to_
                        oldest = from_tracker - discard
                        latest_ = to_ - oldest
                        weights.append(
                            (oldest, latest_)
                        )
                        from_hits += 1
                    elif (i * to_) == from_tracker:
                        # from_ coincides with to_
                        # put whole weight on from_ latest value
                        # and update from_ hits
                        weights.append(
                            (0, to_)
                        )
                        from_hits += 1
                    else:
                        # from_ is beyond to_ and to_'s next step
                        # put whole weight on from_ latest value
                        # but do not update from_ hits
                        weights.append(
                            (0, to_)
                        )

        weights = np.array(weights)

        assert keep == weights.shape[-1], 'error in interface weights'

        return weights

    def initialise_transfers_dump(self, tag, clock, compass,
                                  overwrite_dump=True):
        self.dump_file = '_'.join([self.identifier, 'interface',
                                   tag, 'dump.nc'])
        if (overwrite_dump or not path.exists(sep.join([self.output_directory,
                                                        self.dump_file]))):
            create_transfers_dump(
                sep.join([self.output_directory, self.dump_file]),
                self.transfers, clock.timedomain, compass.spacedomain
            )

    def dump_transfers(self, timestamp):
        update_transfers_dump(
            sep.join([self.output_directory, self.dump_file]),
            self.transfers, timestamp
        )

    def __getitem__(self, key):
        i = self.transfers[key]['iter']

        # customise the action between existing and incoming arrays
        # depending on method for that particular transfer
        if self.transfers[key]['method'] == 'mean':
            value = np.average(
                self.transfers[key]['slices'],
                weights=self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'sum':
            value = np.sum(
                self.transfers[key]['slices']
                * self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'point':
            value = self.transfers[key]['slices'][-1]
        elif self.transfers[key]['method'] == 'minimum':
            value = np.amin(self.transfers[key]['slices'], axis=0)
        elif self.transfers[key]['method'] == 'maximum':
            value = np.amax(self.transfers[key]['slices'], axis=0)
        else:
            raise ValueError('method for interface transfer unknown')

        # record that another value was retrieved by incrementing count
        self.transfers[key]['iter'] += 1

        return value

    def __setitem__(self, key, value):
        # special case for transfers towards a DataComponent or
        # a NullComponent (or towards outside framework which will
        # remain possible until Ocean and Atmosphere components are
        # implemented in the framework)
        if self.transfers[key].get('from') is None:
            return

        lhs = [a for a in self.transfers[key]['slices']]
        rhs = ([a for a in self.transfers[key]['slices'][1:]]
               + [self.transfers[key]['slices'][0]])

        lhs[:] = rhs[:]

        self.transfers[key]['slices'][:] = lhs
        self.transfers[key]['slices'][-1] = value

    def __delitem__(self, key):
        del self.transfers[key]

    def __iter__(self):
        return iter(self.transfers)

    def __len__(self):
        return len(self.transfers)


def create_transfers_dump(filepath, transfers_info, timedomain, spacedomain):
    with Dataset(filepath, 'w') as f:
        axes = spacedomain.axes

        # description
        f.description = "Dump file created on {}".format(
            datetime.now().strftime('%Y-%m-%d at %H:%M:%S'))

        # dimensions
        f.createDimension('time', None)
        for axis in axes:
            f.createDimension(axis, len(getattr(spacedomain, axis)))

        # coordinate variables
        t = f.createVariable('time', np.float64, ('time',))
        t.units = timedomain.units
        t.calendar = timedomain.calendar
        for axis in axes:
            a = f.createVariable(axis, dtype_float(), (axis,))
            a[:] = getattr(spacedomain, axis).array

        # state variables
        for var in transfers_info:
            s = f.createVariable(var, dtype_float(),
                                 ('time', *axes))
            s.units = transfers_info[var]['units']


def update_transfers_dump(filepath, transfers, timestamp):
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

        for transfer in transfers:
            if transfers[transfer].get('from') is None:
                continue
            f.variables[transfer][t, ...] = transfers[transfer]['slices'][-1]


def load_transfers_dump(filepath, datetime_, transfers_info):
    transfers = {}

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

        # try to get each of the transfers, if not in file, carry on anyway
        for transfer in transfers_info:
            try:
                transfers[transfer] = f.variables[transfer][t, ...]
            except KeyError:
                pass

    return transfers, datetime_
