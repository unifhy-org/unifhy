from collections.abc import MutableMapping


class Interface(MutableMapping):

    def __init__(self, fluxes, surfacelayer_states,
                 subsurface_states, openwater_states):
        self.content = dict()
        self.fluxes = fluxes
        self.update(
            {f: None for f in fluxes}
        )
        self.surfacelayer_states = surfacelayer_states
        self.update(
            {s: None for s in surfacelayer_states}
        )
        self.subsurface_states = subsurface_states
        self.update(
            {s: None for s in subsurface_states}
        )
        self.openwater_states = openwater_states
        self.update(
            {s: None for s in openwater_states}
        )

    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value):
        self.content[key] = value

    def __delitem__(self, key):
        del self.content[key]

    def __iter__(self):
        return iter(self.content)

    def __len__(self):
        return len(self.content)

    def __repr__(self):
        return "Interface(\n\tfluxes: %r\n\tsurfacelayer states: %r\n\t" \
               "subsurface states: %r\n\topenwater states: %r\n)" % \
               ({f: self.content[f] for f in self.fluxes},
                {s: self.content[s] for s in self.surfacelayer_states},
                {s: self.content[s] for s in self.subsurface_states},
                {s: self.content[s] for s in self.openwater_states})

    def _initialise_states(self, component_kind, component_states, states):
        for s in states.keys():
            if s in component_states:
                self.content[s] = State(*states[s])
            else:
                raise KeyError(
                    "Trying to initialise the state '{}' which is not in the "
                    "definition of the {} component.".format(s, component_kind)
                )

    def initialise_surfacelayer_states(self, states):
        self._initialise_states(
            'surfacelayer', self.surfacelayer_states, states
        )

    def initialise_subsurface_states(self, states):
        self._initialise_states(
            'subsurface', self.subsurface_states, states
        )

    def initialise_openwater_states(self, states):
        self._initialise_states(
            'openwater', self.openwater_states, states
        )

    def _increment_states(self, states):
        for s in states:
            # determine first index in the State
            # (function of solver's history)
            first_index = -len(self.content[s]) + 1
            # prepare the left-hand side of the name re-binding
            lhs = [t for t in self.content[s]]
            # prepare the right-hand side of the name re-binding
            rhs = [t for t in self.content[s][first_index + 1:]] + \
                [self.content[s][first_index]]
            # carry out the permutation (i.e. name re-binding)
            # to avoid new object creations
            lhs[:] = rhs[:]
            # apply new name bindings to the State
            z = self.content[s][:]
            self.content[s][:] = lhs

            # re-initialise current timestep of State to zero
            self.content[s][0][:] = 0.0

    def increment_surfacelayer_states(self):
        self._increment_states(self.surfacelayer_states)

    def increment_subsurface_states(self):
        self._increment_states(self.subsurface_states)

    def increment_openwater_states(self):
        self._increment_states(self.openwater_states)


class State(object):
    """
    The State class behaves like a list which stores the values of a
    given component state for several consecutive timesteps (in
    chronological order, i.e. the oldest timestep is the first item,
    the most recent is the last item).

    Although, unlike a list, its indexing is shifted so that the last
    item has index 0, and all previous items are accessible via a
    negative integer (e.g. -1 for the 2nd-to-last, -2 for the
    3rd-to-last, etc.). The first item (i.e. the oldest timestep stored)
    is accessible at the index equals to minus the length of the list
    plus one. Since the list remains in chronological order, it means
    that for a given timestep t, index -1 corresponds to timestep t-1,
    index -2 to timestep t-2, etc. Current timestep t is accessible at
    index 0.
    """
    def __init__(self, *args):
        self.history = list(args)

    def __getitem__(self, index):
        index = self.shift_index(index)
        return self.history[index]

    def __setitem__(self, index, item):
        index = self.shift_index(index)
        self.history[index] = item

    def shift_index(self, index):
        if isinstance(index, int):
            index = index + len(self) - 1
        elif isinstance(index, slice):
            start, stop = index.start, index.stop
            if start is not None:
                start = start + len(self) - 1
            if stop is not None:
                stop = stop + len(self) - 1
            index = slice(start, stop, index.step)
        return index

    def __delitem__(self, index):
        index = self.shift_index(index)
        del self.history[index]

    def __len__(self):
        return len(self.history)

    def __iter__(self):
        return iter(self.history)

    def __repr__(self):
        return "%r" % self.history
