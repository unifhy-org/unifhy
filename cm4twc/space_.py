import numpy as np
import cf


class SpaceDomain(object):
    """SpaceDomain characterises a spatial dimension that is needed by a
    `Component`. Any supported spatial configuration for a `Component`
    is a subclass of SpaceDomain.

    TODO: create a XYGrid subclass for Cartesian coordinates
    TODO: deal with sub-grid heterogeneity schemes (e.g. tiling, HRUs)
    """

    def __init__(self):
        self.f = cf.Field()

    @property
    def shape(self):
        return None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.is_space_equal_to(other.f)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_space_equal_to(self, *args):
        raise TypeError("An instance of {} cannot be used to "
                        "characterise a spatial configuration directly, "
                        "please use a subclass of it instead.")

    def to_field(self):
        """Return the inner cf.Field used to characterise the
        SpaceDomain.
        """
        return self.f


class Grid(SpaceDomain):
    """Grid is a `SpaceDomain` subclass which represents space as
    a regular grid. Any supported regular grid for a `Component` is a
    subclass of Grid.
    """

    def __init__(self):
        super(Grid, self).__init__()

    @property
    def shape(self):
        has_altitude = self.f.has_construct('altitude')
        return (
            (self.f.construct('Z').shape if has_altitude else ())
            + self.f.construct('Y').shape
            + self.f.construct('X').shape
        )

    def _set_space(self, dimension, dimension_bounds, name, units, axis):
        if not isinstance(dimension, np.ndarray):
            dimension = np.asarray(dimension)
        dimension = np.squeeze(dimension)
        if not isinstance(dimension_bounds, np.ndarray):
            dimension_bounds = np.asarray(dimension_bounds)
        dimension_bounds = np.squeeze(dimension_bounds)
        if dimension.ndim > 1:
            raise RuntimeError("Error when initialising a {}: the "
                               "{} array given is not convertible to a "
                               "1D-array.".format(
                                    name, self.__class__.__name__))
        if dimension_bounds.shape != (*dimension.shape, 2):
            raise RuntimeError("Error when initialising a {}: the {} bounds "
                               "array given is not compatible in size with "
                               "the {} array given.".format(
                                    self.__class__.__name__, name, name))
        axis_lat = self.f.set_construct(cf.DomainAxis(dimension.size))
        self.f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    'standard_name': name,
                    'units': units,
                    'axis': axis
                },
                data=cf.Data(dimension),
                bounds=cf.Bounds(data=cf.Data(dimension_bounds))),
            axes=axis_lat
        )

    def __repr__(self):
        has_altitude = self.f.has_construct('altitude')
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    shape {}: {}".format("{Z, Y, X}" if has_altitude
                                         else "{Y, X}", self.shape)]
            + (["    Z, %s %s: %s" %
               (self.f.construct('Z').standard_name,
                self.f.construct('Z').data.shape,
                self.f.construct('Z').data)] if has_altitude else [])
            + ["    Y, %s %s: %s" %
               (self.f.construct('Y').standard_name,
                self.f.construct('Y').data.shape,
                self.f.construct('Y').data)]
            + ["    X, %s %s: %s" %
               (self.f.construct('X').standard_name,
                self.f.construct('X').data.shape,
                self.f.construct('X').data)]
            + (["    Z_bounds %s: %s" %
                (self.f.construct('Z').bounds.data.shape,
                 self.f.construct('Z').bounds.data)] if has_altitude else [])
            + ["    Y_bounds %s: %s" %
               (self.f.construct('Y').bounds.data.shape,
                self.f.construct('Y').bounds.data)]
            + ["    X_bounds %s: %s" %
               (self.f.construct('X').bounds.data.shape,
                self.f.construct('X').bounds.data)]
            + [")"]
        )


