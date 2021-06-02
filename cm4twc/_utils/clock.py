import numpy as np
from datetime import timedelta
from cftime import date2num
from math import gcd

from ..time import TimeDomain


class Clock(object):

    def __init__(self, timedomains):
        self.categories = tuple(timedomains)
        self.timedomains = timedomains
        # check time compatibility between components
        self._check_timedomain_compatibilities(timedomains)

        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        supermesh_delta = min(
            *[timedomains[cat].timedelta for cat in timedomains]
        )
        supermesh_length = max(
            *[timedomains[cat].time.size for cat in timedomains]
        )
        supermesh_step = supermesh_delta.total_seconds()

        # check that all timesteps are multiple integers of the supermesh step
        steps = {}
        for category in timedomains:
            steps[category] = (
                timedomains[category].timedelta.total_seconds()
            )
            if not steps[category] % supermesh_step == 0:
                raise ValueError(
                    "timestep of {} component ({}s) not a multiple "
                    "integer of timestep of fastest component ({}s).".format(
                        category, steps[category], supermesh_step
                    )
                )

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self.switches = {}
        self.increments = {}
        for category in timedomains:
            self.switches[category] = np.zeros((supermesh_length,), dtype=bool)
            sl_increment = int(steps[category] // supermesh_step)
            self.switches[category][sl_increment - 1::sl_increment] = True
            self.increments[category] = sl_increment

        # determine model states minimum dumping delta and set initial dump
        self.switches['dumping'] = np.zeros((supermesh_length,), dtype=bool)
        # dump delta is the least common multiple across components
        dumping_delta = self._lcm_timedelta(
            timedomains[self.categories[0]].timedelta,
            timedomains[self.categories[1]].timedelta
        )
        for category in self.categories[2:]:
            dumping_delta = self._lcm_timedelta(
                dumping_delta,
                timedomains[category].timedelta
            )
        self.min_dumping_delta = dumping_delta
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

    def _check_timedomain_compatibilities(self, timedomains):
        for category in timedomains:
            # check that components' timedomains start/end on same datetime
            if not timedomains[category].spans_same_period_as(
                    timedomains[self.categories[0]]):
                raise ValueError(
                    "components' timedomains do not span same period"
                )

    @staticmethod
    def _lcm_timedelta(timedelta_a, timedelta_b):
        a = int(timedelta_a.total_seconds())
        b = int(timedelta_b.total_seconds())
        lcm = a * b // gcd(a, b)
        return timedelta(seconds=lcm)

    def set_dumping_frequency(self, dumping_frequency):
        # check that dumpy frequency is a multiple of dumping delta
        dumping_step = dumping_frequency.total_seconds()
        if not dumping_step % self.min_dumping_delta.total_seconds() == 0:
            raise ValueError(
                "dumping frequency ({}s) is not a multiple integer "
                "of smallest common multiple across components' "
                "timedomains ({}s).".format(
                    dumping_step, self.min_dumping_delta.total_seconds()
                )
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

