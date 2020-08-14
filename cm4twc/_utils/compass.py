

class Compass(object):

    def __init__(self, spacedomains):
        self.categories = tuple(spacedomains)
        # for now components have the same spacedomain, so take
        # arbitrarily one component to be the supermesh
        self.shape = spacedomains[self.categories[0]].shape
