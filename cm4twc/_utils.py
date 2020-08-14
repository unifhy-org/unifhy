from collections.abc import MutableMapping
from datetime import timedelta
from math import gcd
import numpy as np

from .settings import dtype_float


class Interface(MutableMapping):

    def __init__(self, components, clock, compass):
        # transfers that are both inwards and outwards will exist
        # only once because dictionary keys are unique
        transfers = {}
        for c in components:
            for i in [components[c].inwards_info, components[c].outwards_info]:
                for t in i:
                    if t not in transfers:
                        transfers[t] = {}
                    transfers[t].update(i[t])

        steps = {
            c: components[c].timedomain.timedelta // clock.timedelta
            for c in components
        }

        for t in transfers:
            # special case for transfers towards outside framework
            # (should only be temporary until Ocean and Atmosphere
            # are included in the framework)
            if steps.get(transfers[t]['to']) is None:
                transfers[t]['arrays'] = [
                    np.zeros(compass.shape, dtype_float())
                ]
                continue

            to_ = steps[transfers[t]['to']]
            from_ = steps[transfers[t]['from']]

            transfers[t]['weights'] = self._calculate_weights(from_, to_,
                                                              clock.length)

            arr = np.zeros((transfers[t]['weights'].shape[-1],)
                           + compass.shape, dtype_float())
            transfers[t]['arrays'] = [
                arr[i] for i in range(transfers[t]['weights'].shape[-1])
            ]

            transfers[t]['iter'] = 0

            if transfers[t]['method'] == 'sum':
                # need to add dimensions for numpy broadcasting
                transfers[t]['weights'] = np.expand_dims(
                    transfers[t]['weights'],
                    axis=[-(i+1) for i in range(len(compass.shape))]
                )

        self.transfers = transfers

    @staticmethod
    def _calculate_weights(from_, to_, length):
        weights = []

        if to_ == from_:
            # need to keep only one step with full weight
            keep = 1
            for i in range(length // to_):
                weights.append((to_,))
        elif to_ > from_:
            if to_ % from_ == 0:
                # need to keep several steps with equal weights
                keep = to_ // from_
                for i in range(length // to_):
                    weights.append(
                        (from_,) * (to_ // from_)
                    )
            else:
                # need to keep several steps with varying weights
                keep = (to_ // from_) + 1
                previous = 0
                for i in range(length // to_):
                    start = from_ - previous
                    middle = ((to_ - start) // from_)
                    end = to_ - start - (middle * from_)
                    weights.append(
                        (start,
                         *((from_,) * middle),
                         *((end,) if end > 0 else ()))
                    )
                    previous = end
        else:
            if from_ % to_ == 0:
                # need to keep only one step with full weight
                keep = 1
                for i in range(length // to_):
                    weights.append(
                        (to_,)
                    )
            else:
                # need to keep two steps with varying weights
                keep = 2
                from_hits = 1
                for i in range(length // to_):
                    from_tracker = from_ * from_hits
                    if ((i * to_) < from_tracker) and (from_tracker < ((i + 1) * to_)):
                        # from_ falls in-between two consecutive steps of to_
                        # spread weight across from_ kept values
                        # and update from_ hits
                        discard = (from_tracker // to_) * to_
                        oldest = from_tracker - discard
                        latest_ = to_ - oldest
                        weights.append(
                            (oldest, latest_)
                        )
                        from_hits += 1
                    elif (i * to_) == from_tracker:
                        # from_ coincides with to_
                        # put whole weight on from_ latest value
                        # and update from_ hits
                        weights.append(
                            (0, to_)
                        )
                        from_hits += 1
                    else:
                        # from_ is beyond to_ and to_'s next step
                        # put whole weight on from_ latest value
                        # but do not update from_ hits
                        weights.append(
                            (0, to_)
                        )

        weights = np.array(weights)

        assert keep == weights.shape[-1], 'error in interface weights'

        return weights

    def __getitem__(self, key):
        i = self.transfers[key]['iter']

        # customise the action between existing and incoming arrays
        # depending on method for that particular transfer
        if self.transfers[key]['method'] == 'mean':
            value = np.average(
                self.transfers[key]['arrays'],
                weights=self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'sum':
            value = np.sum(
                self.transfers[key]['arrays']
                * self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'point':
            value = self.transfers[key]['arrays'][-1]
        elif self.transfers[key]['method'] == 'minimum':
            value = np.amin(self.transfers[key]['arrays'], axis=0)
        elif self.transfers[key]['method'] == 'maximum':
            value = np.amax(self.transfers[key]['arrays'], axis=0)
        else:
            raise ValueError('method for interface transfer unknown')

        # record that another value was processed by incrementing count
        self.transfers[key]['iter'] += 1

        return value

    def __setitem__(self, key, value):
        lhs = [a for a in self.transfers[key]['arrays']]
        rhs = ([a for a in self.transfers[key]['arrays'][1:]]
               + [self.transfers[key]['arrays'][0]])

        lhs[:] = rhs[:]

        self.transfers[key]['arrays'][:] = lhs
        self.transfers[key]['arrays'][-1] = value

    def __delitem__(self, key):
        del self.transfers[key]

    def __iter__(self):
        return iter(self.transfers)

    def __len__(self):
        return len(self.transfers)

    def __repr__(self):
        return "Interface(\n\tfluxes: %r\n" % \
               {f: self.transfers[f] for f in self.transfers}


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
