import numpy as np
from copy import deepcopy
import re
import cf

from .settings import atol, rtol, decr, dtype_float


class SpaceDomain(object):
    """SpaceDomain characterises a spatial dimension that is needed by a
    `Component`. Any supported spatial configuration for a `Component`
    is a subclass of SpaceDomain.

    TODO: create a XYGrid subclass for Cartesian coordinates
    TODO: deal with sub-grid heterogeneity schemes (e.g. tiling, HRUs)
    """

    def __init__(self):
        self._f = cf.Field()

    @property
    def shape(self):
        """Return the size of the SpaceDomain dimension axes as a
        `tuple`. The corresponding names and order of the axes is
        accessible through the `axes` property.
        """
        return None

    @property
    def axes(self):
        """Return the name of the SpaceDomain dimension axes as a
        `tuple`. These names are properties of SpaceDomain, which give
        access to the coordinate values along each axis.
        """
        return None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.is_space_equal_to(other._f)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_space_equal_to(self, *args):
        raise TypeError("An instance of {} cannot be used to "
                        "characterise a spatial configuration directly, "
                        "please use a subclass of it instead.")

    def to_field(self):
        """Return a deep copy of the inner cf.Field used to characterise
        the SpaceDomain.
        """
        return deepcopy(self._f)


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

    @property
    def shape(self):
        has_z = self._f.has_construct(self._Z_name)
        return (
            (self._f.construct('Z').shape if has_z else ())
            + self._f.construct('Y').shape
            + self._f.construct('X').shape
        )

    @property
    def axes(self):
        has_z = self._f.has_construct(self._Z_name)
        return ('Z', 'Y', 'X') if has_z else ('Y', 'X')

    @property
    def Z(self):
        """Return the Z-axis of the SpaceDomain instance as a `cf.Data`
        instance if the Z-axis exists, otherwise return None.
        """
        if self._f.has_construct('Z'):
            return self._f.construct('Z').data
        else:
            return None

    @property
    def Y(self):
        """Return the Y-axis of the SpaceDomain instance as a `cf.Data`
        instance.
        """
        return self._f.construct('Y').data

    @property
    def X(self):
        """Return the X-axis of the SpaceDomain instance as a `cf.Data`
        instance.
        """
        return self._f.construct('X').data

    @property
    def Z_bounds(self):
        """Return the bounds of the Z-axis of the SpaceDomain instance
        as a `cf.Data` instance if the Z-axis exists, otherwise
        return None.
        """
        if self._f.has_construct('Z'):
            return self._f.construct('Z').bounds.data
        else:
            return None

    @property
    def Y_bounds(self):
        """Return the bounds of the Y-axis of the SpaceDomain instance
        as a `cf.Data` instance.
        """
        return self._f.construct('Y').bounds.data

    @property
    def X_bounds(self):
        """Return the bounds of the X-axis of the SpaceDomain instance
        as a `cf.Data` instance.
        """
        return self._f.construct('X').bounds.data

    @staticmethod
    def _check_dimension_regularity(dimension, name):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_regularity(numpy.array([0., 1., 2.]), 'test')
        >>> Grid._check_dimension_regularity(numpy.array([0., .9, 1.]), 'test')
        Traceback (most recent call last):
            ...
        RuntimeError: test space gap not constant across region
        """
        space_diff = np.diff(dimension) if dimension.ndim > 0 else 0
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol(), atol()):
            raise RuntimeError(
                "{} space gap not constant across region".format(name))

    @staticmethod
    def _check_dimension_bounds_regularity(bounds, name):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_regularity(
        ...     numpy.array([0., 1.]), 'test')
        >>> Grid._check_dimension_bounds_regularity(
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]), 'test')
        >>> Grid._check_dimension_bounds_regularity(
        ...     numpy.array([[0., .9], [.9, 2.], [2., 3.]]), 'test')
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        >>> Grid._check_dimension_bounds_regularity(
        ...     numpy.array([[0., 1.], [2., 3.], [2., 3.]]), 'test')
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds space gap not constant across region
        """
        rtol_ = rtol()
        atol_ = atol()

        space_diff = np.diff(bounds, axis=0) if bounds.ndim > 0 else 0
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol_, atol_):
            raise RuntimeError(
                "{} bounds space gap not constant across region".format(name))
        space_diff = np.diff(bounds, axis=1) if bounds.ndim > 1 else 0
        if not np.isclose(np.amin(space_diff), np.amax(space_diff),
                          rtol_, atol_):
            raise RuntimeError(
                "{} bounds space gap not constant across region".format(name))

    @staticmethod
    def _check_dimension_bounds_contiguity(bounds, name):
        """**Examples:**

        >>> import numpy
        >>> Grid._check_dimension_bounds_contiguity(
        ...     numpy.array([0., 1.]), 'test')
        >>> Grid._check_dimension_bounds_contiguity(
        ...     numpy.array([[0., 1.], [1., 2.], [2., 3.]]), 'test')
        >>> Grid._check_dimension_bounds_contiguity(
        ...     numpy.array([[0.0, 0.9], [1.0, 1.9], [2.0, 2.9]]), 'test')
        Traceback (most recent call last):
            ...
        RuntimeError: test bounds not contiguous across region
        """
        prev_to_next = bounds[1:, 0] - bounds[:-1, 1] \
            if bounds.ndim > 1 else 0
        if not np.allclose(prev_to_next, 0, rtol(), atol()):
            raise RuntimeError(
                "{} bounds not contiguous across region".format(name))

    def _set_space(self, dimension, dimension_bounds, name, units, axis):
        """**Examples:**

        >>> import numpy
        >>> Grid()._set_space([[0.5]], [0., 1.], 'test', '1', 'I')
        >>> Grid()._set_space([[0, 1], [1, 2]], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I')
        Traceback (most recent call last):
            ...
        RuntimeError: Grid test not convertible to 1D-array
        >>> Grid()._set_space([0.5, 1.5, 2.5], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I')
        >>> Grid()._set_space([0.5, 1.5], [[0., 1.], [1., 2.], [2., 3.]],
        ...                   'test', '1', 'I')
        Traceback (most recent call last):
            ...
        RuntimeError: Grid test bounds not compatible in size with test
        """
        # checks on dimension
        if not isinstance(dimension, np.ndarray):
            dimension = np.asarray(dimension)
        dimension = np.squeeze(dimension)
        if dimension.ndim > 1:
            raise RuntimeError(
                "{} {} not convertible to 1D-array".format(
                    self.__class__.__name__, name))
        self._check_dimension_regularity(dimension, name)

        # checks on dimension bounds
        if not isinstance(dimension_bounds, np.ndarray):
            dimension_bounds = np.asarray(dimension_bounds)
        dimension_bounds = np.squeeze(dimension_bounds)
        if dimension_bounds.shape != (*dimension.shape, 2):
            raise RuntimeError(
                "{} {} bounds not compatible in size with {}".format(
                    self.__class__.__name__, name, name))
        self._check_dimension_bounds_regularity(dimension_bounds, name)
        self._check_dimension_bounds_contiguity(dimension_bounds, name)

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
    def _get_grid_from_extent_and_resolution(cls, y_extent, x_extent,
                                             y_resolution, x_resolution,
                                             yx_location, z_extent,
                                             z_resolution, z_location):
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
                "{} {}-{} location '{}' not supported".format(
                    cls.__name__, cls._Y_name, cls._X_name, yx_location))

        # determine Y and X coordinates and their bounds
        y, y_bounds = cls._get_dimension_from_extent_and_resolution(
            y_extent, y_resolution, y_span, cls._Y_name
        )
        x, x_bounds = cls._get_dimension_from_extent_and_resolution(
            x_extent, x_resolution, x_span, cls._X_name
        )

        # infer Z span in relation to coordinate from location
        if z_extent is not None and z_resolution is not None:
            if z_location in cls._Z_loc_map['centre']:
                z_span = [[-0.5, 0.5]]
            elif z_location in cls._Z_loc_map['bottom']:
                z_span = [[0, 1]]
            elif z_location in cls._Z_loc_map['top']:
                z_span = [[-1, 0]]
            else:
                raise ValueError(
                    "{} {} location '{}' not supported".format(
                        cls.__name__, cls._Z_name, z_location))

            # determine latitude and longitude coordinates and their bounds
            z, z_bounds = cls._get_dimension_from_extent_and_resolution(
                z_extent, z_resolution, z_span, cls._Z_name
            )
        else:
            z = None
            z_bounds = None

        return {cls._Y_name: y,
                cls._X_name: x,
                cls._Z_name: z,
                cls._Y_name + '_bounds': y_bounds,
                cls._X_name + '_bounds': x_bounds,
                cls._Z_name + '_bounds': z_bounds}

    @staticmethod
    def _get_dimension_from_extent_and_resolution(extent, resolution, span,
                                                  name):
        # check compatibility between extent and resolution
        # (i.e. need to produce a whole number of grid cells)
        dim_start, dim_end = extent

        rtol_ = rtol()
        atol_ = atol()
        if np.isclose((dim_end - dim_start) % resolution, 0, rtol_, atol_):
            dim_size = (dim_end - dim_start) // resolution
        elif np.isclose((dim_end - dim_start) % resolution, resolution,
                        rtol_, atol_):
            dim_size = ((dim_end - dim_start) // resolution) + 1
        else:
            raise RuntimeError(
                "{} extent and resolution do not define a whole number "
                "of grid cells".format(name))

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
                dim_bnds = getattr(self, axis + '_bounds').array
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
                dim_bnds = getattr(self, axis + '_bounds').array
                return (np.around(dim_bnds[0, 0], decr_).tolist(),
                        np.around(dim_bnds[-1, -1], decr_).tolist())

    def _get_dimension_span(self, axis):
        if getattr(self, axis) is None:
            return None
        else:
            # infer dimension span from first coordinate and its bounds
            # (i.e. relative location of bounds around coordinate)
            dim = getattr(self, axis).array
            dim_bnds = getattr(self, axis + '_bounds').array
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
        # check constructs
        if not field.has_construct(cls._Y_name):
            raise RuntimeError("{} field missing '{}' construct".format(
                               cls.__name__, cls._Y_name))
        y = field.construct(cls._Y_name)
        if not field.has_construct(cls._X_name):
            raise RuntimeError("{} field missing '{}' construct".format(
                               cls.__name__, cls._X_name))
        x = field.construct(cls._X_name)
        z_array = None
        z_bounds_array = None
        if field.has_construct(cls._Z_name):
            if field.construct(cls._Z_name).has_bounds():
                z_array = field.construct(cls._Z_name).array
                z_units = field.construct(cls._Z_name).units
                z_bounds_array = field.construct(cls._Z_name).bounds.array
                if z_units not in cls._Z_units:
                    raise RuntimeError(
                        "{} field construct '{}' units are not in {}".format(
                            cls.__name__, cls._Z_name, cls._Z_units[0]))

        # check units
        if y.units not in cls._Y_units:
            raise RuntimeError(
                "{} field construct '{}' units are not in {}".format(
                    cls.__name__, cls._Y_name, cls._Y_units[0])
            )
        if x.units not in cls._X_units:
            raise RuntimeError(
                "{} field construct '{}' units are not in {}".format(
                    cls.__name__, cls._X_name, cls._X_units[0])
            )

        # check bounds
        if not y.has_bounds():
            raise RuntimeError("{} field construct '{}' has no bounds".format(
                                   cls.__name__, cls._Y_name))
        if not x.has_bounds():
            raise RuntimeError("{} field construct '{}' has no bounds".format(
                                   cls.__name__, cls._X_name))

        return {
            'X': x.array, 'X_bounds': x.bounds.array,
            'Y': y.array, 'Y_bounds': y.bounds.array,
            'Z': z_array, 'Z_bounds': z_bounds_array
        }

    def __str__(self):
        has_z = self._f.has_construct(self._Z_name)
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    shape {{{}}}: {}".format(", ".join(self.axes), self.shape)]
            + (["    Z, {} {}: {}".format(
                self._f.construct('Z').standard_name,
                self._f.construct('Z').data.shape,
                self._f.construct('Z').data)] if has_z else [])
            + ["    Y, {} {}: {}".format(
                self._f.construct('Y').standard_name,
                self._f.construct('Y').data.shape,
                self._f.construct('Y').data)]
            + ["    X, {} {}: {}".format(
                self._f.construct('X').standard_name,
                self._f.construct('X').data.shape,
                self._f.construct('X').data)]
            + (["    Z_bounds {}: {}".format(
                 self._f.construct('Z').bounds.data.shape,
                 self._f.construct('Z').bounds.data)] if has_z else [])
            + ["    Y_bounds {}: {}".format(
                self._f.construct('Y').bounds.data.shape,
                self._f.construct('Y').bounds.data)]
            + ["    X_bounds {}: {}".format(
                self._f.construct('X').bounds.data.shape,
                self._f.construct('X').bounds.data)]
            + [")"]
        )

    def is_space_equal_to(self, field, ignore_z=False):
        """Compare equality between the Grid and the spatial (X, Y,
        and Z) dimension coordinate in a `cf.Field`.

        The coordinate values, the bounds, and the units of the field
        are compared against those of the Grid.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against TimeDomain.

            ignore_z: `bool`, optional
                Option to ignore the dimension coordinate along the Z
                axis. If not provided, set to default False (i.e. Z is
                not ignored).

        """
        rtol_ = rtol()
        atol_ = atol()
        # check whether X/Y(/Z if not ignored) constructs are identical
        y_x = (
            self._f.construct(self._Y_name).equals(
                field.construct(re.compile(r'name={}$'.format(self._Y_name)),
                                default=None),
                rtol=rtol_, atol=atol_,
                ignore_data_type=True,
                ignore_properties=('standard_name',
                                   'long_name',
                                   'computed_standard_name'))
            and self._f.construct(self._X_name).equals(
                field.construct(re.compile(r'name={}$'.format(self._X_name)),
                                default=None),
                rtol=rtol_, atol=atol_,
                ignore_data_type=True,
                ignore_properties=('standard_name',
                                   'long_name',
                                   'computed_standard_name'))
        )
        if ignore_z:
            z = True
        else:
            if self._f.has_construct('Z'):
                z = self._f.construct('Z').equals(
                    field.construct(
                        re.compile(r'name={}$'.format(self._Z_name)),
                        default=None),
                    rtol=rtol_, atol=atol_,
                    ignore_data_type=True,
                    ignore_properties=('standard_name',
                                       'long_name',
                                       'computed_standard_name'))
            elif field.has_construct('Z'):
                z = False
            else:
                z = True

        return y_x and z

    def spans_same_region_as(self, grid, ignore_z=False):
        """Compare equality in region spanned between the Grid
        and another instance of Grid.

        For each axis, the lower bound of their first cell and the
        upper bound of their last cell are compared.

        :Parameters:

            timedomain: `Grid`
                The other Grid to be compared against Grid.

            ignore_z: `bool`, optional
                If True, the dimension coordinates along the Z axes of
                the Grid instances will not be compared. If not
                provided, set to default value False (i.e. Z is not
                ignored).

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
            raise TypeError("{} instance cannot be compared to {} "
                            "instance".format(self.__class__.__name__,
                                              grid.__class__.__name__))

    def to_config(self):
        return {
            'class': self.__class__.__name__,
            '{}_extent'.format(self._Y_name):
                self._get_dimension_extent('Y'),
            '{}_resolution'.format(self._Y_name):
                self._get_dimension_resolution('Y'),
            '{}_extent'.format(self._X_name):
                self._get_dimension_extent('X'),
            '{}_resolution'.format(self._X_name):
                self._get_dimension_resolution('X'),
            '{}_{}_location'.format(self._Y_name, self._X_name):
                self._get_yx_location(),
            '{}_extent'.format(self._Z_name):
                self._get_dimension_extent('Z'),
            '{}_resolution'.format(self._Z_name):
                self._get_dimension_resolution('Z'),
            '{}_location'.format(self._Z_name):
                self._get_z_location()
        }


class LatLonGrid(Grid):
    """LatLonGrid characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is aligned with
    the North pole.
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

    def __init__(self, latitude, longitude, latitude_bounds,
                 longitude_bounds, altitude=None, altitude_bounds=None):
        """**Initialisation**

        :Parameters:

            latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees North
                defining the temporal dimension. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values.

                *Parameter example:* ::

                    latitude=[15, 45, 75]

                *Parameter example:* ::

                    latitude=numpy.arange(-89.5, 90.5, 1)

            longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees East
                defining the temporal dimension. May be any type that
                can be cast to a `numpy.ndarray`. Must contain numerical
                values.

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
                `numpy.ndarray`. Must feature two dimensional with the
                first dimension equal to the size of *longitude* and the
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

            altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining the
                temporal dimension (with upwards as the positive
                direction). May be any type that can be cast to a
                `numpy.ndarray`. Must contain numerical values. Ignored
                if *altitude_bounds* not also provided.

                *Parameter example:* ::

                    altitude=[10]

            altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate (with upwards as the positive direction).
                May be any type that can be cast to a `numpy.ndarray`.
                Must be two dimensional with the first dimension equal
                to the size of `altitude` and the second dimension equal
                to 2. Must contain numerical values. Ignored if
                *altitude* not also provided.

                *Parameter example:* ::

                    altitude_bounds=[[0, 20]]

        **Examples**

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
        >>> sd = LatLonGrid(
        ...     latitude=numpy.arange(-89.5, 90.5, 1),
        ...     longitude=numpy.arange(-179.5, 180.5, 1),
        ...     latitude_bounds=numpy.column_stack(
        ...         (numpy.arange(-90, 90, 1),
        ...          numpy.arange(-89, 91, 1))
        ...     ),
        ...     longitude_bounds=numpy.column_stack(
        ...         (numpy.arange(-180, 180, 1),
        ...          numpy.arange(-179, 181, 1))
        ...     ),
        ...     altitude=[10],
        ...     altitude_bounds=[[0, 10]]
        ... )
        >>> print(sd)
        LatLonGrid(
            shape {Z, Y, X}: (1, 180, 360)
            Z, altitude (1,): [10] m
            Y, latitude (180,): [-89.5, ..., 89.5] degrees_north
            X, longitude (360,): [-179.5, ..., 179.5] degrees_east
            Z_bounds (1, 2): [[0, 10]] m
            Y_bounds (180, 2): [[-90, ..., 90]] degrees_north
            X_bounds (360, 2): [[-180, ..., 180]] degrees_east
        )
        """
        super(LatLonGrid, self).__init__()

        if altitude is not None and altitude_bounds is not None:
            self._set_space(altitude, altitude_bounds, name=self._Z_name,
                            units=self._Z_units[0], axis='Z')
            self._f.construct('Z').set_property('positive', 'up')

        self._set_space(latitude, latitude_bounds,
                        name=self._Y_name, units=self._Y_units[0], axis='Y')
        self._set_space(longitude, longitude_bounds,
                        name=self._X_name, units=self._X_units[0], axis='X')

        # set dummy data needed for using inner field for remapping
        self._set_dummy_data()

    @classmethod
    def from_extent_and_resolution(cls, latitude_extent, longitude_extent,
                                   latitude_resolution, longitude_resolution,
                                   latitude_longitude_location='centre',
                                   altitude_extent=None,
                                   altitude_resolution=None,
                                   altitude_location='centre'):
        """Initialise a `LatLonGrid` from the extent and the resolution
        of latitude, longitude (and optionally altitude) coordinates.

        :Parameters:

            latitude_extent: pair of `float` or `int`
                The extent of latitude coordinates in degrees North
                for the desired grid. The first element of the pair is
                the location of the start of the extent along the
                latitude coordinate, the second element of the pair is
                the location of the end of the extent along the latitude
                coordinate. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    latitude_extent=(30, 70)

            longitude_extent: pair of `float` or `int`
                The extent of longitude coordinates in degrees East
                for the desired grid. The first element of the pair is
                the location of the start of the extent along the
                longitude coordinate, the second element of the pair is
                the location of the end of the extent along the
                longitude coordinate. May be any type that can be
                unpacked (e.g. `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    longitude_extent=(0, 90)

            latitude_resolution: `float` or `int`
                The spacing between two consecutive latitude coordinates
                in degrees North for the desired grid.

                *Parameter example:* ::

                    latitude_resolution=10

            longitude_resolution: `float` or `int`
                The spacing between two consecutive longitude
                coordinates in degrees East for the desired grid.

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

            altitude_extent: pair of `float` or `int`, optional
                The extent of altitude coordinate in metres for the
                desired grid. The first element of the pair is the
                location of the start of the extent along the altitude
                coordinate, the second element of the pair is the
                location of the end of the extent along the altitude
                coordinate. May be any type that can be unpacked (e.g.
                `tuple`, `list`, `numpy.ndarray`).

                *Parameter example:* ::

                    altitude_extent=(0, 20)

            altitude_resolution: `float` or `int`, optional
                The spacing between two consecutive altitude coordinates
                in metres for the desired grid.

                *Parameter example:* ::

                    altitude_resolution=20

            altitude_location: `str` or `int`, optional
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

        **Examples**

        >>> sd = LatLonGrid.from_extent_and_resolution(
        ...     latitude_extent=(30, 70),
        ...     longitude_extent=(0, 90),
        ...     latitude_resolution=5,
        ...     longitude_resolution=10,
        ...     altitude_extent=(0, 20),
        ...     altitude_resolution=20
        ... )
        >>> print(sd)
        LatLonGrid(
            shape {Z, Y, X}: (1, 8, 9)
            Z, altitude (1,): [10.0] m
            Y, latitude (8,): [32.5, ..., 67.5] degrees_north
            X, longitude (9,): [5.0, ..., 85.0] degrees_east
            Z_bounds (1, 2): [[0.0, 20.0]] m
            Y_bounds (8, 2): [[30.0, ..., 70.0]] degrees_north
            X_bounds (9, 2): [[0.0, ..., 90.0]] degrees_east
        )
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
        inst = cls(
            **cls._get_grid_from_extent_and_resolution(
                latitude_extent, longitude_extent, latitude_resolution,
                longitude_resolution, latitude_longitude_location,
                altitude_extent, altitude_resolution, altitude_location
            )
        )

        inst._extent = {'Z': altitude_extent,
                        'Y': latitude_extent,
                        'X': longitude_extent}
        inst._resolution = {'Z': altitude_resolution,
                            'Y': latitude_resolution,
                            'X': longitude_resolution}
        inst._location = {'Z': altitude_location,
                          'YX': latitude_longitude_location}

        return inst

    @classmethod
    def from_field(cls, field):
        """Initialise a `LatLonGrid` from a cf.Field instance.

        :Parameters:

            field: cf.Field object
                The field object who will be used to initialise a
                `LatLonGrid` instance. This field must feature a
                'latitude' and a 'longitude' constructs, and these
                constructs must feature bounds. This field may
                optionally feature an 'altitude' construct alongside its
                bounds (both required otherwise ignored).

        **Examples**

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
        >>> alt = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'altitude',
        ...                     'units': 'm',
        ...                     'axis': 'Z'},
        ...         data=cf.Data([10]),
        ...         bounds=cf.Bounds(data=cf.Data([[0, 20]]))
        ...         ),
        ...     axes=f.set_construct(cf.DomainAxis(size=1))
        ... )
        >>> sd = LatLonGrid.from_field(f)
        >>> print(sd)
        LatLonGrid(
            shape {Z, Y, X}: (1, 3, 3)
            Z, altitude (1,): [10] m
            Y, latitude (3,): [15, 45, 75] degrees_north
            X, longitude (3,): [30, 90, 150] degrees_east
            Z_bounds (1, 2): [[0, 20]] m
            Y_bounds (3, 2): [[0, ..., 90]] degrees_north
            X_bounds (3, 2): [[0, ..., 180]] degrees_east
        )
        """
        extraction = cls._extract_xyz_from_field(field)

        return cls(latitude=extraction['Y'],
                   longitude=extraction['X'],
                   altitude=extraction['Z'],
                   latitude_bounds=extraction['Y_bounds'],
                   longitude_bounds=extraction['X_bounds'],
                   altitude_bounds=extraction['Z_bounds'])

    @classmethod
    def from_config(cls, cfg):
        cfg = cfg.copy()
        cfg.pop('class')
        return cls.from_extent_and_resolution(**cfg)


class RotatedLatLonGrid(Grid):
    """LatLonGrid characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is not aligned
    with the North pole.
    """
    # characteristics of the dimension coordinates
    _Z_name = 'altitude'
    _Y_name = 'grid_latitude'
    _X_name = 'grid_longitude'
    _Z_units = ['m', 'metre', 'meter', 'metres', 'meters']
    _Y_units = ['degrees', 'degree']
    _X_units = ['degrees', 'degree']

    def __init__(self, grid_latitude, grid_longitude, grid_latitude_bounds,
                 grid_longitude_bounds, earth_radius, grid_north_pole_latitude,
                 grid_north_pole_longitude, altitude=None,
                 altitude_bounds=None):
        """**Initialisation**

        :Parameters:

            grid_latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees defining
                the temporal dimension. May be any type that can be cast
                to a `numpy.ndarray`. Must contain numerical values.

                *Parameter example:* ::

                    grid_latitude=[0.88, 0.44, 0., -0.44, -0.88]

            grid_longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees defining
                the temporal dimension. May be any type that can be cast
                to a `numpy.ndarray`. Must contain numerical values.

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
                `numpy.ndarray`. Must feature two dimensional with the
                first dimension equal to the size of *grid_longitude*
                and the second dimension equal to 2. Must contain
                numerical values.

                *Parameter example:* ::

                    grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
                                           [-1.84, -1.4], [-1.4, -0.96]]

            earth_radius: `int` or `float`
                The radius of the spherical figure used to approximate
                the shape of the Earth in metres. This parameter is
                required to project the rotated grid into a true
                latitude-longitude coordinate system.

            grid_north_pole_latitude: `int` or `float`
                The true latitude of the north pole of the rotated grid
                in degrees North. This parameter is required to project
                the rotated grid into a true latitude-longitude
                coordinate system.

            grid_north_pole_longitude: `int` or `float`
                The true longitude of the north pole of the rotated grid
                in degrees East. This parameter is required to project
                the rotated grid into a true latitude-longitude
                coordinate system.

            altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining the
                temporal dimension (with upwards as the positive
                direction). May be any type that can be cast to a
                `numpy.ndarray`. Must contain numerical values. Ignored
                if *altitude_bounds* not also provided.

                *Parameter example:* ::

                    altitude=[10]

            altitude_bounds: two-dimensional array-like object, optional
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

        >>> sd = RotatedLatLonGrid(
        ...     grid_latitude=[0.88, 0.44, 0., -0.44, -0.88],
        ...     grid_longitude=[-2.5, -2.06, -1.62, -1.18],
        ...     grid_latitude_bounds=[[1.1, 0.66], [0.66, 0.22], [0.22, -0.22],
        ...                           [-0.22, -0.66], [-0.66, -1.1]],
        ...     grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
        ...                            [-1.84, -1.4], [-1.4, -0.96]],
        ...     earth_radius=6371007,
        ...     grid_north_pole_latitude=38.0,
        ...     grid_north_pole_longitude=190.0,
        ...     altitude=[10],
        ...     altitude_bounds=[[0, 20]]
        ... )
        >>> print(sd)
        RotatedLatLonGrid(
            shape {Z, Y, X}: (1, 5, 4)
            Z, altitude (1,): [10] m
            Y, grid_latitude (5,): [0.88, ..., -0.88] degrees
            X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
            Z_bounds (1, 2): [[0, 20]] m
            Y_bounds (5, 2): [[1.1, ..., -1.1]] degrees
            X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        )
        """
        super(RotatedLatLonGrid, self).__init__()

        if altitude is not None and altitude_bounds is not None:
            self._set_space(altitude, altitude_bounds, name=self._Z_name,
                            units=self._Z_units[0], axis='Z')
            self._f.construct('Z').set_property('positive', 'up')

        self._set_space(grid_latitude, grid_latitude_bounds,
                        name=self._Y_name, units=self._Y_units[0], axis='Y')
        self._set_space(grid_longitude, grid_longitude_bounds,
                        name=self._X_name, units=self._X_units[0], axis='X')

        self._set_rotation_parameters(earth_radius, grid_north_pole_latitude,
                                      grid_north_pole_longitude)

        # set dummy data needed for using inner field for remapping
        self._set_dummy_data()

    @property
    def coordinate_reference(self):
        """Return the coordinate reference of the RotatedLatLonGrid
        instance as a `cf.CoordinateReference` instance.
        """
        return self._f.coordinate_reference('rotated_latitude_longitude')

    def _set_rotation_parameters(self, earth_radius, grid_north_pole_latitude,
                                 grid_north_pole_longitude):
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'grid_north_pole_latitude':
                            grid_north_pole_latitude,
                        'grid_north_pole_longitude':
                            grid_north_pole_longitude})
        self._f.set_construct(
            cf.CoordinateReference(
                datum=cf.Datum(
                    parameters={'earth_radius': earth_radius}),
                coordinate_conversion=coord_conversion,
                coordinates=[self._Y_name, self._X_name])
        )

    def is_space_equal_to(self, field, ignore_z=False):
        """Compare equality between the RotatedLatLonGrid and the
        spatial (X, Y, and Z) dimension coordinate in a `cf.Field`.

        The coordinate values, the bounds, the units, and the coordinate
        conversion and its datum of the field are compared against those
        of the Grid.

        :Parameters:

            field: `cf.Field`
                The field that needs to be compared against TimeDomain.

            ignore_z: `bool`, optional
                Option to ignore the dimension coordinate along the Z
                axis. If not provided, set to default False (i.e. Z is
                not ignored).

        """
        # check whether X/Y(/Z if not ignored) constructs are identical
        # and if coordinate_reference match (by checking its
        # coordinate_conversion and its datum separately, because
        # coordinate_reference.equals() would also check the size of
        # the collections of coordinates, which may be rightfully
        # different if Z is ignored)
        y_x_z = super(RotatedLatLonGrid, self).is_space_equal_to(field,
                                                                 ignore_z)

        if hasattr(field, 'coordinate_reference'):
            conversion = self._check_rotation_parameters(
                field.coordinate_reference)
        if hasattr(rotated_grid, 'coordinate_reference'):
            conversion = self._check_rotation_parameters(
                rotated_grid.coordinate_reference
            )
        else:
            conversion = False

        return y_x_z and conversion

    def _check_rotation_parameters(self, coord_ref):
        if (hasattr(coord_ref, 'coordinate_conversion')
                and hasattr(coord_ref, 'datum')):
            conversion = (
                self._f.coordinate_reference(
                    'rotated_latitude_longitude').coordinate_conversion.equals(
                    coord_ref.coordinate_conversion)
                and self._f.coordinate_reference(
                    'rotated_latitude_longitude').datum.equals(coord_ref.datum)
            )
        else:
            conversion = False

        return conversion

    @classmethod
    def from_field(cls, field):
        """Initialise a `RotatedLatLonGrid` from a cf.Field instance.

        :Parameters:

            field: cf.Field object
                The field object who will be used to initialise a
                `RotatedLatLonGrid` instance. This field must feature a
                'latitude' and a 'longitude' constructs, and these
                constructs must feature bounds. In addition, the
                parameters required for the conversion of the grid to a
                true latitude-longitude reference system must be set
                (i.e. earth_radius, grid_north_pole_latitude,
                grid_north_pole_longitude). This field may optionally
                feature an 'altitude' construct alongside its bounds
                (both required otherwise ignored).

        **Examples**

        >>> import cf
        >>> f = cf.Field()
        >>> lat = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'grid_latitude',
        ...                     'units': 'degrees',
        ...                     'axis': 'Y'},
        ...         data=cf.Data([0.88, 0.44, 0., -0.44, -0.88]),
        ...         bounds=cf.Bounds(data=cf.Data([[1.1, 0.66], [0.66, 0.22],
        ...                                        [0.22, -0.22], [-0.22, -0.66],
        ...                                        [-0.66, -1.1]]))
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
        >>> alt = f.set_construct(
        ...     cf.DimensionCoordinate(
        ...         properties={'standard_name': 'altitude',
        ...                     'units': 'm',
        ...                     'axis': 'Z'},
        ...         data=cf.Data([10]),
        ...         bounds=cf.Bounds(data=cf.Data([[0, 20]]))
        ...         ),
        ...     axes=f.set_construct(cf.DomainAxis(size=1))
        ... )
        >>> crs = f.set_construct(
        ...     cf.CoordinateReference(
        ...         datum=cf.Datum(parameters={'earth_radius': 6371007.}),
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
            shape {Z, Y, X}: (1, 5, 4)
            Z, altitude (1,): [10] m
            Y, grid_latitude (5,): [0.88, ..., -0.88] degrees
            X, grid_longitude (4,): [-2.5, ..., -1.18] degrees
            Z_bounds (1, 2): [[0, 20]] m
            Y_bounds (5, 2): [[1.1, ..., -1.1]] degrees
            X_bounds (4, 2): [[-2.72, ..., -0.96]] degrees
        )
        """
        extraction_xyz = cls._extract_xyz_from_field(field)
        extraction_param = cls._extract_rotation_parameters_from_field(field)

        return cls(grid_latitude=extraction_xyz['Y'],
                   grid_longitude=extraction_xyz['X'],
                   grid_latitude_bounds=extraction_xyz['Y_bounds'],
                   grid_longitude_bounds=extraction_xyz['X_bounds'],
                   altitude=extraction_xyz['Z'],
                   altitude_bounds=extraction_xyz['Z_bounds'],
                   **extraction_param)

    @classmethod
    def _extract_rotation_parameters_from_field(cls, field):
        # check conversion parameters
        if field.has_construct('grid_mapping_name:rotated_latitude_longitude'):
            crs = field.construct(
                'grid_mapping_name:rotated_latitude_longitude')
        else:
            raise RuntimeError(
                "{} field missing coordinate conversion 'grid_mapping_name:"
                "rotated_latitude_longitude".format(cls.__name__))
        if crs.datum.has_parameter('earth_radius'):
            earth_radius = crs.datum.get_parameter('earth_radius')
        else:
            raise RuntimeError("{} field coordinate reference missing "
                               "datum 'earth_radius'".format(cls.__name__))
        if crs.coordinate_conversion.has_parameter('grid_north_pole_latitude'):
            north_pole_lat = crs.coordinate_conversion.get_parameter(
                'grid_north_pole_latitude')
        else:
            raise RuntimeError(
                "{} field coordinate conversion missing property "
                "'grid_north_pole_latitude'".format(cls.__name__))
        if crs.coordinate_conversion.has_parameter('grid_north_pole_longitude'):
            north_pole_lon = crs.coordinate_conversion.get_parameter(
                'grid_north_pole_longitude')
        else:
            raise RuntimeError(
                "{} field coordinate conversion missing property"
                "'grid_north_pole_longitude'".format(cls.__name__))

        return {
            'earth_radius': earth_radius,
            'grid_north_pole_latitude': north_pole_lat,
            'grid_north_pole_longitude': north_pole_lon
        }

    @classmethod
    def _from_extent_and_resolution(cls, grid_latitude_extent,
                                    grid_longitude_extent,
                                    grid_latitude_resolution,
                                    grid_longitude_resolution,
                                    earth_radius, grid_north_pole_latitude,
                                    grid_north_pole_longitude,
                                    grid_latitude_grid_longitude_location='centre',
                                    altitude_extent=None,
                                    altitude_resolution=None,
                                    altitude_location='centre'):
        """Initialise a `RotatedLatLonGrid` from the extent and the
        resolution of grid_latitude and grid_longitude coordinates (and
        optionally altitude coordinate).
        """
        return cls(
            **cls._get_grid_from_extent_and_resolution(
                grid_latitude_extent, grid_longitude_extent,
                grid_latitude_resolution, grid_longitude_resolution,
                grid_latitude_grid_longitude_location, altitude_extent,
                altitude_resolution, altitude_location),
            earth_radius=earth_radius,
            grid_north_pole_latitude=grid_north_pole_latitude,
            grid_north_pole_longitude=grid_north_pole_longitude
        )

    def to_config(self):
        cfg = super(RotatedLatLonGrid, self).to_config()
        cfg.update(
            self._extract_rotation_parameters_from_field(self._f)
        )
        return cfg

    @classmethod
    def from_config(cls, cfg):
        cfg = cfg.copy()
        cfg.pop('class')
        return cls._from_extent_and_resolution(**cfg)
