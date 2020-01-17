from collections.abc import MutableMapping


class DataBase(MutableMapping):
    """
    Class behaving like a dictionary but restricting the values of
    its items to (a) specific type(s).
    """

    def __init__(self, *args, **kwargs):

        self.variables = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key): return self.variables[key]

    def __setitem__(self, key, value):

        if isinstance(value, Variable):
            self.variables[key] = value
        else:
            raise TypeError("The database can only contain Variable instances.")

    def __delitem__(self, key): del self.variables[key]

    def __iter__(self): return iter(self.variables)

    def __len__(self): return len(self.variables)

    def append(self, *args, **kwargs): self.update(*args, **kwargs)


class Variable(object):

    def __init__(self, name, array=None, *args, **kwargs):

        self.standard_name = name
        self.array = array
