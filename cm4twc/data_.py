from collections.abc import MutableMapping
import cf


class DataBase(MutableMapping):
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
            raise TypeError("The database can only contain "
                            "instances of Variable.")

    def __delitem__(self, key): del self.variables[key]

    def __iter__(self): return iter(self.variables)

    def __len__(self): return len(self.variables)

    def append(self, *args, **kwargs): self.update(*args, **kwargs)

    def update_with_cf_nc_file(self, pathname, mapping=None):

        return self.update(
            self._get_dict_variables_from_cf_nc_file(pathname, mapping)
        )

    @classmethod
    def from_cf_nc_file(cls, pathname, mapping=None):

        return cls(
            cls._get_dict_variables_from_cf_nc_file(pathname, mapping)
        )

    @staticmethod
    def _get_dict_variables_from_cf_nc_file(pathname, mapping=None):
        return {
            mapping[field.standard_name]
            if mapping and (field.standard_name in mapping)
            else field.standard_name: Variable(source=field, copy=False)
            for field in cf.read(pathname)
        }


class Variable(cf.Field):

    def __init__(self, source, copy=False):

        super(Variable, self).__init__(source=source, copy=copy)

    @classmethod
    def from_cf_nc_file(cls, variablename, pathname):

        try:
            field = cf.read(pathname)(variablename)
        except FileNotFoundError:
            raise FileNotFoundError("Error during initialisation of {} from "
                                    "CF-netCDF file: there is no such file or "
                                    "directory: {}.".format(cls.__name__,
                                                            pathname))

        if field:
            return cls(source=field)
        else:
            raise ValueError("There is no variable named '{}' in the CF-netCDF"
                             " file located at {}".format(variablename, pathname))
