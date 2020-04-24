from collections.abc import MutableMapping


class Interface(MutableMapping):

    def __init__(self, states, fluxes):
        self.content = dict()
        self.states = states
        self.update(
            {
                s + '_' * trail: None
                for s in states.keys()
                for trail in range(states[s], -1, -1)
            }
        )
        self.fluxes = fluxes
        self.update(
            {f: None for f in fluxes}
        )

    def __getitem__(self, key): return self.content[key]

    def __setitem__(self, key, value):  self.content[key] = value

    def __delitem__(self, key): del self.content[key]

    def __iter__(self): return iter(self.content)

    def __len__(self): return len(self.content)

    def __repr__(self):

        return "Interface(\n\tstates: %r\n\tfluxes: %r\n)" % \
               ({s + '_' * trail: self.content[s + '_' * trail]
                 for s in self.states.keys()
                 for trail in range(self.states[s], -1, -1)},
                {f: self.content[f] for f in self.fluxes})

    def increment_states(self):
        for s in self.states.keys():
            # prepare the left-hand side of the name bindings reassignment
            lhs = [self.content[s + '_' * trail]
                   for trail in range(self.states[s], -1, -1)]
            # prepare the right-hand side of the name bindings reassignment
            rhs = [self.content[s + '_' * trail]
                   for trail in range(self.states[s] - 1, -1, -1)] + \
                  [self.content[s + '_' * self.states[s]]]
            # carry out the permutation (i.e. name bindings reassignment)
            # to avoid new object creations
            lhs[:] = rhs[:]
            # apply the name bindings reassignment in the dictionary mapping
            for trail in range(self.states[s], -1, -1):
                self.content[s + '_' * trail] = lhs[self.states[s] - trail]

            # re-initialise current timestep state to zero
            try:
                self.content[s][:] = 0.0
            except TypeError:
                raise TypeError(
                    "The model state named '{}' was not initialised for "
                    "at least one of its required timesteps. This model state "
                    "requires a history of {} timesteps (excluding the "
                    "current timestep).".format(s, self.states[s])
                )