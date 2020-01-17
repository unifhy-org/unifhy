from ..data_ import DataBase


class _Component(object):
    """
    DOCSTRING REQUIRED
    """

    def __init__(self, category, driving_data_names, ancil_data_names,
                 inwards, outwards):

        self.category = category
        self.driving_data_names = driving_data_names if driving_data_names else ()
        self.ancil_data_names = ancil_data_names if ancil_data_names else ()
        self.inwards = inwards
        self.outwards = outwards

    def __call__(self, tf, sd, db, *args, **kwargs):

        if not all([i in kwargs for i in self.inwards]):
            raise RuntimeError(
                "One or more input variables are missing in {} component '{}': "
                "{} are all required.".format(
                    self.category, self.__class__.__name__, self.inwards)
            )

        # collect required data from database
        for data in self.driving_data_names + self.ancil_data_names:
            try:
                kwargs[data] = db[data]
            except KeyError:
                raise KeyError(
                    "There is no data '{}' available in the database "
                    "for {} component '{}'.".format(
                        data, self.category, self.__class__.__name__))

        # do something with time frame? with space domain?
        # (use them to check database has data for time and space required?)

        outputs = self.run(**kwargs)

        if isinstance(outputs, dict):
            if all([o in outputs for o in self.outwards]):
                return outputs
            else:
                raise RuntimeError(
                    "One or more output variables are not returned by the {} "
                    "component '{}': {} are all required.".format(
                        self.category, self.__class__.__name__, self.outwards)
                )
        else:
            raise TypeError(
                "The 'run' function of the {} component '{}' does not "
                "return a dictionary as required.".format(
                    self.category, self.__class__.__name__)
            )

    def run(self, *args, **kwargs):
        raise NotImplementedError(
            "The {} class '{}' does not feature a 'run' "
            "method.".format(self.category, self.__class__.__name__))


class SurfaceComponent(_Component):

    _cat = 'surface'
    _ins = ()
    _outs = ('throughfall', 'snowmelt', 'transpiration',
             'evaporation_soil_surface', 'evaporation_ponded_water',
             'evaporation_openwater')

    def __init__(self, driving_data_names=None, ancil_data_names=None):

        super(SurfaceComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            self._ins, self._outs)

    def run(self, *args, **kwargs):

        super(SurfaceComponent, self).run(self, *args, **kwargs)


class SubSurfaceComponent(_Component):

    _cat = 'subsurface'
    _ins = ('evaporation_soil_surface', 'evaporation_ponded_water',
            'transpiration', 'throughfall', 'snowmelt')
    _outs = ('surface_runoff', 'subsurface_runoff')

    def __init__(self, driving_data_names=None, ancil_data_names=None):

        super(SubSurfaceComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            self._ins, self._outs)

    def run(self, *args, **kwargs):

        super(SubSurfaceComponent, self).run(self, *args, **kwargs)


class OpenWaterComponent(_Component):

    _cat = 'openwater'
    _ins = ('evaporation_openwater', 'surface_runoff', 'subsurface_runoff')
    _outs = ('discharge',)

    def __init__(self, driving_data_names=None, ancil_data_names=None):

        super(OpenWaterComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            self._ins, self._outs)

    def run(self, *args, **kwargs):

        super(OpenWaterComponent, self).run(self, *args, **kwargs)


class DataComponent(_Component):

    _cat = 'data'
    _ins = ()
    _outs = ()

    def __init__(self, database, required):
        super(DataComponent, self).__init__(
            self._cat, None, None,
            self._ins, self._outs)

        if isinstance(database, DataBase):
            self.database = database
        else:
            raise TypeError("A DataComponent can only be instantiated by "
                            "giving it an instance of Variable.")

    def run(self, *args, **kwargs):

        return {v.standard_name: v.array for v in self.database}


class NoneComponent(_Component):

    _cat = 'none'
    _ins = ()
    _outs = ()

    def __init__(self):

        super(NoneComponent, self).__init__(
            self._cat, None, None,
            self._ins, self._outs)

    def run(self, *args, **kwargs): return {}

