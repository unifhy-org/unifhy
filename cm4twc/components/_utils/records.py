import numpy as np
from netCDF4 import Dataset
from datetime import datetime, timedelta
import cftime

from ...time import TimeDomain
from ...settings import dtype_float


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


def _delta_to_frequency_tag(delta):
    if delta % timedelta(weeks=1) == timedelta(seconds=0):
        factor = delta // timedelta(weeks=1)
        factor = '' if factor == 1 else factor
        frequency = 'weekly'
    elif delta % timedelta(days=1) == timedelta(seconds=0):
        factor = delta // timedelta(days=1)
        factor = '' if factor == 1 else factor
        frequency = 'daily'
    elif delta % timedelta(hours=1) == timedelta(seconds=0):
        factor = delta // timedelta(hours=1)
        factor = '' if factor == 1 else factor
        frequency = 'hourly'
    elif delta % timedelta(minutes=1) == timedelta(seconds=0):
        factor = delta // timedelta(minutes=1)
        factor = '' if factor == 1 else factor
        frequency = 'minute' if factor == 1 else 'min'
    else:
        factor = int(delta.total_seconds())
        frequency = 's'

    return '{}{}'.format(factor, frequency)


def _delta_to_frequency_str(delta):
    if delta % timedelta(weeks=1) == timedelta(seconds=0):
        factor = delta // timedelta(weeks=1)
        factor = '' if factor == 1 else factor
        period = 'weeks'
    elif delta % timedelta(days=1) == timedelta(seconds=0):
        factor = delta // timedelta(days=1)
        factor = '' if factor == 1 else factor
        period = 'days'
    elif delta % timedelta(hours=1) == timedelta(seconds=0):
        factor = delta // timedelta(hours=1)
        factor = '' if factor == 1 else factor
        period = 'hours'
    elif delta % timedelta(minutes=1) == timedelta(seconds=0):
        factor = delta // timedelta(minutes=1)
        factor = '' if factor == 1 else factor
        period = 'minutes'
    else:
        factor = int(delta.total_seconds())
        period = 'seconds'

    return '{}{}'.format(factor, period)


class Record(object):

    def __init__(self, name, units, **kwargs):
        self.name = name
        self.units = units
        self.streams = []


