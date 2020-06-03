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


class TimeDomain(object):
    """TimeDomain characterises a temporal dimension that is needed by a
    `Component`.

    The first timestamp of the sequence is the beginning of the first
    Component timestep, and the last timestamp is the end of the last
    timestep (not its start). The `timedelta` attribute corresponds
    to the length of a timestep (i.e. the gap between two consecutive
    timestamps in the sequence).
    """
    _epoch = datetime(1970, 1, 1, 0, 0, 0, 0)
    _calendar = 'gregorian'
    _units = 'seconds since {}'.format(_epoch.strftime("%Y-%m-%d %H:%M:%SZ"))
    _Units = cfunits.Units(_units, calendar=_calendar)
    _timestep_span = (0, 1)

    def __init__(self, timestamps, units, calendar=None):
        """**Initialisation**

        :Parameters:

            timestamps: one-dimensional array-like object
                The array of timestamps defining the temporal dimension.
                May be any type that can be cast to a `numpy.array`.
                Must contain numerical values.

                *Parameter example:*
                    ``timestamps=[0, 1, 2, 3]``
                *Parameter example:*
                    ``timestamps=(5, 7, 9)``
                *Parameter example:*
                    ``timestamps=numpy.arange(0, 10, 3)``

            units: `str`
                Reference in time for the *timestamps* and *bounds*
                following the format 'unit_of_time since
                reference_datetime'.

                *Parameter example:*
                    ``units='seconds since 1970-01-01'``
                *Parameter example:*
                    ``units='days since 2000-01-01 00:00:00'``
                *Parameter example:*
                    ``units='days since 1970-01-01 09:00:00'``

            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, set to default value
                'gregorian'.

                *Parameter example:*
                    ``calendar='standard'``
                *Parameter example:*
                    ``calendar='all_leap'``
                *Parameter example:*
                    ``calendar='365_day'``

        **Examples**

        >>> td = TimeDomain(timestamps=[0, 1, 2, 3],
        ...                 units='seconds since 1970-01-01 00:00:00',
        ...                 calendar='standard')
        >>> print(td)
        TimeDomain(
            time (4,): [1970-01-01 00:00:00, ..., 1970-01-01 00:00:03] standard
            bounds (4, 2): [[1970-01-01 00:00:00, ..., 1970-01-01 00:00:04]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            timedelta: 0:00:01
        )
        """
        self._f = cf.Field()

        # get a cf.Units instance from units and calendar
        units = self._get_cf_units(units, calendar)

        # define the time construct of the cf.Field
        axis = self._f.set_construct(cf.DomainAxis(size=0))
        self._f.set_construct(
            cf.DimensionCoordinate(
                properties={'standard_name': 'time',
                            'units': units.units,
                            'calendar': units.calendar,
                            'axis': 'T'}),
            axes=axis
        )

        # set timestamps to construct
        self._set_time(timestamps, self._timestep_span)

    @property
    def time(self):
        """Return the time series of the TimeDomain
        instance as a `cf.Data` instance.
        """
        return self._f.construct('time').data

    @property
    def bounds(self):
        """Return the bounds of the time series of the TimeDomain
        instance as a `cf.Data` instance.
        """
        return self._f.construct('time').bounds.data

    @property
    def units(self):
        """Return the units of the time series of the TimeDomain
        instance as a `str`.
        """
        return self._f.construct('time').units

    @property
    def calendar(self):
        """Return the calendar of the time series of the TimeDomain
        instance as a `str`.
        """
        return self._f.construct('time').calendar

    @property
    def timedelta(self):
        """Return the time duration separating time steps in the
        time series of the TimeDomain instance as a `datetime.timedelta`
        instance.
        """
        return (
                self._f.construct('time').datetime_array[1] -
                self._f.construct('time').datetime_array[0]
        )

    def _get_cf_units(self, units, calendar):
        # assign default calendar if not provided
        calendar = self._calendar if calendar is None else calendar
        # check that calendar is a classic one for CF-convention
        if calendar.lower() not in _supported_calendar_mapping:
            raise ValueError(
                "The calendar '{}' is not supported.".format(calendar))

        # get a cf.Units instance from units and calendar
        units = cfunits.Units(units, calendar=calendar)

        if not (units.isvalid and units.isreftime):
            raise ValueError(
                "Error when initialising a {} from a sequence of "
                "timestamps: the reference time is not valid, it must "
                "comply with the format 'unit_of_time since "
                "reference_datetime'.".format(self.__class__.__name__))

        return units

    @staticmethod
    def _check_dimension_regularity(dimension):
        time_diff = np.diff(dimension)
        if np.amin(time_diff) != np.amax(time_diff):
            raise RuntimeWarning("The time step in the sequence is not "
                                 "constant across the period.")

    def _set_time(self, timestamps, span):
        # convert timestamps to np.array if not already
        timestamps = np.asarray(timestamps)
        if not timestamps.ndim == 1:
            raise ValueError(
                "Error when initialising a {} from a sequence of timestamps: "
                "the timestamps provided are not contained in a uni-"
                "dimensional structure.".format(self.__class__.__name__))

        if not np.issubdtype(timestamps.dtype, np.number):
            raise TypeError(
                "Error when initialising a {} from a sequence of timestamps: "
                "the values contained in the sequence must be "
                "numerical.".format(self.__class__.__name__))

        # check that the timestamps is regularly spaced
        self._check_dimension_regularity(timestamps)

        # generate bounds from span and timedelta
        bounds = np.zeros((len(timestamps), 2), dtype=timestamps.dtype)
        delta = timestamps[1] - timestamps[0]
        bounds[:, 0] = timestamps + span[0] * delta
        bounds[:, 1] = timestamps + span[1] * delta

        # add the timestamps
        self._f.domain_axis('time').set_size(len(timestamps))
        self._f.construct('time').set_data(cf.Data(timestamps))
        self._f.construct('time').set_bounds(cf.Bounds(data=cf.Data(bounds)))

    def __repr__(self):
        return "\n".join(
            ["TimeDomain("]
            + ["    time %s: %s" %
               (self.time.shape, self.time)]
            + ["    bounds %s: %s" %
               (self.bounds.shape, self.bounds)]
            + ["    calendar: %s" % self.calendar]
            + ["    units: %s" % self.units]
            + ["    timedelta: %s" % self.timedelta]
            + [")"]
        )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.is_time_equal_to(other._f)
        else:
            raise TypeError("The {} instance cannot be compared to "
                            "a {} instance.".format(self.__class__.__name__,
                                                    other.__class__.__name__))

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_time_equal_to(self, field, _leading_truncation_idx=None,
                         _trailing_truncation_idx=None):
        """
        TODO: DOCSTRING REQUIRED
        """
        # check that the field has a time construct
        if field.construct('time', default=None) is None:
            return RuntimeError(
                "The {} instance cannot be compared to a {} instance because "
                "it does not feature a 'time' construct.".format(
                    field.__class__.__name__, self.__class__.__name__))

        # check that field calendar is a classic one for CF-convention
        if (field.construct('time').calendar.lower()
                not in _supported_calendar_mapping):
            raise ValueError("The calendar '{}' of the {} instance is not "
                             "supported.".format(field.calendar,
                                                 field.__class__.__name__))

        # map alternative names for given calendar to same name
        self_calendar = _supported_calendar_mapping[
            self._f.construct('time').calendar.lower()
        ]
        field_calendar = _supported_calendar_mapping[
            field.construct('time').calendar.lower()
        ]

        # check that the two instances have the same calendar
        if not self_calendar == field_calendar:
            raise ValueError(
                "The {} instance cannot be compared to a {} instance because "
                "they do not have the same calendar.".format(
                    field.__class__.__name__, self.__class__.__name__))

        # check that the two instances have the same time series length
        leading_size = (_trailing_truncation_idx if _leading_truncation_idx
                        else 0)
        trailing_size = (-_trailing_truncation_idx if _trailing_truncation_idx
                         else 0)
        if not (self._f.construct('time').data.size -
                leading_size - trailing_size ==
                field.construct('time').data.size):
            return False

        # check that the time data and time bounds data are equal
        # (__eq__ operator on cf.Data for reference time units will
        # convert data with different reftime as long as they are in
        # the same calendar)
        match1 = (
            self._f.construct('time').data[_leading_truncation_idx:
                                           _trailing_truncation_idx] ==
            field.construct('time').data
        )

        match2 = (
            self._f.construct('time').bounds.data[_leading_truncation_idx:
                                                  _trailing_truncation_idx] ==
            field.construct('time').bounds.data
        )

        # use a trick by checking the minimum value of the boolean arrays
        # (False if any value is False, i.e. at least one value is not equal
        # in the time series) and by squeezing the data to get a single boolean
        return (
            match1.minimum(squeeze=True).array.item()
            and match2.minimum(squeeze=True).array.item()
        )

    def spans_same_period_as(self, timedomain):
        """
        TODO: DOCSTRING REQUIRED
        """
        if isinstance(timedomain, self.__class__):
            start, end = (self._f.construct('time').data[[0, -1]] ==
                          timedomain.time[[0, -1]])

            return start and end
        else:
            raise TypeError("The {} instance cannot be compared to a {} "
                            "instance.".format(self.__class__.__name__,
                                               timedomain.__class__.__name__))

    @classmethod
    def from_datetime_sequence(cls, datetimes, units=None, calendar=None):
        """Initialise a `TimeDomain` from a sequence of datetime objects.

        :Parameters:

            datetimes: one-dimensional array-like object
                The array of datetime objects defining the temporal
                dimension. May be any type that can be cast to a
                `numpy.array`. Must contain datetime objects.

                *Parameter example:*
                    ``datetimes=[datetime.datetime(1970, 1, 1, 0, 0, 1),
                                 datetime.datetime(1970, 1, 1, 0, 0, 2),
                                 datetime.datetime(1970, 1, 1, 0, 0, 3),
                                 datetime.datetime(1970, 1, 1, 0, 0, 4)]``
                *Parameter example:*
                    ``datetimes=(cftime.DatetimeAllLeap(2000, 1, 6),
                                 cftime.DatetimeAllLeap(2000, 1, 8),
                                 cftime.DatetimeAllLeap(2000, 1, 10))``
                *Parameter example:*
                    ``datetimes=numpy.arange(
                        numpy.datetime64('1970-01-01 09:00:00'),
                        numpy.datetime64('1970-01-11 09:00:00'),
                        datetime.timedelta(days=3))``

            units: `str`, optional
                Reference in time for the *timestamps* and *bounds*
                following the format 'unit_of_time since
                reference_datetime'. If not provided, set to default
                value 'seconds since 1970-01-01 00:00:00Z'.

                *Parameter example:*
                    ``units='seconds since 1970-01-01'``
                *Parameter example:*
                    ``units='days since 2000-01-01 00:00:00'``
                *Parameter example:*
                    ``units='days since 1970-01-01 09:00:00'``

            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, inference from datetime object
                is attempted on the calendar attribute (if it exists)
                of the first datetime, otherwise set to default
                'gregorian'.

                *Parameter example:*
                    ``calendar='standard'``
                *Parameter example:*
                    ``calendar='all_leap'``
                *Parameter example:*
                    ``calendar='365_day'``

        **Examples**

        >>> from datetime import datetime
        >>> td = TimeDomain.from_datetime_sequence(
        ...     datetimes=[datetime(1970, 1, 1), datetime(1970, 1, 2),
        ...                datetime(1970, 1, 3), datetime(1970, 1, 4)],
        ...     units='seconds since 1970-01-01 00:00:00',
        ...     calendar='standard')
        >>> print(td)
        TimeDomain(
            time (4,): [1970-01-01 00:00:00, ..., 1970-01-04 00:00:00] standard
            bounds (4, 2): [[1970-01-01 00:00:00, ..., 1970-01-05 00:00:00]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            timedelta: 1 day, 0:00:00
        )
        """

        # convert datetimes to np.array if not already one
        datetimes = np.asarray(datetimes)
        # check that datetimes sequence contains datetime objects
        if (not np.issubdtype(datetimes.dtype, np.dtype(datetime)) and
                not np.issubdtype(datetimes.dtype, np.dtype('datetime64'))):
            raise TypeError("Error when initialising a {} from a sequence of "
                            "datetimes: the sequence given does not contain "
                            "datetime objects.".format(cls.__name__))
        # set units to default if not given
        if units is None:
            units = cls._units
        # determine calendar if not given
        if calendar is None:
            try:
                # try to infer calendar from datetime (i.e. if cftime.datetime)
                calendar = datetimes[0].calendar
            except AttributeError:
                # set calendar to default if not given or inferred
                calendar = cls._calendar

        # convert datetime objects to numerical values (i.e. timestamps)
        timestamps = cftime.date2num(datetimes, units, calendar)

        return cls(timestamps, units, calendar)

    @classmethod
    def from_start_end_step(cls, start, end, step, units=None, calendar=None):
        """Initialise a `TimeDomain` from a sequence of datetime objects.

        :Parameters:

            start: datetime object
                The start of the sequence to be generated for the
                initialisation of the `TimeDomain`. Must be any datetime
                object (except `numpy.datetime64`).

                *Parameter example:*
                    ``start=datetime.datetime(1970, 1, 1, 0, 0, 0)``
                *Parameter example:*
                    ``start=cftime.DatetimeAllLeap(2000, 1, 6)``
                *Parameter example:*
                    ``start=datetime.datetime(1970, 1, 1, 9)``

            end: datetime object
                The end of the sequence to be generated for the
                initialisation of the `TimeDomain`. Must be any datetime
                object (except `numpy.datetime64`).

                *Parameter example:*
                    ``end=datetime.datetime(1970, 1, 1, 0, 0, 4)``
                *Parameter example:*
                    ``end=cftime.DatetimeAllLeap(2000, 1, 10)``
                *Parameter example:*
                    ``end=datetime.datetime(1970, 1, 10, 9)``

            step: timedelta object
                The step separating items in the sequence to be
                generated for the initialisation of the `TimeDomain`.
                Must be `datetime.timedelta` object.

                *Parameter example:*
                    ``step=datetime.timedelta(seconds=1)``
                *Parameter example:*
                    ``step=datetime.timedelta(days=1)``
                *Parameter example:*
                    ``step=datetime.timedelta(seconds=86400)``

            units: `str`, optional
                Reference in time for the *timestamps* and *bounds*
                that will be generated. Must follow the format
                'unit_of_time since reference_datetime'. If not
                provided, set to default value 'seconds since
                1970-01-01 00:00:00Z'.

                *Parameter example:*
                    ``units='seconds since 1970-01-01'``
                *Parameter example:*
                    ``units='days since 2000-01-01 00:00:00'``
                *Parameter example:*
                    ``units='days since 1970-01-01 09:00:00'``

            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, set to default 'gregorian'.

                *Parameter example:*
                    ``calendar='standard'``
                *Parameter example:*
                    ``calendar='all_leap'``
                *Parameter example:*
                    ``calendar='365_day'``

        **Examples**

        >>> from datetime import datetime, timedelta
        >>> td = TimeDomain.from_start_end_step(
        ...     start=datetime(1970, 1, 1),
        ...     end=datetime(1970, 1, 4),
        ...     step=timedelta(days=1),
        ...     units='seconds since 1970-01-01 00:00:00',
        ...     calendar='standard')
        >>> print(td)
        TimeDomain(
            time (4,): [1970-01-01 00:00:00, ..., 1970-01-04 00:00:00] standard
            bounds (4, 2): [[1970-01-01 00:00:00, ..., 1970-01-05 00:00:00]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            timedelta: 1 day, 0:00:00
        )

        """
        if not isinstance(start, (datetime, cftime.datetime)):
            raise TypeError("Start date must be an instance of "
                            "datetime.datetime or cftime.datetime.")
        if not isinstance(end, (datetime, cftime.datetime)):
            raise TypeError("End date must be an instance of "
                            "datetime.datetime or cftime.datetime.")
        if not isinstance(step, timedelta):
            raise TypeError("Step must be an instance of the "
                            "datetime.timedelta.")

        if start >= end:
            raise ValueError("End date is not later than start date.")

        (divisor, remainder) = divmod(int((end - start).total_seconds()),
                                      int(step.total_seconds()))

        datetimes = [start + timedelta(seconds=td * step.total_seconds())
                     for td in range(divisor + 1)]

        return cls.from_datetime_sequence(np.asarray(datetimes),
                                          units, calendar)

    @classmethod
    def from_field(cls, field):
        """Initialise a `TimeDomain` from a cf.Field instance.

        :Parameters:

            field: cf.Field object
                The field object who will be used to initialise a
                'TimeDomain` instance. This field must feature a 'time'
                construct, and this construct must feature a 'units' and
                a 'calendar' property.

        **Examples**

        >>> import cf
        >>> f = cf.Field()
        >>> d = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'time',
        ...                     'units': 'days since 1970-01-01',
        ...                     'calendar': 'gregorian',
        ...                     'axis': 'T'},
        ...         data=cf.Data([0, 1, 2, 3])
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=4))
        ... )
        >>> td = TimeDomain.from_field(f)
        >>> print(td)
        TimeDomain(
            time (4,): [1970-01-01 00:00:00, ..., 1970-01-04 00:00:00] gregorian
            bounds (4, 2): [[1970-01-01 00:00:00, ..., 1970-01-05 00:00:00]] gregorian
            calendar: gregorian
            units: days since 1970-01-01
            timedelta: 1 day, 0:00:00
        )

        """
        if not field.has_construct('time'):
            raise RuntimeError("Error when initialising a {} from a Field: no "
                               "\'time' construct found.".format(cls.__name__))
        t = field.construct('time')

        if not t.has_property('units'):
            raise RuntimeError("Error when initialising a {} from a Field: no "
                               "\'units' property for the 'time' construct "
                               "found.".format(cls.__name__))
        if not t.has_property('calendar'):
            raise RuntimeError("Error when initialising a {} from a Field: no "
                               "\'calendar' property for the 'time' construct "
                               "found.".format(cls.__name__))

        return cls(t.array, t.units, t.calendar)

    def to_field(self):
        """Return the inner cf.Field used to characterise the TimeDomain."""
        return self._f

    @classmethod
    def from_config(cls, cfg):
        for required_key in ['start', 'end', 'step']:
            if required_key not in cfg:
                raise KeyError("The {} property of time in missing in "
                               "the configuration.")
        return cls.from_start_end_step(
            start=cfg['start'], end=cfg['end'],
            step=timedelta(**cfg['step']),
            units=cfg['units'] if 'units' in cfg else None,
            calendar=cfg['units'] if 'units' in cfg else None
        )

    def to_config(self):
        dts = self.as_string_array()
        return {
            'start': dts[0],
            'end': dts[-1],
            'step': {'seconds': self.timedelta.total_seconds()},
            'units': self._f.construct('time').units,
            'calendar': self._f.construct('time').calendar
        }

    def as_datetime_array(self):
        """Return the time series characterising the period covered by
        the TimeDomain as an array of datetime objects.
        """
        return self._f.construct('time').datetime_array

    def as_string_array(self, formatting=None):
        """Return the time series characterising the period covered by
        the TimeDomain as list of datetime strings.
        """
        formatting = formatting if formatting else "%Y-%m-%d %H:%M:%S"

        return np.asarray(
            [dt.strftime(format=formatting) for dt in self.as_datetime_array()]
        )


