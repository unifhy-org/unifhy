from collections.abc import MutableMapping


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
