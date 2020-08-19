from collections.abc import MutableMapping
import numpy as np

from ..settings import dtype_float


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

        self.transfers = transfers
        self.set_up(components, clock, compass)

    def set_up(self, components, clock, compass, overwrite=False):
        # determine how many iterations of the clock
        # each component covers (i.e. steps)
        steps = {
            c: components[c].timedomain.timedelta // clock.timedelta
            for c in components
        }

        # set up each transfer
        for t in self.transfers:
            # special case for transfers towards a DataComponent or
            # a NullComponent (or towards outside framework which will
            # remain possible until Ocean and Atmosphere components are
            # implemented in the framework)
            if self.transfers[t].get('from') is None:
                # in this case only __setitem__ will be called
                continue

            to_ = steps[self.transfers[t]['to']]
            from_ = steps[self.transfers[t]['from']]

            # determine the weights that will be used by the interface
            # on the stored timesteps when a transfer is asked (i.e.
            # when __getitem__ is called)
            self.transfers[t]['weights'] = self._calculate_weights(
                from_, to_, clock.length
            )
            if self.transfers[t]['method'] == 'sum':
                # need to add dimensions of size 1 for numpy broadcasting
                self.transfers[t]['weights'] = np.expand_dims(
                    self.transfers[t]['weights'],
                    axis=[-(i+1) for i in range(len(compass.shape))]
                )

            # history is the number of timesteps that are stored
            self.transfers[t]['history'] = (
                self.transfers[t]['weights'].shape[-1]
            )

            # initialise iterator that allows the interface to know
            # which weights to use
            self.transfers[t]['iter'] = 0

            # if required or requested, initialise array to store
            # required timesteps
            if (
                    overwrite
                    or ('array' not in self.transfers[t])
                    or ('array' in self.transfers[t]
                        and (self.transfers[t]['array'].shape
                             != ((self.transfers[t]['history'],)
                                 + compass.shape)))
            ):
                arr = np.zeros((self.transfers[t]['history'],) + compass.shape,
                               dtype_float())
                self.transfers[t]['array'] = arr
                # set up slices that are views of the array that is be
                # rolled out each time a transfer is asked
                self.transfers[t]['slices'] = [
                    arr[i] for i in range(self.transfers[t]['history'])
                ]

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
                self.transfers[key]['slices'],
                weights=self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'sum':
            value = np.sum(
                self.transfers[key]['slices']
                * self.transfers[key]['weights'][i], axis=0
            )
        elif self.transfers[key]['method'] == 'point':
            value = self.transfers[key]['slices'][-1]
        elif self.transfers[key]['method'] == 'minimum':
            value = np.amin(self.transfers[key]['slices'], axis=0)
        elif self.transfers[key]['method'] == 'maximum':
            value = np.amax(self.transfers[key]['slices'], axis=0)
        else:
            raise ValueError('method for interface transfer unknown')

        # record that another value was retrieved by incrementing count
        self.transfers[key]['iter'] += 1

        return value

    def __setitem__(self, key, value):
        # special case for transfers towards a DataComponent or
        # a NullComponent (or towards outside framework which will
        # remain possible until Ocean and Atmosphere components are
        # implemented in the framework)
        if self.transfers[key].get('from') is None:
            return

        lhs = [a for a in self.transfers[key]['slices']]
        rhs = ([a for a in self.transfers[key]['slices'][1:]]
               + [self.transfers[key]['slices'][0]])

        lhs[:] = rhs[:]

        self.transfers[key]['slices'][:] = lhs
        self.transfers[key]['slices'][-1] = value

    def __delitem__(self, key):
        del self.transfers[key]

    def __iter__(self):
        return iter(self.transfers)

    def __len__(self):
        return len(self.transfers)