class Clock(object):

    def __init__(self, surfacelayer_timedomain, subsurface_timedomain,
                 openwater_timedomain):
        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        supermesh_timedelta = min(
            surfacelayer_timedomain.timedelta,
            subsurface_timedomain.timedelta,
            openwater_timedomain.timedelta
        )
        supermesh_length = max(
            surfacelayer_timedomain.time.size,
            subsurface_timedomain.time.size,
            openwater_timedomain.time.data.size
        )
        supermesh_timestep = supermesh_timedelta.total_seconds()

        # check that all timesteps are multiple integers of the supermesh step
        surfacelayer_timedomain_timestep = (
            surfacelayer_timedomain.timedelta.total_seconds()
        )
        if not surfacelayer_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the surfacelayer component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(surfacelayer_timedomain_timestep,
                                supermesh_timestep))
        subsurface_timedomain_timestep = (
            subsurface_timedomain.timedelta.total_seconds()
        )
        if not subsurface_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the subsurface component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(subsurface_timedomain_timestep,
                                supermesh_timestep))
        openwater_timedomain_timestep = (
            openwater_timedomain.timedelta.total_seconds()
        )
        if not openwater_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the openwater component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(openwater_timedomain_timestep,
                                supermesh_timestep))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self._surfacelayer_switch = np.zeros((supermesh_length,), dtype=bool)
        surfacelayer_increment = (
            int(surfacelayer_timedomain_timestep // supermesh_timestep)
        )
        self._surfacelayer_switch[0::surfacelayer_increment] = True
        self._surfacelayer_index_multiple = surfacelayer_increment

        self._subsurface_switch = np.zeros((supermesh_length,), dtype=bool)
        subsurface_increment = (
            int(subsurface_timedomain_timestep // supermesh_timestep)
        )
        self._subsurface_switch[0::subsurface_increment] = True
        self._subsurface_index_multiple = subsurface_increment

        self._openwater_switch = np.zeros((supermesh_length,), dtype=bool)
        openwater_increment = (
            int(openwater_timedomain_timestep // supermesh_timestep)
        )
        self._openwater_switch[0::openwater_increment] = True
        self._openwater_index_multiple = openwater_increment

        # set static time attributes
        self.start_datetime = (
            surfacelayer_timedomain.time.datetime_array[0]
        )
        self.end_datetime = (
            surfacelayer_timedomain.time.datetime_array[-1]
        )
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