class StateRecord(Record):
    # record for component state
    def __call__(self, states, to_exchanger, outputs):
        for s in self.streams:
            s.update_record(self.name, states[self.name][0])


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

    def __init__(self, delta):
        # check delta validity
        if not isinstance(delta, timedelta):
            raise ValueError('invalid recording frequency {}'.format(delta))

        # instantiate attributes to hold temporal information
        self.delta = delta
        self.frequency = _delta_to_frequency_tag(delta)
        self.length = 0
        self.timedomain = None
        self.time = None
        self.time_bounds = None
        self.time_tracker = None

        # instantiate attributes to hold spatial information
        self.spacedomain = None

        # instantiate holders for file paths
        self.file = None
        self.dump_file = None

        # mapping to store record objects (keys are record names)
        self.records = {}
        # mapping to store record methods (keys are record names)
        self.methods = {}
        # mapping to store record arrays (keys are record names)
        self.arrays = {}
        # mapping for integer tracker to know where in array to write next
        # (keys are record names)
        self.array_trackers = {}

        # integers to track when to write to file
        self.trigger = None
        self.trigger_tracker = None

    def initialise(self, timedomain, spacedomain, _skip_trackers=False):
        # check delta / timedomain resolution compatibility
        if (self.delta % timedomain.timedelta) != timedelta(seconds=0):
            raise ValueError('recording timedelta incompatible '
                             'with component timedelta')

        # determine time series length for storage
        self.length = int(self.delta.total_seconds()
                          // timedomain.timedelta.total_seconds())
        # create timedomain for stream
        self.timedomain = TimeDomain.from_start_end_step(
            start=timedomain.bounds.datetime_array[0, 0],
            end=timedomain.bounds.datetime_array[-1, -1] + self.delta,
            step=self.delta,
            calendar=timedomain.calendar,
            units=timedomain.units
        )
        self.time = self.timedomain.time.array[1:]
        self.time_bounds = self.timedomain.bounds.array[:-1, :]

        # store spacedomain
        self.spacedomain = spacedomain

        # initialise record arrays for accumulating values
        self.trigger = 0
        for name in self.records:
            self.array_trackers[name] = 0
            arr = np.zeros((self.length, *spacedomain.shape), dtype_float())
            arr[:] = np.nan
            self.arrays[name] = arr
            # add on length of stream to the record trigger
            self.trigger += self.length

        if not _skip_trackers:
            # (re)initialise trackers
            self.time_tracker = 0
            self.trigger_tracker = 0

    def add_record(self, record, methods):
        name = record.name
        # store link to record object
        self.records[name] = record
        # store sequence of aggregation methods
        methods_ = set()
        for method in methods:
            if method in _methods_map:
                methods_.add(_methods_map[method])
            else:
                raise ValueError('method {} for record {} aggregation '
                                 'unknown'.format(method, name))
        self.methods[name] = methods_
        # map this very stream in the record
        record.streams.append(self)

    def update_record(self, name, value):
        self.arrays[name][self.array_trackers[name], ...] = value
        self.array_trackers[name] += 1
        self.trigger_tracker += 1
        if self.trigger_tracker == self.trigger:
            self.update_record_to_stream_file()

    def create_record_stream_file(self, filepath):
        self.file = filepath

        with Dataset(self.file, 'w') as f:
            axes = self.spacedomain.axes
            # dimension for space and time lower+upper bounds
            f.createDimension('nv', 2)
            # space coordinate dimensions and coordinate variables
            for axis in axes:
                # dimension (domain axis)
                f.createDimension(axis, len(getattr(self.spacedomain, axis)))
                # variables
                # (domain coordinate)
                coord = self.spacedomain.to_field().construct(axis)
                a = f.createVariable(axis, dtype_float(), (axis,))
                a.standard_name = coord.standard_name
                a.units = coord.units
                a.bounds = axis + '_bounds'
                a[:] = coord.array
                # (domain coordinate bounds)
                b = f.createVariable(axis + '_bounds', dtype_float(),
                                     (axis, 'nv'))
                b.units = coord.units
                b[:] = coord.bounds.array

            # time coordination dimension and coordinate variable
            f.createDimension('time', None)
            t = f.createVariable('time', np.float64, ('time',))
            t.standard_name = 'time'
            t.units = self.timedomain.units
            t.calendar = self.timedomain.calendar
            t.bounds = 'time_bounds'
            b = f.createVariable('time_bounds', np.float64, ('time', 'nv'))
            b.units = self.timedomain.units
            b.calendar = self.timedomain.calendar

            for name, record in self.records.items():
                # record variable
                for method in self.methods[name]:
                    name_method = '_'.join([name, method])
                    v = f.createVariable(name_method, dtype_float(),
                                         ('time', *axes))
                    v.standard_name = name
                    v.units = record.units
                    v.cell_methods = "time: {} over {}".format(
                        method, _delta_to_frequency_str(self.timedomain.timedelta)
                    )

    def update_record_to_stream_file(self):
        with Dataset(self.file, 'a') as f:
            time_ = self.time[self.time_tracker]
            time_bounds = self.time_bounds[self.time_tracker]
            try:
                # check whether given snapshot already in file
                t = cftime.time2index(time_, f.variables['time'])
            # will get a IndexError if time variable is empty
            # will get a ValueError if timestamp not in time variable
            except (IndexError, ValueError):
                # if not, extend time dimension
                t = len(f.variables['time'])
                f.variables['time'][t] = time_
                f.variables['time_bounds'][t] = time_bounds

            for name, array in self.arrays.items():
                for method in self.methods[name]:
                    name_method = '_'.join([name, method])

                    # proceed with required aggregation
                    if method == 'mean':
                        value = np.nanmean(array, axis=0)
                    elif method == 'sum':
                        value = np.nansum(array, axis=0)
                    elif method == 'point':
                        value = array[self.array_trackers[name] - 1]
                    elif method == 'minimum':
                        value = np.nanmin(array, axis=0)
                    elif method == 'maximum':
                        value = np.nanmax(array, axis=0)

                    # store result in file
                    f.variables[name_method][t] = np.ma.array(
                        value, mask=(~self.spacedomain.land_sea_mask
                                     if self.spacedomain.land_sea_mask
                                     is not None else None)
                    )

                # reset array tracker to point to start of array again
                self.array_trackers[name] = 0
                # reset values in array
                array[:] = np.nan
            # increment time tracker to next writing time
            self.time_tracker += 1
            # reset trigger tracker
            self.trigger_tracker = 0

    def create_record_stream_dump(self, filepath):
        self.dump_file = filepath

        with Dataset(self.dump_file, 'w') as f:
            axes = self.spacedomain.axes

            # description
            f.description = "Dump file created on {}".format(
                datetime.now().strftime('%Y-%m-%d at %H:%M:%S'))

            # dimensions
            f.createDimension('time', None)
            f.createDimension('length', self.length)
            for axis in axes:
                f.createDimension(axis, len(getattr(self.spacedomain, axis)))
            f.createDimension('nv', 2)

            # coordinate variables
            t = f.createVariable('time', np.float64, ('time',))
            t.standard_name = 'time'
            t.units = self.timedomain.units
            t.calendar = self.timedomain.calendar
            h = f.createVariable('length', np.uint32, ('length',))
            h[:] = np.arange(self.length)
            for axis in axes:
                coord = self.spacedomain.to_field().construct(axis)
                # (domain coordinate)
                a = f.createVariable(axis, dtype_float(), (axis,))
                a.standard_name = coord.standard_name
                a.units = coord.units
                a.bounds = axis + '_bounds'
                a[:] = coord.data.array
                # (domain coordinate bounds)
                b = f.createVariable(axis + '_bounds', dtype_float(),
                                     (axis, 'nv'))
                b.units = coord.units
                b[:] = coord.bounds.data.array

            # records
            for name, record in self.records.items():
                s = f.createVariable(name, dtype_float(),
                                     ('time', 'length', *axes),
                                     fill_value=9.9692099683868690E36)
                s.standard_name = name
                s.units = record.units
                f.createVariable('_'.join([name, 'tracker']), int, ('time',))

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

            for name in self.records:
                f.variables[name][t, ...] = self.arrays[name]
                f.variables['_'.join([name, 'tracker'])][t] = (
                    self.array_trackers[name]
                )
            f.variables['time_tracker'][t] = self.time_tracker
            f.variables['trigger_tracker'][t] = self.trigger_tracker

    def load_record_stream_dump(self, filepath, datetime_,
                                timedomain, spacedomain):
        self.dump_file = filepath

        with Dataset(self.dump_file, 'r') as f:
            # determine original simulation timedomain from dump start
            start = cftime.num2date(f.variables['time'][0],
                                    f.variables['time'].units,
                                    f.variables['time'].calendar)

            td = TimeDomain.from_start_end_step(
                start=start,
                end=timedomain.bounds.datetime_array[-1, -1],
                step=timedomain.timedelta,
                calendar=timedomain.calendar,
                units=timedomain.units
            )
            self.initialise(td, spacedomain, _skip_trackers=True)

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
                        '{} not available in record stream dump {}'.format(
                            datetime_, self.dump_file)
                    )

            # retrieve each record values
            for name in self.records:
                try:
                    mask = f.variables[name][t, ...].mask
                    self.arrays[name][~mask] = (
                        f.variables[name][t, ...].data[~mask]
                    )
                    self.array_trackers[name] = (
                        f.variables['_'.join([name, 'tracker'])][t]
                    )
                except KeyError:
                    raise KeyError(
                        '{} missing in record stream dump {}'.format(
                            name, self.dump_file)
                    )
            # retrieve stream trackers
            self.time_tracker = f.variables['time_tracker'][t]
            self.trigger_tracker = f.variables['trigger_tracker'][t]

        return datetime_
