import numpy as np
from datetime import timedelta
from cftime import date2num
from math import gcd
from itertools import combinations

from ..time import TimeDomain


class Clock(object):

    def __init__(self, timedomains):
        self.categories = tuple(timedomains)
        self.timedomains = timedomains
        # check time compatibility between components
        supermesh_delta, supermesh_length, supermesh_step = (
            self._check_timedomain_compatibilities(timedomains)
        )

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self.switches = {}
        self.increments = {}

        steps = {c: timedomains[c].timedelta.total_seconds()
                 for c in self.categories}

        for category in timedomains:
            self.switches[category] = np.zeros((supermesh_length,), dtype=bool)
            increment = int(steps[category] // supermesh_step)
            self.switches[category][increment - 1::increment] = True
            self.increments[category] = increment

        # determine model states minimum dumping delta and set initial dump
        self.switches['dumping'] = np.zeros((supermesh_length,), dtype=bool)
        self.min_dumping_step = max(steps.values())
        # set as a minimum requirement one dump for the initial conditions
        self.switches['dumping'][0] = True

        # generate a TimeDomain for the Clock
        start_datetime = (
            timedomains[self.categories[0]].bounds.datetime_array[0, 0]
        )
        end_datetime = (
            timedomains[self.categories[0]].bounds.datetime_array[-1, -1]
        )

        self.timedomain = TimeDomain.from_start_end_step(
            start_datetime, end_datetime, supermesh_delta
        )

        # set some time attributes
        self.timedelta = supermesh_delta
        self.length = supermesh_length
        self.start_timeindex = 0
        self.end_timeindex = supermesh_length - 1

        # initialise 'iterable' time attributes to the point in time just
        # prior the actual specified start of the supermesh because the
        # iterator needs to increment in time prior indexing the switches
        self._current_datetime = start_datetime - supermesh_delta
        self._current_timeindex = self.start_timeindex - 1

    @staticmethod
    def _check_timedomain_compatibilities(timedomains):
        """**Examples:**

        >>> from datetime import datetime, timedelta
        >>> td_sl = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=1)
        ... )
        >>> td_ss = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=2)
        ... )
        >>> td_ow = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=6)
        ... )
        >>> Clock._check_timedomain_compatibilities(
        ...     {'surfacelayer': td_sl, 'subsurface': td_ss, 'openwater': td_ow}
        ... )
        (datetime.timedelta(days=1), 24, 86400.0)

        >>> td_sl = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=1)
        ... )
        >>> td_ss = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 13), timedelta(days=2)
        ... )
        >>> td_ow = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=6)
        ... )
        >>> Clock._check_timedomain_compatibilities(
        ...     {'surfacelayer': td_sl, 'subsurface': td_ss, 'openwater': td_ow}
        ... )
        Traceback (most recent call last):
            ...
        ValueError: timedomains of components surfacelayer and subsurface do not span same period

        >>> td_sl = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=1)
        ... )
        >>> td_ss = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=2)
        ... )
        >>> td_ow = TimeDomain.from_start_end_step(
        ...     datetime(2000, 1, 1), datetime(2000, 1, 25), timedelta(days=3)
        ... )
        >>> Clock._check_timedomain_compatibilities(
        ...     {'surfacelayer': td_sl, 'subsurface': td_ss, 'openwater': td_ow}
        ... )
        Traceback (most recent call last):
            ...
        ValueError: timedomains of components openwater and subsurface are not integer multiple of one another
        """
        # checks on each pair of components
        for c1, c2 in combinations(timedomains, 2):
            # check that components' timedomains start/end on same datetime
            if not timedomains[c1].spans_same_period_as(timedomains[c2]):
                raise ValueError(
                    f"timedomains of components {c1} and {c2} "
                    f"do not span same period"
                )

            # check that components' resolutions are integer multiples
            if timedomains[c1].timedelta < timedomains[c2].timedelta:
                c1, c2 = c2, c1
            if not (timedomains[c1].timedelta.total_seconds()
                    % timedomains[c2].timedelta.total_seconds()) == 0:
                raise ValueError(
                    f"timedomains of components {c1} and {c2} "
                    f"are not integer multiple of one another"
                )

        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        delta = min(
            *[timedomains[cat].timedelta for cat in timedomains]
        )
        length = max(
            *[timedomains[cat].time.size for cat in timedomains]
        )
        step = delta.total_seconds()

        return delta, length, step

    @staticmethod
    def _lcm_timedelta(timedelta_a, timedelta_b):
        a = int(timedelta_a.total_seconds())
        b = int(timedelta_b.total_seconds())
        lcm = a * b // gcd(a, b)
        return timedelta(seconds=lcm)

    def set_dumping_frequency(self, dumping_frequency):
        # check that dumpy frequency is a multiple of dumping delta
        dumping_step = dumping_frequency.total_seconds()
        if not dumping_step % self.min_dumping_step == 0:
            raise ValueError(
                f"dumping frequency ({dumping_step}s) is not a multiple integer "
                f"of smallest common multiple across components' "
                f"timedomains ({self.min_dumping_step}s)."
            )

        # get boolean arrays (switches) to determine when to dump the
        # component states on temporal supermesh
        dumping_increment = int(dumping_step // self.timedelta.total_seconds())
        self.switches['dumping'][0::dumping_increment] = True

    def get_current_datetime(self):
        return self._current_datetime

    def get_current_timestamp(self):
        return date2num(self._current_datetime, self.timedomain.units,
                        self.timedomain.calendar)

    def get_current_timeindex(self, category):
        return self._current_timeindex // self.increments[category]

    def __iter__(self):
        return self

    def __next__(self):
        # loop until it hits to last index (because the last index
        # corresponds to the start of the last timestep)
        if self._current_timeindex < self.end_timeindex:
            self._current_timeindex += 1
            index = self._current_timeindex
            self._current_datetime += self.timedelta

            return (
                *(self.switches[cat][index] for cat in self.categories),
                self.switches['dumping'][index]
            )
        else:
            raise StopIteration

