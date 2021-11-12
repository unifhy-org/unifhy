from os import path, sep
from netCDF4 import Dataset
from datetime import datetime
import cftime
import numpy as np

from ..settings import dtype_float


class Exchanger(object):

    def __init__(self, components, clock, compass,
                 identifier, saving_directory):
        # transfers that are both inwards and outwards will exist
        # only once because dictionary keys are unique
        transfers = {}
        for c in components:
            for i in [components[c].inwards_info, components[c].outwards_info]:
                for t in i:
                    if t not in transfers:
                        transfers[t] = {}
                    transfers[t].update(i[t])
                    if 'to' in i[t]:
                        # store component category for dumping (which
                        # will be identical to 'from' in most cases, but
                        # when 'from' is absent, source component still
                        # needed, namely for dumping to route to the
                        # right netcdf group, and absence of 'from' is
                        # informative, so info should not be added under
                        # 'from', but using a different key)
                        transfers[t]['src_cat'] = (
                            components[c].category
                        )
                        # store component spacedomain for remapping
                        transfers[t]['src_sd'] = (
                            components[c].spacedomain
                        )

        self.transfers = transfers
        # set up transfers according to components' time-/spacedomains
        self.clock = None
        self.compass = None
        self.set_up(clock, compass)

        # assign identifier
        self.identifier = identifier

        # directories and files
        self.saving_directory = saving_directory
        self.dump_file = None

    def set_up(self, clock, compass, overwrite=False):
        # (re)assign clock and compass to exchanger
        self.clock = clock
        self.compass = compass

        # determine how many iterations of the clock
        # each component covers (i.e. steps)
        steps = {
            c: clock.timedomains[c].timedelta // clock.timedelta
            for c in clock.timedomains
        }

        # set up each transfer
        for t in self.transfers:
            histories = []

            # determine shape of transfer while dropping Z axis if
            # spacedomain is 3D because transfers are along 2D interface
            shape = (
                self.transfers[t]['src_sd'].shape[1:]
                if self.transfers[t]['src_sd'].has_vertical_axis()
                else self.transfers[t]['src_sd'].shape
            )

            # special case for transfers towards a DataComponent or
            # a NullComponent (or towards outside framework, which will
            # remain possible until Ocean and Atmosphere components are
            # implemented in the framework)
            if self.transfers[t].get('from') is None:
                # in this case only set_transfer will be called,
                # no component is going to call get_transfer, so no need
                # for time weights, but because transfers still need to be
                # stored for dump, need to define 'history' for creation
                # of 'array' and 'slices'
                histories.append(1)
            else:
                src_ts = steps[self.transfers[t]['from']]
                for c in self.transfers[t]['to']:
                    dst_ts = steps[c]
                    # add a key to store info specific to receiving component
                    self.transfers[t][c] = {}

                    # check if spacedomains are different, if identical set
                    # to None to avoid unnecessary remapping
                    src_sd = self.transfers[t]['src_sd']
                    src_fld = src_sd.to_field()
                    dst_sd = compass.spacedomains[c]
                    dst_fld = dst_sd.to_field()

                    # eliminate Z axis by squeezing fields because
                    # remapping for transfers on a 2D interface
                    if src_sd.has_vertical_axis():
                        src_fld.squeeze(src_sd.vertical_axis, inplace=True)
                    if dst_sd.has_vertical_axis():
                        dst_fld.squeeze(dst_sd.vertical_axis, inplace=True)

                    if src_sd.is_space_equal_to(dst_fld):
                        self.transfers[t][c]['remap'] = None
                    else:
                        # now assign a tuple to 'remap' where first item
                        # is the source field and the second item is the
                        # preprocessed remapping operator (expensive
                        # step but done only once at initialisation)
                        remap = src_fld.regrids(
                            dst_fld, 'conservative', return_operator=True
                        )
                        self.transfers[t][c]['remap'] = (src_fld, remap)

                    # determine the time weights that will be used by the
                    # exchanger on the stored timesteps when a transfer
                    # is asked (i.e. when get_transfer is called)
                    t_weights = self._calculate_temporal_weights(
                        src_ts, dst_ts, clock.length
                    )

                    # history is the number of timesteps that are stored
                    history = t_weights.shape[-1]
                    self.transfers[t][c]['history'] = history
                    histories.append(history)

                    # special case if method is sum
                    if self.transfers[t]['method'] == 'sum':
                        # time weights need to sum to one
                        t_weights = t_weights / dst_ts
                        # need to add dimensions of size 1 for numpy
                        # broadcasting in weighted sum
                        t_weights = np.expand_dims(
                            t_weights, axis=[-(i+1) for i in range(len(shape))]
                        )

                    self.transfers[t][c]['t_weights'] = t_weights

                    # initialise iterator that allows the exchanger to know
                    # which time weights to use
                    self.transfers[t][c]['iter'] = 0

            # determine maximum history to be stored for this transfer
            history = max(histories)
            self.transfers[t]['history'] = history

            # if required or requested, initialise array to store
            # required timesteps
            if (
                    overwrite
                    or ('array' not in self.transfers[t])
                    or ('array' in self.transfers[t]
                        and (self.transfers[t]['array'].shape
                             != ((history,) + shape)))
            ):
                arr = np.zeros((history,) + shape, dtype_float())
                self.transfers[t]['array'] = arr
                # set up slices that are views of the array that is
                # to be rolled around each time a transfer is asked
                self.transfers[t]['slices'] = [
                    arr[i] for i in range(history)
                ]

    @staticmethod
    def _calculate_temporal_weights(src, dst, length):
        """
        TODO: since the constraint on the temporal resolutions has been
              pushed further to only support integer multiples of one
              another, this function could be extensively simplified in
              the future, although "qui peut le plus peut le moins"
              (who can do more can do less), so it still works and could
              be kept as is in case this constraint is relaxed in the
              future.

        **Examples:**

        >>> Exchanger._calculate_temporal_weights(3, 7, 42)
        array([[3, 3, 1],
               [2, 3, 2],
               [1, 3, 3],
               [3, 3, 1],
               [2, 3, 2],
               [1, 3, 3]])
        >>> Exchanger._calculate_temporal_weights(7, 3, 21)
        array([[0, 3],
               [0, 3],
               [1, 2],
               [0, 3],
               [2, 1],
               [0, 3],
               [0, 3]])
        """
        weights = []

        if dst == src:
            # need to keep only one step with full weight
            keep = 1
            for i in range(length // dst):
                weights.append((dst,))
        elif dst > src:
            if dst % src == 0:
                # need to keep several steps with equal weights
                keep = dst // src
                for i in range(length // dst):
                    weights.append(
                        (src,) * (dst // src)
                    )
            else:
                # need to keep several steps with varying weights
                keep = (dst // src) + 1
                previous = 0
                for i in range(length // dst):
                    start = src - previous
                    middle = ((dst - start) // src)
                    end = dst - start - (middle * src)
                    weights.append(
                        (start,
                         *((src,) * middle),
                         *((end,) if end > 0 else ()))
                    )
                    previous = end
        else:
            if src % dst == 0:
                # need to keep only one step with full weight
                keep = 1
                for i in range(length // dst):
                    weights.append(
                        (dst,)
                    )
            else:
                # need to keep two steps with varying weights
                keep = 2
                src_hits = 1
                for i in range(length // dst):
                    src_tracker = src * src_hits
                    if (((i * dst) < src_tracker)
                            and (src_tracker < ((i + 1) * dst))):
                        # src falls in-between two consecutive steps of dst
                        # spread weight across src kept values
                        # and update src hits
                        discard = (src_tracker // dst) * dst
                        oldest = src_tracker - discard
                        latest_ = dst - oldest
                        weights.append(
                            (oldest, latest_)
                        )
                        src_hits += 1
                    elif (i * dst) == src_tracker:
                        # src coincides with dst
                        # put whole weight on src latest value
                        # and update dst hits
                        weights.append(
                            (0, dst)
                        )
                        src_hits += 1
                    else:
                        # src is beyond dst and dst's next step
                        # put whole weight on src latest value
                        # but do not update src hits
                        weights.append(
                            (0, dst)
                        )

        weights = np.array(weights)

        assert keep == weights.shape[-1], 'error in exchanger temporal weights'

        return weights

    def initialise_(self, tag, overwrite=True):
        self.dump_file = '_'.join([self.identifier, 'exchanger',
                                   tag, 'dump_transfers.nc'])
        if (overwrite or not path.exists(sep.join([self.saving_directory,
                                                   self.dump_file]))):
            create_transfers_dump(
                sep.join([self.saving_directory, self.dump_file]),
                self.transfers, self.clock.timedomain,
                self.compass.spacedomains
            )

    def dump_transfers(self, timestamp):
        update_transfers_dump(
            sep.join([self.saving_directory, self.dump_file]),
            self.transfers, timestamp
        )

    def finalise_(self):
        timestamp = self.clock.timedomain.bounds.array[-1, -1]
        update_transfers_dump(
            sep.join([self.saving_directory, self.dump_file]),
            self.transfers, timestamp
        )

    def get_transfer(self, name, component):
        i = self.transfers[name][component]['iter']
        history = self.transfers[name][component]['history']

        # customise the action between existing and incoming arrays
        # depending on method for that particular transfer
        if self.transfers[name]['method'] == 'mean':
            value = np.average(
                self.transfers[name]['slices'][-history:],
                weights=self.transfers[name][component]['t_weights'][i], axis=0
            )
        elif self.transfers[name]['method'] == 'sum':
            value = np.sum(
                self.transfers[name]['slices'][-history:]
                * self.transfers[name][component]['t_weights'][i], axis=0
            )
        elif self.transfers[name]['method'] == 'point':
            value = self.transfers[name]['slices'][-1]
        elif self.transfers[name]['method'] == 'minimum':
            value = np.amin(self.transfers[name]['slices'][-history:], axis=0)
        elif self.transfers[name]['method'] == 'maximum':
            value = np.amax(self.transfers[name]['slices'][-history:], axis=0)
        else:
            raise ValueError('method for exchanger transfer unknown')

        # TODO: remap value from supermesh resolution to destination resolution
        # REPLACED BY:
        # remap value from source resolution to destination resolution
        if self.transfers[name][component]['remap'] is not None:
            src, remap = self.transfers[name][component]['remap']
            src[:] = value
            value = src.regrids(remap).array

        # record that another value was retrieved by incrementing count
        self.transfers[name][component]['iter'] += 1

        # convert value to masked array if mask exists
        mask = self.compass.spacedomains[component].land_sea_mask
        if mask is not None:
            value = np.ma.array(value, mask=~mask)

        return value

    def set_transfer(self, name, array):
        # TODO: remap value from source resolution to supermesh resolution

        # make room for new value by time incrementing
        lhs = [a for a in self.transfers[name]['slices']]
        rhs = ([a for a in self.transfers[name]['slices'][1:]]
               + [self.transfers[name]['slices'][0]])

        lhs[:] = rhs[:]

        self.transfers[name]['slices'][:] = lhs
        self.transfers[name]['slices'][-1][:] = array

    def update_transfers(self, transfers):
        for name, array in transfers.items():
            self.set_transfer(name, array)


def create_transfers_dump(filepath, transfers_info, timedomain, spacedomains):
    with Dataset(filepath, 'w') as f:
        # description
        f.description = (
            f"dump file created on "
            f"{datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
        )

        # common to all groups
        # dimensions
        f.createDimension('time', None)
        f.createDimension('nv', 2)
        # coordinate variables
        t = f.createVariable('time', np.float64, ('time',))
        t.standard_name = 'time'
        t.units = timedomain.units
        t.calendar = timedomain.calendar
        # for each group (corresponding to each source component)
        for c in spacedomains:
            g = f.createGroup(c)
            spacedomain = spacedomains[c]

            # drop Z axis if spacedomain is 3D because transfers are
            # along 2D interface only
            axes = (
                spacedomain.axes[1:]
                if spacedomain.has_vertical_axis()
                else spacedomain.axes
            )

            # dimensions and coordinate variables
            for axis in axes:
                # dimension (domain axis)
                g.createDimension(axis, len(getattr(spacedomain, axis)))
                # variables (dimension coordinates)
                coord = spacedomain.to_field().dim(axis)
                a = g.createVariable(axis, dtype_float(), (axis,))
                a.standard_name = coord.standard_name
                a.units = coord.units
                a.bounds = axis + '_bounds'
                a[:] = coord.data.array
                # (dimension coordinate bounds)
                b = g.createVariable(axis + '_bounds', dtype_float(),
                                     (axis, 'nv'))
                b.units = coord.units
                b[:] = coord.bounds.data.array

        # transfer variables
        for trf in transfers_info:
            s = f.groups[transfers_info[trf]['src_cat']].createVariable(
                trf, dtype_float(), ('time', *axes)
            )
            s.standard_name = trf
            s.units = transfers_info[trf]['units']


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

        for trf in transfers:
            f.groups[transfers[trf]['src_cat']].variables[trf][t, ...] = (
                transfers[trf]['slices'][-1]
            )


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
                    f"{datetime_} not available in dump {filepath}"
                )

        # try to get each of the transfers, if not in file, carry on anyway
        for trf in transfers_info:
            try:
                transfers[trf] = (
                    f.groups[transfers_info[trf]['src_cat']].variables[trf][t, ...]
                )
            except KeyError:
                pass

    return transfers, datetime_
