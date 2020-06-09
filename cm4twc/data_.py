from collections.abc import MutableMapping
import cf


class DataSet(MutableMapping):
    """DataSet is a dictionary-like data structure which maps variable
    names to `Field` objects. Namely, it allows to use custom variable
    names instead of the standard_name attribute of `Field` to identify
    them.
    """

    def __init__(self, files=None, name_mapping=None, select=None):
        """**Initialisation**

        :Parameters:

            files: (sequence of) `str`, optional
                A string or sequence of strings providing the netCDF
                file names or directory names containing netCDF files
                from which to read the variables.

                *Parameter example:*
                    ``files='tests/dummy_data/dummy_driving_data.nc'``
                *Parameter example:*
                    ``files=['tests/dummy_data/dummy_driving_data.nc',
                             'tests/dummy_data/dummy_ancillary_data.nc'`

            select: (sequence of) `str`, optional
                A string or sequence of strings providing the identities
                of the variables to read in the netCDF file. By default,
                all variables in the netCDF file are read.

                *Parameter example:*
                    ``select=['rainfall_flux', 'snowfall_flux']``

            name_mapping: `dict`, optional
                A dictionary with the Field identities as keys and the
                desired new name variables as values. If a Field is read
                from the netCDF file, and its identity is not a key in
                *name_mapping* (if provided), its standard_name
                attribute is used instead.

        **Examples**

        >>> ds = DataSet()
        >>> print(ds)
        DataSet{ }
        >>> ds = DataSet(
        ...     files='dummy_data/dummy_driving_data.nc'
        ... )
        >>> print(ds)
        DataSet{
            air_temperature: <CF Field: air_temperature(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
            rainfall_flux: <CF Field: rainfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            soil_temperature: <CF Field: soil_temperature(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
        }
        >>> ds = DataSet(
        ...     files='dummy_data/dummy_driving_data.nc',
        ...     select=['rainfall_flux', 'snowfall_flux'],
        ...     name_mapping={'rainfall_flux': 'rainfall'}
        ... )
        >>> print(ds)
        DataSet{
            rainfall: <CF Field: rainfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        """
        self._variables = {}
        if files is not None:
            self.update(
                self._get_dict_variables_from_file(files, name_mapping, select)
            )

    def __getitem__(self, key):
        return self._variables[key]

    def __setitem__(self, key, value):
        if isinstance(value, cf.Field):
            self._variables[key] = value
        else:
            raise TypeError("A {} can only contain instances of "
                            "{}.".format(self.__class__.__name__,
                                         cf.Field.__name__))

    def __delitem__(self, key):
        del self._variables[key]

    def __iter__(self):
        return iter(self._variables)

    def __len__(self):
        return len(self._variables)

    def __repr__(self):
        return "\n".join(
            ["DataSet{"] +
            ["    %s: %r" % (v, self._variables[v])
             for v in sorted(self._variables.keys())] +
            ["}"]
        ) if self._variables else "DataSet{ }"

    def load_from_file(self, files, name_mapping=None, select=None):
        """Append to the `DataSet` the variables that are contained in
        the file(s) provided.

        :Parameters:

            files: (sequence of) `str`
                A string or sequence of strings providing the netCDF
                file names or directory names containing netCDF files
                from which to read the variables.

                *Parameter example:*
                    ``files='tests/dummy_data/dummy_driving_data.nc'``
                *Parameter example:*
                    ``files=['tests/dummy_data/dummy_driving_data.nc',
                             'tests/dummy_data/dummy_ancillary_data.nc'`

            select: (sequence of) `str`, optional
                A string or sequence of strings providing the identities
                of the variables to read in the netCDF file. By default,
                all variables in the netCDF file are read.

                *Parameter example:*
                    ``select=['rainfall_flux', 'snowfall_flux']``

            name_mapping: `dict`, optional
                A dictionary with the Field identities as keys and the
                desired new name variables as values. If a Field is read
                from the netCDF file, and its identity is not a key in
                *name_mapping* (if provided), its standard_name
                attribute is used instead.

        **Examples**

        >>> ds = DataSet()
        >>> print(ds)
        DataSet{ }
        >>> ds.load_from_file(
        ...     files='dummy_data/dummy_driving_data.nc',
        ...     select='snowfall_flux'
        ... )
        >>> print(ds)
        DataSet{
            snowfall_flux: <CF Field: snowfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        >>> ds.load_from_file(
        ...     files='dummy_data/dummy_driving_data.nc',
        ...     select=('rainfall_flux',)
        ... )
        >>> print(ds)
        DataSet{
            rainfall_flux: <CF Field: rainfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        """
        self.update(
            self._get_dict_variables_from_file(files, name_mapping, select)
        )

    @staticmethod
    def _get_dict_variables_from_file(files, name_mapping, select):
        return {
            name_mapping[field.standard_name]
            if name_mapping and (field.standard_name in name_mapping)
            else field.standard_name: cf.Field(source=field, copy=False)
            for field in cf.read(files, select=select)
        }

    @classmethod
    def from_config(cls, cfg):
        inst = cls()
        if cfg:
            for var in cfg:
                inst.load_from_file(
                    files=cfg[var]['files'],
                    select=cfg[var]['select'],
                    name_mapping={cfg[var]['select']: var}
                )
        return inst

    def to_config(self):
        return {
            var: {
                'files': self[var].data.get_filenames(),
                'select': self[var].standard_name
            } for var in self
        }
