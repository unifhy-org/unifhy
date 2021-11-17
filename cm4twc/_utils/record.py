import numpy as np
from netCDF4 import Dataset
from datetime import datetime, timedelta
import cftime

from ..time import TimeDomain
from ..settings import dtype_float


# dictionary of supported aggregation methods
# - keys provide list of supported methods,
# - key-to-value provides mapping allowing for aliases to point to the
#   same arbitrarily chosen method name
_methods_map = {
    'mean': 'mean',
    'average': 'mean',
    'sum': 'sum',
    'cumulative': 'sum',
    'point': 'point',
    'instantaneous': 'point',
    'min': 'minimum',
    'minimum': 'minimum',
    'max': 'maximum',
    'maximum': 'maximum'
}


def _frequency_to_frequency_tag(freq):
    if freq % timedelta(weeks=1) == timedelta(seconds=0):
        factor = freq // timedelta(weeks=1)
        factor = '' if factor == 1 else factor
        adverb = 'weekly'
    elif freq % timedelta(days=1) == timedelta(seconds=0):
        factor = freq // timedelta(days=1)
        factor = '' if factor == 1 else factor
        adverb = 'daily'
    elif freq % timedelta(hours=1) == timedelta(seconds=0):
        factor = freq // timedelta(hours=1)
        factor = '' if factor == 1 else factor
        adverb = 'hourly'
    elif freq % timedelta(minutes=1) == timedelta(seconds=0):
        factor = freq // timedelta(minutes=1)
        factor = '' if factor == 1 else factor
        adverb = 'minute' if factor == 1 else 'min'
    else:
        factor = int(freq.total_seconds())
        adverb = 's'

    return f'{factor}{adverb}'


def _frequency_to_frequency_str(freq):
    if freq % timedelta(weeks=1) == timedelta(seconds=0):
        factor = freq // timedelta(weeks=1)
        factor = '' if factor == 1 else factor
        units = 'weeks'
    elif freq % timedelta(days=1) == timedelta(seconds=0):
        factor = freq // timedelta(days=1)
        factor = '' if factor == 1 else factor
        units = 'days'
    elif freq % timedelta(hours=1) == timedelta(seconds=0):
        factor = freq // timedelta(hours=1)
        factor = '' if factor == 1 else factor
        units = 'hours'
    elif freq % timedelta(minutes=1) == timedelta(seconds=0):
        factor = freq // timedelta(minutes=1)
        factor = '' if factor == 1 else factor
        units = 'minutes'
    else:
        factor = int(freq.total_seconds())
        units = 'seconds'

    return f'{factor}{units}'


class Record(object):

    def __init__(self, name, units, divisions=(), **kwargs):
        self.name = name
        self.units = units
        self.divisions = divisions
        self.streams = []


class StateRecord(Record):
    # record for component state
    def __call__(self, states, to_exchanger, outputs):
        for s in self.streams:
            s.update_record(self.name, states[self.name].get_timestep(0))


class OutwardRecord(Record):
    # record for component outward to interface
    def __call__(self, states, to_exchanger, outputs):
        for s in self.streams:
            s.update_record(self.name, to_exchanger[self.name])


class OutputRecord(Record):
    # record for component bespoke output
    def __call__(self, states, to_exchanger, outputs):
        for s in self.streams:
            s.update_record(self.name, outputs[self.name])


