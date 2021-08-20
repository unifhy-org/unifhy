

class Compass(object):

    def __init__(self, spacedomains):
        self.categories = tuple(spacedomains)
        self.spacedomains = spacedomains
        # check time compatibility between components
        self._check_spacedomain_compatibilities(spacedomains)

    def _check_spacedomain_compatibilities(self, spacedomains):
        for category in spacedomains:
            # check that components' spacedomains are equal
            # (to stay until spatial supermesh supported)
            if not spacedomains[category].spans_same_region_as(
                    spacedomains[self.categories[0]]):
                raise NotImplementedError(
                    "components' spacedomains are not identical"
                )
