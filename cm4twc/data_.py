from collections.abc import MutableMapping
import cf


class DataSet(MutableMapping):
    """DataSet is a dictionary-like data structure which maps variable
    names to `Field` objects. Namely, it allows to use custom variable
    names instead of the standard_name attribute of `Field` to identify
    them.
    """

    def __init__(self, variables=None):
        """**Initialisation**

        :Parameters:

            variables: `dict`, optional
                A dictionary with the variable names as keys referencing
                `Field` objects.

                *Parameter example:*
                    ``dictionary={'rainfall': cf.Field()}``

        **Examples**

        >>> import cf
        >>> ds = cm4twc.DataSet(variables={'rainfall': cf.Field()})
        >>> print(ds)
        DataSet{
            rainfall: <CF Field: >
        }
        """
        self._variables = {}
        if variables is not None:
            self.update(dict(**variables))

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
            ["\t%s: %r" % (v, self._variables[v])
             for v in sorted(self._variables.keys())] +
            ["}"]
        ) if self._variables else "DataSet{ }"

    def update_with_file(self, files, name_mapping=None,
                         squeeze=True, select=None, **kwargs):
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

            squeeze: `bool`, optional
                If True, dimension coordinates of the variables of size
                1 are removed. The default value is True.

        **Examples**

        >>> ds = cm4twc.DataSet()
        >>> print(ds)
        DataSet{ }
        >>> ds.update_with_file(
        ...     files='tests/dummy_data/dummy_driving_data.nc',
        ...     select='snowfall_flux'
        ...)
        >>> print(ds)
        DataSet{
            snowfall_flux: <CF Field: snowfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        >>> ds.update_with_file(
        ...     files='tests/dummy_data/dummy_driving_data.nc',
        ...     select=('rainfall_flux',),
        ...     squeeze=False
        ... )
        >>> print(ds)
        DataSet{
            rainfall_flux: <CF Field: rainfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        """
        return self.update(
            self._get_dict_variables_from_file(files, name_mapping,
                                               squeeze, select, **kwargs)
        )

    @classmethod
    def from_file(cls, files, name_mapping=None,
                  squeeze=True, select=None, **kwargs):
        """Initialise a `DataSet` from the variables contained in a
        netCDF file.

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

            squeeze: `bool`, optional
                If True, dimension coordinates of the variables of size
                1 are removed. The default value is True.

        **Examples**

        >>> ds = cm4twc.DataSet.from_file(
        ...     files='tests/dummy_data/dummy_driving_data.nc'
        ... )
        >>> print(ds)
        DataSet{
            air_temperature: <CF Field: air_temperature(time(6), grid_latitude(10), grid_longitude(9)) K>
            rainfall_flux: <CF Field: rainfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            soil_temperature: <CF Field: soil_temperature(time(6), grid_latitude(10), grid_longitude(9)) K>
        }
        >>> ds = cm4twc.DataSet.from_file(
        ...     files='tests/dummy_data/dummy_driving_data.nc',
        ...     select=['rainfall_flux', 'snowfall_flux'],
        ...     name_mapping={'rainfall_flux': 'rainfall'}
        ...)
        >>> print(ds)
        DataSet{
            rainfall: <CF Field: rainfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
            snowfall_flux: <CF Field: snowfall_flux(time(6), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
        }
        """
        return cls(
            cls._get_dict_variables_from_file(files, name_mapping,
                                              squeeze, select, **kwargs)
        )

    @staticmethod
    def _get_dict_variables_from_file(pathname, name_mapping,
                                      squeeze, select, **kwargs):
        return {
            name_mapping[field.standard_name]
            if name_mapping and (field.standard_name in name_mapping)
            else field.standard_name: cf.Field(source=field, copy=False)
            for field in cf.read(pathname, squeeze=squeeze,
                                 select=select, **kwargs)
        }
