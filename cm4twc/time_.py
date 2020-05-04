import numpy as np
from datetime import datetime, timedelta
import cf
import cftime
import cfunits


# dictionary of supported calendar names (i.e. classic in CF-convention sense):
# - keys provide list of supported calendars,
# - key-to-value provides mapping allowing for aliases to point to the
#   same arbitrarily chosen name
# note: 'none' calendar is not supported, unlike CF-convention, because you
# cannot yield a datetime_array from it
_supported_calendar_mapping = {
    'standard': 'standard',
    'gregorian': 'standard',
    'proleptic_gregorian': 'proleptic_gregorian',
    '365_day': '365_day',
    'noleap': '365_day',
    '366_day': '366_day',
    'all_leap': '366_day',
    '360_day': '360_day',
    'julian': 'julian'
}


class TimeDomain(cf.Field):
    """
    Class to define a temporal dimension to be given to a Component.
    The first datetime (timestamp) of the sequence is the beginning of the
    first Component timestep, and the last datetime (timestamp) is the end of
    the last timestep (not its start). The `timedelta` attribute corresponds
    to the length of a timestep (i.e. the gap between two consecutive datetimes
    in the sequence.
    """

    _epoch = datetime(1970, 1, 1, 0, 0, 0, 0)
    _calendar = 'gregorian'
    _units = 'seconds since {}'.format(_epoch.strftime("%Y-%m-%d %H:%M:%SZ"))
    _Units = cfunits.Units(_units, calendar=_calendar)

    def __init__(self, timestamps, units, calendar=_calendar):

        super(TimeDomain, self).__init__()

        # check that calendar is a classic one for CF-convention
        if calendar.lower() not in _supported_calendar_mapping:
            raise ValueError(
                "The calendar '{}' is not supported.".format(calendar))

        # check that timestamps is a sequence and get it as an array
        timestamps = self._issequence(timestamps)

        # get a cf.Units instance from units (and calendar if necessary)
        if np.issubdtype(timestamps.dtype, np.number):
            if isinstance(units, str):
                units = cfunits.Units(units, calendar=calendar)
            elif isinstance(units, cfunits.Units):
                units = units
            else:
                raise TypeError(
                    "Error when initialising a {} from a sequence of "
                    "timestamps: the units must be an instance of "
                    "cfunits.Units or a string.".format(
                        self.__class__.__name__))

            if not (units.isvalid and units.isreftime):
                raise ValueError(
                    "Error when initialising a {} from a sequence of "
                    "timestamps: the reference time is not valid, it must "
                    "comply with the format 'unit_of_time since "
                    "reference_datetime'.".format(self.__class__.__name__))
        else:
            raise TypeError("Error when initialising a {} from a sequence of "
                            "timestamps: the values contained in the sequence "
                            "must be numerical.")

        # check that the time series is regularly spaced
        self._check_timestep_consistency(timestamps)

        # define the time construct of the cf.Field
        axis = self.set_construct(cf.DomainAxis(len(timestamps)))
        self.set_construct(
            cf.DimensionCoordinate(
                properties={'standard_name': 'time',
                            'units': units.units,
                            'calendar': units.calendar,
                            'axis': 'T'},
                data=cf.Data(timestamps)),
            axes=axis
        )

        # determine timedelta
        self.timedelta = (
                self.construct('time').datetime_array[1] -
                self.construct('time').datetime_array[0]
        )

    def __eq__(self, other):

        if isinstance(other, TimeDomain):
            return self.is_time_equal_to(other)
        else:
            raise TypeError("The {} instance cannot be compared to "
                            "a {} instance.".format(self.__class__.__name__,
                                                    other.__class__.__name__))

    def __ne__(self, other):

        return not self.__eq__(other)

    def is_time_equal_to(self, variable, _leading_truncation_idx=None,
                         _trailing_truncation_idx=None):

        # check that the variable has a time construct
        if variable.construct('time', default=None) is None:
            return RuntimeError(
                "The {} instance cannot be compared to a {} instance because "
                "it does not feature a 'time' construct.".format(
                    variable.__class__.__name__, self.__class__.__name__))

        # check that variable calendar is a classic one for CF-convention
        if variable.construct('time').calendar.lower() \
                not in _supported_calendar_mapping:
            raise ValueError("The calendar '{}' of the {} instance is not "
                             "supported.".format(variable.calendar,
                                                 variable.__class__.__name__))

        # map alternative names for given calendar to same name
        self_calendar = _supported_calendar_mapping[
            self.construct('time').calendar.lower()
        ]
        variable_calendar = _supported_calendar_mapping[
            variable.construct('time').calendar.lower()
        ]

        # check that the two instances have the same calendar
        if not self_calendar == variable_calendar:
            raise ValueError(
                "The {} instance cannot be compared to a {} instance because "
                "they do not have the same calendar.".format(
                    variable.__class__.__name__, self.__class__.__name__))

        # check that the two instances have the same time series length
        leading_size = _trailing_truncation_idx if _leading_truncation_idx else 0
        trailing_size = - _trailing_truncation_idx if _trailing_truncation_idx else 0
        if not (self.construct('time').data.size -
                leading_size - trailing_size ==
                variable.construct('time').data.size):
            return False

        # check that the time data are equal (__eq__ operator on cf.Data for
        # reference time units will convert data with different reftime as long
        # as they are in the same calendar)
        match = self.construct('time').data[_leading_truncation_idx:
                                            _trailing_truncation_idx] == \
            variable.construct('time').data

        # use a trick by checking the minimum value of the boolean array
        # (False if any value is False, i.e. at least one value is not equal
        # in the time series) and by squeezing the data to get one boolean
        return match.min(squeeze=True)

    @classmethod
    def from_datetime_sequence(cls, datetimes):

        datetimes = cls._issequence(datetimes)

        if np.issubdtype(datetimes.dtype, np.dtype(datetime)):
            try:
                timestamps = cftime.date2num(datetimes, units=cls._units,
                                             calendar=datetimes[0].calendar)
                calendar = datetimes[0].calendar
            except AttributeError:
                timestamps = cftime.date2num(datetimes, units=cls._units,
                                             calendar=cls._calendar)
                calendar = cls._calendar
        elif np.issubdtype(datetimes.dtype, np.dtype('datetime64')):
            timestamps = cftime.date2num(datetimes, units=cls._units,
                                         calendar=cls._calendar)
            calendar = cls._calendar
        else:
            raise TypeError("Error when initialising a {} from sequence of "
                            "datetime objects: the sequence given does not "
                            "contain datetime objects.")

        return cls(timestamps, cls._units, calendar)

    @classmethod
    def from_start_end_step(cls, start, end, step):

        if not isinstance(start, (datetime, cftime.datetime)):
            raise TypeError("Start date must be an instance of "
                            "datetime.datetime or cftime.datetime.")
        if not isinstance(end, (datetime, cftime.datetime)):
            raise TypeError("End date must be an instance of "
                            "datetime.datetime or cftime.datetime.")
        if not isinstance(step, timedelta):
            raise TypeError("Step must be an instance of the "
                            "datetime.timedelta.")

        (divisor, remainder) = divmod(int((end - start).total_seconds()),
                                      int(step.total_seconds()))

        datetimes = [start + timedelta(seconds=td * step.total_seconds())
                     for td in range(divisor + 1)]

        return cls.from_datetime_sequence(np.asarray(datetimes))

    @classmethod
    def _issequence(cls, sequence):

        if isinstance(sequence, (list, tuple)):
            sequence = np.asarray(sequence)

        if isinstance(sequence, np.ndarray):
            if not sequence.ndim == 1:
                raise ValueError(
                    "Error when initialising a {} from sequence: the sequence "
                    "given is not unidimensional.".format(cls.__name__))
            else:
                return sequence
        else:
            raise TypeError(
                "Error when initialising a {} from sequence: the sequence "
                "given must be a list, a tuple, or a numpy.ndarray.".format(
                    cls.__name__))

    def as_datetime_array(self):

        return self.construct('time').datetime_array

    def as_string_array(self, formatting=None):

        formatting = formatting if formatting else "%Y-%m-%d %H:%M:%S"

        return np.asarray(
            [dt.strftime(format=formatting) for dt in self.as_datetime_array()]
        )

    @staticmethod
    def _check_timestep_consistency(timestamps):

        time_diff = np.diff(timestamps)
        if np.amin(time_diff) != np.amax(time_diff):
            raise RuntimeWarning("The timestep in the sequence is not "
                                 "constant across the period.")


