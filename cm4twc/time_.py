import numpy as np
from datetime import datetime, timedelta
import cf
import cfunits


class TimeDomain(cf.Field):
    """
    Class to handle temporal considerations
    (note: assumes everything is UTC for now).
    """

    _epoch = datetime(1970, 1, 1, 0, 0, 0, 0)
    _calendar = 'gregorian'
    _reftime = 'seconds since {}'.format(_epoch.strftime("%Y-%m-%d %H:%M:%SZ"))
    _units = cfunits.Units(_reftime, calendar=_calendar)

    def __init__(self, timestamps, reftime, calendar='gregorian',
                 timestep_check=True):

        super(TimeDomain, self).__init__()

        timestamps = self._issequence(timestamps)

        if np.issubdtype(timestamps.dtype, np.number):
            if not reftime:
                raise RuntimeError(
                    "Error when initialising a {} from a sequence of "
                    "timestamps: the reference time must be provided.".format(
                        self.__class__.__name__))
            elif isinstance(reftime, str):
                units = cfunits.Units(reftime, calendar=calendar)
            elif isinstance(reftime, cfunits.Units):
                units = reftime
            else:
                raise TypeError(
                    "Error when initialising a {} from a sequence of "
                    "timestamps: the reference time must be an instance of "
                    "cfunits.Units or a string.".format(
                        self.__class__.__name__))

            if not (units.isvalid and units.isreftime):
                raise ValueError(
                    "Error when initialising a {} from a sequence of "
                    "timestamps: the reference time is not valid, it must "
                    "comply with the format 'unit_of_time since date'.".format(
                        self.__class__.__name__))
        else:
            raise TypeError("Error when initialising a {} from a sequence of "
                            "timestamps: the values contained in the sequence "
                            "must be numerical.")

        if timestep_check:
            self._check_timestep_consistency(timestamps)

        axis = self.set_construct(cf.DomainAxis(len(timestamps)))
        self.set_construct(
            cf.DimensionCoordinate(
                properties={'standard_name': 'time',
                            'units': units.units,
                            'calendar': units.calendar},
                data=cf.Data(timestamps)),
            axes=axis
        )

        self.cfunits = units

    def __eq__(self, other):

        if isinstance(other, TimeDomain):
            return self.is_matched_in(other)
        else:
            raise TypeError("The {} instance cannot be compared to "
                            "a {} instance.".format(self.__class__.__name__,
                                                    other.__class__.__name__))

    def __ne__(self, other):

        return not self.__eq__(other)

    def is_matched_in(self, variable):

        return self.construct('time').equals(
            variable.construct('time', default=None),
            ignore_data_type=True)

    @classmethod
    def from_datetime_sequence(cls, datetimes, timestep_check=True):

        datetimes = cls._issequence(datetimes)

        if np.issubdtype(datetimes.dtype, np.dtype(datetime)):
            timestamps = cls._convert_datetimes_to_timestamps(
                datetimes.astype('datetime64'), cls._epoch)
        elif np.issubdtype(datetimes.dtype, np.dtype('datetime64')):
            timestamps = cls._convert_datetimes_to_timestamps(
                datetimes, cls._epoch)
        else:
            raise TypeError("Error when initialising a {} from sequence of "
                            "datetime objects: the sequence given does not "
                            "contain datetime objects.")

        if timestep_check:
            cls._check_timestep_consistency(timestamps)

        return cls(timestamps, cls._reftime, cls._calendar)

    @classmethod
    def from_start_end_step(cls, start, end, step):

        if not isinstance(start, datetime):
            try:
                start = datetime.strptime(start, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                raise ValueError("Start date given is not in a valid format: "
                                 "'{0}'.".format(start))
        if not isinstance(end, datetime):
            try:
                end = datetime.strptime(end, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                raise ValueError("End date given is not in a valid format: "
                                 "'{0}'.".format(end))

        if not isinstance(step, timedelta):
            raise ValueError("Timestep given is not an instance of the "
                             "built-in class datetime.timedelta.")

        (divisor, remainder) = divmod(int((end - start).total_seconds()),
                                      int(step.total_seconds()))

        datetimes = [start + timedelta(seconds=td * step.total_seconds())
                     for td in range(divisor + 1)]

        return cls.from_datetime_sequence(np.asarray(datetimes),
                                          timestep_check=False)

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

    def as_utc_datetime_sequence(self):

        return self._convert_timestamps_to_datetimes(
            cfunits.Units.conform(self.construct('time').array,
                                  self.cfunits,
                                  self._units),
            reference=self._epoch
        )

    def as_utc_string_sequence(self):

        return [
            s.isoformat() for s in self.as_utc_datetime_sequence()
        ]

    @staticmethod
    def _convert_datetimes_to_timestamps(datetimes, reference):

        return (datetimes - np.datetime64(reference)) / np.timedelta64(1, 's')

    @staticmethod
    def _convert_timestamps_to_datetimes(timestamps, reference):

        return np.asarray(
            [reference + timedelta(seconds=tstamp) for tstamp in timestamps],
            dtype=datetime
        )

    @staticmethod
    def _shift_timestamps_reference(timestamps, current_ref, new_ref):

        return timestamps - (new_ref - current_ref).total_seconds()

    @staticmethod
    def _check_timestep_consistency(timestamps):

        time_diff = np.diff(timestamps)
        if np.amin(time_diff) != np.amax(time_diff):
            raise RuntimeWarning("The timestep in the sequence is not constant "
                                 "across the period.")
