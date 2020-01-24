import numpy as np


class SpaceDomain(object):
    """
    Class to handle geospatial considerations.
    """

    _supported_kinds = (
        'grid',
        'network',
    )

    def __init__(self, kind):

        if kind in self._supported_kinds:
            self.kind = kind
        else:
            raise TypeError("The SpaceDomain kind is not supported.")

    def __eq__(self, other):

        if not self.kind == other.kind:
            return TypeError("The two SpaceDomain instances cannot be "
                             "compared because they are of different kinds.")


class Grid(SpaceDomain):

    def __init__(self, geo_coordinate_system, x, y):

        super(Grid, self).__init__('grid')

        self.geo_coord_sys = geo_coordinate_system
        if isinstance(x, np.ndarray):
            self.x = x
        else:
            raise TypeError("The 'x' attribute of the Grid is not a "
                            "numpy.ndarray.")
        if isinstance(y, np.ndarray):
            self.y = y
        else:
            raise TypeError("The 'y' attribute of the Grid is not a "
                            "numpy.ndarray.")

    def __eq__(self, other):

        if self.geo_coord_sys == other.geo_coord_sys \
                and np.array_equal(self.x, other.x) \
                and np.array_equal(self.y, other.y):
            return True
        else:
            return False


class Network(SpaceDomain):

    def __init__(self, topology):

        super(Network, self).__init__('network')

        self.topo = topology  # some form of mapping type?

    def __eq__(self, other):

        if self.topo == other.topo:
            return True
        else:
            return False