class Clock(object):

    def __init__(self, surfacelayer_timedomain, subsurface_timedomain,
                 openwater_timedomain):

        # check that the time domains have the same start and the same end
        match = (surfacelayer_timedomain.construct('time').data[[0, -1]] ==
                 subsurface_timedomain.construct('time').data[[0, -1]]) * \
                (surfacelayer_timedomain.construct('time').data[[0, -1]] ==
                 openwater_timedomain.construct('time').data[[0, -1]])
        if not match.min(squeeze=True):
            raise RuntimeError(
                "The three {}s for the three components do not feature the "
                "same start and/or end.".format(TimeDomain.__name__))

        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        supermesh_timedelta = min(
            surfacelayer_timedomain.timedelta,
            subsurface_timedomain.timedelta,
            openwater_timedomain.timedelta
        )
        supermesh_length = max(
            surfacelayer_timedomain.construct('time').data.size,
            subsurface_timedomain.construct('time').data.size,
            openwater_timedomain.construct('time').data.size
        )
        supermesh_timestep = supermesh_timedelta.total_seconds()

        # check that all timesteps are multiple integers of the supermesh step
        surfacelayer_timedomain_timestep = \
            surfacelayer_timedomain.timedelta.total_seconds()
        if not surfacelayer_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the surfacelayer component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(surfacelayer_timedomain_timestep,
                                supermesh_timestep))
        subsurface_timedomain_timestep = \
            subsurface_timedomain.timedelta.total_seconds()
        if not subsurface_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the subsurface component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(subsurface_timedomain_timestep,
                                supermesh_timestep))
        openwater_timedomain_timestep = \
            openwater_timedomain.timedelta.total_seconds()
        if not openwater_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the openwater component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(openwater_timedomain_timestep,
                                supermesh_timestep))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self._surfacelayer_switch = np.zeros((supermesh_length,), dtype=bool)
        surfacelayer_increment = \
            int(surfacelayer_timedomain_timestep // supermesh_timestep)
        self._surfacelayer_switch[0::surfacelayer_increment] = True
        self._surfacelayer_index_multiple = surfacelayer_increment

        self._subsurface_switch = np.zeros((supermesh_length,), dtype=bool)
        subsurface_increment = \
            int(subsurface_timedomain_timestep // supermesh_timestep)
        self._subsurface_switch[0::subsurface_increment] = True
        self._subsurface_index_multiple = subsurface_increment

        self._openwater_switch = np.zeros((supermesh_length,), dtype=bool)
        openwater_increment = \
            int(openwater_timedomain_timestep // supermesh_timestep)
        self._openwater_switch[0::openwater_increment] = True
        self._openwater_index_multiple = openwater_increment

        # set static time attributes
        self.start_datetime = \
            surfacelayer_timedomain.construct('time').datetime_array[0]
        self.end_datetime = \
            surfacelayer_timedomain.construct('time').datetime_array[-1]
        self.timedelta = supermesh_timedelta
        self.start_timeindex = 0
        self.end_timeindex = supermesh_length - 1

        # initialise 'iterable' time attributes to the point in time just
        # prior the actual specified start of the supermesh because the
        # iterator needs to increment in time prior indexing the switches
        self._current_datetime = self.start_datetime - supermesh_timedelta
        self._current_timeindex = self.start_timeindex - 1

    def get_current_datetime(self):
        return self._current_datetime

    def get_current_timeindex(self, component_type):
        if component_type == 'surfacelayer':
            return (self._current_timeindex //
                    self._surfacelayer_index_multiple)
        if component_type == 'subsurface':
            return (self._current_timeindex //
                    self._subsurface_index_multiple)
        if component_type == 'openwater':
            return (self._current_timeindex //
                    self._openwater_index_multiple)
        else:
            raise ValueError("Cannot get current time index: unknown "
                             "component type {}.".format(component_type))

    def __iter__(self):

        return self

    def __next__(self):

        # loop until it hits the second to last index (because the last index
        # corresponds to the end of the last timestep, so that it should not
        # be used as the start of another iteration
        if self._current_timeindex < self.end_timeindex - 1:
            self._current_timeindex += 1
            self._current_datetime += self.timedelta

            switches = (
                self._surfacelayer_switch[self._current_timeindex],
                self._subsurface_switch[self._current_timeindex],
                self._openwater_switch[self._current_timeindex]
            )
            return switches
        else:
            raise StopIteration
