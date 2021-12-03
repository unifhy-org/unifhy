import numpy as np
from datetime import datetime, timedelta
from copy import deepcopy
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
    'standard': 'gregorian',
    'gregorian': 'gregorian',
    'proleptic_gregorian': 'proleptic_gregorian',
    '365_day': '365_day',
    'noleap': '365_day',
    '366_day': '366_day',
    'all_leap': '366_day',
    '360_day': '360_day',
    'julian': 'julian'
}

_calendar_to_cftime_datetime = {
    'standard': cftime.DatetimeGregorian,
    'gregorian': cftime.DatetimeGregorian,
    'proleptic_gregorian': cftime.DatetimeProlepticGregorian,
    '365_day': cftime.DatetimeNoLeap,
    'noleap': cftime.DatetimeNoLeap,
    '366_day': cftime.DatetimeAllLeap,
    'all_leap': cftime.DatetimeAllLeap,
    '360_day': cftime.Datetime360Day,
    'julian': cftime.DatetimeJulian
}


class TimeDomain(object):
    """TimeDomain characterises a temporal dimension that is needed by a
    `Component`.
    """
    _epoch = datetime(1970, 1, 1, 0, 0, 0, 0)
    _calendar = 'gregorian'
    _units = f"seconds since {_epoch.strftime('%Y-%m-%d %H:%M:%SZ')}"
    _Units = cfunits.Units(_units, calendar=_calendar)
    _timestep_span = (0, 1)

    def __init__(self, timestamps, units, calendar=None):
        """**Instantiation**

        :Parameters:

            timestamps: one-dimensional array-like object
                The array of timestamps defining the temporal dimension.
                May be any type that can be cast to a `numpy.ndarray`.
                Must contain numerical values.

                Note: the first timestamp of the array is the beginning
                of the first timestep, and the last timestamp is the end
                of the last timestep (not its start).

                *Parameter example:* ::

                    timestamps=[0, 1, 2, 3]

                *Parameter example:* ::

                    timestamps=(5, 7, 9)

                *Parameter example:* ::

                    timestamps=numpy.arange(0, 10, 3)

            units: `str`
                Reference in time for the *timestamps* following the
                format 'unit_of_time since reference_datetime'.

                *Parameter example:* ::

                    units='seconds since 1970-01-01'

                *Parameter example:* ::

                    units='days since 2000-01-01 09:00:00'

            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, set to default value
                'gregorian'.

                *Parameter example:* ::

                    calendar='all_leap'

                *Parameter example:* ::

                    calendar='365_day'

        **Examples**

        >>> td = TimeDomain(timestamps=[0, 1, 2, 3],
        ...                 units='seconds since 1970-01-01 00:00:00',
        ...                 calendar='standard')
        >>> print(td)
        TimeDomain(
            time (3,): [1970-01-01 00:00:00, 1970-01-01 00:00:01, 1970-01-01 00:00:02] standard
            bounds (3, 2): [[1970-01-01 00:00:00, ..., 1970-01-01 00:00:03]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            period: 0:00:03
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
    def period(self):
        """Return the period that the TimeDomain is covering as a
        `datetime.timedelta`.
        """
        return (self._f.construct('time').bounds.datetime_array[-1, -1]
                - self._f.construct('time').bounds.datetime_array[0, 0])

    @property
    def timedelta(self):
        """Return the time duration separating time steps in the
        time series of the TimeDomain instance as a `datetime.timedelta`
        instance.
        """
        return (
                self._f.construct('time').bounds.datetime_array[0, 1]
                - self._f.construct('time').bounds.datetime_array[0, 0]
        )

    def _get_cf_units(self, units, calendar):
        # assign default calendar if not provided
        calendar = self._calendar if calendar is None else calendar
        # check that calendar is a classic one for CF-convention
        if calendar.lower() not in _supported_calendar_mapping:
            raise ValueError(
                f"calendar '{calendar}' is not supported"
            )

        # get a cf.Units instance from units and calendar
        units = cfunits.Units(units, calendar=calendar)

        if not (units.isvalid and units.isreftime):
            raise ValueError("reference time not valid, format 'unit_of_time "
                             "since reference_datetime' expected")

        return units

    @staticmethod
    def _check_dimension_regularity(dimension):
        time_diff = np.diff(dimension)
        if time_diff.size == 0:
            raise RuntimeError("timestamps sequence must contain 2 items "
                               "or more")
        if np.amin(time_diff) != np.amax(time_diff):
            raise RuntimeError("timestep in sequence not constant "
                               "across period")

    def _set_time(self, timestamps, span):
        # convert timestamps to np.array if not already
        timestamps = np.asarray(timestamps)
        if not timestamps.ndim == 1:
            raise ValueError(
                "timestamps array provided is not uni-dimensional"
            )

        if not np.issubdtype(timestamps.dtype, np.number):
            raise TypeError(
                "items in timestamps array must be numerical"
            )

        # check that the timestamps is regularly spaced
        self._check_dimension_regularity(timestamps)

        # determine the timedelta between timestamps
        delta = timestamps[1] - timestamps[0]

        # eliminate last timestamp (because it is end of last time step)
        timestamps = timestamps[0:-1]

        # generate bounds from span and timedelta
        bounds = np.zeros((len(timestamps), 2), dtype=timestamps.dtype)
        bounds[:, 0] = timestamps + span[0] * delta
        bounds[:, 1] = timestamps + span[1] * delta

        # add the timestamps
        self._f.domain_axis('time').set_size(len(timestamps))
        self._f.construct('time').set_data(cf.Data(timestamps))
        self._f.construct('time').set_bounds(cf.Bounds(data=cf.Data(bounds)))

    @classmethod
    def _extract_time_from_field(cls, field):
        # check construct
        if not field.has_construct('time'):
            raise RuntimeError("no 'time' construct found in field")
        t = field.construct('time')
        cls._check_dimension_regularity(t.array)
        if not field.construct('time').has_bounds():
            raise RuntimeError("no 'time' bounds found in field")
        t_bnds = field.construct('time').bounds
        cls._check_dimension_regularity(t_bnds.array[:, 0])
        cls._check_dimension_regularity(t_bnds.array[:, 1])

        if not t.has_property('units'):
            raise RuntimeError("no 'units' property in field")
        if not t.has_property('calendar'):
            raise RuntimeError("no 'calendar' property in field")

        return {
            'start': t_bnds.datetime_array[0, 0],
            'end': t_bnds.datetime_array[-1, -1],
            'step': t.datetime_array[1] - t.datetime_array[0],
            'units': t.units,
            'calendar': t.calendar
        }

    def __str__(self):
        return "\n".join(
            ["TimeDomain("]
            + [f"    time {self.time.shape}: {self.time}"]
            + [f"    bounds {self.bounds.shape}: {self.bounds}"]
            + [f"    calendar: {self.calendar}"]
            + [f"    units: {self.units}"]
            + [f"    period: {self.period}"]
            + [f"    timedelta: {self.timedelta}"]
            + [")"]
        )

    def __eq__(self, other):
        """Compare equality between the TimeDomain and another instance
        of TimeDomain.

        Their time dimension, their bounds, their units, and their
        calendars are compared against one another.
        """

        if isinstance(other, self.__class__):
            return self.is_time_equal_to(other._f)
        else:
            raise TypeError(
                f"{self.__class__.__name__} cannot be compared "
                f"to {other.__class__.__name__}"
            )

    def __ne__(self, other):
        """Compare inequality between the TimeDomain and another
        instance of TimeDomain.

        Their time dimension, their bounds, their units, and their
        calendars are compared against one another.
        """

        return not self.__eq__(other)

    def is_time_equal_to(self, field, ignore_bounds=True,
                         _leading_truncation_idx=None,
                         _trailing_truncation_idx=None):
        """Compare equality between the TimeDomain and the 'time'
        dimension  coordinate in a `cf.Field`.

        The time dimension, the bounds, the units, and the calendar
        of the field are compared against those of the TimeDomain.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against TimeDomain.

            ignore_bounds: `bool`, optional
                Option to ignore the time bounds in the comparison. If
                not provided, set to default value `True` (i.e. bounds
                are ignored in the comparison).

        :Returns: `bool`
        """
        # check that the field has a time construct
        if field.dim('time', default=None) is None:
            return RuntimeError(
                f"{field.__class__.__name__} cannot be compared to "
                f"{self.__class__.__name__} because no time construct"
            )

        # check that field calendar is a classic one for CF-convention
        if hasattr(field.dim('time'), 'calendar'):
            if (field.dim('time').calendar.lower()
                    not in _supported_calendar_mapping):
                raise ValueError(
                    f"{field.__class__.__name__} calendar "
                    f"'{field.dim('time').calendar}' is not supported"
                )
        else:
            field.dim('time').calendar = 'gregorian'

        # map alternative names for given calendar to same name
        self_calendar = _supported_calendar_mapping[
            self._f.dim('time').calendar.lower()
        ]
        field_calendar = _supported_calendar_mapping[
            field.dim('time').calendar.lower()
        ]

        # check that the two instances have the same calendar
        if not self_calendar == field_calendar:
            raise ValueError(
                f"{field.__class__.__name__} cannot be compared to "
                f"{self.__class__.__name__} due to different calendars"
            )

        # check that the two instances have the same time series length
        leading_size = (_trailing_truncation_idx if _leading_truncation_idx
                        else 0)
        trailing_size = (-_trailing_truncation_idx if _trailing_truncation_idx
                         else 0)
        if not (self.time.size - leading_size - trailing_size ==
                field.dim('time').data.size):
            return False

        # check that the time data and time bounds data are equal
        # (__eq__ operator on cf.Data for reference time units will
        # convert data with different reftime as long as they are in
        # the same calendar)
        time_match = (
            self.time[_leading_truncation_idx:_trailing_truncation_idx] ==
            field.dim('time').data
        )

        if ignore_bounds:
            bounds_match = cf.Data([True])
        else:
            bounds_match = (
                self.bounds[_leading_truncation_idx:_trailing_truncation_idx] ==
                field.dim('time').bounds.data
            )

        # use a trick by checking the minimum value of the boolean arrays
        # (False if any value is False, i.e. at least one value is not equal
        # in the time series) and by squeezing the data to get a single boolean
        return (
            time_match.minimum(squeeze=True).array.item()
            and bounds_match.minimum(squeeze=True).array.item()
        )

    def spans_same_period_as(self, timedomain):
        """Compare equality in period spanned between the TimeDomain
        and another instance of TimeDomain.

        The lower bound of their first timestamps and the upper bound of
        their last timestamps are compared.

        :Parameters:

            timedomain: `TimeDomain`
                The other TimeDomain to be compared against TimeDomain.

        :Returns: `bool`
        """
        if isinstance(timedomain, self.__class__):
            start = self.bounds[[0], [0]] == timedomain.bounds[[0], [0]]
            end = self.bounds[[-1], [-1]] == timedomain.bounds[[-1], [-1]]

            return start.array.item() and end.array.item()
        else:
            raise TypeError(
                f"{self.__class__.__name__} instance cannot be compared "
                f"to {timedomain.__class__.__name__}"
            )

    def subset_and_compare(self, field):
        error = RuntimeError(
            f"field not compatible with {self.__class__.__name__}"
        )

        # try to subset in time
        kwargs = {
            'time': cf.wi(*self.time.datetime_array[[0, -1]])
        }
        if field.subspace('test', **kwargs):
            field_subset = field.subspace(**kwargs)
        else:
            raise error

        # check that data and component timedomains are compatible
        if not self.is_time_equal_to(field_subset):
            raise error

        return field_subset

    @classmethod
    def from_datetime_sequence(cls, datetimes, units=None, calendar=None):
        """Instantiate a `TimeDomain` from a sequence of datetime objects.

        :Parameters:

            datetimes: one-dimensional array-like object
                The array of datetime objects defining the temporal
                dimension. May be any type that can be cast to a
                `numpy.ndarray`. Must contain datetime objects (i.e.
                `datetime.datetime`, `cftime.datetime`,
                `numpy.datetime64`).

                Note: the first datetime of the array is the beginning
                of the first timestep, and the last datetime is the end
                of the last timestep (not its start).

                *Parameter example:* ::

                    datetimes=[datetime.datetime(1970, 1, 1, 0, 0, 1),
                               datetime.datetime(1970, 1, 1, 0, 0, 2),
                               datetime.datetime(1970, 1, 1, 0, 0, 3),
                               datetime.datetime(1970, 1, 1, 0, 0, 4)]

                *Parameter example:* ::

                    datetimes=(cftime.DatetimeAllLeap(2000, 1, 6),
                               cftime.DatetimeAllLeap(2000, 1, 8),
                               cftime.DatetimeAllLeap(2000, 1, 10))

                *Parameter example:* ::

                    datetimes=numpy.arange(
                        numpy.datetime64('1970-01-01 09:00:00'),
                        numpy.datetime64('1970-01-11 09:00:00'),
                        datetime.timedelta(days=3)
                    )

            units: `str`, optional
                Reference in time for the *timestamps* that will be
                generated, following the format 'unit_of_time since
                reference_datetime'. If not provided, set to default
                value 'seconds since 1970-01-01 00:00:00Z'.

                *Parameter example:* ::

                    units='seconds since 1970-01-01'

                *Parameter example:* ::

                    units='days since 2000-01-01 00:00:00'


            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, inference from datetime object
                is attempted on the 'calendar' attribute (if it exists)
                of the first item in *datetimes*, otherwise set to
                default 'gregorian'.

                *Parameter example:* ::

                    calendar='all_leap'

                *Parameter example:* ::

                    calendar='365_day'

        :Returns: `TimeDomain`

        **Examples**

        >>> from datetime import datetime
        >>> td = TimeDomain.from_datetime_sequence(
        ...     datetimes=[datetime(1970, 1, 1), datetime(1970, 1, 2),
        ...                datetime(1970, 1, 3), datetime(1970, 1, 4)],
        ...     units='seconds since 1970-01-01 00:00:00',
        ...     calendar='standard'
        ... )
        >>> print(td)
        TimeDomain(
            time (3,): [1970-01-01 00:00:00, 1970-01-02 00:00:00, 1970-01-03 00:00:00] standard
            bounds (3, 2): [[1970-01-01 00:00:00, ..., 1970-01-04 00:00:00]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            period: 3 days, 0:00:00
            timedelta: 1 day, 0:00:00
        )
        """

        # convert datetimes to np.array if not already one
        datetimes = np.asarray(datetimes)
        # check that datetimes sequence contains datetime objects
        if (not np.issubdtype(datetimes.dtype, np.dtype(datetime)) and
                not np.issubdtype(datetimes.dtype, np.dtype('datetime64'))):
            raise TypeError(
                "datetime sequence given does not contain datetime objects"
            )
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
        """Instantiate a `TimeDomain` from start, end, and step for period.

        :Parameters:

            start: datetime object
                The start of the sequence to be generated for the
                initialisation of the `TimeDomain`. Must be any datetime
                object (except `numpy.datetime64`).

                Note: this is the start of the first timestep.

                *Parameter example:* ::

                    start=datetime.datetime(1970, 1, 1, 9, 0, 0)

                *Parameter example:* ::

                    start=cftime.DatetimeAllLeap(2000, 1, 6)

            end: datetime object
                The end of the sequence to be generated for the
                initialisation of the `TimeDomain`. Must be any datetime
                object (except `numpy.datetime64`).

                Note: this is the end of the last timestep (not its
                start).

                *Parameter example:* ::

                    end=datetime.datetime(1970, 1, 1, 0, 0, 4)

                *Parameter example:* ::

                    end=cftime.DatetimeAllLeap(2000, 1, 10)

            step: timedelta object
                The step separating items in the sequence to be
                generated for the initialisation of the `TimeDomain`.
                Must be `datetime.timedelta` object.

                *Parameter example:* ::

                    step=datetime.timedelta(seconds=1)

                *Parameter example:* ::

                    step=datetime.timedelta(days=1)

            units: `str`, optional
                Reference in time for the *timestamps* that will be
                generated. Must follow the format 'unit_of_time since
                reference_datetime'. If not provided, set to default
                value 'seconds since 1970-01-01 00:00:00Z'.

                *Parameter example:* ::

                    units='seconds since 1970-01-01'

                *Parameter example:* ::

                    units='days since 2000-01-01 00:00:00'

            calendar: `str`, optional
                Calendar to be used for the reference in time of
                *units*. If not provided, set to default 'gregorian'.

                *Parameter example:* ::

                    calendar='standard'

                *Parameter example:* ::

                    calendar='all_leap'

        :Returns: `TimeDomain`

        **Examples**

        >>> from datetime import datetime, timedelta
        >>> td = TimeDomain.from_start_end_step(
        ...     start=datetime(2020, 1, 1),
        ...     end=datetime(2020, 3, 1),
        ...     step=timedelta(days=1),
        ...     units='seconds since 1970-01-01 00:00:00',
        ...     calendar='standard'
        ... )
        >>> print(td)
        TimeDomain(
            time (60,): [2020-01-01 00:00:00, ..., 2020-02-29 00:00:00] standard
            bounds (60, 2): [[2020-01-01 00:00:00, ..., 2020-03-01 00:00:00]] standard
            calendar: standard
            units: seconds since 1970-01-01 00:00:00
            period: 60 days, 0:00:00
            timedelta: 1 day, 0:00:00
        )

        >>> from datetime import datetime, timedelta
        >>> td = TimeDomain.from_start_end_step(
        ...     start=datetime(2020, 1, 1),
        ...     end=datetime(2020, 3, 1),
        ...     step=timedelta(days=1),
        ...     units='seconds since 1970-01-01 00:00:00',
        ...     calendar='noleap'
        ... )
        >>> print(td)
        TimeDomain(
            time (59,): [2020-01-01 00:00:00, ..., 2020-02-28 00:00:00] noleap
            bounds (59, 2): [[2020-01-01 00:00:00, ..., 2020-03-01 00:00:00]] noleap
            calendar: noleap
            units: seconds since 1970-01-01 00:00:00
            period: 59 days, 0:00:00
            timedelta: 1 day, 0:00:00
        )

        """
        if not isinstance(start, (datetime, cftime.datetime)):
            raise TypeError(
                "start date must be of type datetime.datetime or cftime.datetime"
            )
        if not isinstance(end, (datetime, cftime.datetime)):
            raise TypeError(
                "end date must be of type datetime.datetime or cftime.datetime"
            )
        if not isinstance(step, timedelta):
            raise TypeError("step must be of type datetime.timedelta")

        if start >= end:
            raise ValueError("end date is not later than start date")

        # convert datetimes to expected calendar before generating sequence
        if calendar is not None:
            start = _calendar_to_cftime_datetime[calendar](
                start.year, start.month, start.day,
                start.hour, start.minute, start.second, start.microsecond)
            end = _calendar_to_cftime_datetime[calendar](
                end.year, end.month, end.day,
                end.hour, end.minute, end.second, end.microsecond)

        # determine whole number of timesteps to loop over
        (divisor, remainder) = divmod(int((end - start).total_seconds()),
                                      int(step.total_seconds()))

        # generate sequence of datetimes
        datetimes = [start + timedelta(seconds=td * step.total_seconds())
                     for td in range(divisor + 1)]

        return cls.from_datetime_sequence(np.asarray(datetimes),
                                          units, calendar)

    @classmethod
    def from_field(cls, field):
        """Instantiate a `TimeDomain` from temporal dimension coordinate
        of a `cf.Field`.

        :Parameters:

            field: `cf.Field`
                The field object that will be used to initialise a
                `TimeDomain` instance. This field must feature a 'time'
                construct with bounds, and this construct must feature
                'units' and 'calendar' properties.

        :Returns: `TimeDomain`

        **Examples**

        >>> import cf
        >>> f = cf.Field()
        >>> d = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'time',
        ...                     'units': 'days since 1970-01-01',
        ...                     'calendar': 'gregorian',
        ...                     'axis': 'T'},
        ...         data=cf.Data([0, 1, 2, 3]),
        ...         bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2],
        ...                                        [2, 3], [3, 4]]))
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
            period: 4 days, 0:00:00
            timedelta: 1 day, 0:00:00
        )

        """
        return cls.from_start_end_step(**cls._extract_time_from_field(field))

    def to_field(self):
        """Return a deep copy of the inner `cf.Field` used to
        characterise the TimeDomain.

        **Examples**
        >>> td = TimeDomain.from_start_end_step(
        ...     start=datetime(2020, 1, 1),
        ...     end=datetime(2020, 3, 1),
        ...     step=timedelta(days=1)
        ... )
        >>> f = td.to_field()
        >>> td_ = TimeDomain.from_field(f)
        >>> td == td_
        True

        """
        return deepcopy(self._f)

    @classmethod
    def from_config(cls, cfg):
        for required_key in ['start', 'end', 'step']:
            if required_key not in cfg:
                raise KeyError(
                    f"no {required_key} property of time found in configuration"
                )
        return cls.from_start_end_step(
            start=datetime.strptime(str(cfg['start']), '%Y-%m-%d %H:%M:%S'),
            end=datetime.strptime(str(cfg['end']), '%Y-%m-%d %H:%M:%S'),
            step=cfg['step'],
            units=cfg['units'] if 'units' in cfg else None,
            calendar=cfg['calendar'] if 'calendar' in cfg else None
        )

    def to_config(self):
        t_bnds = self.bounds.datetime_array
        return {
            'start': t_bnds[0, 0].strftime('%Y-%m-%d %H:%M:%S'),
            'end': t_bnds[-1, -1].strftime('%Y-%m-%d %H:%M:%S'),
            'step': self.timedelta,
            'units': self.units,
            'calendar': self.calendar
        }
