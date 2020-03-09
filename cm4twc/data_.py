from collections.abc import MutableMapping
import cf


class DataSet(MutableMapping):
    """
    Class behaving like a dictionary but restricting the values of
    its items of type Variable.
    """

    def __init__(self, *args, **kwargs):

        self.variables = dict()
        self.update(dict(*args, **kwargs))  # use the 'free' update to set keys

    def __getitem__(self, key): return self.variables[key]

    def __setitem__(self, key, value):

        if isinstance(value, Variable):
            self.variables[key] = value
        else:
            raise TypeError("A {} can only contain instances of "
                            "{}.".format(self.__class__.__name__,
                                         Variable.__name__))

    def __delitem__(self, key): del self.variables[key]

    def __iter__(self): return iter(self.variables)

    def __len__(self): return len(self.variables)

    def update_with_cf_nc_file(self, pathname, name_mapping=None,
                               squeeze=True):

        return self.update(
            self._get_dict_variables_from_cf_nc_file(pathname, squeeze,
                                                     name_mapping)
        )

    @classmethod
    def from_cf_nc_file(cls, pathname, name_mapping=None, squeeze=True):

        return cls(
            cls._get_dict_variables_from_cf_nc_file(pathname, squeeze,
                                                    name_mapping)
        )

    @staticmethod
    def _get_dict_variables_from_cf_nc_file(pathname, squeeze, name_mapping):
        return {
            name_mapping[field.standard_name]
            if name_mapping and (field.standard_name in name_mapping)
            else field.standard_name: Variable(source=field, copy=False,
                                               squeeze=squeeze)
            for field in cf.read(pathname)
        }


class Variable(cf.Field):

    def __init__(self, source, copy=False, squeeze=True):

        super(Variable, self).__init__(source=source, copy=copy)

        if squeeze:
            self.data.squeeze(inplace=True)

    @classmethod
    def from_cf_nc_file(cls, variablename, pathname, squeeze=True):

        try:
            field = cf.read(pathname).select_by_property(
                standard_name=variablename)
        except FileNotFoundError:
            raise FileNotFoundError("Error during initialisation of {} from "
                                    "CF-netCDF file: there is no such file or "
                                    "directory: {}.".format(cls.__name__,
                                                            pathname))

        if field:
            if len(field) == 1:
                return cls(source=field[0], squeeze=squeeze)
            else:
                raise UserWarning(
                    "AmbiguityWarning - There is more than one variable whose "
                    "standard_name are '{}' in CF-netCDF file located at "
                    "{}.".format(variablename, pathname))
        else:
            raise ValueError(
                "There is no variable whose standard_name is '{}' in the "
                "CF-netCDF file located at {}".format(variablename, pathname))