class RecordStream(object):

    def __init__(self, frequency, writing_slice):
        # check frequency validity
        if not isinstance(frequency, timedelta):
            raise ValueError(f"invalid recording frequency {frequency}")

        # instantiate attributes to hold temporal information
        self.frequency = frequency
        self.frequency_tag = _frequency_to_frequency_tag(frequency)
        self._time = None
        self._time_bounds = None
        self._time_units = None
        self._time_calendar = None
        self._time_tracker = None
        self._desired_steps_per_slice = writing_slice
        # "steps" refer to the component resolution
        self._steps_per_slice = None
        # "beats" refer to the record stream frequency
        self._beats_per_slice = None

        # instantiate attributes to hold spatial information
        self._spacedomain = None
        self._spaceshapes = {}

        # instantiate holders for file paths
        self.file = None
        self.dump_file = None

        # mapping to store record objects (keys are record names)
        self._records = {}
        # mapping to store record methods (keys are record names)
        self._methods = {}
        # mapping to store record arrays (keys are record names)
        self._arrays = {}
        # mapping for integer tracker to know where in array to write next
        # (keys are record names)
        self._array_trackers = {}
        # mapping to store record masks (keys are record names)
        self._masks = {}

        # integers to track when to write to file
        self._trigger = None
        self._trigger_tracker = None

    def add_record(self, record, methods):
        name = record.name
        # store link to record object
        self._records[name] = record
        # store sequence of aggregation methods
        methods_ = set()
        for method in methods:
            if method in _methods_map:
                methods_.add(_methods_map[method])
            else:
                raise ValueError(
                    f"method {method} for record {name} aggregation unknown"
                )
        self._methods[name] = methods_
        # map this very stream in the record
        record.streams.append(self)

    def initialise(self, timedomain, spacedomain):
        # check frequency / timedomain resolution compatibility
        if (self.frequency % timedomain.timedelta) != timedelta(seconds=0):
            raise ValueError(
                f"recording frequency ({self.frequency}) not a multiple of "
                f"component timedelta ({timedomain.timedelta})"
            )
        if self.frequency > timedomain.period:
            raise ValueError(
                f"recording frequency ({self.frequency}) greater than "
                f"component timedelta ({timedomain.period})"
            )
        if (timedomain.period % self.frequency) != timedelta(seconds=0):
            raise ValueError(
                f"recording frequency ({self.frequency}) not a divisor of "
                f"simulation period ({timedomain.period})"
            )

        # determine most suited time slice
        steps_per_beat = int(
            self.frequency.total_seconds()
            / timedomain.timedelta.total_seconds()
        )

        candidates = np.arange(1, len(timedomain.time) + 1)
        # candidates must be a multiple of the record stream beat
        # while also being a multiple of the component simulation period
        # to guarantee that the last beat will be complete
        candidates = candidates[(candidates % steps_per_beat == 0)
                                & (len(timedomain.time) % candidates == 0)]

        # slice needs to be long enough to hold at least one beat
        min_steps_per_slice = max(
            self._desired_steps_per_slice, steps_per_beat
        )

        selected = candidates[candidates <= min_steps_per_slice][-1]

        self._steps_per_slice = selected
        self._beats_per_slice = int(selected / steps_per_beat)

        # create timedomain for stream
        _timedomain = TimeDomain.from_start_end_step(
            start=timedomain.bounds.datetime_array[0, 0],
            end=timedomain.bounds.datetime_array[-1, -1] + self.frequency,
            step=self.frequency,
            calendar=timedomain.calendar,
            units=timedomain.units
        )

        self._time = _timedomain.time.array[1:]
        self._time_bounds = _timedomain.bounds.array[:-1, :]
        self._time_units = _timedomain.units
        self._time_calendar = _timedomain.calendar

        # store spacedomain
        self._spacedomain = spacedomain

        # initialise record arrays for accumulating values
        self._trigger = 0
        for name, record in self._records.items():
            self._array_trackers[name] = 0

            d = record.divisions

            # initialise array
            arr = np.zeros(
                (self._steps_per_slice, *spacedomain.shape, *d), dtype_float()
            )
            arr[:] = np.nan
            self._arrays[name] = arr

            # process array mask
            if spacedomain.land_sea_mask is None:
                msk = None
            else:
                msk = ~spacedomain.land_sea_mask
                if d:
                    axes = [-(a + 1) for a in range(len(d))]
                    msk = np.broadcast_to(
                        np.expand_dims(msk, axis=axes),
                        (*spacedomain.shape, *d)
                    )

            spc_shp = (*spacedomain.shape, *d) if d else spacedomain.shape

            self._spaceshapes[name] = spc_shp
            self._masks[name] = msk

            # add on length of stream to the record trigger
            self._trigger += self._steps_per_slice

        # (re)initialise trackers
        self._time_tracker = 0
        self._trigger_tracker = 0

    def update_record(self, name, value):
        self._arrays[name][self._array_trackers[name], ...] = value
        self._array_trackers[name] += 1
        self._trigger_tracker += 1
        if self._trigger_tracker == self._trigger:
            self.update_record_to_stream_file()

    def create_record_stream_file(self, filepath):
        self.file = filepath

        with Dataset(self.file, 'w') as f:
            axes = self._spacedomain.axes
            # dimension for space and time lower+upper bounds
            f.createDimension('nv', 2)
            # space coordinate dimensions and coordinate variables
            for axis in axes:
                # dimension (domain axis)
                f.createDimension(axis, len(getattr(self._spacedomain, axis)))
                # variables
                # (domain coordinate)
                coord = self._spacedomain.to_field().dim(axis)
                a = f.createVariable(axis, dtype_float(), (axis,))
                a.standard_name = coord.standard_name
                a.units = coord.units
                a.bounds = f'{axis}_bounds'
                a[:] = coord.array
                # (domain coordinate bounds)
                b = f.createVariable(f'{axis}_bounds', dtype_float(),
                                     (axis, 'nv'))
                b.units = coord.units
                b[:] = coord.bounds.array

            # time coordination dimension and coordinate variable
            f.createDimension('time', None)
            t = f.createVariable('time', np.float64, ('time',))
            t.standard_name = 'time'
            t.units = self._time_units
            t.calendar = self._time_calendar
            t.bounds = 'time_bounds'
            b = f.createVariable('time_bounds', np.float64, ('time', 'nv'))
            b.units = self._time_units
            b.calendar = self._time_calendar

            for name, record in self._records.items():
                d = record.divisions
                if d:
                    dims = []
                    for n, v in enumerate(d):
                        dim_name = '_'.join([name, 'divisions', str(n + 1)])
                        f.createDimension(dim_name, v)
                        dims.append(dim_name)
                    dims = ('time', *axes, *dims)
                else:
                    dims = ('time', *axes)

                # record variable
                for method in self._methods[name]:
                    name_method = '_'.join([name, method])
                    v = f.createVariable(name_method, dtype_float(), dims)
                    v.standard_name = name
                    v.units = record.units
                    v.cell_methods = (
                        f"time: {method} over "
                        f"{_frequency_to_frequency_str(self.frequency)}"
                    )

    def update_record_to_stream_file(self):
        with Dataset(self.file, 'a') as f:
            start = self._time_tracker * self._beats_per_slice
            end = start + self._beats_per_slice

            time_ = self._time[start:end]
            time_bounds = self._time_bounds[start:end]
            time_len = len(time_)

            try:
                # check whether all timestamps already in file
                ts = cftime.time2index(time_, f.variables['time'])

            # will get a IndexError if time variable is empty
            except IndexError:
                # start expanding time dimension
                ts = np.arange(0, self._beats_per_slice)

            # will get a ValueError if any timestamp not in time variable
            except ValueError:
                # keep expanding time dimension
                try:
                    start = cftime.time2index(time_[0], f.variables['time'])
                    # at least one timestamp already in time variable
                    ts = np.arange(start, start + time_len)
                except ValueError:
                    # no timestamp already in time variable
                    ts = np.arange(len(f.variables['time']),
                                   len(f.variables['time']) + time_len)

            f.variables['time'][ts] = time_
            f.variables['time_bounds'][ts] = time_bounds

            for name, array in self._arrays.items():
                arr = array.reshape(
                    (time_len, -1, *self._spaceshapes[name])
                )

                if self._masks[name] is not None:
                    msk = np.broadcast_to(
                        np.expand_dims(self._masks[name], axis=0),
                        (time_len, *self._spaceshapes[name])
                    )
                else:
                    msk = None

                for method in self._methods[name]:
                    name_method = '_'.join([name, method])

                    # proceed with required aggregation
                    if method == 'mean':
                        value = np.nanmean(arr, axis=1)
                    elif method == 'sum':
                        value = np.nansum(arr, axis=1)
                    elif method == 'point':
                        value = arr[:, -1]
                    elif method == 'minimum':
                        value = np.nanmin(arr, axis=1)
                    elif method == 'maximum':
                        value = np.nanmax(arr, axis=1)

                    # store result in file
                    f.variables[name_method][ts] = np.ma.array(value, mask=msk)

                # reset array tracker to point to start of array again
                self._array_trackers[name] = 0
                # reset values in array
                array[:] = np.nan
            # increment time tracker to next writing time
            self._time_tracker += 1
            # reset trigger tracker
            self._trigger_tracker = 0

    def create_record_stream_dump(self, filepath):
        self.dump_file = filepath

        with Dataset(self.dump_file, 'w') as f:
            axes = self._spacedomain.axes

            # description
            f.description = (
                f"dump file created on "
                f"{datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
            )

            # dimensions
            f.createDimension('time', None)
            f.createDimension('length', self._steps_per_slice)
            for axis in axes:
                f.createDimension(axis, len(getattr(self._spacedomain, axis)))
            f.createDimension('nv', 2)

            # coordinate variables
            t = f.createVariable('time', np.float64, ('time',))
            t.standard_name = 'time'
            t.units = self._time_units
            t.calendar = self._time_calendar
            h = f.createVariable('length', np.uint32, ('length',))
            h[:] = np.arange(self._steps_per_slice)
            for axis in axes:
                coord = self._spacedomain.to_field().dim(axis)
                # (domain coordinate)
                a = f.createVariable(axis, dtype_float(), (axis,))
                a.standard_name = coord.standard_name
                a.units = coord.units
                a.bounds = f'{axis}_bounds'
                a[:] = coord.data.array
                # (domain coordinate bounds)
                b = f.createVariable(f'{axis}_bounds', dtype_float(),
                                     (axis, 'nv'))
                b.units = coord.units
                b[:] = coord.bounds.data.array

            # records
            for name, record in self._records.items():
                d = record.divisions
                if d:
                    dims = []
                    for n, v in enumerate(d):
                        dim_name = '_'.join([name, 'divisions', str(n + 1)])
                        f.createDimension(dim_name, v)
                        dims.append(dim_name)
                    dims = ('time', 'length', *axes, *dims)
                else:
                    dims = ('time', 'length', *axes)

                s = f.createVariable(name, dtype_float(), dims,
                                     fill_value=9.9692099683868690E36)
                s.standard_name = name
                s.units = record.units
                f.createVariable(f'{name}_tracker', int, ('time',))

            # stream-specific variables
            f.createVariable('time_tracker', int, ('time',))
            f.createVariable('trigger_tracker', int, ('time',))

    def update_record_stream_dump(self, timestamp):
        with Dataset(self.dump_file, 'a') as f:
            try:
                # check whether given snapshot already in file
                t = cftime.time2index(timestamp, f.variables['time'])
            # will get a IndexError if time variable is empty
            # will get a ValueError if timestamp not in time variable
            except (IndexError, ValueError):
                # if not, extend time dimension
                t = len(f.variables['time'])
                f.variables['time'][t] = timestamp

            for name in self._records:
                f.variables[name][t, ...] = self._arrays[name]
                f.variables[f'{name}_tracker'][t] = (
                    self._array_trackers[name]
                )
            f.variables['time_tracker'][t] = self._time_tracker
            f.variables['trigger_tracker'][t] = self._trigger_tracker

    def load_record_stream_dump(self, filepath, datetime_,
                                timedomain, spacedomain):
        self.dump_file = filepath

        with Dataset(self.dump_file, 'r') as f:
            # determine original simulation timedomain from dump start
            self.initialise(timedomain, spacedomain)

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
                        f"{datetime_} not available in record stream "
                        f"dump {self.dump_file}"
                    )

            # retrieve each record values
            for name in self._records:
                try:
                    mask = f.variables[name][t, ...].mask
                    self._arrays[name][~mask] = (
                        f.variables[name][t, ...].data[~mask]
                    )
                    self._array_trackers[name] = (
                        f.variables['_'.join([name, 'tracker'])][t]
                    )
                except KeyError:
                    raise KeyError(
                        f"{name} missing in record stream dump {self.dump_file}"
                    )
            # retrieve stream trackers
            self._time_tracker = f.variables['time_tracker'][t].item()
            self._trigger_tracker = f.variables['trigger_tracker'][t].item()

        return datetime_
