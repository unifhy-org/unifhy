from collections.abc import MutableMapping
import cf


class DataSet(MutableMapping):
    """
    Class behaving like a dictionary but restricting the values of
    its items of type Variable.
    """

    def __init__(self, *args, **kwargs):

        self.variables = {}
        self.update(dict(*args, **kwargs))  # use the 'free' update to set keys

    def __getitem__(self, key): return self.variables[key]

    def __setitem__(self, key, value):

        if isinstance(value, cf.Field):
            self.variables[key] = value
        else:
            raise TypeError("A {} can only contain instances of "
                            "{}.".format(self.__class__.__name__,
                                         cf.Field.__name__))

    def __delitem__(self, key): del self.variables[key]

    def __iter__(self): return iter(self.variables)

    def __len__(self): return len(self.variables)

    def update_with_file(self, pathname, name_mapping=None,
                         squeeze=True, select=None, **kwargs):

        return self.update(
            self._get_dict_variables_from_file(pathname, name_mapping,
                                               squeeze, select, **kwargs)
        )

    @classmethod
    def from_file(cls, pathname, name_mapping=None,
                  squeeze=True, select=None, **kwargs):

        return cls(
            cls._get_dict_variables_from_file(pathname, name_mapping,
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
