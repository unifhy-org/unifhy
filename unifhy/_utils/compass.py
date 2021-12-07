from itertools import combinations
from ..space import LatLonGrid


class Compass(object):

    def __init__(self, spacedomains):
        self.categories = tuple(spacedomains)
        self.spacedomains = spacedomains
        # check time compatibility between components
        self._check_spacedomain_compatibilities(spacedomains)

    @staticmethod
    def _check_spacedomain_compatibilities(spacedomains):
        """**Examples:**

        >>> sd_sl = LatLonGrid(
        ...     longitude=[0, 20],
        ...     longitude_bounds=[[-10, 10], [10, 30]],
        ...     latitude=[13],
        ...     latitude_bounds=[[10, 16]]
        ... )
        >>> sd_ss = LatLonGrid(
        ...     longitude=[-5, 5, 15, 25],
        ...     longitude_bounds=[[-10, 0], [0, 10], [10, 20], [20, 30]],
        ...     latitude=[11, 13, 15],
        ...     latitude_bounds=[[10, 12], [12, 14], [14, 16]]
        ... )
        >>> sd_ow = LatLonGrid(
        ...     longitude=[-7.5, -2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5],
        ...     longitude_bounds=[[-10, -5], [-5, 0], [0, 5], [5, 10],
        ...                       [10, 15], [15, 20], [20, 25], [25, 30]],
        ...     latitude=[10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
        ...     latitude_bounds=[[10, 11], [11, 12], [12, 13],
        ...                      [13, 14], [14, 15], [15, 16]]
        ... )
        >>> Compass._check_spacedomain_compatibilities(
        ...     {'surfacelayer': sd_sl, 'subsurface': sd_ss, 'openwater': sd_ow}
        ... )
        {('surfacelayer', 'subsurface'): 'subsurface', ('surfacelayer', 'openwater'): 'openwater', ('subsurface', 'openwater'): 'openwater'}

        >>> sd_sl = LatLonGrid(
        ...     longitude=[0, 20],
        ...     longitude_bounds=[[-10, 10], [10, 30]],
        ...     latitude=[13],
        ...     latitude_bounds=[[9, 17]]
        ... )
        >>> sd_ss = LatLonGrid(
        ...     longitude=[-5, 5, 15, 25],
        ...     longitude_bounds=[[-10, 0], [0, 10], [10, 20], [20, 30]],
        ...     latitude=[11, 13, 15],
        ...     latitude_bounds=[[10, 12], [12, 14], [14, 16]]
        ... )
        >>> sd_ow = LatLonGrid(
        ...     longitude=[-7.5, -2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5],
        ...     longitude_bounds=[[-10, -5], [-5, 0], [0, 5], [5, 10],
        ...                       [10, 15], [15, 20], [20, 25], [25, 30]],
        ...     latitude=[10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
        ...     latitude_bounds=[[10, 11], [11, 12], [12, 13],
        ...                      [13, 14], [14, 15], [15, 16]]
        ... )
        >>> Compass._check_spacedomain_compatibilities(
        ...     {'surfacelayer': sd_sl, 'subsurface': sd_ss, 'openwater': sd_ow}
        ... )
        Traceback (most recent call last):
            ...
        ValueError: spacedomains of components surfacelayer and subsurface do not span same region

        >>> sd_sl = LatLonGrid(
        ...     longitude=[0, 20],
        ...     longitude_bounds=[[-10, 10], [10, 30]],
        ...     latitude=[11.5, 14.5],
        ...     latitude_bounds=[[10, 13], [13, 16]]
        ... )
        >>> sd_ss = LatLonGrid(
        ...     longitude=[-5, 5, 15, 25],
        ...     longitude_bounds=[[-10, 0], [0, 10], [10, 20], [20, 30]],
        ...     latitude=[11, 13, 15],
        ...     latitude_bounds=[[10, 12], [12, 14], [14, 16]]
        ... )
        >>> sd_ow = LatLonGrid(
        ...     longitude=[-7.5, -2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5],
        ...     longitude_bounds=[[-10, -5], [-5, 0], [0, 5], [5, 10],
        ...                       [10, 15], [15, 20], [20, 25], [25, 30]],
        ...     latitude=[10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
        ...     latitude_bounds=[[10, 11], [11, 12], [12, 13],
        ...                      [13, 14], [14, 15], [15, 16]]
        ... )
        >>> Compass._check_spacedomain_compatibilities(
        ...     {'surfacelayer': sd_sl, 'subsurface': sd_ss, 'openwater': sd_ow}
        ... )
        Traceback (most recent call last):
            ...
        ValueError: spacedomains of components surfacelayer and subsurface cannot be matched onto one another

        """
        supermeshes = {}

        # checks on each pair of components
        for c1, c2 in combinations(spacedomains, 2):
            # check that components' spacedomains are equal
            # (to stay until spatial supermesh supported)
            if not spacedomains[c1].spans_same_region_as(spacedomains[c2]):
                raise ValueError(
                    f"spacedomains of components {c1} and {c2} "
                    f"do not span same region"
                )

            # check that components' space resolutions are integer multiples
            # (to effectively guarantee that one component resolution
            #  is the supermesh for the pair of components coupled, i.e.
            #  that no cell in one domain "cuts through" a cell of another)
            if spacedomains[c1].is_matched_in(spacedomains[c2]):
                supermeshes[(c1, c2)] = c2
            elif spacedomains[c2].is_matched_in(spacedomains[c1]):
                supermeshes[(c1, c2)] = c1
            else:
                raise ValueError(
                    f"spacedomains of components {c1} and {c2} "
                    f"cannot be matched onto one another"
                )

        return supermeshes