class LatLonGrid(Grid):
    """LatLonGrid characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is aligned with
    the North pole.
    """

    def __init__(self, latitude, longitude, latitude_bounds,
                 longitude_bounds, altitude=None, altitude_bounds=None):
        """**Initialisation**

        :Parameters:

            latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees North
                defining the temporal dimension. May be any type that
                can be cast to a `numpy.array`. Must contain numerical
                values.

                *Parameter example:*
                    ``latitude=[15, 45, 75]``
                *Parameter example:*
                    ``latitude=(-60, 0, 60)``
                *Parameter example:*
                    ``latitude=numpy.arange(-89.5, 90.5, 1)``

            longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees East
                defining the temporal dimension. May be any type that
                can be cast to a `numpy.array`. Must contain numerical
                values.

                *Parameter example:*
                    ``longitude=[30, 90, 150]``
                *Parameter example:*
                    ``longitude=(-150, -90, -30, 30, 90, 150)``
                *Parameter example:*
                    ``longitude=numpy.arange(-179.5, 180.5, 1)``

            latitude_bounds: two-dimensional array-like object
                The array of latitude coordinate bounds in degrees North
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must be two dimensional with the first
                dimension equal to the size of `latitude` and the second
                dimension equal to 2. Must contain numerical values.

                *Parameter example:*
                    ``latitude_bounds=[[0, 30], [30, 60], [60, 90]]``
                *Parameter example:*
                    ``latitude_bounds=((-90, -30), (-30, 30), (30, 90))``
                *Parameter example:*
                    ``latitude_bounds=numpy.column_stack(
                        (numpy.arange(-90, 90, 1),
                         numpy.arange(-89, 91, 1))
                    )``

            longitude_bounds: two-dimensional array-like object
                The array of longitude coordinate bounds in degrees
                East defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must feature two dimensional with the
                first dimension equal to the size of `longitude` and the
                second dimension equal to 2. Must contain numerical
                values.

                *Parameter example:*
                    ``longitude_bounds=[[0, 60], [60, 120], [120, 180]]``
                *Parameter example:*
                    ``longitude_bounds=((-180, -120), (-120, -60), (-60, 0)
                                        (0, 60), (60, 120), (120, 180))``
                *Parameter example:*
                    ``longitude_bounds=numpy.column_stack(
                        (numpy.arange(-180, 180, 1),
                         numpy.arange(-179, 181, 1))
                    )``

            altitude: one-dimensional array-like object, optional
                The array of altitude coordinates in metres defining the
                temporal dimension. May be any type that can be cast to
                a `numpy.array`. Must contain numerical values. Ignored
                if `altitude_bounds` not also provided.

                *Parameter example:*
                    ``altitude=[10]``

            altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must be two dimensional with the first
                dimension equal to the size of `altitude` and the second
                dimension equal to 2. Must contain numerical values.
                Ignored if `altitude` not also provided.

                *Parameter example:*
                    ``altitude=[[0, 20]]``

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
            self._set_space(altitude, altitude_bounds,
                            name='altitude', units='m', axis='Z')
            self.f.construct('Z').set_property('positive', 'up')

        self._set_space(latitude, latitude_bounds,
                        name='latitude', units='degrees_north', axis='Y')
        self._set_space(longitude, longitude_bounds,
                        name='longitude', units='degrees_east', axis='X')

    def is_space_equal_to(self, field, ignore_altitude=False):
        # check if latitude match, check if longitude
        lat_lon = (
            self.f.construct('latitude').equals(
                field.construct('latitude', default=None),
                ignore_data_type=True)
            and self.f.construct('longitude').equals(
                field.construct('longitude', default=None),
                ignore_data_type=True)
        )
        # check whether altitude constructs are identical
        if ignore_altitude:
            alt = True
        else:
            if self.f.has_construct('altitude'):
                alt = self.f.construct('altitude').equals(
                    field.construct('altitude', default=None),
                    ignore_data_type=True)
            else:
                alt = True

        return lat_lon and alt


class RotatedLatLonGrid(Grid):
    """LatLonGrid characterises the spatial dimension for a `Component`
    as a regular grid on a spherical domain whose coordinates are
    latitudes and longitudes, and whose rotation axis is not aligned
    with the North pole.
    """

    def __init__(self, grid_latitude, grid_longitude, grid_latitude_bounds,
                 grid_longitude_bounds, earth_radius, grid_north_pole_latitude,
                 grid_north_pole_longitude, altitude=None,
                 altitude_bounds=None):
        """**Initialisation**

        :Parameters:

            grid_latitude: one-dimensional array-like object
                The array of latitude coordinates in degrees defining
                the temporal dimension. May be any type that can be cast
                to a `numpy.array`. Must contain numerical values.

                *Parameter example:*
                    ``grid_latitude=[0.88, 0.44, 0., -0.44, -0.88]``

            grid_longitude: one-dimensional array-like object
                The array of longitude coordinates in degrees defining
                the temporal dimension. May be any type that can be cast
                to a `numpy.array`. Must contain numerical values.

                *Parameter example:*
                    ``grid_longitude=[-2.5, -2.06, -1.62, -1.18]``

            grid_latitude_bounds: two-dimensional array-like object
                The array of latitude coordinate bounds in degrees
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must be two dimensional with the first
                dimension equal to the size of `grid_latitude` and the
                second dimension equal to 2. Must contain numerical
                values.

                *Parameter example:*
                    ``grid_latitude_bounds=[[1.1, 0.66], [0.66, 0.22],
                                            [0.22, -0.22], [-0.22, -0.66],
                                            [-0.66, -1.1]]``

            grid_longitude_bounds: two-dimensional array-like object
                The array of longitude coordinate bounds in degrees
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must feature two dimensional with the
                first dimension equal to the size of `grid_longitude`
                and the second dimension equal to 2. Must contain
                numerical values.

                *Parameter example:*
                    ``grid_longitude_bounds=[[-2.72, -2.28], [-2.28, -1.84],
                                             [-1.84, -1.4], [-1.4, -0.96]]```

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
                temporal dimension. May be any type that can be cast to
                a `numpy.array`. Must contain numerical values. Ignored
                if `altitude_bounds` not also provided.

                *Parameter example:*
                    ``altitude=[10]``

            altitude_bounds: two-dimensional array-like object, optional
                The array of altitude coordinate bounds in metres
                defining the extent of the grid cell around the
                coordinate. May be any type that can be cast to a
                `numpy.array`. Must be two dimensional with the first
                dimension equal to the size of `altitude` and the second
                dimension equal to 2. Must contain numerical values.
                Ignored if `altitude` not also provided.

                *Parameter example:*
                    ``altitude=[[0, 20]]``

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
            self._set_space(altitude, altitude_bounds,
                            name='altitude', units='m', axis='Z')
            self.f.construct('Z').set_property('positive', 'up')

        self._set_space(grid_latitude, grid_latitude_bounds,
                        name='grid_latitude', units='degrees', axis='Y')
        self._set_space(grid_longitude, grid_longitude_bounds,
                        name='grid_longitude', units='degrees', axis='X')

        self._set_rotation_parameters(earth_radius, grid_north_pole_latitude,
                                      grid_north_pole_longitude)

    def _set_rotation_parameters(self, earth_radius, grid_north_pole_latitude,
                                 grid_north_pole_longitude):
        coord_conversion = cf.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'grid_north_pole_latitude':
                            grid_north_pole_latitude,
                        'grid_north_pole_longitude':
                            grid_north_pole_longitude})
        self.f.set_construct(
            cf.CoordinateReference(
                datum=cf.Datum(
                    parameters={'earth_radius': earth_radius}),
                coordinate_conversion=coord_conversion,
                coordinates=['grid_latitude', 'grid_longitude'])
        )

    def is_space_equal_to(self, field, ignore_altitude=False):
        # check whether latitude and longitude constructs are identical
        # by checking if grid_latitude match, if grid_longitude match
        # and if coordinate_reference match (by checking its
        # coordinate_conversion and its datum separately, because
        # coordinate_reference.equals() would also check the size of the
        # collections of coordinates)
        lat_lon = (
            self.f.construct('grid_latitude').equals(
                field.construct('grid_latitude', default=None),
                ignore_data_type=True)
            and self.f.construct('grid_longitude').equals(
                field.construct('grid_longitude', default=None),
                ignore_data_type=True)
            and self.f.coordinate_reference(
                'rotated_latitude_longitude').coordinate_conversion.equals(
                field.coordinate_reference(
                    'rotated_latitude_longitude',
                    default=None).coordinate_conversion)
            and self.f.coordinate_reference(
                'rotated_latitude_longitude').datum.equals(
                field.coordinate_reference(
                    'rotated_latitude_longitude',
                    default=None).datum)
        )
        # check whether altitude constructs are identical
        if ignore_altitude:
            alt = True
        else:
            if self.f.has_construct('altitude'):
                alt = self.f.construct('altitude').equals(
                    field.construct('altitude', default=None),
                    ignore_data_type=True)
            else:
                alt = True

        return lat_lon and alt
