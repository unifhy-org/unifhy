from collections.abc import MutableMapping
from datetime import timedelta
from math import gcd
import numpy as np


class Interface(MutableMapping):

    def __init__(self, fluxes):
        self.fluxes = {}
        self.update(fluxes)

    def __getitem__(self, key):
        return self.fluxes[key]

    def __setitem__(self, key, value):
        self.fluxes[key] = value

    def __delitem__(self, key):
        del self.fluxes[key]

    def __iter__(self):
        return iter(self.fluxes)

    def __len__(self):
        return len(self.fluxes)

    def __repr__(self):
        return "Interface(\n\tfluxes: %r\n" % \
               {f: self.fluxes[f] for f in self.fluxes}


class Clock(object):

    def __init__(self, timedomains, dumping_frequency=None):
        self.categories = tuple(timedomains)
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
                        category, steps[category], supermesh_step))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self.switches = {}
        self.increments = {}
        for category in timedomains:
            self.switches[category] = np.zeros((supermesh_length,), dtype=bool)
            sl_increment = int(steps[category] // supermesh_step)
            self.switches[category][sl_increment - 1::sl_increment] = True
            self.increments[category] = sl_increment

        # determine whether model states dumping is required, and if so, when
        self.switches['dumping'] = np.zeros((supermesh_length,), dtype=bool)
        if dumping_frequency is not None:
            # check that dumpy frequency is a multiple of
            # the least common multiple across components
            dumping_delta = self._lcm_timedelta(
                timedomains[self.categories[0]].timedelta,
                timedomains[self.categories[1]].timedelta
            )
            for category in self.categories[2:]:
                dumping_delta = self._lcm_timedelta(
                    dumping_delta,
                    timedomains[category].timedelta
                )
            dumping_step = dumping_frequency.total_seconds()
            if not dumping_step % dumping_delta.total_seconds() == 0:
                raise ValueError(
                    "dumping frequency ({}s) is not a multiple integer "
                    "of smallest common multiple across components' "
                    "timedomains ({}s).".format(
                        dumping_step, dumping_delta.total_seconds()))

            # get boolean arrays (switches) to determine when to dump the
            # component states on temporal supermesh
            dumping_increment = int(dumping_step // supermesh_step)
            self.switches['dumping'][0::dumping_increment] = True
        else:
            # get only one dump for the initial conditions
            self.switches['dumping'][0] = True

        # set some time attributes
        self.timedelta = supermesh_delta
        self.length = supermesh_length

        self.start_datetime = (
            timedomains[self.categories[0]].time.datetime_array[0]
        )
        self.end_datetime = (
            timedomains[self.categories[0]].time.datetime_array[-1]
        )

        self.start_timeindex = 0
        self.end_timeindex = supermesh_length - 1

        # initialise 'iterable' time attributes to the point in time just
        # prior the actual specified start of the supermesh because the
        # iterator needs to increment in time prior indexing the switches
        self._current_datetime = self.start_datetime - supermesh_delta
        self._current_timeindex = self.start_timeindex - 1

    @staticmethod
    def _lcm_timedelta(timedelta_a, timedelta_b):
        a = int(timedelta_a.total_seconds())
        b = int(timedelta_b.total_seconds())
        lcm = a * b // gcd(a, b)
        return timedelta(seconds=lcm)

    def get_current_datetime(self):
        return self._current_datetime

    def get_current_timeindex(self, category):
        return (self._current_timeindex //
                self.increments[category])

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


class Compass(object):

    def __init__(self, spacedomains):
        self.categories = tuple(spacedomains)
        # for now components have the same spacedomain, so take
        # arbitrarily one component to be the supermesh
        self.shape = spacedomains[self.categories[0]].shape
