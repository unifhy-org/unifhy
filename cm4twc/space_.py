import numpy as np
import cf


class SpaceDomain(cf.Field):
    """
    Class to handle geospatial considerations.
    """

    def __init__(self):

        super(SpaceDomain, self).__init__()


class Grid(SpaceDomain):

    def __init__(self, latitude_deg, longitude_deg,
                 latitude_bounds_deg, longitude_bounds_deg,
                 altitude_m=None,
                 rotated=False, earth_radius_m=None,
                 grid_north_pole_latitude_deg=None,
                 grid_north_pole_longitude_deg=None):

        super(Grid, self).__init__()

        # initialise a list to store the shape of the domain
        shape_ = []

        # set the altitude construct
        if altitude_m:
            if not isinstance(altitude_m, np.ndarray):
                altitude_m = np.asarray(altitude_m)
            if altitude_m.ndim != 1:
                raise RuntimeError("Error when initialising a {}: the "
                                   "altitude array given is not "
                                   "unidimensional".format(
                                        self.__class__.__name__))

            axis_alt = self.set_construct(cf.DomainAxis(len(altitude_m)))
            self.set_construct(
                cf.DimensionCoordinate(
                    properties={
                        'standard_name': 'altitude',
                        'units': 'm',
                        'axis': 'Z'
                    },
                    data=cf.Data(altitude_m)),
                axes=axis_alt)
            shape_.append(len(altitude_m))

        # set the latitude construct
        if not isinstance(latitude_deg, np.ndarray):
            latitude_deg = np.asarray(latitude_deg)
        if not isinstance(latitude_bounds_deg, np.ndarray):
            latitude_bounds_deg = np.asarray(latitude_bounds_deg)
        if latitude_deg.ndim != 1:
            raise RuntimeError("Error when initialising a {}: the "
                               "latitude array given is not "
                               "unidimensional".format(
                                    self.__class__.__name__))
        if latitude_bounds_deg.shape != (latitude_deg.size, 2):
            raise RuntimeError("Error when initialising a {}: the "
                               "latitude bounds array given is not "
                               "compatible in size with the latitude "
                               "array given.".format(
                                    self.__class__.__name__))
        axis_lat = self.set_construct(cf.DomainAxis(len(latitude_deg)))
        self.set_construct(
            cf.DimensionCoordinate(
                properties={
                    'standard_name':
                        'grid_latitude' if rotated else 'latitude',
                    'units': 'degrees' if rotated else 'degrees_north',
                    'axis': 'Y'
                },
                data=cf.Data(latitude_deg),
                bounds=cf.Bounds(data=cf.Data(latitude_bounds_deg))),
            axes=axis_lat
        )
        shape_.append(len(latitude_deg))

        # set the longitude construct
        if not isinstance(longitude_deg, np.ndarray):
            longitude_deg = np.asarray(longitude_deg)
        if not isinstance(longitude_bounds_deg, np.ndarray):
            longitude_bounds_deg = np.asarray(longitude_bounds_deg)
        if longitude_deg.ndim != 1:
            raise RuntimeError("Error when initialising a {}: the "
                               "longitude array given is not "
                               "unidimensional".format(
                                    self.__class__.__name__))
        if longitude_bounds_deg.shape != (longitude_deg.size, 2):
            raise RuntimeError("Error when initialising a {}: the "
                               "longitude bounds array given is not "
                               "compatible in size with the latitude "
                               "array given.".format(
                                    self.__class__.__name__))
        axis_lon = self.set_construct(cf.DomainAxis(len(longitude_deg)))
        self.set_construct(
            cf.DimensionCoordinate(
                properties={
                    'standard_name':
                        'grid_longitude' if rotated else 'longitude',
                    'units': 'degrees' if rotated else 'degrees_east',
                    'axis': 'X'
                },
                data=cf.Data(longitude_deg),
                bounds=cf.Bounds(data=cf.Data(longitude_bounds_deg))),
            axes=axis_lon
        )
        shape_.append(len(longitude_deg))

        # set the coordinate reference construct if relevant
        if rotated:
            if not earth_radius_m or not grid_north_pole_latitude_deg \
                    or not grid_north_pole_longitude_deg:
                raise RuntimeError("Error when initialising a {}: a rotated "
                                   "grid is indicated, but one or more of the "
                                   "required parameters is not provided: "
                                   "earth_radius_m, grid_north_pole_latitude, "
                                   "grid_north_pole_longitude".format(
                                        self.__class__.__name__))
            coord_conv = cf.CoordinateConversion(
                parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                            'grid_north_pole_latitude':
                                grid_north_pole_latitude_deg,
                            'grid_north_pole_longitude':
                                grid_north_pole_longitude_deg})
            self.set_construct(
                cf.CoordinateReference(
                    datum=cf.Datum(
                        parameters={'earth_radius': earth_radius_m}),
                    coordinate_conversion=coord_conv)
            )

        # set a few attributes to avoid more sophisticated tests later on
        self.has_altitude = True if altitude_m else False
        self.is_rotated = rotated

        # store the shape of the domain as an attribute
        self.shape_ = tuple(shape_)

    def __eq__(self, other):

        if isinstance(other, Grid):
            return self.is_space_equal_to(other)
        else:
            raise TypeError("The {} instance cannot be compared to "
                            "a {} instance.".format(self.__class__.__name__,
                                                    other.__class__.__name__))

    def __ne__(self, other):

        return not self.__eq__(other)

    def is_space_equal_to(self, variable, ignore_altitude=False):

        # check whether latitude and longitude constructs are identical
        if self.is_rotated:
            # check if grid_latitude match, check if grid_longitude match and
            # check if coordinate_reference match (by checking its
            # coordinate_conversion and its datum separately, because
            # coordinate_reference.equals() would also check the size of the
            # collections of coordinates)
            lat_lon = \
                self.construct('grid_latitude').equals(
                    variable.construct('grid_latitude', default=None),
                    ignore_data_type=True) \
                and self.construct('grid_longitude').equals(
                    variable.construct('grid_longitude', default=None),
                    ignore_data_type=True) \
                and self.coordinate_reference(
                    'rotated_latitude_longitude').coordinate_conversion.equals(
                    variable.coordinate_reference(
                        'rotated_latitude_longitude',
                        default=None).coordinate_conversion) \
                and self.coordinate_reference(
                    'rotated_latitude_longitude').datum.equals(
                    variable.coordinate_reference(
                        'rotated_latitude_longitude',
                        default=None).datum)
        else:
            # check if latitude match, check if longitude
            lat_lon = \
                self.construct('latitude').equals(
                    variable.construct('latitude', default=None),
                    ignore_data_type=True) \
                and self.construct('longitude').equals(
                    variable.construct('longitude', default=None),
                    ignore_data_type=True)

        # check whether altitude constructs are identical
        if ignore_altitude:
            alt = True
        else:
            if self.has_altitude:
                alt = self.construct('altitude').equals(
                    variable.construct('altitude', default=None),
                    ignore_data_type=True)
            else:
                alt = True

        return lat_lon and alt
