import numpy as np
from datetime import datetime, timedelta


class TimeFrame(object):
    """
    Class to handle temporal considerations
    (note: assumes everything is UTC for now).
    """

    _epoch = datetime(1970, 1, 1, 0, 0, 0)

    def __init__(self, timestamps):

        self.timestamps = timestamps

    def __eq__(self, other):

        return np.array_equal(self.timestamps, other.timestamps)

    @classmethod
    def from_sequence(cls, sequence, reference=None, check=True):

        if isinstance(sequence, (list, tuple)):
            sequence = np.asarray(sequence)

        if np.issubdtype(sequence.dtype, np.dtype(datetime)):
            timestamps = cls._convert_datetimes_to_timestamps(
                sequence.astype('datetime64'), cls._epoch)
        elif np.issubdtype(sequence.dtype, np.dtype('datetime64')):
            timestamps = cls._convert_datetimes_to_timestamps(sequence, cls._epoch)
        elif np.issubdtype(sequence.dtype, np.number):
            if not reference:
                timestamps = sequence
            elif not isinstance(reference, datetime):
                raise TypeError("Error when initialising a TimeFrame from "
                                "sequence: if a reference is given, it must "
                                "be a datetime object.")
            elif reference == cls._epoch:
                timestamps = sequence
            else:
                timestamps = cls._shift_timestamps_reference(
                    sequence, reference, cls._epoch)
        else:
            raise TypeError("The values contained in the sequence are neither "
                            "of DateTime nor numerical type.")

        if check:
            cls._check_timestep_consistency(timestamps)

        return cls(timestamps)

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

        sequence = [start + timedelta(seconds=td * step.total_seconds())
                    for td in range(divisor + 1)]

        return cls.from_sequence(np.asarray(sequence), check=False)

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

    def as_datetime_sequence(self):

        return self._convert_timestamps_to_datetimes(
            self.timestamps, reference=self._epoch)
