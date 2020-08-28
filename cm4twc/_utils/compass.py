

class Compass(object):

    def __init__(self, spacedomains):
        self.categories = tuple(spacedomains)
        # check time compatibility between components
        self._check_spacedomain_compatibilities(spacedomains)

        # for now components have the same spacedomain, so take
        # arbitrarily one component to be the supermesh
        self.shape = spacedomains[self.categories[0]].shape

        # generate a SpaceDomain for the Compass (for now take a
        # TimeDomain of a Component arbitrarily)
        self.spacedomain = spacedomains[self.categories[0]]

    def _check_spacedomain_compatibilities(self, spacedomains):
        for category in spacedomains:
            # check that components' spacedomains are equal
            # (to stay until spatial supermesh supported)
            if spacedomains[category] != spacedomains[self.categories[0]]:
                raise NotImplementedError(
                    "components' spacedomains are not identical")
