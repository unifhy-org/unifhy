import abc
import numpy as np
from copy import deepcopy
import re
import cf
import cfunits
import pyproj

from .settings import atol, rtol, decr, dtype_float


class SpaceDomain(metaclass=abc.ABCMeta):
    """SpaceDomain characterises a spatial dimension that is needed by a
    `Component`. Any supported spatial configuration for a `Component`
    is a subclass of SpaceDomain.

    TODO: deal with sub-grid heterogeneity schemes (e.g. tiling, HRUs)
    """

    def __init__(self):
        # inner CF data model
        self._f = cf.Field()
        self._cell_area = None
        self._cell_area_field = None

        # optional flow direction attributes
        self._flow_direction = None
        self._flow_direction_field = None
        self._routing_out_mask = None
        self._routing_masks = {}

        # optional land sea mask attributes
        self._land_sea_mask = None
        self._land_sea_mask_field = None

    @property
    @abc.abstractmethod
    def shape(self):
        # The sizes of the SpaceDomain dimension axes as a `tuple`.
        # The corresponding names and order of the axes is accessible
        # through the `axes` property.
        return None

    @property
    @abc.abstractmethod
    def axes(self):
        # The names of the SpaceDomain dimension axes as a `tuple`.
        # These names are properties of SpaceDomain, which give access
        # to the coordinate values along each axis.
        return None

    @abc.abstractmethod
    def has_vertical_axis(self):
        return None

    @property
    @abc.abstractmethod
    def vertical_axis(self):
        # The name of the SpaceDomain vertical dimension axis as a `str`.
        return None

    @property
    @abc.abstractmethod
    def flow_direction(self):
        return self._flow_direction

    @flow_direction.setter
    @abc.abstractmethod
    def flow_direction(self, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def land_sea_mask(self):
        return self._land_sea_mask

    @land_sea_mask.setter
    @abc.abstractmethod
    def land_sea_mask(self, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def cell_area(self):
        return self._cell_area

    @cell_area.setter
    @abc.abstractmethod
    def cell_area(self, **kwargs):
        pass

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.is_space_equal_to(other._f)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @abc.abstractmethod
    def is_space_equal_to(self, *args):
        pass

    @abc.abstractmethod
    def spans_same_region_as(self, *args):
        pass

    @abc.abstractmethod
    def is_matched_in(self, *args):
        pass

    @abc.abstractmethod
    def subset_and_compare(self, field):
        pass

    @classmethod
    @abc.abstractmethod
    def from_field(cls, field):
        pass

    def to_field(self):
        """Return a deep copy of the inner cf.Field used to characterise
        the SpaceDomain.
        """
        return deepcopy(self._f)

    @classmethod
    @abc.abstractmethod
    def from_config(cls, cfg):
        pass

    @abc.abstractmethod
    def to_config(self):
        pass


class Grid(SpaceDomain):
    """Grid is a `SpaceDomain` subclass which represents space as
    a regular grid made of contiguous grid cells. Any supported regular
    grid for a `Component` is a subclass of Grid.
    """
    # characteristics of the dimension coordinates
    _Z_name = None
    _Y_name = None
    _X_name = None
    _Z_units = []
    _Y_units = []
    _X_units = []
    _Z_limits = None
    _Y_limits = None
    _X_limits = None
    # contiguity of lower and upper limits
    _Z_limits_contiguous = False
    _Y_limits_contiguous = False
    _X_limits_contiguous = False
    # allow domain to wrap around limits
    _Z_wrap_around = False
    _Y_wrap_around = False
    _X_wrap_around = False

    # characterise the routing directions as relative (Y, X)
    _routing_cardinal_map = {
        'N': (1, 0),
        'NE': (1, 1),
        'E': (0, 1),
        'SE': (-1, 1),
        'S': (-1, 0),
        'SW': (-1, -1),
        'W': (0, -1),
        'NW': (1, -1),
        'O': (0, 0)
    }
    _routing_digits_map = {
        1: (1, 0),
        2: (1, 1),
        3: (0, 1),
        4: (-1, 1),
        5: (-1, 0),
        6: (-1, -1),
        7: (0, -1),
        8: (1, -1),
        0: (0, 0)
    }

    # supported locations to generate grid
    _YX_loc_map = {
        'centre': ('centre', 'center', '0', 0),
        'lower_left': ('lower_left', 'lower left', '1', 1),
        'upper_left': ('upper_left', 'upper left', '2', 2),
        'lower_right': ('lower_right', 'lower right', '3', 3),
        'upper_right': ('upper_right', 'upper right', '4', 4)
    }
    _Z_loc_map = {
        'centre': ('centre', 'center', '0', 0),
        'bottom': ('bottom', '1', 1),
        'top': ('top', '2', 2)
    }

    # geometrical properties
    _earth_radius_m = 6371229.0

    def __init__(self, **kwargs):
        super(Grid, self).__init__()

    @property
    def shape(self):
        """Return the size of the `Grid` dimension axes as a `tuple`.
        The corresponding names and order of the axes is accessible
        through the `axes` property.
        """
        return (
            (self._f.dim('Z').shape if self.has_vertical_axis() else ())
            + self._f.dim('Y').shape
            + self._f.dim('X').shape
        )

    @property
    def axes(self):
        """Return the name of the properties to use to get access to
        the axes defined for the `Grid` instance as a `tuple`.
        """
        return ('Z', 'Y', 'X') if self.has_vertical_axis() else ('Y', 'X')

    def has_vertical_axis(self):
        """Determine whether the `Grid` features a vertical dimension.
        Return a `bool`.
        """
        return (
            True if self._f.dim(self._Z_name, key=True, default=False)
            else False
        )

    @property
    def vertical_axis(self):
        """Return the name of the property to use to get access to
        the vertical axis defined for the `Grid` as a `str`. If not
        defined, return `None`.
        """
        return 'Z' if self.has_vertical_axis() else None

    @property
    def Z(self):
        """Return the Z-axis of the `Grid` instance as a `cf.Data`
        instance if the Z-axis exists, otherwise return `None`.
        """
        if self.has_vertical_axis():
            return self._f.dim('Z').data
        else:
            return None

    @property
    def Y(self):
        """Return the Y-axis of the `Grid` instance as a `cf.Data`
        instance.
        """
        return self._f.dim('Y').data

    @property
    def X(self):
        """Return the X-axis of the `Grid` instance as a `cf.Data`
        instance.
        """
        return self._f.dim('X').data

    @property
    def Z_bounds(self):
        """Return the bounds of the Z-axis of the `Grid` instance
        as a `cf.Data` instance if the Z-axis exists, otherwise
        return `None`.
        """
        if self.has_vertical_axis():
            return self._f.dim('Z').bounds.data
        else:
            return None

    @property
    def Y_bounds(self):
        """Return the bounds of the Y-axis of the `Grid` instance
        as a `cf.Data` instance.
        """
        return self._f.dim('Y').bounds.data

    @property
    def X_bounds(self):
        """Return the bounds of the X-axis of the `Grid` instance
        as a `cf.Data` instance.
        """
        return self._f.dim('X').bounds.data

    @property
    def Z_name(self):
        """Return the name of the Z-axis of the `Grid` instance
        as a `str` if the Z-axis exists, otherwise return `None`.
        """
        if self.has_vertical_axis():
            return self._f.dim('Z').standard_name
        else:
            return None

    @property
    def Y_name(self):
        """Return the name of the Y-axis of the `Grid` instance
        as a `str`.
        """
        return self._f.dim('Y').standard_name

    @property
    def X_name(self):
        """Return the name of the X-axis of the `Grid` instance
        as a `str`.
        """
        return self._f.dim('X').standard_name

    @property
    def land_sea_mask(self):
        """The land-sea mask for the `Grid` of boolean/binary
        values (i.e. True/1 for land, False/0 for sea) given as a
        `cf.Field` and returned as a processed `numpy.ndarray`.

        :Parameters:

            mask: `cf.Field`
                The field containing the land-sea information. The
                shape of the data array must be the same as the
                `Grid`. The field data must contain boolean/binary
                values (True/1 for land, False/0 for sea).

        :Returns:

            `numpy.ndarray`
                The array containing the land-sea information as boolean
                values (True for land, False for sea). The shape of the
                array is the same as of the `Grid`. If not set,
                return `None`.

        **Examples**

        Assigning land sea mask to grid using binary values:

        >>> import numpy
        >>> grid = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(51, 55),
        ...     latitude_resolution=1,
        ...     longitude_extent=(-2, 1),
        ...     longitude_resolution=1
        ... )
        >>> print(grid.land_sea_mask)
        None
        >>> mask = grid.to_field()
        >>> mask.set_data(numpy.array([[0, 1, 1],
        ...                            [1, 1, 0],
        ...                            [0, 1, 0],
        ...                            [0, 0, 0]]))
        >>> grid.land_sea_mask = mask
        >>> print(grid.land_sea_mask)
        [[False  True  True]
         [ True  True False]
         [False  True False]
         [False False False]]
        >>> print(grid)
        LatLonGrid(
            shape {Y, X}: (4, 3)
            Y, latitude (4,): [51.5, ..., 54.5] degrees_north
            X, longitude (3,): [-1.5, -0.5, 0.5] degrees_east
            Y_bounds (4, 2): [[51.0, ..., 55.0]] degrees_north
            X_bounds (3, 2): [[-2.0, ..., 1.0]] degrees_east
            land_sea_mask (4, 3): [[False, ..., False]]
        )

        Assigning land sea mask to grid using boolean values:

        >>> mask.set_data(numpy.array([[False, True, True],
        ...                            [True, True, False],
        ...                            [False, True, False],
        ...                            [False, False, False]]))
        >>> grid.land_sea_mask = mask
        >>> print(grid.land_sea_mask)
        [[False  True  True]
         [ True  True False]
         [False  True False]
         [False False False]]
        """
        return self._land_sea_mask

    @land_sea_mask.setter
    def land_sea_mask(self, mask):
        error = RuntimeError(
            f"mask shape incompatible with {self.__class__.__name__}"
        )

        # check type
        if not isinstance(mask, cf.Field):
            raise TypeError("mask not a cf.Field")
        # store given field for config file
        self._land_sea_mask_field = mask

        # drop potential size-1 Z axis since land sea mask is
        # only relevant horizontally
        if mask.domain_axis(self.vertical_axis, key=True, default=False):
            mask.squeeze(self.vertical_axis, inplace=True)

        # check that mask and spacedomain are compatible
        grid = self.to_horizontal_grid()
        try:
            mask = grid.subset_and_compare(mask)
        except RuntimeError:
            raise error

        # determine horizontal-only shape of spacedomain
        shp = grid.shape

        # get field's data array
        mask = mask.array
        # convert binary to boolean if necessary
        if not mask.dtype == np.dtype(bool):
            if (np.sum(mask == 1) + np.sum(mask == 0)) == mask.size:
                mask = np.asarray(mask, dtype=bool)
            else:
                raise TypeError("mask must contain boolean/binary values")
        if not mask.shape == shp:
            raise error

        # apply mask to underlying data to be taken into account in remapping
        self._f.data[:] = np.ma.array(self._f.array, mask=~mask)

        self._land_sea_mask = mask

    @property
    def flow_direction(self):
        """The information necessary to move any variable laterally
        (i.e. along Y and/or X) to its nearest receiving neighbour in
        the `Grid` given as a `cf.Field` and returned as a processed
        `numpy.ndarray`.

        :Parameters:

            directions: `cf.Field`
                The field containing flow direction. The supported kinds
                of directional information are listed in the table
                below. The shape of the array must be the same as the
                Grid, except for the relative kind, where an additional
                trailing axis of size two holding the pairs must be
                present.

                =================  =====================================
                kind               information
                =================  =====================================
                cardinal           The field data contains the direction
                                   using `str` for the eight following
                                   cardinal points: 'N' for North, 'NE'
                                   for North-East, 'E' for East,
                                   'SE' for South East, 'S' for South,
                                   'SW' for South West, 'W' for West,
                                   'NW' for North West.

                digits             The field data contains the direction
                                   using `int` for the eight following
                                   cardinal points: 1 for North, 2 for
                                   North-East, 3 for East, 4 for South
                                   East, 5 for South, 6 for South West,
                                   7 for West, 8 for North West.

                relative           The field data contains the direction
                                   using pairs of `int` (Y, X) for the
                                   eight following cardinal points:
                                   (1, 0) for North, (1, 1) for
                                   North-East, (0, 1) for East, (-1, 1)
                                   for South East, (-1, 0) for South,
                                   (-1, -1) for South West, (0, -1)
                                   for West, (1, -1) for North West.
                =================  =====================================

        :Returns:

            `numpy.ndarray`
                The information to route any variable to its destination
                in the `Grid` in the relative format (see table above).
                If not set, return `None`.

        **Examples**

        Assigning flow direction to grid using cardinal values:

        >>> import numpy
        >>> grid = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(51, 55),
        ...     latitude_resolution=1,
        ...     longitude_extent=(-2, 1),
        ...     longitude_resolution=1
        ... )
        >>> print(grid.flow_direction)
        None
        >>> directions = grid.to_field()
        >>> directions.set_data(numpy.array([['SE', 'S', 'E'],
        ...                                  ['NE', 'E', 'N'],
        ...                                  ['S', 'S', 'W'],
        ...                                  ['NW', 'E', 'SW']]))
        >>> grid.flow_direction = directions
        >>> print(grid.flow_direction)
        [[[-1  1]
          [-1  0]
          [ 0  1]]
        <BLANKLINE>
         [[ 1  1]
          [ 0  1]
          [ 1  0]]
        <BLANKLINE>
         [[-1  0]
          [-1  0]
          [ 0 -1]]
        <BLANKLINE>
         [[ 1 -1]
          [ 0  1]
          [-1 -1]]]
        >>> print(grid)
        LatLonGrid(
            shape {Y, X}: (4, 3)
            Y, latitude (4,): [51.5, ..., 54.5] degrees_north
            X, longitude (3,): [-1.5, -0.5, 0.5] degrees_east
            Y_bounds (4, 2): [[51.0, ..., 55.0]] degrees_north
            X_bounds (3, 2): [[-2.0, ..., 1.0]] degrees_east
            flow_direction (4, 3, 2): [[[-1, ..., -1]]]
        )

        Assigning flow direction to grid using digits:

        >>> flow_direction = grid.flow_direction
        >>> directions.set_data(numpy.array([[4, 5, 3],
        ...                                  [2, 3, 1],
        ...                                  [5, 5, 7],
        ...                                  [8, 3, 6]]))
        >>> grid.flow_direction = directions
        >>> numpy.array_equal(flow_direction, grid.flow_direction)
        True

        Assigning flow direction to grid using relative values:

        >>> import cf
        >>> ax = directions.set_construct(cf.DomainAxis(2))
        >>> dim = cf.DimensionCoordinate(
        ...     properties={'name': 'relative flow direction along y and x components',
        ...                 'units': '1'},
        ...     data=cf.Data(['y_rel', 'x_rel'])
        ... )
        >>> dim = directions.set_construct(dim, axes=ax)
        >>> directions.set_data(
        ...     numpy.array([[[-1, 1], [-1, 0], [0, 1]],
        ...                  [[1, 1], [0, 1], [1, 0]],
        ...                  [[-1, 0], [-1, 0], [0, -1]],
        ...                  [[1, -1], [0, 1], [-1, -1]]]
        ...     ),
        ...     axes=('Y', 'X', dim)
        ... )
        >>> grid.flow_direction = directions
        >>> numpy.array_equal(flow_direction, grid.flow_direction)
        True

        Assigning masked flow direction to grid:

        >>> directions = grid.to_field()
        >>> directions.set_data(
        ...     numpy.ma.array(
        ...         [['SE', 'S', 'E'],
        ...          ['NE', 'E', 'N'],
        ...          ['S', 'S', 'W'],
        ...          ['NW', 'E', 'SW']],
        ...         mask=[[1, 0, 0],
        ...               [1, 0, 0],
        ...               [1, 1, 0],
        ...               [0, 0, 0]]
        ...     )
        ... )
        >>> grid.flow_direction = directions
        >>> print(grid.flow_direction)
        [[[-- --]
          [-1 0]
          [0 1]]
        <BLANKLINE>
         [[-- --]
          [0 1]
          [1 0]]
        <BLANKLINE>
         [[-- --]
          [-- --]
          [0 -1]]
        <BLANKLINE>
         [[1 -1]
          [0 1]
          [-1 -1]]]
        """
        return self._flow_direction

    @flow_direction.setter
    def flow_direction(self, directions):
        error_valid = RuntimeError("flow direction contains invalid data")
        error_dim = RuntimeError(
            f"flow direction dimensions not compatible "
            f"with {self.__class__.__name__}"
        )

        # check type
        if not isinstance(directions, cf.Field):
            raise TypeError("flow direction not a cf.Field")
        # store given field for config file
        self._flow_direction_field = directions

        # drop potential size-1 Z axis since flow direction is
        # only relevant horizontally
        if directions.domain_axis(self.vertical_axis, key=True, default=False):
            directions.squeeze(self.vertical_axis, inplace=True)

        # check that directions and spacedomain are compatible
        grid = self.to_horizontal_grid()
        try:
            directions = grid.subset_and_compare(directions)
        except RuntimeError:
            raise error_dim

        # get field's data array
        directions = directions.array

        # determine horizontal-only shape of spacedomain
        shp = grid.shape

        # initialise info array by extending by one trailing axis of
        # size 2 (for relative Y movement, and relative X movement)

        # if masked array, use same mask on info
        if np.ma.is_masked(directions):
            if (shp + (2,)) == directions.shape:
                info = np.ma.masked_array(
                    np.zeros(shp + (2,), int),
                    mask=directions.mask
                )
            elif shp == directions.shape:
                info = np.ma.masked_array(
                    np.zeros(shp + (2,), int),
                    mask=np.tile(directions.mask[..., np.newaxis], 2)
                )
            else:
                raise error_dim
            info[~info.mask] = -9
        else:
            info = np.zeros(shp + (2,), int)
            info[:] = -9

        # convert directions to relative Y X movement
        if directions.dtype == np.dtype('<U2'):
            # cardinal
            if not directions.shape == shp:
                raise error_dim

            # strip and capitalise strings
            if np.ma.is_masked(directions):
                directions[~directions.mask] = np.char.strip(
                    np.char.upper(directions[~directions.mask])
                )
            else:
                directions = np.char.strip(np.char.upper(directions))

            for card, yx_rel in self._routing_cardinal_map.items():
                info[directions == card] = yx_rel
        elif issubclass(directions.dtype.type, np.integer):
            if info.shape == directions.shape:
                # relative
                if np.amin(directions) < -1 or np.amax(directions) > 1:
                    raise error_valid
                info[:] = directions
            elif shp == directions.shape:
                # digits
                for digit, yx_rel in self._routing_digits_map.items():
                    info[directions == digit] = yx_rel
            else:
                raise error_dim
        else:
            raise error_valid

        # check that match found for everywhere in grid
        if not np.sum(info == -9) == 0:
            raise error_valid

        # assign main routing mask
        self._flow_direction = info

        # find outflow towards outside domain
        # to set relative direction special value 9
        info_ = np.zeros(shp + (2,), int)
        info_[:] = info
        if not (self._Y_limits_contiguous
                and (self.Y_bounds.array[0, 0] in self._Y_limits)
                and (self.Y_bounds.array[-1, -1] in self._Y_limits)):
            # northwards on north edge
            info_[..., 0, :, 0][info_[..., 0, :, 0] == -1] = 9
            # southwards on south edge
            info_[..., -1, :, 0][info_[..., -1, :, 0] == 1] = 9
        if not (self._X_limits_contiguous
                and (self.X_bounds.array[0, 0] in self._X_limits)
                and (self.X_bounds.array[-1, -1] in self._X_limits)):
            # eastwards on east edge
            info_[..., :, -1, 1][info_[..., :, -1, 1] == 1] = 9
            # westwards on west edge
            info_[..., :, 0, 1][info_[..., :, 0, 1] == -1] = 9

        # create mask for location with outflow towards outside domain
        to_out = (info_[..., 0] == 9) | (info_[..., 1] == 9)

        # find outflow towards masked location
        if np.ma.is_masked(directions):
            # get absolute destination from relative directions
            y, x = to_out.shape[-2:]
            abs_dst = np.zeros(info_.shape, dtype=int)
            abs_dst[..., 0][~to_out] = (np.arange(y, dtype=int)[:, np.newaxis]
                                        + info_[..., 0])[~to_out]
            abs_dst[..., 1][~to_out] = (np.arange(x, dtype=int)[np.newaxis, :]
                                        + info_[..., 1])[~to_out]
            # avoid IndexError by arbitrarily setting (0, 0) where domain outflow
            abs_dst[..., 0][to_out] = 0
            abs_dst[..., 1][to_out] = 0

            # use destination on mask to determine if towards masked location
            to_msk = directions.mask[tuple(abs_dst.T)].T

            # eliminate previous arbitrary action that avoided IndexError
            to_msk[to_out] = False

            # set relative direction to special value 9
            # where outflow towards masked location
            info_[..., 0][to_msk] = 9
            info_[..., 1][to_msk] = 9

        else:
            to_msk = np.zeros(shp, dtype=bool)

        # pre-process some convenience masks out of main routing mask
        # to avoid generating them every time *route* method is called

        # Y-wards movement
        for j in [-1, 0, 1]:
            # X-wards movement
            for i in [-1, 0, 1]:
                # note: special value 9 set previously allows here to
                # ignore them in the routing masks
                self._routing_masks[(j, i)] = (
                        (info_[..., 0] == j) & (info_[..., 1] == i)
                )
        # OUT-wards movement
        # (i.e. towards outside domain or towards masked location)
        self._routing_out_mask = to_out | to_msk

    def route(self, values_to_route):
        """Move the given values from their current location in the
        `Grid` to their downstream/downslope location according to the
        *flow_direction* property of `Grid`.

        :Parameters:

            values_to_route: `numpy.ndarray`
                The values to route following the flow direction, e.g.
                how river discharge to route. The shape of this array
                must be the same as of the grid.

        :Returns:

            values_routed: `numpy.ndarray`
                The values routed following the flow direction, e.g. how
                much river discharge is coming into each grid element
                from their upstream grid elements. The shape of this
                array is the same as of the grid.

            values_out: `numpy.ndarray`
                The values that routed following the flow direction would
                have left the domain (a value is considered to leave the
                domain if it is directed towards beyond the bounds of
                of the domain, or towards a masked location within the
                domain, if the *flow_direction* is masked), e.g. how
                much river discharge has not been routed towards the
                downstream grid element because this one is not defined
                (i.e. outside the grid) or masked (i.e. outside the
                drainage area or into the sea). The shape of this array
                is the same as of the grid.

        **Examples**

        .. warning ::

           Given that Y and X `Grid` coordinates are ordered increasingly
           northwards and eastwards, respectively, and given that a 2D
           `numpy.ndarray` origin (i.e. [0, 0]) is in the upper-left
           corner when visualising the content of an array (i.e. using
           `print`), routing a value northwards will result in visualising
           it "moving down" the array (and not up), and routing a value
           eastwards will result in visualising it "moving right".

        Using grid routing functionality with basic domain and flow direction:

        >>> import numpy
        >>> grid = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(51, 55),
        ...     latitude_resolution=1,
        ...     longitude_extent=(-2, 1),
        ...     longitude_resolution=1
        ... )
        >>> values = numpy.arange(12).reshape(4, 3) + 1
        >>> print(values)
        [[ 1  2  3]
         [ 4  5  6]
         [ 7  8  9]
         [10 11 12]]
        >>> directions = grid.to_field()
        >>> directions.set_data(numpy.array([['NE', 'N', 'E'],
        ...                                  ['SE', 'E', 'S'],
        ...                                  ['N', 'N', 'W'],
        ...                                  ['SW', 'E', 'NW']]))
        >>> grid.flow_direction = directions
        >>> moved, out = grid.route(values)
        >>> print(moved)
        [[ 0  4  6]
         [ 0  3  5]
         [ 0  9  0]
         [ 7  8 11]]
        >>> print(out)
        [[ 0  0  3]
         [ 0  0  0]
         [ 0  0  0]
         [10  0 12]]

        Using grid routing functionality with masked flow direction:

        >>> directions.set_data(
        ...     numpy.ma.array(
        ...         [['NE', 'N', 'E'],
        ...          ['SE', 'E', 'S'],
        ...          ['N', 'N', 'W'],
        ...          ['SW', 'E', 'NW']],
        ...         mask=[[1, 0, 0],
        ...               [1, 0, 0],
        ...               [1, 1, 0],
        ...               [0, 0, 0]]
        ...     )
        ... )
        >>> grid.flow_direction = directions
        >>> moved, out = grid.route(values)
        >>> print(moved)
        [[-- 0 6]
         [-- 2 5]
         [-- -- 0]
         [0 0 11]]
        >>> print(out)
        [[-- 0 3]
         [-- 0 0]
         [-- -- 9]
         [10 0 12]]

        Using grid routing functionality with a wrap-around domain:

        >>> grid = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(-90, 90),
        ...     latitude_resolution=45,
        ...     longitude_extent=(-180, 180),
        ...     longitude_resolution=120
        ... )
        >>> values = numpy.arange(12).reshape(4, 3) + 1
        >>> print(values)
        [[ 1  2  3]
         [ 4  5  6]
         [ 7  8  9]
         [10 11 12]]
        >>> directions = grid.to_field()
        >>> directions.set_data(numpy.array([['NE', 'N', 'E'],
        ...                                  ['SE', 'E', 'S'],
        ...                                  ['N', 'N', 'W'],
        ...                                  ['SW', 'E', 'NW']]))
        >>> grid.flow_direction = directions
        >>> moved, out = grid.route(values)
        >>> print(moved)
        [[ 3 16  6]
         [ 0  3  5]
         [ 0  9 10]
         [ 7  8 11]]
        >>> print(out)
        [[0 0 0]
         [0 0 0]
         [0 0 0]
         [0 0 0]]

        Using grid routing functionality on a whole cartesian domain:

        >>> grid = BritishNationalGrid.from_extent_and_resolution(
        ...     projection_y_coordinate_extent=(0, 1300000),
        ...     projection_y_coordinate_resolution=325000,
        ...     projection_x_coordinate_extent=(0, 700000),
        ...     projection_x_coordinate_resolution=700000/3
        ... )
        >>> values = numpy.arange(12).reshape(4, 3) + 1
        >>> directions = grid.to_field()
        >>> directions.set_data(numpy.array([['NE', 'N', 'E'],
        ...                                  ['SE', 'E', 'S'],
        ...                                  ['N', 'N', 'W'],
        ...                                  ['SW', 'E', 'NW']]))
        >>> grid.flow_direction = directions
        >>> moved, out = grid.route(values)
        >>> print(moved)
        [[ 0  4  6]
         [ 0  3  5]
         [ 0  9  0]
         [ 7  8 11]]
        >>> print(out)
        [[ 0  0  3]
         [ 0  0  0]
         [ 0  0  0]
         [10  0 12]]
        """
        # check whether method can be used
        if self.flow_direction is None:
            raise RuntimeError("method 'route' requires setting "
                               "property 'flow_direction'")

        # check that values_to_route has the same shape as flow_direction
        if not self.flow_direction.shape[:-1] == values_to_route.shape:
            raise RuntimeError("shape mismatch between 'values_to_route' "
                               "and 'flow_direction' in 'route' method")

        # initialise routed and out arrays depending on mask/no-mask
        if np.ma.is_masked(self.flow_direction):
            mask = self.flow_direction.mask[..., 0]
            values_routed = np.ma.array(
                np.zeros(values_to_route.shape, values_to_route.dtype),
                mask=mask
            )
            values_out = np.ma.array(
                np.zeros(values_to_route.shape, values_to_route.dtype),
                mask=mask
            )
        else:
            mask = None
            values_routed = np.zeros(values_to_route.shape,
                                     values_to_route.dtype)
            values_out = np.zeros(values_to_route.shape,
                                  values_to_route.dtype)
        # if no mask, keep as is, if not, take logical negation of it
        mask = None if mask is None else ~mask

        # collect the values routed towards outside the domain
        out_mask = self._routing_out_mask
        if np.ma.is_masked(self.flow_direction):
            values_out[out_mask & mask] = values_to_route[out_mask & mask]
        else:
            values_out[out_mask] = values_to_route[out_mask]

        # perform the routing using the routing mask
        # Y-wards movement
        for j in [-1, 0, 1]:
            # X-wards movement
            for i in [-1, 0, 1]:
                routing_mask = self._routing_masks[(j, i)]
                values_routed[mask] += np.roll(
                    values_to_route * routing_mask,
                    shift=(j, i), axis=(-2, -1)
                )[mask]

        return values_routed, values_out

    @property
    def cell_area(self):
        """The horizontal area for the grid cells of the `Grid` in
        square metres given as a `cf.Field` and returned as a
        `numpy.ndarray`.

        :Parameters:

            areas: `cf.Field`
                The field containing the horizontal grid cell area. The
                shape of the data array must be the same as the `Grid`.
                The field data must contain surface area values in
                square metres.

        :Returns:

            `numpy.ndarray`
                The array containing the horizontal grid cell area
                values in square metres. If not set previously, computed
                automatically.

        **Examples**

        >>> grid = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(51, 55),
        ...     latitude_resolution=1,
        ...     longitude_extent=(-2, 1),
        ...     longitude_resolution=1
        ... )
        >>> print(grid.cell_area)
        [[7.69725703e+09 7.69725703e+09 7.69725703e+09]
         [7.52719193e+09 7.52719193e+09 7.52719193e+09]
         [7.35483450e+09 7.35483450e+09 7.35483450e+09]
         [7.18023725e+09 7.18023725e+09 7.18023725e+09]]
        >>> print(grid)  # doctest: +ELLIPSIS
        LatLonGrid(
            shape {Y, X}: (4, 3)
            Y, latitude (4,): [51.5, ..., 54.5] degrees_north
            X, longitude (3,): [-1.5, -0.5, 0.5] degrees_east
            Y_bounds (4, 2): [[51.0, ..., 55.0]] degrees_north
            X_bounds (3, 2): [[-2.0, ..., 1.0]] degrees_east
            cell_area (4, 3): [[7697257030.0..., ..., 7180237253.9...]] m2
        )

        >>> import numpy
        >>> areas = grid.to_field()
        >>> areas.set_data(numpy.array([[7.70e+09, 7.70e+09, 7.70e+09],
        ...                             [7.53e+09, 7.53e+09, 7.53e+09],
        ...                             [7.35e+09, 7.35e+09, 7.35e+09],
        ...                             [7.18e+09, 7.18e+09, 7.18e+09]]))
        >>> areas.units = 'm2'
        >>> grid.cell_area = areas
        >>> print(grid.cell_area)
        [[7.70e+09 7.70e+09 7.70e+09]
         [7.53e+09 7.53e+09 7.53e+09]
         [7.35e+09 7.35e+09 7.35e+09]
         [7.18e+09 7.18e+09 7.18e+09]]

        """
        if self._cell_area is None:
            self._cell_area = self._compute_cell_area()
        return self._cell_area

    @cell_area.setter
    def cell_area(self, areas):
        error_dim = RuntimeError(
            f"cell_area shape incompatible with {self.__class__.__name__}"
        )
        error_units = ValueError(
            "cell_area units are missing or not in square metres"
        )

        # check type
        if not isinstance(areas, cf.Field):
            raise TypeError("cell_area not a cf.Field")
        # store given field for config file
        self._cell_area_field = areas

        # drop potential size-1 Z axis since areas is
        # only relevant horizontally
        if areas.domain_axis(self.vertical_axis, key=True, default=False):
            areas.squeeze(self.vertical_axis, inplace=True)

        # check that mask and spacedomain are compatible
        grid = self.to_horizontal_grid()
        try:
            areas = grid.subset_and_compare(areas)
        except RuntimeError:
            raise error_dim

        # check area units
        if not (areas.data.has_units()
                and cfunits.Units('m2').equals(areas.Units)):
            raise error_units

        # get field's data array
        areas = areas.array

        self._cell_area = areas

    def _compute_cell_area(self):
        # make use of cf-python to retrieve ESMF objects
        operator = self._f.regrids(
            self._f, 'conservative', return_operator=True
        )
        # retrieve ESMF source (arbitrarily chosen) field
        esmf_field = operator.regrid.srcfield

        # let ESMF compute the cell area
        esmf_field.get_area()
        # retrieve the values and scale them from unit sphere to Earth
        area_unit_sphere = esmf_field.data.T
        area = area_unit_sphere * self._earth_radius_m ** 2

        return area

    @staticmethod
    def _check_dimension_limits(dimension, name, limits):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_limits(  # scalar
        ...     numpy.array(-1.), 'test', (-2, 2))
        >>> Grid._check_dimension_limits(  # no wrap around
        ...     numpy.array([-1., 0., 1., 2.]), 'test', (-2, 2))
        >>> Grid._check_dimension_limits(  # wrap around
        ...     numpy.array([0.5, 1.5, -1.5]), 'test', (-2, 2))
        >>> Grid._check_dimension_limits(  # exceed lower limit
        ...     numpy.array([-3., -2., -1.]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension beyond limits [-2, 2]
        >>> Grid._check_dimension_limits(  # exceed upper limit
        ...     numpy.array([1., 2., 3.]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension beyond limits [-2, 2]

        >>> Grid._check_dimension_limits(  # wrapping around repetition
        ...     numpy.array([0., 1., 2., -1., 0.]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: duplicates in test dimension: [0.]
        """
        # check for values outside of limits
        if limits is not None:
            if np.amin(dimension) < limits[0] or np.amax(dimension) > limits[1]:
                raise RuntimeError(f"{name} dimension beyond limits "
                                   f"[{limits[0]}, {limits[1]}]")

        # check for duplicated coordinates, meaning domain overlap
        # for cyclic dimensions, but should not happen anyway so check
        # for non-cyclic dimensions too
        if dimension.ndim > 0:
            sort_dim = np.sort(dimension)
            dup_dim = sort_dim[1:][sort_dim[1:] == sort_dim[:-1]]
            if dup_dim.size > 0:
                raise RuntimeError(f"duplicates in {name} dimension: {dup_dim}")

    @staticmethod
    def _check_dimension_direction(dimension, name, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_direction(  # scalar
        ...     numpy.array(1.), 'test', (-2, 2), False)
        >>> Grid._check_dimension_direction(  # not cyclic, no wrap around
        ...     numpy.array([0., 1., 2.]), 'test', (-2, 2), False)
        >>> Grid._check_dimension_direction(  # cyclic, no wrap around
        ...     numpy.array([0., 1., 2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_direction(  # cyclic, wrap around, sign case 1
        ...     numpy.array([-1., 0., 2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_direction(  # cyclic, wrap around, sign case 2
        ...     numpy.array([-1., 0., -2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_direction(  # cyclic, wrap around, end
        ...     numpy.array([0., 2., -2.]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_direction(  # cyclic, wrap around, start
        ...     numpy.array([2., -2., 0.]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_direction(  # negative direction
        ...     numpy.array([2., 1., 0.]), 'test', (-2, 2), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension not directed positively
        """
        error = RuntimeError(f"{name} dimension not directed positively")

        if dimension.ndim > 0:
            space_diff = np.diff(dimension)
            if wrap_around:
                if np.any(space_diff < 0):
                    # add one full rotation to first negative difference
                    # to assume it is wrapping around (since positive
                    # direction is required, and cross-over can happen
                    # at most once without domain wrapping on itself)
                    neg = space_diff[space_diff < 0]
                    neg[0] += limits[1] - limits[0]
                    space_diff[space_diff < 0] = neg
        else:
            # it is a scalar, set difference to one to pass next check
            space_diff = 1
        if not np.all(space_diff > 0):
            # if not all positive, at least one space gap is in
            # negative direction
            raise error

    @staticmethod
    def _check_dimension_regularity(dimension, name, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_regularity(  # scalar
        ...     numpy.array(1.), 'test', (-2, 2), False)
        >>> Grid._check_dimension_regularity(  # not cyclic, no wrap around
        ...     numpy.array([0., 1., 2.]), 'test', (-2, 2), False)
        >>> Grid._check_dimension_regularity(  # cyclic, no wrap around
        ...     numpy.array([0., 1., 2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_regularity(  # cyclic, wrap around, sign case 1
        ...     numpy.array([-2., 0., 2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_regularity(  # cyclic, wrap around, sign case 2
        ...     numpy.array([-2., 0., -2.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_regularity(  # cyclic, wrap around, end
        ...     numpy.array([.9, 1.9, -1.1]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_regularity(  # cyclic, wrap around, start
        ...     numpy.array([1.9, -1.1, -0.1]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_regularity(  # irregular, not cyclic
        ...     numpy.array([0., .9, 1.]), 'test', (-2, 2), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test space gap not constant across region
        >>> Grid._check_dimension_regularity(  # irregular, cyclic
        ...     numpy.array([1., 1.9, -1]), 'test', (-2, 2), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test space gap not constant across region
        """
        if dimension.ndim > 0:
            space_diff = np.diff(dimension)
            if wrap_around:
                if np.any(space_diff < 0):
                    # add one full rotation to first negative difference
                    # to assume it is wrapping around (since positive
                    # direction is required, and cross-over can happen
                    # at most once without domain wrapping on itself)
                    neg = space_diff[space_diff < 0]
                    neg[0] += limits[1] - limits[0]
                    space_diff[space_diff < 0] = neg
        else:
            # it is a scalar, set difference to one to pass next check
            space_diff = 1
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol(), atol()):
            raise RuntimeError(
                f"{name} space gap not constant across region"
            )

    @staticmethod
    def _check_dimension_bounds_limits(bounds, name, limits):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_limits(  # 1D
        ...     numpy.array([0., -1.]), 'test', (-2, 2))
        >>> Grid._check_dimension_bounds_limits(  # 2D, edging upper limit
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]), 'test', (-3, 3))
        >>> Grid._check_dimension_bounds_limits(  # 2D, edging lower limit
        ...     numpy.array([[-3., -2.], [-2., -1.], [-1., 0.]]), 'test', (-3, 3))
        >>> Grid._check_dimension_bounds_limits(  # 1D, beyond upper limit
        ...     numpy.array([0., 3.]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds beyond limits [-2, 2]
        >>> Grid._check_dimension_bounds_limits(  # 2D, beyond upper limit
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds beyond limits [-2, 2]
        >>> Grid._check_dimension_bounds_limits(  # 2D, beyond lower limit
        ...     numpy.array([[-3., -2.], [-2., -1.], [-1., 0.]]), 'test', (-2, 2))
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds beyond limits [-2, 2]
        """
        if limits is not None:
            if np.amin(bounds) < limits[0] or np.amax(bounds) > limits[1]:
                raise RuntimeError(f"{name} dimension bounds beyond limits "
                                   f"[{limits[0]}, {limits[1]}]")

    @staticmethod
    def _check_dimension_bounds_direction(bounds, name, limits, wrap_around):
        """
        TODO: Last example should raise error because last pair of
              bounds is either in the negative direction or a second
              wrap around, but because the algorithm allows for up to
              two negative differences to cover for a pair of bounds
              across the limits, the negative value for this last pair
              is caught in the assumption it is a wrap around, while the
              first wrap around only generated one negative difference,
              so the second negative difference was tolerated
              erroneously. This is likely to be really an edge case, so
              it is kept as is for now. Plus, it is caught as an error
              in `_check_dimension_bounds_regularity`.

        **Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_direction(  # 1D, not cyclic
        ...     numpy.array([0., 1.]), 'test', (-2, 2), False)
        >>> Grid._check_dimension_bounds_direction(  # 1D, cyclic, no wrap around
        ...     numpy.array([0., 1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_direction(  # 1D, cyclic, wrap around
        ...     numpy.array([0., -1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, not cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), False)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic, wrap around, bound across
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic, wrap around, bound edging, sign case 1
        ...     numpy.array([[1., 2.], [2., 3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic, wrap around, bound edging, sign case 2
        ...     numpy.array([[1., 2.], [2., 3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic, wrap around, bound edging, sign case 3
        ...     numpy.array([[1., 2.], [2., -3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # 2D, cyclic, wrap around, bound edging, sign case 4
        ...     numpy.array([[1., 2.], [2., -3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_direction(  # negative direction
        ...     numpy.array([2., 1.]), 'test', (-2, 2), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds not directed positively
        >>> Grid._check_dimension_bounds_direction(  # not cyclic but wrap around
        ...     numpy.array([0., -1.]), 'test', (-2, 2), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds not directed positively
        >>> Grid._check_dimension_bounds_direction(  # negative direction, not cyclic
        ...     numpy.array([[3., 2.], [2., 1.], [1., 0.]]), 'test', (-3, 3), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds not directed positively
        >>> Grid._check_dimension_bounds_direction(  # negative direction, cyclic
        ...     numpy.array([[3., 2.], [2., 1.], [1., 0.]]), 'test', (-3, 3), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds not directed positively
        >>> Grid._check_dimension_bounds_direction(  # wrap around, negative after
        ...     numpy.array([[2., 3.], [-3., -2.], [-1., -2.]]), 'test', (-3, 3), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test dimension bounds not directed positively
        >>> Grid._check_dimension_bounds_direction(  # [!] current bug
        ...     numpy.array([[1., 2.], [-2., -1.], [-1., -2]]), 'test', (-2, 2), True)
        """
        # replace lower limit by upper limit to acknowledge it is same
        # location (e.g. -180degE same as +180degE, so replace -180degE
        # by +180degE)
        bnds = deepcopy(bounds)
        if wrap_around:
            bnds[np.isclose(bnds, limits[0], rtol(), atol())] = limits[1]

        error = RuntimeError(f"{name} dimension bounds not directed positively")

        if bnds.ndim > 0:
            space_diff = np.diff(bnds, axis=0)
            if wrap_around:
                if np.any(space_diff <= 0):
                    # add one full rotation to first and second negative
                    # differences to assume it is wrapping around (since
                    # positive direction is required, and cross-over
                    # can happen at most once without domain wrapping on
                    # itself)
                    neg = space_diff[space_diff <= 0]
                    neg[0:2] += limits[1] - limits[0]
                    space_diff[space_diff <= 0] = neg
        else:
            # it is a scalar, set difference to one to pass next check
            space_diff = 1
        if not np.all(space_diff > 0):
            raise error

        if bnds.ndim > 1:
            space_diff = np.diff(bnds, axis=1)
            if wrap_around:
                if np.any(space_diff <= 0):
                    # add one full rotation to first negative difference
                    # to assume it is wrapping around (since positive
                    # direction is required, and cross-over can happen
                    # at most once without domain wrapping on itself)
                    neg = space_diff[space_diff <= 0]
                    neg[0] += limits[1] - limits[0]
                    space_diff[space_diff <= 0] = neg
        else:
            # it is a scalar, set difference to one to pass next check
            space_diff = 1
        if not np.all(space_diff > 0):
            raise error

    @staticmethod
    def _check_dimension_bounds_regularity(bounds, name, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_regularity(  # 1D, not cyclic
        ...     numpy.array([0., 1.]), 'test', (-2, 2), False)
        >>> Grid._check_dimension_bounds_regularity(  # 1D, cyclic, no wrap around
        ...     numpy.array([0., 1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around
        ...     numpy.array([0., -1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, not cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), False)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around, bound across
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around, bound edging, sign case 1
        ...     numpy.array([[1., 2.], [2., 3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around, bound edging, sign case 2
        ...     numpy.array([[1., 2.], [2., 3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around, bound edging, sign case 3
        ...     numpy.array([[1., 2.], [2., -3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # 2D, cyclic, wrap around, bound edging, sign case 4
        ...     numpy.array([[1., 2.], [2., -3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_regularity(  # irregular (not cyclic)
        ...     numpy.array([[0., .9], [.9, 2.], [2., 3.]]), 'test', (0, 3), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        >>> Grid._check_dimension_bounds_regularity(  # irregular (cyclic)
        ...     numpy.array([[0., .9], [.9, 2.], [2., 3.]]), 'test', (-2, 2), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        >>> Grid._check_dimension_bounds_regularity(  # not cyclic, no wrap around
        ...     numpy.array([[1., 2.], [2., -1.], [-1., 0.]]), 'test', (-2, 2), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        >>> Grid._check_dimension_bounds_regularity(  # gap
        ...     numpy.array([[-1., 0.], [0., 1.], [2., 3.]]), 'test', (-3, 3), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        >>> Grid._check_dimension_bounds_regularity(  # inverted direction
        ...     numpy.array([[1., 2.], [-2., -1.], [-1., -2]]), 'test', (-2, 2), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        """
        rtol_ = rtol()
        atol_ = atol()

        # replace lower limit by upper limit to acknowledge it is same
        # location (e.g. -180degE same as +180degE, so replace -180degE
        # by +180degE)
        bnds = deepcopy(bounds)
        if wrap_around:
            bnds[np.isclose(bnds, limits[0], rtol_, atol_)] = limits[1]

        error = RuntimeError(f"{name} bounds space gap not constant across region")

        if bnds.ndim > 0:
            space_diff = np.diff(bnds, axis=0)
            if wrap_around:
                if np.any(space_diff < 0):
                    # add one full rotation to first and second negative
                    # differences to assume it is wrapping around (since
                    # positive  direction is required, and cross-over
                    # can happen at most once without domain wrapping on
                    # itself)
                    neg = space_diff[space_diff < 0]
                    neg[0:2] += limits[1] - limits[0]
                    space_diff[space_diff < 0] = neg
        else:
            space_diff = 0
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol_, atol_):
            raise error

        if bnds.ndim > 1:
            space_diff = np.diff(bnds, axis=1)
            if wrap_around:
                if np.any(space_diff < 0):
                    # add one full rotation to first negative difference
                    # to assume it is wrapping around (since positive
                    # direction is required, and cross-over can happen
                    # at most once without domain wrapping on itself)
                    neg = space_diff[space_diff < 0]
                    neg[0] += limits[1] - limits[0]
                    space_diff[space_diff < 0] = neg
        else:
            space_diff = 0
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol_, atol_):
            raise error

    @staticmethod
    def _check_dimension_bounds_contiguity(bounds, name, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_contiguity(  # 1D, not cyclic
        ...     numpy.array([0., 1.]), 'test', (-2, 2), False)
        >>> Grid._check_dimension_bounds_contiguity(  # 1D, cyclic, no wrap around
        ...     numpy.array([0., 1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around
        ...     numpy.array([0., -1.]), 'test', (-2, 2), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, not cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), False)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic
        ...     numpy.array([[-1., 0.], [0., 1.], [1., 2.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around, bound across
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around, bound edging, sign case 1
        ...     numpy.array([[1., 2.], [2., 3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around, bound edging, sign case 2
        ...     numpy.array([[1., 2.], [2., 3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around, bound edging, sign case 3
        ...     numpy.array([[1., 2.], [2., -3.], [3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # 2D, cyclic, wrap around, bound edging, sign case 4
        ...     numpy.array([[1., 2.], [2., -3.], [-3., -2.], [-2., -1.]]), 'test', (-3, 3), True)
        >>> Grid._check_dimension_bounds_contiguity(  # gaps (not cyclic)
        ...     numpy.array([[0.0, 0.9], [1.0, 1.9], [2.0, 2.9]]), 'test', (-3, 3), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds not contiguous across region
        >>> Grid._check_dimension_bounds_contiguity(  # gaps (cyclic)
        ...     numpy.array([[0.0, 0.9], [1.0, 1.9], [-2.0, -1.1]]), 'test', (-2, 2), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds not contiguous across region
        """
        rtol_ = rtol()
        atol_ = atol()

        # replace lower limit by upper limit to acknowledge it is same
        # location (e.g. -180degE same as +180degE, so replace -180degE
        # by +180degE)
        bnds = deepcopy(bounds)
        if wrap_around:
            bnds[np.isclose(bnds, limits[0], rtol_, atol_)] = limits[1]

        # compare previous upper bound to next lower bound
        prev_to_next = (bnds[1:, 0] - bnds[:-1, 1]
                        if bnds.ndim > 1 else 0)
        if not np.allclose(prev_to_next, 0, rtol_, atol_):
            raise RuntimeError(f"{name} bounds not contiguous across region")

    @staticmethod
    def _check_dimension_in_bounds(dimension, bounds, name, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_in_bounds(  # 1 coord, not cyclic
        ...     numpy.array(.5), numpy.array([0., 1.]), 'test', (0, 2), False)
        >>> Grid._check_dimension_in_bounds(  # 1 coord, cyclic, no wrap around
        ...     numpy.array(.5), numpy.array([0., 1.]), 'test', (0, 2), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, not cyclic
        ...     numpy.array([0.5, 1.5, 2.5]),
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]),
        ...     'test', (0, 3), False)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, no wrap around
        ...     numpy.array([0.5, 1.5, 2.5]),
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]),
        ...     'test', (0, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around
        ...     numpy.array([0.5, 1.5, -1.5]),
        ...     numpy.array([[0., 1.], [1., 2.], [2., -1.]]),
        ...     'test', (-2, 2), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound across, sign case 1
        ...     numpy.array([2., 3., -2.]),
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound across, sign case 2
        ...     numpy.array([2., -3., -2.]),
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound edging, sign case 1
        ...     numpy.array([1.5, 2.5, -2.5, -1.5]),
        ...     numpy.array([[1., 2.], [2., 3.], [3., -2.], [-2., -1.]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound edging, sign case 2
        ...     numpy.array([1.5, 2.5, -2.5, -1.5]),
        ...     numpy.array([[1., 2.], [2., 3.], [-3., -2.], [-2., -1.]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound edging, sign case 3
        ...     numpy.array([1.5, 2.5, -2.5, -1.5]),
        ...     numpy.array([[1., 2.], [2., -3.], [3., -2.], [-2., -1.]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # x coords, cyclic, wrap around, bound edging, sign case 4
        ...     numpy.array([1.5, 2.5, -2.5, -1.5]),
        ...     numpy.array([[1., 2.], [2., -3.], [-3., -2.], [-2., -1.]]),
        ...     'test', (-3, 3), True)
        >>> Grid._check_dimension_in_bounds(  # last coord not in its bounds, not cyclic
        ...     numpy.array([0.5, 1.5, 1.9]),
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]),
        ...     'test', (0, 3), False)
        Traceback (most recent call last):
            ...
        RuntimeError: test coordinates not all in their bounds
        >>> Grid._check_dimension_in_bounds(  # last coord not in its bounds, cyclic, wrap around
        ...     numpy.array([2., -2., -2.]),
        ...     numpy.array([[1.5, 2.5], [2.5, -2.5], [-2.5, -1.5]]),
        ...     'test', (-3, 3), True)
        Traceback (most recent call last):
            ...
        RuntimeError: test coordinates not all in their bounds
        """
        # replace lower limit by upper limit to acknowledge it is same
        # location (e.g. -180degE same as +180degE, so replace -180degE
        # by +180degE)
        bnds = deepcopy(bounds)
        if wrap_around:
            bnds[np.isclose(bnds, limits[0], rtol(), atol())] = limits[1]

        # check if coordinates inside their bounds
        if dimension.ndim > 0:
            inside = (bnds[:, 0] <= dimension) & (dimension <= bnds[:, 1])
            if wrap_around:
                if np.sum(~inside) >= 1:
                    not_in_dim = dimension[~inside]
                    not_in_bnds = bnds[~inside]
                    not_in = inside[~inside]
                    # add one full rotation to upper bound in first
                    # inequality to assume it is wrapping around
                    if ((not_in_bnds[0, 0] <= not_in_dim[0])
                            & (not_in_dim[0] > not_in_bnds[0, 1])):
                        not_in[0] = ((not_in_bnds[0, 0] <= not_in_dim[0])
                                     & (not_in_dim[0] <= (not_in_bnds[0, 1]
                                                          + limits[1]
                                                          - limits[0])))
                    # remove one full rotation to lower bound in first
                    # inequality to assume it is wrapping around
                    elif ((not_in_bnds[0, 0] > not_in_dim[0])
                          & (not_in_dim[0] <= not_in_bnds[0, 1])):
                        not_in[0] = (
                                ((not_in_bnds[0, 0] - limits[1] + limits[0])
                                 <= not_in_dim[0])
                                & (not_in_dim[0] <= not_in_bnds[0, 1])
                        )
                    inside[~inside] = not_in
        else:
            inside = (bnds[0] <= dimension) & (dimension <= bnds[1])
            if wrap_around:
                if not inside:
                    # add one full rotation to upper bound in first
                    # inequality to assume it is wrapping around
                    if (bnds[0] <= dimension) & (dimension > bnds[1]):
                        inside = (
                                (bnds[0] <= dimension)
                                & (dimension <= (bnds[1]
                                                 + limits[1] - limits[0]))
                        )
                    # remove one full rotation to lower bound in first
                    # inequality to assume it is wrapping around
                    elif (bnds[0] > dimension) & (dimension <= bnds[1]):
                        inside = (
                                ((bnds[0] - limits[1] + limits[0])
                                 <= dimension)
                                & (dimension <= bnds[1])
                        )

        if not np.all(inside):
            raise RuntimeError(f"{name} coordinates not all in their bounds")

    def _set_space(self, dimension, dimension_bounds, name,
                   units, axis, limits, wrap_around):
        """**Examples:**

        >>> import numpy
        >>> Grid()._set_space([[0.5]], [0., 1.], 'test', '1', 'I', (0, 2), False)
        >>> Grid()._set_space([[0, 1], [1, 2]], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I', (-3, 3), True)
        Traceback (most recent call last):
            ...
        RuntimeError: Grid test not convertible to 1D-array
        >>> Grid()._set_space([0.5, 1.5, 2.5], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I', (-3, 3), True)
        >>> Grid()._set_space([0.5, 1.5], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I', (-3, 3), True)
        Traceback (most recent call last):
            ...
        RuntimeError: Grid test bounds not compatible in size with test coordinates
        """
        # checks on dimension coordinates
        if not isinstance(dimension, np.ndarray):
            dimension = np.asarray(dimension)
        dimension = np.squeeze(dimension)
        if dimension.ndim > 1:
            raise RuntimeError(
                f"{self.__class__.__name__} {name} not convertible to 1D-array"
            )
        self._check_dimension_limits(dimension, name, limits)
        self._check_dimension_direction(dimension, name, limits, wrap_around)
        self._check_dimension_regularity(dimension, name, limits, wrap_around)

        # checks on dimension coordinate bounds
        if not isinstance(dimension_bounds, np.ndarray):
            dimension_bounds = np.asarray(dimension_bounds)
        dimension_bounds = np.squeeze(dimension_bounds)
        if dimension_bounds.shape != (*dimension.shape, 2):
            raise RuntimeError(
                f"{self.__class__.__name__} {name} bounds not compatible "
                f"in size with {name} coordinates"
            )
        self._check_dimension_bounds_limits(dimension_bounds, name, limits)
        self._check_dimension_bounds_direction(
            dimension_bounds, name, limits, wrap_around
        )
        self._check_dimension_bounds_regularity(
            dimension_bounds, name, limits, wrap_around
        )
        self._check_dimension_bounds_contiguity(
            dimension_bounds, name, limits, wrap_around
        )

        # check coordinates in their bounds
        self._check_dimension_in_bounds(
            dimension, dimension_bounds, name, limits, wrap_around
        )

        # deal with special case of dimension with only one-element
        # due to squeeze, dimension is scalar array, dimension_bounds is 1D
        # cf-python will want 1D dimension coordinates, and 2D
        # dimension coordinate bounds, respectively
        if dimension.ndim == 0:
            dimension = np.array([dimension])
            dimension_bounds = np.array([dimension_bounds])

        # set construct
        axis_ = self._f.set_construct(cf.DomainAxis(dimension.size))
        self._f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    'standard_name': name,
                    'units': units,
                    'axis': axis
                },
                data=cf.Data(dimension),
                bounds=cf.Bounds(data=cf.Data(dimension_bounds))),
            axes=axis_
        )

    def _set_dummy_data(self):
        self._f.set_data(cf.Data(np.zeros(self.shape, dtype_float())),
                         axes=self.axes)

    @classmethod
    def _get_grid_from_extent_and_resolution(
            cls,
            y_extent, x_extent, y_resolution, x_resolution, yx_location,
            # z_extent=None, z_resolution=None, z_location=None
    ):
        # infer grid span in relation to coordinate from location
        if yx_location in cls._YX_loc_map['centre']:
            x_span, y_span = [[-0.5, 0.5]], [[-0.5, 0.5]]
        elif yx_location in cls._YX_loc_map['lower_left']:
            x_span, y_span = [[0, 1]], [[0, 1]]
        elif yx_location in cls._YX_loc_map['upper_left']:
            x_span, y_span = [[0, 1]], [[-1, 0]]
        elif yx_location in cls._YX_loc_map['lower_right']:
            x_span, y_span = [[-1, 0]], [[0, 1]]
        elif yx_location in cls._YX_loc_map['upper_right']:
            x_span, y_span = [[-1, 0]], [[-1, 0]]
        else:
            raise ValueError(
                f"{cls.__name__} {cls._Y_name}-{cls._X_name} location "
                f"'{yx_location}' not supported"
            )

        # determine Y and X coordinates and their bounds
        y, y_bounds = cls._get_dimension_from_extent_and_resolution(
            y_extent, y_resolution, y_span, cls._Y_name,
            cls._Y_limits, cls._Y_wrap_around
        )
        x, x_bounds = cls._get_dimension_from_extent_and_resolution(
            x_extent, x_resolution, x_span, cls._X_name,
            cls._X_limits, cls._X_wrap_around
        )

        # # infer Z span in relation to coordinate from location
        # if z_extent is not None and z_resolution is not None:
        #     if z_location in cls._Z_loc_map['centre'] or z_location is None:
        #         z_span = [[-0.5, 0.5]]
        #     elif z_location in cls._Z_loc_map['bottom']:
        #         z_span = [[0, 1]]
        #     elif z_location in cls._Z_loc_map['top']:
        #         z_span = [[-1, 0]]
        #     else:
        #         raise ValueError(
        #             f"{cls.__name__} {cls._Z_name} location '{z_location}' "
        #             f"not supported"
        #         )
        #
        #     # determine latitude and longitude coordinates and their bounds
        #     z, z_bounds = cls._get_dimension_from_extent_and_resolution(
        #         z_extent, z_resolution, z_span, cls._Z_name,
        #         cls._Z_limits, cls._Z_wrap_around
        #     )
        # else:
        #     z = None
        #     z_bounds = None

        return {
            cls._Y_name: y,
            cls._X_name: x,
            # cls._Z_name: z,
            cls._Y_name + '_bounds': y_bounds,
            cls._X_name + '_bounds': x_bounds,
            # cls._Z_name + '_bounds': z_bounds
        }

    @staticmethod
    def _get_dimension_from_extent_and_resolution(extent, resolution, span,
                                                  name, limits, wrap_around):
        # check sign of resolution
        if resolution <= 0:
            raise ValueError(f"{name} resolution must be positive")

        # check extent
        dim_start, dim_end = extent
        if limits is not None:
            if (dim_start < limits[0]) or (dim_start > limits[1]):
                raise ValueError(
                    f"{name} extent start beyond limits "
                    f"[{limits[0]}, {limits[1]}]"
                )
            if (dim_end < limits[0]) or (dim_end > limits[1]):
                raise ValueError(
                    f"{name} extent end beyond limits "
                    f"[{limits[0]}, {limits[1]}]"
                )

        if wrap_around:
            if dim_end == dim_start:
                dim_end += limits[1] - limits[0]
            if dim_end < dim_start:
                dim_end += limits[1] - limits[0]
        else:
            if dim_start == dim_end:
                raise ValueError(f"{name} extent empty")
            if dim_end < dim_start:
                raise ValueError(f"{name} extent oriented negatively")

        # check compatibility between extent and resolution
        # (i.e. need to produce a whole number of grid cells)
        rtol_ = rtol()
        atol_ = atol()
        if np.isclose((dim_end - dim_start) % resolution, 0, rtol_, atol_):
            dim_size = (dim_end - dim_start) // resolution
        elif np.isclose((dim_end - dim_start) % resolution, resolution,
                        rtol_, atol_):
            dim_size = ((dim_end - dim_start) // resolution) + 1
        else:
            raise RuntimeError(
                f"{name} extent and resolution do not define a whole number "
                f"of grid cells"
            )

        # determine dimension coordinates
        dim = (
                (np.arange(dim_size) + 0.5 - np.mean(span))
                * resolution + dim_start
        )

        # determine dimension coordinate bounds
        dim_bounds = (
                dim.reshape((dim.size, -1)) +
                np.array(span) * resolution
        )

        # deal with wrap around values
        if wrap_around:
            dim[dim > limits[1]] -= limits[1] - limits[0]
            dim_bounds[dim_bounds > limits[1]] -= limits[1] - limits[0]

        # round the arrays and return them
        decr_ = decr()
        return (
            np.around(dim, decimals=decr_).tolist(),
            np.around(dim_bounds, decimals=decr_).tolist()
        )

    def _get_dimension_resolution(self, axis):
        # return dimension extent (i.e. (start, end) for dimension)
        if getattr(self, axis) is None:
            return None
        else:
            # try to use _resolution attribute
            # (available if instantiated via method from_extent_and_resolution)
            if hasattr(self, '_resolution'):
                return self._resolution[axis]
            # infer from first and second coordinates along dimension
            else:
                dim = getattr(self, axis).array
                dim_bnds = getattr(self, f'{axis}_bounds').array
                return np.around(dim[1] - dim[0] if dim.size > 1
                                 else dim_bnds[0, 1] - dim_bnds[0, 0],
                                 decr()).tolist()

    def _get_dimension_extent(self, axis):
        # return dimension extent (i.e. (start, end) for dimension)
        if getattr(self, axis) is None:
            return None
        else:
            # try to use _extent attribute
            # (available if instantiated via method from_extent_and_resolution)
            if hasattr(self, '_extent'):
                return self._extent[axis]
            # infer from first coordinate lower/upper bounds along dimension
            else:
                decr_ = decr()
                dim_bnds = getattr(self, f'{axis}_bounds').array
                return (np.around(dim_bnds[0, 0], decr_).tolist(),
                        np.around(dim_bnds[-1, -1], decr_).tolist())

    def _get_dimension_span(self, axis):
        if getattr(self, axis) is None:
            return None
        else:
            # infer dimension span from first coordinate and its bounds
            # (i.e. relative location of bounds around coordinate)
            dim = getattr(self, axis).array
            dim_bnds = getattr(self, f'{axis}_bounds').array
            dim_res = self._get_dimension_resolution(axis)

            left_wing = (dim_bnds[0, 0] - dim[0]) / dim_res
            right_wing = (dim_bnds[0, 1] - dim[0]) / dim_res

            decr_ = decr()
            return (np.around(left_wing, decr_).tolist(),
                    np.around(right_wing, decr_).tolist())

    def _get_yx_location(self):
        # return location of Y/X coordinates relative to their grid cell

        # try to use _location attribute
        # (available if instantiated via method from_extent_and_resolution)
        if hasattr(self, '_location'):
            return self._location['YX']
        # infer YX location from spans
        else:
            x_span = self._get_dimension_span('X')
            y_span = self._get_dimension_span('Y')

            rtol_ = rtol()
            atol_ = atol()

            if (np.allclose(x_span, [-0.5, 0.5], rtol_, atol_)
                    and np.allclose(y_span, [-0.5, 0.5], rtol_, atol_)):
                yx_loc = 'centre'
            elif (np.allclose(x_span, [0, 1], rtol_, atol_)
                  and np.allclose(y_span, [0, 1], rtol_, atol_)):
                yx_loc = 'lower_left'
            elif (np.allclose(x_span, [0, 1], rtol_, atol_)
                  and np.allclose(y_span, [-1, 0], rtol_, atol_)):
                yx_loc = 'upper_left'
            elif (np.allclose(x_span, [-1, 0], rtol_, atol_)
                  and np.allclose(y_span, [0, 1], rtol_, atol_)):
                yx_loc = 'lower_right'
            elif (np.allclose(x_span, [-1, 0], rtol_, atol_)
                  and np.allclose(y_span, [-1, 0], rtol_, atol_)):
                yx_loc = 'upper_right'
            else:
                yx_loc = None

            return yx_loc

    def _get_z_location(self):
        # return location of Z coordinate relative to its grid cell
        if self.Z is None:
            return None
        else:
            # try to use _location attribute
            # (available if instantiated via method from_extent_and_resolution)
            if hasattr(self, '_location'):
                return self._location['Z']
            # infer Z location from span
            else:
                z_span = self._get_dimension_span('Z')

                rtol_ = rtol()
                atol_ = atol()

                if np.allclose(z_span, [-0.5, 0.5], rtol_, atol_):
                    z_loc = 'centre'
                elif np.allclose(z_span, [0, 1], rtol_, atol_):
                    z_loc = 'bottom'
                elif np.allclose(z_span, [-1, 0], rtol_, atol_):
                    z_loc = 'top'
                else:
                    z_loc = None

                return z_loc

    @classmethod
    def _extract_xyz_from_field(cls, field):
        # check dimension coordinates
        if not field.dim(cls._Y_name, default=False):
            raise RuntimeError(
                f"{cls.__name__} field missing '{cls._Y_name}' "
                f"dimension coordinate"
            )
        y = field.dim(cls._Y_name)
        if not field.dim(cls._X_name, default=False):
            raise RuntimeError(
                f"{cls.__name__} field missing '{cls._X_name}' "
                f"dimension coordinate"
            )
        x = field.dim(cls._X_name)
        z_array = None
        z_bounds_array = None
        if field.dim(cls._Z_name, default=False):
            if field.dim(cls._Z_name).has_bounds():
                z_array = field.dim(cls._Z_name).array
                z_units = field.dim(cls._Z_name).units
                z_bounds_array = field.dim(cls._Z_name).bounds.array
                if z_units not in cls._Z_units:
                    raise RuntimeError(
                        f"{cls.__name__} field dimension coordinate "
                        f"'{cls._Z_name}' units are not in {cls._Z_units[0]}"
                    )

        # check units
        if y.units not in cls._Y_units:
            raise RuntimeError(
                f"{cls.__name__} field dimension coordinate "
                f"'{cls._Y_name}' units are not in {cls._Y_units[0]}"
            )
        if x.units not in cls._X_units:
            raise RuntimeError(
                f"{cls.__name__} field dimension coordinate "
                f"'{cls._X_name}' units are not in {cls._X_units[0]}"
            )

        # check bounds
        if not y.has_bounds():
            raise RuntimeError(
                f"{cls.__name__} field dimension coordinate "
                f"'{cls._Y_name}' has no bounds"
            )
        if not x.has_bounds():
            raise RuntimeError(
                f"{cls.__name__} field dimension coordinate "
                f"'{cls._X_name}' has no bounds"
            )

        return {
            'X': x.array, 'X_bounds': x.bounds.array,
            'Y': y.array, 'Y_bounds': y.bounds.array,
            'Z': z_array, 'Z_bounds': z_bounds_array
        }

    def __str__(self):
        has_z = self.has_vertical_axis()
        return "\n".join(
            [f"{self.__class__.__name__}("]
            + [f"    shape {{{', '.join(self.axes)}}}: {self.shape}"]
            + (["    Z, {} {}: {}".format(
                self._f.dim('Z').standard_name,
                self._f.dim('Z').data.shape,
                self._f.dim('Z').data)] if has_z else [])
            + ["    Y, {} {}: {}".format(
                self._f.dim('Y').standard_name,
                self._f.dim('Y').data.shape,
                self._f.dim('Y').data)]
            + ["    X, {} {}: {}".format(
                self._f.dim('X').standard_name,
                self._f.dim('X').data.shape,
                self._f.dim('X').data)]
            + (["    Z_bounds {}: {}".format(
                 self._f.dim('Z').bounds.data.shape,
                 self._f.dim('Z').bounds.data)] if has_z else [])
            + ["    Y_bounds {}: {}".format(
                self._f.dim('Y').bounds.data.shape,
                self._f.dim('Y').bounds.data)]
            + ["    X_bounds {}: {}".format(
                self._f.dim('X').bounds.data.shape,
                self._f.dim('X').bounds.data)]
            + (["    cell_area {}: {}".format(
                self._cell_area.shape,
                cf.Data(self._cell_area, 'm2'))]
               if self._cell_area is not None else [])
            + (["    land_sea_mask {}: {}".format(
                self._land_sea_mask.shape,
                cf.Data(self._land_sea_mask))]
               if self._land_sea_mask is not None else [])
            + (["    flow_direction {}: {}".format(
                self._flow_direction.shape,
                cf.Data(self._flow_direction))]
               if self._flow_direction is not None else [])
            + [")"]
        )

    def is_space_equal_to(self, field, ignore_z=False):
        """Compare equality between the `Grid` and the spatial (X, Y,
        and Z) dimension coordinates in a `cf.Field`.

        The coordinate values, the bounds (if field has some), and the
        units of the field are compared against those of the `Grid`.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against this grid.

            ignore_z: `bool`, optional
                Option to ignore the dimension coordinate along the Z
                axis. If not provided, set to default `False` (i.e. Z is
                not ignored).

        :Returns: `bool`
        """
        rtol_ = rtol()
        atol_ = atol()

        # check whether X/Y dimension coordinates are identical
        x_y = []
        for axis_name in [self._X_name, self._Y_name]:
            # try to retrieve dimension coordinate using name
            dim_coord = field.dim(
                re.compile(r'name={}$'.format(axis_name)), default=None
            )

            if dim_coord is not None:
                # collect properties of given dimension coordinate
                properties = list(dim_coord.properties())
                try:
                    # these will be ignored except for 'units'
                    properties.remove('units')
                except ValueError:
                    pass

                # if field has no bounds, remove them from spacedomain
                bounds = None
                if not dim_coord.has_bounds():
                    bounds = self._f.dim(axis_name).del_bounds()

                # compare dimension coordinates
                try:
                    x_y.append(
                        self._f.dim(axis_name).equals(
                            dim_coord,
                            rtol=rtol_, atol=atol_,
                            ignore_data_type=True,
                            ignore_fill_value=True,
                            ignore_properties=properties
                        )
                    )
                finally:
                    # if bounds were removed, append them back to spacedomain
                    if bounds is not None:
                        self._f.dim(axis_name).set_bounds(bounds)
            else:
                x_y.append(False)

        # check whether Z dimension coordinates are identical (if not ignored)
        if ignore_z:
            z = True
        else:
            if self._f.dim('Z', default=False):
                # try to retrieve dimension coordinate using name
                dim_coord = field.dim(
                    re.compile(r'name={}$'.format(self._Z_name)), default=None
                )

                if dim_coord is not None:
                    # collect properties of given dimension coordinate
                    properties = list(dim_coord.properties())
                    try:
                        # these will be ignored except for 'units'
                        properties.remove('units')
                    except ValueError:
                        pass

                    # compare dimension coordinates
                    z = self._f.dim(self._Z_name).equals(
                        dim_coord,
                        rtol=rtol_, atol=atol_,
                        ignore_data_type=True,
                        ignore_fill_value=True,
                        ignore_properties=properties
                    )
                else:
                    z = False
            elif field.dim('Z', default=False):
                z = False
            else:
                z = True

        return all(x_y) and z

    def spans_same_region_as(self, grid, ignore_z=False):
        """Compare equality in region spanned between the grid
        and another instance of `Grid`.

        For each axis, the lower bound of their first cell and the
        upper bound of their last cell are compared.

        :Parameters:

            grid: `Grid`
                The other grid to be compared against this grid. Note,
                the two grids must be of the same type (e.g.
                `LatLonGrid`).

            ignore_z: `bool`, optional
                If True, the dimension coordinates along the Z axes of
                the `Grid` instances will not be compared. If not
                provided, set to default value `False` (i.e. Z is not
                ignored).

        :Returns: `bool`
        """
        if isinstance(grid, self.__class__):
            start_x = self.X_bounds[[0], [0]] == grid.X_bounds[[0], [0]]
            end_x = self.X_bounds[[-1], [-1]] == grid.X_bounds[[-1], [-1]]

            start_y = self.Y_bounds[[0], [0]] == grid.Y_bounds[[0], [0]]
            end_y = self.Y_bounds[[-1], [-1]] == grid.Y_bounds[[-1], [-1]]

            if ignore_z:
                start_z, end_z = True, True
            else:
                if self.Z_bounds is not None and grid.Z_bounds is not None:
                    start_z = (
                        self.Z_bounds[[0], [0]] == grid.Z_bounds[[0], [0]]
                    ).array.item()
                    end_z = (
                        self.Z_bounds[[-1], [-1]] == grid.Z_bounds[[-1], [-1]]
                    ).array.item()
                elif self.Z_bounds is not None or grid.Z_bounds is not None:
                    start_z, end_z = False, False
                else:
                    start_z, end_z = True, True

            return all((start_x.array.item(), end_x.array.item(),
                        start_y.array.item(), end_y.array.item(),
                        start_z, end_z))

        else:
            raise TypeError(
                f"{self.__class__.__name__} instance cannot be "
                f"compared to {grid.__class__.__name__} instance"
            )

    def is_matched_in(self, grid):
        """Determine whether the horizontal cell bounds of the grid are
        overlapping with the cell bounds of another instance of `Grid`.

        In other words, determine whether the cells of the grid are
        fully containing the cells (i.e. not area fractions) of another
        instance of `Grid`.

        :Parameters:

            grid: `Grid`
                The grid whose cells are checked as being fully
                contained this grid. Note, the two grids must be of
                the same type (e.g. `LatLonGrid`).

        :Returns: `bool`
        """
        if isinstance(grid, self.__class__):
            x_match = (
                np.all(np.in1d(self.X_bounds[:, 0], grid.X_bounds[:, 0]))
                and self.X_bounds.array[-1, -1] == grid.X_bounds.array[-1, -1]
            )
            y_match = (
                np.all(np.in1d(self.Y_bounds[:, 0], grid.Y_bounds[:, 0]))
                and self.Y_bounds.array[-1, -1] == grid.Y_bounds.array[-1, -1]
            )
            return x_match and y_match

        else:
            raise TypeError(
                f"{self.__class__.__name__} instance cannot be "
                f"compared to {grid.__class__.__name__} instance"
            )

    def subset_and_compare(self, field):
        error = RuntimeError(
            f"field not compatible with {self.__class__.__name__}"
        )

        # TODO: include Z axis in subset when 3D components are
        #       effectively supported

        # avoid floating-point error problems by rounding up
        for axis in [self.X_name, self.Y_name]:
            field.dim(axis, error).round(decr(), inplace=True)

        # try to subset in space
        kwargs = {
            self.X_name: cf.wi(*self.X.array[[0, -1]]),
            self.Y_name: cf.wi(*self.Y.array[[0, -1]])
        }
        if field.subspace('test', **kwargs):
            field_subset = field.subspace(**kwargs)
        else:
            raise error

        # check that data and component spacedomains are compatible
        if not self.is_space_equal_to(field_subset):
            raise error

        return field_subset

    @classmethod
    def from_extent_and_resolution(cls, **kwargs):
        inst = cls(
            **cls._get_grid_from_extent_and_resolution(
                kwargs[f'{cls._Y_name}_extent'],
                kwargs[f'{cls._X_name}_extent'],
                kwargs[f'{cls._Y_name}_resolution'],
                kwargs[f'{cls._X_name}_resolution'],
                kwargs[f'{cls._Y_name}_{cls._X_name}_location'],
                # kwargs[f'{cls._Z_name}_extent'],
                # kwargs[f'{cls._Z_name}_resolution'],
                # kwargs[f'{cls._Z_name}_location']
            )
        )

        inst._extent = {
            # 'Z': kwargs[f'{cls._Z_name}_extent'],
            'Y': kwargs[f'{cls._Y_name}_extent'],
            'X': kwargs[f'{cls._X_name}_extent']
        }
        inst._resolution = {
            # 'Z': kwargs[f'{cls._Z_name}_resolution'],
            'Y': kwargs[f'{cls._Y_name}_resolution'],
            'X': kwargs[f'{cls._X_name}_resolution']
        }
        inst._location = {
            # 'Z': kwargs[f'{cls._Z_name}_location'],
            'YX': kwargs[f'{cls._Y_name}_{cls._X_name}_location']
        }

        return inst

    @classmethod
    def from_config(cls, cfg):
        cfg = cfg.copy()
        cfg.pop('class')

        extras = {}
        for extra in ['land_sea_mask', 'flow_direction', 'cell_area']:
            extras[extra] = cfg.pop(extra, None)

        inst = cls.from_extent_and_resolution(**cfg)

        for extra in ['land_sea_mask', 'flow_direction', 'cell_area']:
            value = extras[extra]
            if value is not None:
                setattr(
                    inst, extra,
                    cf.read(value['files']).select_field(value['select'])
                )

        return inst

    def to_config(self):
        extras = {}
        for extra in ['land_sea_mask', 'flow_direction', 'cell_area']:
            attrib = getattr(self, f'_{extra}_field')
            if attrib and attrib.get_filenames():
                extras[extra] = {'files': attrib.get_filenames(),
                                 'select': attrib.identity()}
            else:
                extras[extra] = None

        return {
            'class': self.__class__.__name__,
            f'{self._Y_name}_extent': self._get_dimension_extent('Y'),
            f'{self._Y_name}_resolution': self._get_dimension_resolution('Y'),
            f'{self._X_name}_extent': self._get_dimension_extent('X'),
            f'{self._X_name}_resolution': self._get_dimension_resolution('X'),
            f'{self._Y_name}_{self._X_name}_location': self._get_yx_location(),
            # f'{self._Z_name}_extent': self._get_dimension_extent('Z'),
            # f'{self._Z_name}_resolution': self._get_dimension_resolution('Z'),
            # f'{self._Z_name}_location': self._get_z_location(),
            **extras
        }

    @classmethod
    def from_field(cls, field):
        extraction = cls._extract_xyz_from_field(field)

        return cls(
            **{
                getattr(cls, f'_{axis}_name') + prop:
                    extraction[axis + prop]
                # for axis in ['X', 'Y', 'Z']
                for axis in ['X', 'Y']
                for prop in ['', '_bounds']
            }
        )

    def to_horizontal_grid(self, drop_extras=True):
        cfg = self.to_config()

        for prop in ['extent', 'resolution']:
            cfg.pop(f'{self._Z_name}_{prop}', None)

        if drop_extras:
            for extra in ['land_sea_mask', 'flow_direction', 'cell_area']:
                cfg.pop(extra)

        return self.__class__.from_config(cfg)


class LatLonGrid(Grid):
    """This class characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is aligned with
    the North pole (`EPSG:4326 <https://epsg.io/4326>`_).
    """
    # characteristics of the dimension coordinates
    _Z_name = 'altitude'
    _Y_name = 'latitude'
    _X_name = 'longitude'
    _Z_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _Y_units = ['degrees_north', 'degree_north', 'degrees_N', 'degree_N',
                'degreesN', 'degreeN']
    _X_units = ['degrees_east', 'degree_east', 'degrees_E',
                'degree_E', 'degreesE', 'degreeE']
    _Z_limits = None
    _Y_limits = (-90, 90)
    _X_limits = (-180, 180)
    # contiguity of lower and upper limits
    _Z_limits_contiguous = False
    _Y_limits_contiguous = True
    _X_limits_contiguous = True
    # allow domain to wrap around limits
    _Z_wrap_around = False
    _Y_wrap_around = False
    _X_wrap_around = True

    def __init__(
            self,
            latitude, longitude,
            latitude_bounds, longitude_bounds,
            # altitude=None, altitude_bounds=None
    ):
        """**Instantiation**

        :Parameters:

            latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees North
                defining a spatial dimension of the domain. May be any
                type that can be cast to a `numpy.ndarray`. Must contain
                numerical values. Coordinates must be ordered from South
                to North. Coordinates must be regularly spaced.

                *Parameter example:* ::

                    latitude=[15, 45, 75]

                *Parameter example:* ::

                    latitude=numpy.arange(-89.5, 90.5, 1)

            longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees East
                defining a spatial dimension of the domain. May be any
                type that can be cast to a `numpy.ndarray`. Must contain
                numerical values. Coordinates must be ordered from West
                to East. Coordinates must be regularly spaced.

                *Parameter example:* ::

                    longitude=(-150, -90, -30, 30, 90, 150)

                *Parameter example:* ::

                    longitude=numpy.arange(-179.5, 180.5, 1)

            latitude_bounds: two-dimensional array-like object
                The array of latitude coordinate bounds in degrees North
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *latitude* and the second
                dimension equal to 2. Must contain numerical values.

                *Parameter example:* ::

                    latitude_bounds=[[0, 30], [30, 60], [60, 90]]

                *Parameter example:* ::

                    latitude_bounds=numpy.column_stack(
                        (numpy.arange(-90, 90, 1), numpy.arange(-89, 91, 1))
                    )

            longitude_bounds: two-dimensional array-like object
                The array of longitude coordinate bounds in degrees
                East defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *longitude* and the
                second dimension equal to 2. Must contain numerical
                values.

                *Parameter example:* ::

                    longitude_bounds=((-180, -120), (-120, -60), (-60, 0)
                                      (0, 60), (60, 120), (120, 180))

                *Parameter example:* ::

                    longitude_bounds=numpy.column_stack(
                        (numpy.arange(-180, 180, 1),
                         numpy.arange(-179, 181, 1))
                    )

            .. altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining a
                spatial dimension (with upwards as the positive
                direction). May be any type that can be cast to a
                `numpy.ndarray`. Must contain numerical values. Ignored
                if *altitude_bounds* not also provided.

                *Parameter example:* ::

                    altitude=[10]

            .. altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate (with upwards as the positive direction).
                May be any type that can be cast to a `numpy.ndarray`.
                Must be two dimensional with the first dimension equal
                to the size of *altitude* and the second dimension equal
                to 2. Must contain numerical values. Ignored if
                *altitude* not also provided.

                *Parameter example:* ::

                    altitude_bounds=[[0, 20]]

        **Examples**

        Instantiating grid using lists:

        >>> import numpy
        >>> sd = LatLonGrid(
        ...     latitude=[15, 45, 75],
        ...     longitude=[30, 90, 150],
        ...     latitude_bounds=[[0, 30], [30, 60], [60, 90]],
        ...     longitude_bounds=[[0, 60], [60, 120], [120, 180]]
        ... )
        >>> print(sd)
        LatLonGrid(
            shape {Y, X}: (3, 3)
            Y, latitude (3,): [15, 45, 75] degrees_north
            X, longitude (3,): [30, 90, 150] degrees_east
            Y_bounds (3, 2): [[0, ..., 90]] degrees_north
            X_bounds (3, 2): [[0, ..., 180]] degrees_east
        )

        .. Instantiating grid using numpy arrays and Z axis:
        ..
        .. >>> sd = LatLonGrid(
        .. ...     latitude=numpy.arange(-89.5, 90.5, 1),
        .. ...     longitude=numpy.arange(-179.5, 180.5, 1),
        .. ...     latitude_bounds=numpy.column_stack(
        .. ...         (numpy.arange(-90, 90, 1),
        .. ...          numpy.arange(-89, 91, 1))
        .. ...     ),
        .. ...     longitude_bounds=numpy.column_stack(
        .. ...         (numpy.arange(-180, 180, 1),
        .. ...          numpy.arange(-179, 181, 1))
        .. ...     ),
        .. ...     altitude=[10],
        .. ...     altitude_bounds=[[0, 10]]
        .. ... )
        .. >>> print(sd)
        .. LatLonGrid(
        ..     shape {Z, Y, X}: (1, 180, 360)
        ..     Z, altitude (1,): [10] m
        ..     Y, latitude (180,): [-89.5, ..., 89.5] degrees_north
        ..     X, longitude (360,): [-179.5, ..., 179.5] degrees_east
        ..     Z_bounds (1, 2): [[0, 10]] m
        ..     Y_bounds (180, 2): [[-90, ..., 90]] degrees_north
        ..     X_bounds (360, 2): [[-180, ..., 180]] degrees_east
        .. )

        Trying to instantiate grid with latitudes from East to West:

        >>> sd = LatLonGrid(
        ...     latitude=[75, 45, 15],
        ...     longitude=[30, 90, 150],
        ...     latitude_bounds=[[90, 60], [60, 30], [30, 0]],
        ...     longitude_bounds=[[0, 60], [60, 120], [120, 180]]
        ... )
        Traceback (most recent call last):
            ...
        RuntimeError: latitude dimension not directed positively

        Trying to instantiate grid with latitude cells of varying width:

        >>> sd = LatLonGrid(
        ...     latitude=[15, 45, 75],
        ...     longitude=[30, 90, 150],
        ...     latitude_bounds=[[10, 20], [20, 70], [70, 80]],
        ...     longitude_bounds=[[0, 60], [60, 120], [120, 180]]
        ... )
        Traceback (most recent call last):
            ...
        RuntimeError: latitude bounds space gap not constant across region
        """
        super(LatLonGrid, self).__init__()

        # TODO: reintroduce Z dimension when 3D components
        #       are effectively supported
        # if altitude is not None and altitude_bounds is not None:
        #     self._set_space(altitude, altitude_bounds, name=self._Z_name,
        #                     units=self._Z_units[0], axis='Z',
        #                     limits=self._Z_limits, wrap_around=self._Z_wrap_around)
        #     self._f.dim('Z').set_property('positive', 'up')

        self._set_space(latitude, latitude_bounds,
                        name=self._Y_name, units=self._Y_units[0], axis='Y',
                        limits=self._Y_limits, wrap_around=self._Y_wrap_around)
        self._set_space(longitude, longitude_bounds,
                        name=self._X_name, units=self._X_units[0], axis='X',
                        limits=self._X_limits, wrap_around=self._X_wrap_around)

        # set dummy data needed for using inner field for remapping
        self._set_dummy_data()

    @classmethod
    def from_extent_and_resolution(
            cls,
            latitude_extent, longitude_extent,
            latitude_resolution, longitude_resolution,
            latitude_longitude_location='centre',
            # altitude_extent=None,
            # altitude_resolution=None,
            # altitude_location='centre'
    ):
        """Instantiate a `LatLonGrid` from the extent and the resolution
        of latitude, longitude (and optionally altitude) coordinates.

        :Parameters:

            latitude_extent: pair of `float` or `int`
                The extent of latitude coordinates in degrees North
                for the desired grid. The first element of the pair is
                the location of the start of the extent along the
                latitude coordinate, the second element of the pair is
                the location of the end of the extent along the latitude
                coordinate. Extent must be from South to North. May be
                any type that can be unpacked (e.g. `tuple`, `list`,
                `numpy.ndarray`).

                *Parameter example:* ::

                    latitude_extent=(30, 70)

            longitude_extent: pair of `float` or `int`
                The extent of longitude coordinates in degrees East
                for the desired grid. The first element of the pair is
                the location of the start of the extent along the
                longitude coordinate, the second element of the pair is
                the location of the end of the extent along the
                longitude coordinate. Extent must be from West to East.
                May be any type that can be unpacked (e.g. `tuple`,
                `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    longitude_extent=(0, 90)

            latitude_resolution: `float` or `int`
                The spacing between two consecutive latitude coordinates
                in degrees North for the desired grid. Must be positive.

                *Parameter example:* ::

                    latitude_resolution=10

            longitude_resolution: `float` or `int`
                The spacing between two consecutive longitude
                coordinates in degrees East for the desired grid. Must
                be positive.

                *Parameter example:* ::

                    longitude_resolution=10

            latitude_longitude_location: `str` or `int`, optional
                The location of the latitude and longitude coordinates
                in relation to their grid cells (i.e. their bounds).
                This information is required to generate the latitude
                and longitude bounds for each grid coordinate. If not
                provided, set to default 'centre'.

                The locations left and right are related to the
                longitude coordinates (X-axis), while the locations
                lower and upper are related to the latitude coordinates
                (Y-axis). The orientation of the coordinate system
                considered is detailed below (i.e. positive directions
                are northwards and eastwards).
                ::

                    Y, latitude (degrees North)
                    ↑
                    ·
                    * · → X, longitude (degrees East)

                This parameter can be set using the labels (as a `str`)
                or the indices (as an `int`) detailed in the table
                below.

                =================  =====  ==============================
                label              idx    description
                =================  =====  ==============================
                ``'centre'``       ``0``  The latitude and longitude
                                          bounds extend equally on both
                                          sides of the coordinate along
                                          the two axes of a length equal
                                          to half the resolution along
                                          the given coordinate axis.

                ``'lower left'``   ``1``  The latitude bounds extend
                                          northwards of a length equal
                                          to the latitude resolution.
                                          The longitude bounds extend
                                          eastwards of a length equal to
                                          the longitude resolution.

                ``'upper left'``   ``2``  The latitude bounds extend
                                          southwards of a length equal
                                          to the latitude resolution.
                                          The longitude bounds extend
                                          eastwards of a length equal to
                                          the longitude resolution.

                ``'lower right'``  ``3``  The latitude bounds extend
                                          northwards of a length equal
                                          to the latitude resolution.
                                          The longitude bounds extend
                                          westwards of a length equal to
                                          the longitude resolution.

                ``'upper right'``  ``4``  The latitude bounds extend
                                          southwards of a length equal
                                          to the latitude resolution.
                                          The longitude bounds extend
                                          westwards of a length equal to
                                          the longitude resolution.
                =================  =====  ==============================

                The indices defining the location of the coordinate in
                relation to its grid cell are made explicit below, where
                the '+' characters depict the coordinates, and the '·'
                characters delineate the relative location of the grid
                cell whose height and width are determined using the
                latitude and longitude resolutions, respectively.
                ::

                    2             4               northwards
                     +  ·  ·  ·  +                    ↑
                     ·           ·                    ·
                     ·   0 +     ·      westwards ← · * · → eastwards
                     ·           ·                    ·
                     +  ·  ·  ·  +                    ↓
                    1             3               southwards

                *Parameter example:* ::

                    latitude_longitude_location='centre'

                *Parameter example:* ::

                    latitude_longitude_location=0

            .. altitude_extent: pair of `float` or `int`, optional
                The extent of altitude coordinate in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the altitude
                coordinate, the second element of the pair is the
                location of the end of the extent along the altitude
                coordinate. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    altitude_extent=(0, 20)

            .. altitude_resolution: `float` or `int`, optional
                The spacing between two consecutive altitude coordinates
                in metres for the desired grid.

                *Parameter example:* ::

                    altitude_resolution=20

            .. altitude_location: `str` or `int`, optional
                The location of the altitude coordinates in relation to
                their grid cells (i.e. their bounds). This information
                is required to generate the altitude bounds for each
                grid coordinate. If not provided, set to default
                'centre'.

                The locations top and bottom are related to the
                altitude coordinate (Z-axis). The orientation of the
                coordinate system considered is such that the positive
                direction is upwards.

                This parameter can be set using the labels (as a `str`)
                or the indices (as an `int`) detailed in the table
                below.

                ================  =====  ===============================
                label             idx    description
                ================  =====  ===============================
                ``'centre'``      ``0``  The altitude bounds extend
                                         equally upwards and downwards
                                         of a length equal to half the
                                         resolution along the altitude
                                         axis.

                ``'bottom'``      ``1``  The altitude bounds extend
                                         upwards of a length equal to
                                         the resolution along the
                                         altitude axis.

                ``'top'``         ``2``  The altitude bounds extend
                                         downwards of a length equal to
                                         the resolution along the
                                         altitude axis.
                ================  =====  ===============================

                *Parameter example:* ::

                    altitude_location='centre'

        :Returns: `LatLonGrid`

        **Examples**

        .. Instantiating grid with optional altitude coordinates:
        ..
        .. >>> sd = LatLonGrid.from_extent_and_resolution(
        .. ...     latitude_extent=(30, 70),
        .. ...     longitude_extent=(0, 90),
        .. ...     latitude_resolution=5,
        .. ...     longitude_resolution=10,
        .. ...     altitude_extent=(0, 20),
        .. ...     altitude_resolution=20
        .. ... )
        .. >>> print(sd)
        .. LatLonGrid(
        ..     shape {Z, Y, X}: (1, 8, 9)
        ..     Z, altitude (1,): [10.0] m
        ..     Y, latitude (8,): [32.5, ..., 67.5] degrees_north
        ..     X, longitude (9,): [5.0, ..., 85.0] degrees_east
        ..     Z_bounds (1, 2): [[0.0, 20.0]] m
        ..     Y_bounds (8, 2): [[30.0, ..., 70.0]] degrees_north
        ..     X_bounds (9, 2): [[0.0, ..., 90.0]] degrees_east
        .. )

        Instantiating grid using non-standard coordinates location in their cells:

        >>> sd = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(30, 70),
        ...     longitude_extent=(0, 90),
        ...     latitude_resolution=5,
        ...     longitude_resolution=10,
        ...     latitude_longitude_location='upper right'
        ... )
        >>> print(sd)
        LatLonGrid(
            shape {Y, X}: (8, 9)
            Y, latitude (8,): [35.0, ..., 70.0] degrees_north
            X, longitude (9,): [10.0, ..., 90.0] degrees_east
            Y_bounds (8, 2): [[30.0, ..., 70.0]] degrees_north
            X_bounds (9, 2): [[0.0, ..., 90.0]] degrees_east
        )
        """
        return super(LatLonGrid, cls).from_extent_and_resolution(
            latitude_extent=latitude_extent,
            longitude_extent=longitude_extent,
            latitude_resolution=latitude_resolution,
            longitude_resolution=longitude_resolution,
            latitude_longitude_location=latitude_longitude_location,
            # altitude_extent=altitude_extent,
            # altitude_resolution=altitude_resolution,
            # altitude_location=altitude_location
        )

    @classmethod
    def from_field(cls, field):
        """Instantiate a `LatLonGrid` from spatial dimension coordinates
        of a `cf.Field`.

        :Parameters:

            field: `cf.Field`
                The field object that will be used to instantiate a
                `LatLonGrid` instance. This field must feature a
                'latitude' and a 'longitude' dimension coordinates, and
                these coordinates must feature bounds.

                ..
                   This field may optionally feature an 'altitude'
                   dimension coordinate alongside its bounds (both required
                   otherwise ignored).

        :Returns: `LatLonGrid`

        **Examples**

        Instantiating from a 2D field:

        >>> import cf
        >>> f = cf.Field()
        >>> lat = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'latitude',
        ...                     'units': 'degrees_north',
        ...                     'axis': 'Y'},
        ...         data=cf.Data([15, 45, 75]),
        ...         bounds=cf.Bounds(data=cf.Data([[0, 30], [30, 60], [60, 90]]))
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=3))
        ... )
        >>> lon = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'longitude',
        ...                     'units': 'degrees_east',
        ...                     'axis': 'X'},
        ...         data=cf.Data([30, 90, 150]),
        ...         bounds=cf.Bounds(data=cf.Data([[0, 60], [60, 120], [120, 180]]))
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=3))
        ... )
        >>> sd = LatLonGrid.from_field(f)
        >>> print(sd)
        LatLonGrid(
            shape {Y, X}: (3, 3)
            Y, latitude (3,): [15, 45, 75] degrees_north
            X, longitude (3,): [30, 90, 150] degrees_east
            Y_bounds (3, 2): [[0, ..., 90]] degrees_north
            X_bounds (3, 2): [[0, ..., 180]] degrees_east
        )

        Using the field interface back and forth:

        >>> sd1 = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(30, 70),
        ...     longitude_extent=(0, 90),
        ...     latitude_resolution=5,
        ...     longitude_resolution=10,
        ...     latitude_longitude_location='upper right'
        ... )
        >>> sd2 = LatLonGrid.from_field(sd1.to_field())
        >>> sd2 == sd1
        True

        .. Instantiating from a 3D field:
        ..
        .. >>> import cf
        .. >>> f = cf.Field()
        .. >>> lat = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'latitude',
        .. ...                     'units': 'degrees_north',
        .. ...                     'axis': 'Y'},
        .. ...         data=cf.Data([15, 45, 75]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[0, 30], [30, 60], [60, 90]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=3))
        .. ... )
        .. >>> lon = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'longitude',
        .. ...                     'units': 'degrees_east',
        .. ...                     'axis': 'X'},
        .. ...         data=cf.Data([30, 90, 150]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[0, 60], [60, 120], [120, 180]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=3))
        .. ... )
        .. >>> alt = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'altitude',
        .. ...                     'units': 'm',
        .. ...                     'axis': 'Z'},
        .. ...         data=cf.Data([10]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[0, 20]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=1))
        .. ... )
        .. >>> sd = LatLonGrid.from_field(f)
        .. >>> print(sd)
        .. LatLonGrid(
        ..     shape {Z, Y, X}: (1, 3, 3)
        ..     Z, altitude (1,): [10] m
        ..     Y, latitude (3,): [15, 45, 75] degrees_north
        ..     X, longitude (3,): [30, 90, 150] degrees_east
        ..     Z_bounds (1, 2): [[0, 20]] m
        ..     Y_bounds (3, 2): [[0, ..., 90]] degrees_north
        ..     X_bounds (3, 2): [[0, ..., 180]] degrees_east
        .. )
        """
        return super(LatLonGrid, cls).from_field(field)


class RotatedLatLonGrid(Grid):
    """This class characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is not aligned
    with the North pole. Its ellipsoid and datum are those of WGS 84
    (see `EPSG:4326 <https://epsg.io/4326>`_).
    """
    # characteristics of the dimension coordinates
    _Z_name = 'altitude'
    _Y_name = 'grid_latitude'
    _X_name = 'grid_longitude'
    _Z_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _Y_units = ['degrees', 'degree']
    _X_units = ['degrees', 'degree']
    _Z_limits = None
    _Y_limits = (-90, 90)
    _X_limits = (-180, 180)
    # contiguity of lower and upper limits
    _Z_limits_contiguous = False
    _Y_limits_contiguous = True
    _X_limits_contiguous = True
    # allow domain to wrap around limits
    _Z_wrap_around = False
    _Y_wrap_around = False
    _X_wrap_around = True

    def __init__(
            self,
            grid_latitude, grid_longitude,
            grid_latitude_bounds, grid_longitude_bounds,
            grid_north_pole_latitude, grid_north_pole_longitude,
            north_pole_grid_longitude=0.,
            # altitude=None, altitude_bounds=None
    ):
        """**Instantiation**

        :Parameters:

            grid_latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees defining
                a spatial dimension of the domain. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values.

                *Parameter example:* ::

                    grid_latitude=[0.88, 0.44, 0., -0.44, -0.88]

            grid_longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees defining
                a spatial dimension of the domain. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values.

                *Parameter example:* ::

                    grid_longitude=[-2.5, -2.06, -1.62, -1.18]

            grid_latitude_bounds: two-dimensional array-like object
                The array of latitude coordinate bounds in degrees
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *grid_latitude* and the
                second dimension equal to 2. Must contain numerical
                values.

                *Parameter example:* ::

                    grid_latitude_bounds=[[1.1, 0.66], [0.66, 0.22],
                                          [0.22, -0.22], [-0.22, -0.66],
                                          [-0.66, -1.1]]

            grid_longitude_bounds: two-dimensional array-like object
                The array of longitude coordinate bounds in degrees
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *grid_longitude* and the
                second dimension equal to 2. Must contain numerical
                values.

                *Parameter example:* ::

                    grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
                                           [-1.84, -1.4], [-1.4, -0.96]]

            grid_north_pole_latitude: `int` or `float`
                The true latitude (i.e. in `EPSG:4326`_) of the north
                pole of the rotated grid in degrees North. This parameter
                is required to project the rotated grid into a true
                latitude-longitude coordinate system.

            grid_north_pole_longitude: `int` or `float`
                The true longitude (i.e. in `EPSG:4326`_) of the north
                pole of the rotated grid in degrees East. This parameter
                is required to project the rotated grid into a true
                latitude-longitude coordinate system.

            north_pole_grid_longitude: `int` or `float`, optional
                The longitude of the true north pole (i.e. in `EPSG:4326`_)
                in the rotated grid in degrees. This parameter is
                optional to project the rotated grid into a true
                latitude-longitude coordinate system. If not provided,
                set to default value 0.

            .. altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining a
                spatial dimension of the domain (with upwards as the
                positive direction). May be any type that can be cast to
                a `numpy.ndarray`. Must contain numerical values.
                Ignored if *altitude_bounds* not also provided.

                *Parameter example:* ::

                    altitude=[10]

            .. altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate (with upwards as the positive direction).
                May be any type that can be cast to a `numpy.ndarray`.
                Must be two dimensional with the first dimension equal
                to the size of *altitude* and the second dimension equal
                to 2. Must contain numerical values. Ignored if
                *altitude* not also provided.

                *Parameter example:* ::

                    altitude_bounds=[[0, 20]]

            .. _`EPSG:4326`: https://epsg.io/4326

        **Examples**

        Instantiate 2D grid using lists:

        >>> sd = RotatedLatLonGrid(
        ...     grid_latitude=[-0.88, -0.44, 0., 0.44, 0.88],
        ...     grid_longitude=[-2.5, -2.06, -1.62, -1.18],
        ...     grid_latitude_bounds=[[-1.1, -0.66], [-0.66, -0.22], [-0.22, 0.22],
        ...                           [0.22, 0.66], [0.66, 1.1]],
        ...     grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
        ...                            [-1.84, -1.4], [-1.4, -0.96]],
        ...     grid_north_pole_latitude=38.0,
        ...     grid_north_pole_longitude=190.0,
        ... )
        >>> print(sd)
        RotatedLatLonGrid(
            shape {Y, X}: (5, 4)
            Y, grid_latitude (5,): [-0.88, ..., 0.88] degrees
            X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
            Y_bounds (5, 2): [[-1.1, ..., 1.1]] degrees
            X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        )

        .. Instantiate 3D grid using lists:
        ..
        .. >>> sd = RotatedLatLonGrid(
        .. ...     grid_latitude=[-0.88, -0.44, 0., 0.44, 0.88],
        .. ...     grid_longitude=[-2.5, -2.06, -1.62, -1.18],
        .. ...     grid_latitude_bounds=[[-1.1, -0.66], [-0.66, -0.22], [-0.22, 0.22],
        .. ...                           [0.22, 0.66], [0.66, 1.1]],
        .. ...     grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
        .. ...                            [-1.84, -1.4], [-1.4, -0.96]],
        .. ...     grid_north_pole_latitude=38.0,
        .. ...     grid_north_pole_longitude=190.0,
        .. ...     altitude=[10],
        .. ...     altitude_bounds=[[0, 20]]
        .. ... )
        .. >>> print(sd)
        .. RotatedLatLonGrid(
        ..     shape {Y, X}: (1, 5, 4)
        ..     Y, grid_latitude (5,): [-0.88, ..., 0.88] degrees
        ..     X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
        ..     Z_bounds (1, 2): [[0, 20]] m
        ..     Y_bounds (5, 2): [[-1.1, ..., 1.1]] degrees
        ..     X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        .. )
        """
        super(RotatedLatLonGrid, self).__init__()

        # TODO: reintroduce Z dimension when 3D components
        #       are effectively supported
        # if altitude is not None and altitude_bounds is not None:
        #     self._set_space(altitude, altitude_bounds, name=self._Z_name,
        #                     units=self._Z_units[0], axis='Z',
        #                     limits=self._Z_limits, wrap_around=self._Z_wrap_around)
        #     self._f.dim('Z').set_property('positive', 'up')

        self._set_space(grid_latitude, grid_latitude_bounds,
                        name=self._Y_name, units=self._Y_units[0], axis='Y',
                        limits=self._Y_limits, wrap_around=self._Y_wrap_around)
        self._set_space(grid_longitude, grid_longitude_bounds,
                        name=self._X_name, units=self._X_units[0], axis='X',
                        limits=self._X_limits, wrap_around=self._X_wrap_around)

        self._rotate_and_set_lat_lon(grid_north_pole_latitude,
                                     grid_north_pole_longitude,
                                     north_pole_grid_longitude)

        self._set_crs_parameters(grid_north_pole_latitude,
                                 grid_north_pole_longitude,
                                 north_pole_grid_longitude)

        # set dummy data needed for using inner field for remapping
        self._set_dummy_data()

    @classmethod
    def from_extent_and_resolution(
            cls,
            grid_latitude_extent, grid_longitude_extent,
            grid_latitude_resolution, grid_longitude_resolution,
            grid_north_pole_latitude, grid_north_pole_longitude,
            north_pole_grid_longitude=0.,
            grid_latitude_grid_longitude_location='centre',
            # altitude_extent=None,
            # altitude_resolution=None,
            # altitude_location='centre'
    ):
        """Instantiate a `RotatedLatLonGrid` from the extent and the
        resolution of grid_latitude and grid_longitude coordinates (and
        optional altitude coordinates).

        :Parameters:

            grid_latitude_extent: pair of `float` or `int`
                The extent of grid_latitude coordinates in degrees for
                the desired grid. The first element of the pair is the
                location of the start of the extent along the
                grid_latitude coordinate, the second element of the pair
                is the location of the end of the extent along the
                grid_latitude coordinate. Extent must be oriented
                positively. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    grid_latitude_extent=(30, 70)

            grid_longitude_extent: pair of `float` or `int`
                The extent of grid_longitude coordinates in degrees for
                the desired grid. The first element of the pair is the
                location of the start of the extent along the
                grid_longitude coordinate, the second element of the
                pair is the location of the end of the extent along the
                grid_latitude coordinate. Extent must be oriented
                positively. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    grid_longitude_extent=(0, 90)

            grid_latitude_resolution: `float` or `int`
                The spacing between two consecutive grid_latitude
                coordinates in degrees for the desired grid. Must be
                positive.

                *Parameter example:* ::

                    grid_latitude_resolution=10

            grid_longitude_resolution: `float` or `int`
                The spacing between two consecutive grid_longitude
                coordinates in degrees for the desired grid. Must be
                positive.

                *Parameter example:* ::

                    grid_longitude_resolution=10

            grid_latitude_grid_longitude_location: `str` or `int`, optional
                The location of the grid_latitude and grid_longitude
                coordinates in relation to their grid cells (i.e. their
                bounds). This information is required to generate the
                grid_latitude and grid_longitude bounds for each grid
                coordinate. If not provided, set to default 'centre'.

                The locations left and right are related to the
                grid_longitude coordinates (X-axis), while the locations
                lower and upper are related to the grid_latitude
                coordinates (Y-axis). The orientation of the coordinate
                system considered is detailed below.

                .. seealso::

                   *latitude_longitude_location* in
                   `LatLonGrid.from_extent_and_resolution`

            grid_north_pole_latitude: `int` or `float`
                The true latitude (i.e. in `EPSG:4326`_) of the north
                pole of the rotated grid in degrees North. This parameter
                is required to project the rotated grid into a true
                latitude-longitude coordinate system.

            grid_north_pole_longitude: `int` or `float`
                The true longitude (i.e. in `EPSG:4326`_) of the north
                pole of the rotated grid in degrees East. This parameter
                is required to project the rotated grid into a true
                latitude-longitude coordinate system.

            north_pole_grid_longitude: `int` or `float`, optional
                The longitude of the true north pole in the rotated grid
                in degrees. This parameter is optional to project the
                rotated grid into a true latitude-longitude coordinate
                system (i.e. `EPSG:4326`_). If not provided, set to
                default value 0.

            .. altitude_extent: pair of `float` or `int`, optional
                The extent of altitude coordinate in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the altitude
                coordinate, the second element of the pair is the
                location of the end of the extent along the altitude
                coordinate. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    altitude_extent=(0, 20)

            .. altitude_resolution: `float` or `int`, optional
                The spacing between two consecutive altitude coordinates
                in metres for the desired grid.

                *Parameter example:* ::

                    altitude_resolution=20

            .. altitude_location: `str` or `int`, optional
                The location of the altitude coordinates in relation to
                their grid cells (i.e. their bounds). This information
                is required to generate the altitude bounds for each
                grid coordinate. If not provided, set to default
                'centre'.

                The locations top and bottom are related to the
                altitude coordinate (Z-axis). The orientation of the
                coordinate system considered is such that the positive
                direction is upwards.

                .. seealso::

                   *altitude_location* in `LatLonGrid.from_extent_and_resolution`

                *Parameter example:* ::

                    altitude_location='centre'

            .. _`EPSG:4326`: https://epsg.io/4326

        :Returns: `RotatedLatLonGrid`

        **Examples**

        >>> sd = RotatedLatLonGrid.from_extent_and_resolution(
        ...     grid_latitude_extent=(-1.1, 1.1),
        ...     grid_longitude_extent=(-2.72, -0.96),
        ...     grid_latitude_resolution=0.44,
        ...     grid_longitude_resolution=0.44,
        ...     grid_north_pole_latitude=38.0,
        ...     grid_north_pole_longitude=190.0
        ... )
        >>> print(sd)
        RotatedLatLonGrid(
            shape {Y, X}: (5, 4)
            Y, grid_latitude (5,): [-0.88, ..., 0.88] degrees
            X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
            Y_bounds (5, 2): [[-1.1, ..., 1.1]] degrees
            X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        )
        """
        inst = cls(
            **cls._get_grid_from_extent_and_resolution(
                grid_latitude_extent, grid_longitude_extent,
                grid_latitude_resolution, grid_longitude_resolution,
                grid_latitude_grid_longitude_location,
                # altitude_extent, altitude_resolution, altitude_location
            ),
            grid_north_pole_latitude=grid_north_pole_latitude,
            grid_north_pole_longitude=grid_north_pole_longitude,
            north_pole_grid_longitude=north_pole_grid_longitude
        )

        inst._extent = {
            # 'Z': altitude_extent,
            'Y': grid_latitude_extent,
            'X': grid_longitude_extent
        }
        inst._resolution = {
            # 'Z': altitude_resolution,
            'Y': grid_latitude_resolution,
            'X': grid_longitude_resolution
        }
        inst._location = {
            # 'Z': altitude_location,
            'YX': grid_latitude_grid_longitude_location
        }

        return inst

    @classmethod
    def from_field(cls, field):
        """Instantiate a `RotatedLatLonGrid` from spatial dimension
        coordinates of a `cf.Field`.

        :Parameters:

            field: `cf.Field`
                The field object that will be used to instantiate a
                `RotatedLatLonGrid` instance. This field must feature a
                'grid_latitude' and a 'grid_longitude' dimension
                coordinates, and these must feature bounds. In addition,
                the parameters required for the conversion of the grid
                to a true latitude-longitude reference system must be set
                (i.e. grid_north_pole_latitude, grid_north_pole_longitude,
                and optional north_pole_grid_longitude).

                ..
                   This field may optionally feature an 'altitude'
                   dimension coordinate alongside its bounds (both
                   required otherwise ignored).

        :Returns: `RotatedLatLonGrid`

        **Examples**

        Instantiating from a 2D field:

        >>> import cf
        >>> f = cf.Field()
        >>> lat = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'grid_latitude',
        ...                     'units': 'degrees',
        ...                     'axis': 'Y'},
        ...         data=cf.Data([-0.88, -0.44, 0., 0.44, 0.88]),
        ...         bounds=cf.Bounds(data=cf.Data([[-1.1, -0.66], [-0.66, -0.22],
        ...                                        [-0.22, 0.22], [0.22, 0.66],
        ...                                        [0.66, 1.1]]))
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=5))
        ... )
        >>> lon = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'grid_longitude',
        ...                     'units': 'degrees',
        ...                     'axis': 'X'},
        ...         data=cf.Data([-2.5, -2.06, -1.62, -1.18]),
        ...         bounds=cf.Bounds(data=cf.Data([[-2.72, -2.28], [-2.28, -1.84],
        ...                                        [-1.84, -1.4], [-1.4, -0.96]]))
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=4))
        ... )
        >>> crs = f.set_construct(
        ...     cf.CoordinateReference(
        ...         coordinate_conversion=cf.CoordinateConversion(
        ...             parameters={'grid_mapping_name': 'rotated_latitude_longitude',
        ...                         'grid_north_pole_latitude': 38.0,
        ...                         'grid_north_pole_longitude': 190.0}),
        ...         coordinates=(lat, lon)
        ...     )
        ... )
        >>> sd = RotatedLatLonGrid.from_field(f)
        >>> print(sd)
        RotatedLatLonGrid(
            shape {Y, X}: (5, 4)
            Y, grid_latitude (5,): [-0.88, ..., 0.88] degrees
            X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
            Y_bounds (5, 2): [[-1.1, ..., 1.1]] degrees
            X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        )

        Using the field interface back and forth:

        >>> sd1 = RotatedLatLonGrid.from_extent_and_resolution(
        ...     grid_latitude_extent=(-1.1, 1.1),
        ...     grid_longitude_extent=(-2.72, -0.96),
        ...     grid_latitude_resolution=0.44,
        ...     grid_longitude_resolution=0.44,
        ...     grid_north_pole_latitude=38.0,
        ...     grid_north_pole_longitude=190.0
        ... )
        >>> sd2 = RotatedLatLonGrid.from_field(sd1.to_field())
        >>> sd2 == sd1
        True

        .. Instantiating from a 3D field:
        ..
        .. >>> import cf
        .. >>> f = cf.Field()
        .. >>> lat = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'grid_latitude',
        .. ...                     'units': 'degrees',
        .. ...                     'axis': 'Y'},
        .. ...         data=cf.Data([-0.88, -0.44, 0., 0.44, 0.88]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[-1.1, -0.66], [-0.66, -0.22],
        .. ...                                        [-0.22, 0.22], [0.22, 0.66],
        .. ...                                        [0.66, 1.1]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=5))
        .. ... )
        .. >>> lon = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'grid_longitude',
        .. ...                     'units': 'degrees',
        .. ...                     'axis': 'X'},
        .. ...         data=cf.Data([-2.5, -2.06, -1.62, -1.18]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[-2.72, -2.28], [-2.28, -1.84],
        .. ...                                        [-1.84, -1.4], [-1.4, -0.96]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=4))
        .. ... )
        .. >>> alt = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'altitude',
        .. ...                     'units': 'm',
        .. ...                     'axis': 'Z'},
        .. ...         data=cf.Data([10]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[0, 20]]))
        .. ...         ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=1))
        .. ... )
        .. >>> crs = f.set_construct(
        .. ...     cf.CoordinateReference(
        .. ...         coordinate_conversion=cf.CoordinateConversion(
        .. ...             parameters={'grid_mapping_name': 'rotated_latitude_longitude',
        .. ...                         'grid_north_pole_latitude': 38.0,
        .. ...                         'grid_north_pole_longitude': 190.0}),
        .. ...         coordinates=(lat, lon)
        .. ...     )
        .. ... )
        .. >>> sd = RotatedLatLonGrid.from_field(f)
        .. >>> print(sd)
        .. RotatedLatLonGrid(
        ..     shape {Y, X}: (1, 5, 4)
        ..     Y, grid_latitude (5,): [-0.88, ..., 0.88] degrees
        ..     X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
        ..     Z_bounds (1, 2): [[0, 20]] m
        ..     Y_bounds (5, 2): [[-1.1, ..., 1.1]] degrees
        ..     X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        .. )
        """
        extraction_xyz = cls._extract_xyz_from_field(field)
        extraction_param = cls._extract_crs_rotation_parameters_from_field(field)

        return cls(grid_latitude=extraction_xyz['Y'],
                   grid_longitude=extraction_xyz['X'],
                   grid_latitude_bounds=extraction_xyz['Y_bounds'],
                   grid_longitude_bounds=extraction_xyz['X_bounds'],
                   # altitude=extraction_xyz['Z'],
                   # altitude_bounds=extraction_xyz['Z_bounds'],
                   **extraction_param)

    def to_config(self):
        cfg = super(RotatedLatLonGrid, self).to_config()
        cfg.update(
            self._extract_crs_rotation_parameters_from_field(self._f)
        )
        return cfg

    @property
    def coordinate_reference(self):
        """Return the coordinate reference of the RotatedLatLonGrid
        instance as a `cf.CoordinateReference` instance.
        """
        return self._f.coordinate_reference(
            'grid_mapping_name:rotated_latitude_longitude'
        )

    @classmethod
    def _extract_crs_rotation_parameters_from_field(cls, field):
        # check conversion parameters
        if field.coordinate_reference(
                'grid_mapping_name:rotated_latitude_longitude',
                default=False
        ):
            crs = field.coordinate_reference(
                'grid_mapping_name:rotated_latitude_longitude'
            )
        else:
            raise RuntimeError(
                f"{cls.__name__} field missing coordinate conversion "
                f"'grid_mapping_name:rotated_latitude_longitude"
            )
        if crs.coordinate_conversion.has_parameter('grid_north_pole_latitude'):
            grid_north_pole_lat = crs.coordinate_conversion.get_parameter(
                'grid_north_pole_latitude')
        else:
            raise RuntimeError(
                f"{cls.__name__} field coordinate conversion missing "
                f"property 'grid_north_pole_latitude'"
            )
        if crs.coordinate_conversion.has_parameter('grid_north_pole_longitude'):
            grid_north_pole_lon = crs.coordinate_conversion.get_parameter(
                'grid_north_pole_longitude')
        else:
            raise RuntimeError(
                f"{cls.__name__} field coordinate conversion missing "
                f"property 'grid_north_pole_longitude'"
            )
        if crs.coordinate_conversion.has_parameter('north_pole_grid_longitude'):
            north_pole_grid_lon = crs.coordinate_conversion.get_parameter(
                'north_pole_grid_longitude')
        else:
            north_pole_grid_lon = 0.

        return {
            'grid_north_pole_latitude': grid_north_pole_lat,
            'grid_north_pole_longitude': grid_north_pole_lon,
            'north_pole_grid_longitude': north_pole_grid_lon
        }

    def _set_crs_parameters(self, grid_north_pole_latitude,
                            grid_north_pole_longitude,
                            north_pole_grid_longitude):
        # WGS84
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'latitude_longitude',
                        'unit_conversion_factor': 0.0174532925199433})

        datum = cf.Datum(
            parameters={'geographic_crs_name': 'WGS 84',
                        'horizontal_datum_name': 'WGS_1984',
                        'semi_major_axis': 6378137.0,
                        'inverse_flattening': 298.257223563,
                        'longitude_of_prime_meridian': 0.0}
        )

        self._f.set_construct(
            cf.CoordinateReference(
                datum=datum,
                coordinate_conversion=coord_conversion,
                coordinates=[self._f.dim(self._Y_name, key=True),
                             self._f.dim(self._X_name, key=True),
                             self._f.aux('latitude', key=True),
                             self._f.aux('longitude', key=True)]
            )
        )

        # Rotated Grid
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'unit_conversion_factor': 0.0174532925199433,
                        'grid_north_pole_latitude':
                            grid_north_pole_latitude,
                        'grid_north_pole_longitude':
                            grid_north_pole_longitude,
                        'north_pole_grid_longitude':
                            north_pole_grid_longitude}
        )

        datum = cf.Datum(
            parameters={'horizontal_datum_name': 'WGS_1984',
                        'semi_major_axis': 6378137.0,
                        'inverse_flattening': 298.257223563,
                        'longitude_of_prime_meridian': 0.0}
        )

        self._f.set_construct(
            cf.CoordinateReference(
                datum=datum,
                coordinate_conversion=coord_conversion,
                coordinates=[self._f.dim(self._Y_name, key=True),
                             self._f.dim(self._X_name, key=True),
                             self._f.aux('latitude', key=True),
                             self._f.aux('longitude', key=True)]
            )
        )

    def _check_crs_rotation_parameters(self, coord_ref):
        if hasattr(coord_ref, 'coordinate_conversion'):
            # eliminate 'unit'/'units' parameter as it is not standardised in
            # the CF convention, and the split of the coordinate reference into
            # coordinate conversion/datum is a CF data model artifact so they
            # are bundled in as one and can share parameters in CF-netCDF
            # (which can result in one unit parameter overwriting another)
            for p in ['unit', 'units']:
                coord_ref.coordinate_conversion.del_parameter(p, None)

            conversion = self._f.coordinate_reference(
                'grid_mapping_name:rotated_latitude_longitude'
            ).coordinate_conversion.equals(coord_ref.coordinate_conversion)
        else:
            conversion = False

        return conversion

    def _rotate_and_set_lat_lon(self, grid_north_pole_latitude,
                                grid_north_pole_longitude,
                                north_pole_grid_longitude):
        # define transformation from rotated lat/lon to 'true' lat/lon
        trans = pyproj.Transformer.from_crs(
            # Rotated Grid
            f"+proj=ob_tran +o_proj=lonlat +ellps=WGS84 +datum=WGS84 "
            f"+o_lat_p={grid_north_pole_latitude} "
            f"+o_lon_p={north_pole_grid_longitude} "
            f"+lon_0={grid_north_pole_longitude + 180.}",
            # WGS84
            'epsg:4326',
            always_xy=True
        )

        # project coordinates
        lon, lat = trans.transform(*np.meshgrid(self.X.array, self.Y.array))

        # project coordinate bounds
        lon_bnds = np.zeros(lon.shape + (4,), lon.dtype)
        lat_bnds = np.zeros(lat.shape + (4,), lat.dtype)
        lon_bnds[..., 0], lat_bnds[..., 0] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 0],
                         self.Y_bounds.array[..., 0])
        )
        lon_bnds[..., 1], lat_bnds[..., 1] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 1],
                         self.Y_bounds.array[..., 0])
        )
        lon_bnds[..., 2], lat_bnds[..., 2] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 1],
                         self.Y_bounds.array[..., 1])
        )
        lon_bnds[..., 3], lat_bnds[..., 3] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 0],
                         self.Y_bounds.array[..., 1])
        )

        # set constructs
        self._f.set_construct(
            cf.AuxiliaryCoordinate(
                      properties={'standard_name': 'latitude',
                                  'units': 'degrees_north'},
                      data=cf.Data(lat),
                      bounds=cf.Bounds(data=cf.Data(lat_bnds))
            ),
            axes=['Y', 'X']
        )
        self._f.set_construct(
            cf.AuxiliaryCoordinate(
                properties={'standard_name': 'longitude',
                            'units': 'degrees_east'},
                data=cf.Data(lon),
                bounds=cf.Bounds(data=cf.Data(lon_bnds))
            ),
            axes=['Y', 'X']
        )

    def is_space_equal_to(self, field, ignore_z=False):
        """Compare equality between the RotatedLatLonGrid and the
        spatial (X, Y, and Z) dimension coordinate in a `cf.Field`.

        The coordinate values, the bounds, the units, and the coordinate
        conversion and its datum of the field are compared against those
        of the Grid.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against RotatedLatLonGrid.

            ignore_z: `bool`, optional
                Option to ignore the dimension coordinate along the Z
                axis. If not provided, set to default False (i.e. Z is
                not ignored).

        :Returns: `bool`
        """
        # check whether X/Y(/Z if not ignored) constructs are identical
        # and if coordinate_reference match (by checking its
        # coordinate_conversion and its datum separately, because
        # coordinate_reference.equals() would also check the size of
        # the collections of coordinates, which may be rightfully
        # different if Z is ignored)
        y_x_z = super(RotatedLatLonGrid, self).is_space_equal_to(field,
                                                                 ignore_z)

        conversion = False
        if hasattr(field, 'coordinate_reference'):
            if field.coordinate_reference('grid_mapping_name:'
                                          'rotated_latitude_longitude',
                                          default=False):
                conversion = self._check_crs_rotation_parameters(
                    field.coordinate_reference(
                        'grid_mapping_name:rotated_latitude_longitude'
                    )
                )

        return y_x_z and conversion

    def spans_same_region_as(self, rotated_grid, ignore_z=False):
        """Compare equality in region spanned between the
        RotatedLatLonGrid and another instance of RotatedLatLonGrid.

        For each axis, the lower bound of their first cell and the
        upper bound of their last cell are compared.

        :Parameters:

            rotated_grid: `RotatedLatLonGrid`
                The other RotatedLatLonGrid to be compared against
                RotatedLatLonGrid.

            ignore_z: `bool`, optional
                If True, the dimension coordinates along the Z axes of
                the RotatedLatLonGrid instances will not be compared.
                If not provided, set to default value False (i.e. Z is
                not ignored).

        :Returns: `bool`
        """
        if not isinstance(rotated_grid, RotatedLatLonGrid):
            return False
        else:
            y_x_z = super(RotatedLatLonGrid, self).spans_same_region_as(
                rotated_grid, ignore_z
            )

            if hasattr(rotated_grid, 'coordinate_reference'):
                conversion = self._check_crs_rotation_parameters(
                    rotated_grid.coordinate_reference
                )
            else:
                conversion = False

            return y_x_z and conversion


class BritishNationalGrid(Grid):
    """This class characterises the spatial dimension for a `Component`
    as a regular grid on a cartesian domain whose coordinates are
    northings and eastings covering Great Britain and Northern Ireland
    (`EPSG:27700 <https://epsg.io/27700>`_).
    """
    # characteristics of the dimension coordinates
    _Z_name = 'altitude'
    _Y_name = 'projection_y_coordinate'
    _X_name = 'projection_x_coordinate'
    _Z_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _Y_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _X_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _Z_limits = None
    _Y_limits = (0, 1300000)
    _X_limits = (0, 700000)
    # contiguity of lower and upper limits
    _Z_limits_contiguous = False
    _Y_limits_contiguous = False
    _X_limits_contiguous = False
    # allow domain to wrap around limits
    _Z_wrap_around = False
    _Y_wrap_around = False
    _X_wrap_around = False

    def __init__(
            self,
            projection_y_coordinate, projection_x_coordinate,
            projection_y_coordinate_bounds, projection_x_coordinate_bounds,
            # altitude=None, altitude_bounds=None
    ):
        """**Instantiation**

        :Parameters:

            projection_y_coordinate: one-dimensional array-like object
                The array of northing coordinates in metres defining a
                spatial dimension of the domain. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values. Coordinates must be ordered positively.

                *Parameter example:* ::

                    projection_y_coordinate=[12500, 13500, 14500]

                *Parameter example:* ::

                    projection_y_coordinate=numpy.arange(12500, 15500, 1000)

            projection_x_coordinate: one-dimensional array-like object
                The array of easting coordinates in metres defining a
                spatial dimension of the domain. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values. Coordinates must be ordered positively.

                *Parameter example:* ::

                    projection_x_coordinate=(80500, 81500, 82500, 83500)

                *Parameter example:* ::

                    projection_x_coordinate=numpy.arange(80500, 84500, 1000)

            projection_y_coordinate_bounds: two-dimensional array-like object
                The array of northing coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *projection_y_coordinate*
                and the second dimension equal to 2. Must contain
                numerical values.

                *Parameter example:* ::

                    projection_y_coordinate_bounds=[
                        [12e3, 13e3], [13e3, 14e3], [14e3, 15e3]
                    ]

                *Parameter example:* ::

                    projection_y_coordinate_bounds=numpy.column_stack(
                        (numpy.arange(12000, 15000, 1000),
                         numpy.arange(13000, 16000, 1000))
                    )

            projection_x_coordinate_bounds: two-dimensional array-like object
                The array of easting coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.ndarray`. Must be two dimensional with the first
                dimension equal to the size of *projection_x_coordinate*
                and the second dimension equal to 2. Must contain
                numerical values.

                *Parameter example:* ::

                    projection_x_coordinate_bounds=((80e3, 81e3), (81e3, 82e3),
                                                    (82e3, 83e3), (83e3, 84e3))

                *Parameter example:* ::

                    projection_x_coordinate_bounds=numpy.column_stack(
                        (numpy.arange(80000, 84000, 1000),
                         numpy.arange(81000, 85000, 1000))
                    )

            .. altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining a
                spatial dimension of the domain (with upwards as the
                positive direction). May be any type that can be cast to
                a `numpy.ndarray`. Must contain numerical values.
                Ignored if *altitude_bounds* not also provided.

                *Parameter example:* ::

                    altitude=[10]

            .. altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate (with upwards as the positive direction).
                May be any type that can be cast to a `numpy.ndarray`.
                Must be two dimensional with the first dimension equal
                to the size of *altitude* and the second dimension equal
                to 2. Must contain numerical values. Ignored if
                *altitude* not also provided.

                *Parameter example:* ::

                    altitude_bounds=[[0, 20]]

        **Examples**

        Instantiating a 2D grid:

        >>> import numpy
        >>> sd = BritishNationalGrid(
        ...     projection_y_coordinate=[12500, 13500, 14500],
        ...     projection_x_coordinate=(80500, 81500, 82500, 83500),
        ...     projection_y_coordinate_bounds=numpy.column_stack(
        ...         (numpy.arange(12000, 15000, 1000),
        ...          numpy.arange(13000, 16000, 1000))
        ...     ),
        ...     projection_x_coordinate_bounds=numpy.column_stack(
        ...         (numpy.arange(80000, 84000, 1000),
        ...          numpy.arange(81000, 85000, 1000))
        ...     )
        ... )
        >>> print(sd)
        BritishNationalGrid(
            shape {Y, X}: (3, 4)
            Y, projection_y_coordinate (3,): [12500, 13500, 14500] m
            X, projection_x_coordinate (4,): [80500, ..., 83500] m
            Y_bounds (3, 2): [[12000, ..., 15000]] m
            X_bounds (4, 2): [[80000, ..., 84000]] m
        )

        .. Instantiating a 3D grid:
        ..
        .. >>> import numpy
        .. >>> sd = BritishNationalGrid(
        .. ...     projection_y_coordinate=[12500, 13500, 14500],
        .. ...     projection_x_coordinate=(80500, 81500, 82500, 83500),
        .. ...     projection_y_coordinate_bounds=numpy.column_stack(
        .. ...         (numpy.arange(12000, 15000, 1000),
        .. ...          numpy.arange(13000, 16000, 1000))
        .. ...     ),
        .. ...     projection_x_coordinate_bounds=numpy.column_stack(
        .. ...         (numpy.arange(80000, 84000, 1000),
        .. ...          numpy.arange(81000, 85000, 1000))
        .. ...     ),
        .. ...     altitude=[10],
        .. ...     altitude_bounds=[[0, 20]]
        .. ... )
        .. >>> print(sd)
        .. BritishNationalGrid(
        ..     shape {Z, Y, X}: (1, 3, 4)
        ..     Z, altitude (1,): [10] m
        ..     Y, projection_y_coordinate (3,): [12500, 13500, 14500] m
        ..     X, projection_x_coordinate (4,): [80500, ..., 83500] m
        ..     Z_bounds (1, 2): [[0, 20]] m
        ..     Y_bounds (3, 2): [[12000, ..., 15000]] m
        ..     X_bounds (4, 2): [[80000, ..., 84000]] m
        .. )
        """
        super(BritishNationalGrid, self).__init__()

        # TODO: reintroduce Z dimension when 3D components
        #       are effectively supported
        # if altitude is not None and altitude_bounds is not None:
        #     self._set_space(altitude, altitude_bounds, name=self._Z_name,
        #                     units=self._Z_units[0], axis='Z',
        #                     limits=self._Z_limits, wrap_around=self._Z_wrap_around)
        #     self._f.dim('Z').set_property('positive', 'up')

        self._set_space(projection_y_coordinate, projection_y_coordinate_bounds,
                        name=self._Y_name, units=self._Y_units[0], axis='Y',
                        limits=self._Y_limits, wrap_around=self._Y_wrap_around)
        self._set_space(projection_x_coordinate, projection_x_coordinate_bounds,
                        name=self._X_name, units=self._X_units[0], axis='X',
                        limits=self._X_limits, wrap_around=self._X_wrap_around)

        self._project_and_set_lat_lon()

        self._set_crs_parameters()

        # set dummy data needed for using inner field for remapping
        self._set_dummy_data()

    @classmethod
    def from_extent_and_resolution(
            cls,
            projection_y_coordinate_extent,
            projection_x_coordinate_extent,
            projection_y_coordinate_resolution,
            projection_x_coordinate_resolution,
            projection_y_coordinate_projection_x_coordinate_location='centre',
            # altitude_extent=None,
            # altitude_resolution=None,
            # altitude_location='centre'
    ):
        """Instantiate a `BritishNationalGrid` from the extent and the
        resolution of northing, easting coordinates.

        :Parameters:

            projection_y_coordinate_extent: pair of `float` or `int`
                The extent of northing coordinates in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the northing
                coordinate, the second element of the pair is the
                location of the end of the extent along the northing
                coordinate. Extent must be oriented positively. May be
                any type that can be unpacked (e.g. `tuple`, `list`,
                `numpy.ndarray`).

                *Parameter example:* ::

                    projection_y_coordinate_extent=(12000, 15000)

            projection_x_coordinate_extent: pair of `float` or `int`
                The extent of easting coordinates in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the easting
                coordinate, the second element of the pair is the
                location of the end of the extent along the easting
                coordinate. Extent must be oriented positively. May be
                any type that can be unpacked (e.g. `tuple`, `list`,
                `numpy.ndarray`).

                *Parameter example:* ::

                    projection_x_coordinate_extent=(80000, 84000)

            projection_y_coordinate_resolution: `float` or `int`
                The spacing between two consecutive northing coordinates
                in metres for the desired grid. Must be positive.

                *Parameter example:* ::

                    projection_y_coordinate_resolution=1000

            projection_x_coordinate_resolution: `float` or `int`
                The spacing between two consecutive easting coordinates
                in metres for the desired grid. Must be positive.

                *Parameter example:* ::

                    projection_x_coordinate_resolution=1000

            projection_y_coordinate_projection_x_coordinate_location: `str` or `int`, optional
                The location of the northing and easting coordinates
                in relation to their grid cells (i.e. their bounds).
                This information is required to generate the latitude
                and longitude bounds for each grid coordinate. If not
                provided, set to default 'centre'.

                The locations left and right are related to the
                easting coordinates (X-axis), while the locations lower
                and upper are related to the northing coordinates
                (Y-axis). The orientation of the coordinate system
                considered is detailed below (i.e. positive directions
                are northwards and eastwards).

                .. seealso::

                   *latitude_longitude_location* in
                   `LatLonGrid.from_extent_and_resolution`

            .. altitude_extent: pair of `float` or `int`, optional
                The extent of altitude coordinate in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the altitude
                coordinate, the second element of the pair is the
                location of the end of the extent along the altitude
                coordinate. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    altitude_extent=(0, 20)

            .. altitude_resolution: `float` or `int`, optional
                The spacing between two consecutive altitude coordinates
                in metres for the desired grid.

                *Parameter example:* ::

                    altitude_resolution=20

            .. altitude_location: `str` or `int`, optional
                The location of the altitude coordinates in relation to
                their grid cells (i.e. their bounds). This information
                is required to generate the altitude bounds for each
                grid coordinate. If not provided, set to default
                'centre'.

                The locations top and bottom are related to the
                altitude coordinate (Z-axis). The orientation of the
                coordinate system considered is such that the positive
                direction is upwards.

                .. seealso::

                   *altitude_location* in `LatLonGrid.from_extent_and_resolution`

        :Returns: `BritishNationalGrid`

        **Examples**

        .. Instantiating grid with optional altitude coordinates:
        ..
        .. >>> sd = BritishNationalGrid.from_extent_and_resolution(
        .. ...     projection_y_coordinate_extent=(12000, 15000),
        .. ...     projection_x_coordinate_extent=(80000, 84000),
        .. ...     projection_y_coordinate_resolution=1000,
        .. ...     projection_x_coordinate_resolution=1000,
        .. ...     altitude_extent=(0, 20),
        .. ...     altitude_resolution=20
        .. ... )
        .. >>> print(sd)
        .. BritishNationalGrid(
        ..     shape {Z, Y, X}: (1, 3, 4)
        ..     Z, altitude (1,): [10.0] m
        ..     Y, projection_y_coordinate (3,): [12500.0, 13500.0, 14500.0] m
        ..     X, projection_x_coordinate (4,): [80500.0, ..., 83500.0] m
        ..     Z_bounds (1, 2): [[0.0, 20.0]] m
        ..     Y_bounds (3, 2): [[12000.0, ..., 15000.0]] m
        ..     X_bounds (4, 2): [[80000.0, ..., 84000.0]] m
        .. )

        Instantiating grid using non-standard coordinates location in their cells:

        >>> sd = BritishNationalGrid.from_extent_and_resolution(
        ...     projection_y_coordinate_extent=(12000, 15000),
        ...     projection_x_coordinate_extent=(80000, 84000),
        ...     projection_y_coordinate_resolution=1000,
        ...     projection_x_coordinate_resolution=1000,
        ...     projection_y_coordinate_projection_x_coordinate_location='upper right'
        ... )
        >>> print(sd)
        BritishNationalGrid(
            shape {Y, X}: (3, 4)
            Y, projection_y_coordinate (3,): [13000.0, 14000.0, 15000.0] m
            X, projection_x_coordinate (4,): [81000.0, ..., 84000.0] m
            Y_bounds (3, 2): [[12000.0, ..., 15000.0]] m
            X_bounds (4, 2): [[80000.0, ..., 84000.0]] m
        )
        """
        return super(BritishNationalGrid, cls).from_extent_and_resolution(
            projection_y_coordinate_extent=projection_y_coordinate_extent,
            projection_x_coordinate_extent=projection_x_coordinate_extent,
            projection_y_coordinate_resolution=projection_y_coordinate_resolution,
            projection_x_coordinate_resolution=projection_x_coordinate_resolution,
            projection_y_coordinate_projection_x_coordinate_location=(
                projection_y_coordinate_projection_x_coordinate_location
            ),
            # altitude_extent=altitude_extent,
            # altitude_resolution=altitude_resolution,
            # altitude_location=altitude_location
        )

    @classmethod
    def from_field(cls, field):
        """Instantiate a `BritishNationalGrid` from spatial dimension
        coordinates of a `cf.Field`.

        :Parameters:

            field: `cf.Field`
                The field object that will be used to instantiate a
                `BritishNationalGrid` instance. This field must feature
                a 'projection_y_coordinate' and a 'projection_x_coordinate'
                dimension coordinates, and these must feature bounds. In
                addition, the coordination conversion 'transverse_mercator'
                must correspond to the parameters of the British National
                Grid (`EPSG:27700`_).

                ..
                   This field may optionally feature an 'altitude'
                   dimension coordinate alongside its bounds (both
                   required otherwise ignored).

                .. _`EPSG:27700`: https://epsg.io/27700

        :Returns: `BritishNationalGrid`

        **Examples**

        Instantiating from a 2D field:

        >>> import cf
        >>> import numpy
        >>> f = cf.Field()
        >>> yc = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'projection_y_coordinate',
        ...                     'units': 'metres',
        ...                     'axis': 'Y'},
        ...         data=cf.Data([12500, 13500, 14500]),
        ...         bounds=cf.Bounds(
        ...             data=cf.Data(
        ...                 numpy.column_stack(
        ...                     (numpy.arange(12000, 15000, 1000),
        ...                      numpy.arange(13000, 16000, 1000))
        ...                 )
        ...             )
        ...         )
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=3))
        ... )
        >>> xc = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'projection_x_coordinate',
        ...                     'units': 'metres',
        ...                     'axis': 'X'},
        ...         data=cf.Data([80500, 81500, 82500, 83500]),
        ...         bounds=cf.Bounds(
        ...             data=cf.Data(
        ...                 numpy.column_stack(
        ...                     (numpy.arange(80000, 84000, 1000),
        ...                      numpy.arange(81000, 85000, 1000))
        ...                 )
        ...             )
        ...         )
        ...     ),
        ...     axes=f.set_construct(cf.DomainAxis(size=4))
        ... )
        >>> crs = f.set_construct(
        ...     cf.CoordinateReference(
        ...         coordinate_conversion=cf.CoordinateConversion(
        ...             parameters={'grid_mapping_name': 'transverse_mercator',
        ...                         'projected_crs_name': 'OSGB 1936 / British National Grid',
        ...                         'latitude_of_projection_origin': 49.0,
        ...                         'longitude_of_central_meridian': -2.0,
        ...                         'scale_factor_at_central_meridian': 0.9996012717,
        ...                         'false_easting': 400000.0,
        ...                         'false_northing': -100000.0,
        ...                         'unit_conversion_factor': 0.0174532925199433}
        ...         ),
        ...         datum=cf.Datum(
        ...             parameters={'geographic_crs_name': 'OSGB 1936',
        ...                         'horizontal_datum_name': 'OSGB_1936',
        ...                         'semi_major_axis': 6377563.396,
        ...                         'inverse_flattening': 299.3249646,
        ...                         'towgs84': [375., -111., 431., 0., 0., 0., 0.],
        ...                         'longitude_of_prime_meridian': 0.0}
        ...         ),
        ...         coordinates=(yc, xc)
        ...     )
        ... )
        >>> sd = BritishNationalGrid.from_field(f)
        >>> print(sd)
        BritishNationalGrid(
            shape {Y, X}: (3, 4)
            Y, projection_y_coordinate (3,): [12500, 13500, 14500] m
            X, projection_x_coordinate (4,): [80500, ..., 83500] m
            Y_bounds (3, 2): [[12000, ..., 15000]] m
            X_bounds (4, 2): [[80000, ..., 84000]] m
        )

        Using the field interface back and forth:

        >>> sd1 = BritishNationalGrid.from_extent_and_resolution(
        ...     projection_y_coordinate_extent=(12000, 15000),
        ...     projection_x_coordinate_extent=(80000, 84000),
        ...     projection_y_coordinate_resolution=1000,
        ...     projection_x_coordinate_resolution=1000,
        ... )
        >>> sd2 = BritishNationalGrid.from_field(sd1.to_field())
        >>> sd2 == sd1
        True

        .. Instantiating from a 3D field:
        ..
        .. >>> import cf
        .. >>> import numpy
        .. >>> f = cf.Field()
        .. >>> yc = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'projection_y_coordinate',
        .. ...                     'units': 'metres',
        .. ...                     'axis': 'Y'},
        .. ...         data=cf.Data([12500, 13500, 14500]),
        .. ...         bounds=cf.Bounds(
        .. ...             data=cf.Data(
        .. ...                 numpy.column_stack(
        .. ...                     (numpy.arange(12000, 15000, 1000),
        .. ...                      numpy.arange(13000, 16000, 1000))
        .. ...                 )
        .. ...             )
        .. ...         )
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=3))
        .. ... )
        .. >>> xc = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'projection_x_coordinate',
        .. ...                     'units': 'metres',
        .. ...                     'axis': 'X'},
        .. ...         data=cf.Data([80500, 81500, 82500, 83500]),
        .. ...         bounds=cf.Bounds(
        .. ...             data=cf.Data(
        .. ...                 numpy.column_stack(
        .. ...                     (numpy.arange(80000, 84000, 1000),
        .. ...                      numpy.arange(81000, 85000, 1000))
        .. ...                 )
        .. ...             )
        .. ...         )
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=4))
        .. ... )
        .. >>> alt = f.set_construct(
        .. ...     cf.DimensionCoordinate(
        .. ...         properties={'standard_name': 'altitude',
        .. ...                     'units': 'm',
        .. ...                     'axis': 'Z'},
        .. ...         data=cf.Data([10]),
        .. ...         bounds=cf.Bounds(data=cf.Data([[0, 20]]))
        .. ...     ),
        .. ...     axes=f.set_construct(cf.DomainAxis(size=1))
        .. ... )
        .. >>> crs = f.set_construct(
        .. ...     cf.CoordinateReference(
        .. ...         coordinate_conversion=cf.CoordinateConversion(
        .. ...             parameters={'grid_mapping_name': 'transverse_mercator',
        .. ...                         'projected_crs_name': 'OSGB 1936 / British National Grid',
        .. ...                         'latitude_of_projection_origin': 49.0,
        .. ...                         'longitude_of_central_meridian': -2.0,
        .. ...                         'scale_factor_at_central_meridian': 0.9996012717,
        .. ...                         'false_easting': 400000.0,
        .. ...                         'false_northing': -100000.0,
        .. ...                         'unit_conversion_factor': 0.0174532925199433}
        .. ...         ),
        .. ...         datum=cf.Datum(
        .. ...             parameters={'geographic_crs_name': 'OSGB 1936',
        .. ...                         'horizontal_datum_name': 'OSGB_1936',
        .. ...                         'semi_major_axis': 6377563.396,
        .. ...                         'inverse_flattening': 299.3249646,
        .. ...                         'towgs84': [375., -111., 431., 0., 0., 0., 0.],
        .. ...                         'longitude_of_prime_meridian': 0.0}
        .. ...         ),
        .. ...         coordinates=(yc, xc)
        .. ...     )
        .. ... )
        .. >>> sd = BritishNationalGrid.from_field(f)
        .. >>> print(sd)
        .. BritishNationalGrid(
        ..     shape {Y, X}: (1, 3, 4)
        ..     Y, projection_y_coordinate (3,): [12500, 13500, 14500] m
        ..     X, projection_x_coordinate (4,): [80500, ..., 83500] m
        ..     Z_bounds (1, 2): [[0, 20]] m
        ..     Y_bounds (3, 2): [[12000, ..., 15000]] m
        ..     X_bounds (4, 2): [[80000, ..., 84000]] m
        .. )
        """
        extraction_xyz = cls._extract_xyz_from_field(field)

        inst = cls(
            projection_y_coordinate=extraction_xyz['Y'],
            projection_x_coordinate=extraction_xyz['X'],
            projection_y_coordinate_bounds=extraction_xyz['Y_bounds'],
            projection_x_coordinate_bounds=extraction_xyz['X_bounds'],
            # altitude=extraction_xyz['Z'],
            # altitude_bounds=extraction_xyz['Z_bounds']
        )

        conversion = False
        if hasattr(field, 'coordinate_reference'):
            if field.coordinate_reference('grid_mapping_name:'
                                          'transverse_mercator',
                                          default=False):
                conversion = inst._check_crs_projection_parameters(
                    field.coordinate_reference(
                        'grid_mapping_name:transverse_mercator'
                    )
                )

        if conversion:
            return inst
        else:
            raise RuntimeError(
                'field coordinate reference not compatible '
                'with British National Grid (EPSG:27700)'
            )

    @property
    def coordinate_reference(self):
        """Return the coordinate reference of the `BritishNationalGrid`
        instance as a `cf.CoordinateReference` instance.
        """
        return self._f.coordinate_reference(
            'grid_mapping_name:transverse_mercator'
        )

    def _set_crs_parameters(self):
        # WGS84
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'latitude_longitude',
                        'unit_conversion_factor': 0.0174532925199433}
        )

        datum = cf.Datum(
            parameters={'geographic_crs_name': 'WGS 84',
                        'horizontal_datum_name': 'WGS_1984',
                        'semi_major_axis': 6378137.0,
                        'inverse_flattening': 298.257223563,
                        'longitude_of_prime_meridian': 0.0}
        )

        self._f.set_construct(
            cf.CoordinateReference(
                datum=datum,
                coordinate_conversion=coord_conversion,
                coordinates=[self._f.dim(self._Y_name, key=True),
                             self._f.dim(self._X_name, key=True),
                             self._f.aux('latitude', key=True),
                             self._f.aux('longitude', key=True)]
            )
        )

        # OSGB_1936/BNG
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'transverse_mercator',
                        'projected_crs_name': 'OSGB 1936 / British National Grid',
                        'latitude_of_projection_origin': 49.0,
                        'longitude_of_central_meridian': -2.0,
                        'scale_factor_at_central_meridian': 0.9996012717,
                        'false_easting': 400000.0,
                        'false_northing': -100000.0,
                        'unit_conversion_factor': 0.0174532925199433}
        )

        datum = cf.Datum(
            parameters={'geographic_crs_name': 'OSGB 1936',
                        'horizontal_datum_name': 'OSGB_1936',
                        'semi_major_axis': 6377563.396,
                        'inverse_flattening': 299.3249646,
                        'towgs84': [375., -111., 431., 0., 0., 0., 0.],
                        'longitude_of_prime_meridian': 0.0}
        )

        self._f.set_construct(
            cf.CoordinateReference(
                datum=datum,
                coordinate_conversion=coord_conversion,
                coordinates=[self._f.dim(self._Y_name, key=True),
                             self._f.dim(self._X_name, key=True),
                             self._f.aux('latitude', key=True),
                             self._f.aux('longitude', key=True)]
            )
        )

    def _check_crs_projection_parameters(self, coord_ref):
        if (hasattr(coord_ref, 'coordinate_conversion')
                and hasattr(coord_ref, 'datum')):
            # eliminate 'unit'/'units' parameter as it is not standardised in
            # the CF convention, and the split of the coordinate reference into
            # coordinate conversion/datum is a CF data model artifact so they
            # are bundled in as one and can share parameters in CF-netCDF
            # (which can result in one unit parameter overwriting another)
            for p in ['unit', 'units']:
                coord_ref.coordinate_conversion.del_parameter(p, None)
                coord_ref.datum.del_parameter(p, None)

            coord_conversion = self._f.coordinate_reference(
                    'grid_mapping_name:transverse_mercator'
            ).coordinate_conversion.equals(coord_ref.coordinate_conversion)

            datum = self._f.coordinate_reference(
                    'grid_mapping_name:transverse_mercator'
            ).datum.equals(coord_ref.datum)

            conversion = coord_conversion and datum
        else:
            conversion = False

        return conversion

    def _project_and_set_lat_lon(self):
        # define transformation from BNG to 'true' lat/lon
        trans = pyproj.Transformer.from_crs(
            # British National Grid
            'epsg:27700',
            # WGS84
            'epsg:4326',
            always_xy=True
        )

        # project coordinates
        lon, lat = trans.transform(*np.meshgrid(self.X.array, self.Y.array))

        # project coordinate bounds
        lon_bnds = np.zeros(lon.shape + (4,), lon.dtype)
        lat_bnds = np.zeros(lat.shape + (4,), lat.dtype)
        lon_bnds[..., 0], lat_bnds[..., 0] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 0],
                         self.Y_bounds.array[..., 0])
        )
        lon_bnds[..., 1], lat_bnds[..., 1] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 1],
                         self.Y_bounds.array[..., 0])
        )
        lon_bnds[..., 2], lat_bnds[..., 2] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 1],
                         self.Y_bounds.array[..., 1])
        )
        lon_bnds[..., 3], lat_bnds[..., 3] = trans.transform(
            *np.meshgrid(self.X_bounds.array[..., 0],
                         self.Y_bounds.array[..., 1])
        )

        # set constructs
        self._f.set_construct(
            cf.AuxiliaryCoordinate(
                      properties={'standard_name': 'latitude',
                                  'units': 'degrees_north'},
                      data=cf.Data(lat),
                      bounds=cf.Bounds(data=cf.Data(lat_bnds))
            ),
            axes=['Y', 'X']
        )
        self._f.set_construct(
            cf.AuxiliaryCoordinate(
                properties={'standard_name': 'longitude',
                            'units': 'degrees_east'},
                data=cf.Data(lon),
                bounds=cf.Bounds(data=cf.Data(lon_bnds))
            ),
            axes=['Y', 'X']
        )

    @Grid.cell_area.getter
    def cell_area(self):
        """The horizontal area for the grid cells of the SpaceDomain in
        square metres given as a `cf.Field` and returned as a
        `numpy.ndarray`.

        :Parameters:

           areas: `cf.Field`
               The field containing the horizontal grid cell area. The
               shape of the data array must be the same as the
               SpaceDomain. The field data must contain surface area
               values in square metres.

        :Returns:

           `numpy.ndarray`
               The array containing the horizontal grid cell area
               values in square metres. If not set previously, computed
               automatically.

        **Examples**

        Retrieving automatically computed grid cell area:

        >>> grid = BritishNationalGrid.from_extent_and_resolution(
        ...     projection_y_coordinate_extent=(12000, 15000),
        ...     projection_y_coordinate_resolution=1000,
        ...     projection_x_coordinate_extent=(80000, 84000),
        ...     projection_x_coordinate_resolution=2000
        ... )
        >>> print(grid.cell_area)
        [[2000000. 2000000.]
         [2000000. 2000000.]
         [2000000. 2000000.]]
        >>> print(grid)
        BritishNationalGrid(
            shape {Y, X}: (3, 2)
            Y, projection_y_coordinate (3,): [12500.0, 13500.0, 14500.0] m
            X, projection_x_coordinate (2,): [81000.0, 83000.0] m
            Y_bounds (3, 2): [[12000.0, ..., 15000.0]] m
            X_bounds (2, 2): [[80000.0, ..., 84000.0]] m
            cell_area (3, 2): [[2000000.0, ..., 2000000.0]] m2
        )

        Manually assigning grid cell area values:

        >>> import numpy
        >>> areas = grid.to_field()
        >>> areas.set_data(numpy.array([[1999999, 1999999],
        ...                             [1999999, 1999999],
        ...                             [1999999, 1999999]]))
        >>> areas.units = 'm2'
        >>> grid.cell_area = areas
        >>> print(grid.cell_area)
        [[1999999. 1999999.]
         [1999999. 1999999.]
         [1999999. 1999999.]]
        """
        if self._cell_area is None:
            self._cell_area = self._compute_cell_area()
        return self._cell_area

    def _compute_cell_area(self):
        x_side = self.X_bounds.array[:, 1] - self.X_bounds.array[:, 0]
        y_side = self.Y_bounds.array[:, 1] - self.Y_bounds.array[:, 0]

        return np.dot(y_side[:, np.newaxis], x_side[np.newaxis, :])

    def is_space_equal_to(self, field, ignore_z=False):
        """Compare equality between the BritishNationalGrid and the
        spatial (X, Y, and Z) dimension coordinate in a `cf.Field`.

        The coordinate values, the bounds, the units, and the coordinate
        conversion and its datum of the field are compared against those
        of the BritishNationalGrid.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against
                BritishNationalGrid.

            ignore_z: `bool`, optional
                Option to ignore the dimension coordinate along the Z
                axis. If not provided, set to default False (i.e. Z is
                not ignored).

        :Returns: `bool`
        """
        # check whether X/Y(/Z if not ignored) constructs are identical
        # and if coordinate_reference match (by checking its
        # coordinate_conversion and its datum separately, because
        # coordinate_reference.equals() would also check the size of
        # the collections of coordinates, which may be rightfully
        # different if Z is ignored)
        y_x_z = super(BritishNationalGrid, self).is_space_equal_to(
            field, ignore_z
        )

        conversion = False
        if hasattr(field, 'coordinate_reference'):
            if field.coordinate_reference('grid_mapping_name:'
                                          'transverse_mercator',
                                          default=False):
                conversion = self._check_crs_projection_parameters(
                    field.coordinate_reference(
                        'grid_mapping_name:transverse_mercator'
                    )
                )

        return y_x_z and conversion

    def spans_same_region_as(self, grid, ignore_z=False):
        """Compare equality in region spanned between the
        RotatedLatLonGrid and another instance of RotatedLatLonGrid.

        For each axis, the lower bound of their first cell and the
        upper bound of their last cell are compared.

        :Parameters:

            grid: `BritishNationalGrid`
                The other BritishNationalGrid to be compared against
                BritishNationalGrid.

            ignore_z: `bool`, optional
                If True, the dimension coordinates along the Z axes of
                the BritishNationalGrid instances will not be compared.
                If not provided, set to default value False (i.e. Z is
                not ignored).

        :Returns: `bool`
        """
        if not isinstance(grid, BritishNationalGrid):
            return False
        else:
            y_x_z = super(BritishNationalGrid, self).spans_same_region_as(
                grid, ignore_z
            )
            if hasattr(grid, 'coordinate_reference'):
                conversion = self._check_crs_projection_parameters(
                    grid.coordinate_reference
                )
            else:
                conversion = False

            return y_x_z and conversion
