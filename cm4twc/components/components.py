

class Component(object):
    """
    DOCSTRING REQUIRED
    """

    _cat = None
    _ups = None
    _ins = None
    _downs = None
    _outs = None

    def __init__(self, category, driving_data_names, ancil_data_names,
                 parameter_names, upwards, inwards, downwards, outwards):

        self.category = category
        self.driving_data_names = \
            driving_data_names if driving_data_names else ()
        self.ancil_data_names = \
            ancil_data_names if ancil_data_names else ()
        self.parameter_names = \
            parameter_names if parameter_names else ()
        self.upwards = upwards
        self.inwards = inwards
        self.downwards = downwards
        self.outwards = outwards

    def __call__(self, td, sd, db, **kwargs):

        # check that all inward fluxes of info are provided
        if not all([i in kwargs for i in self.inwards]):
            raise RuntimeError(
                "One or more input variables are missing in {} component '{}': "
                "{} are all required.".format(
                    self.category, self.__class__.__name__, self.inwards)
            )

        # collect required data from database
        for data in self.driving_data_names + self.ancil_data_names:
            kwargs[data] = db[data].array

        # do something with time frame? with space domain?
        # (use them to check database has data for time and space required?)

        # run simulation for the component
        outputs = self.run(**kwargs)

        # check that all outward fluxes of info are returned
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

    @classmethod
    def get_upwards(cls): return cls._ups

    @classmethod
    def get_inwards(cls): return cls._ins

    @classmethod
    def get_downwards(cls): return cls._downs

    @classmethod
    def get_outwards(cls): return cls._outs

    def run(self, *args, **kwargs):

        raise NotImplementedError(
            "The {} class '{}' does not feature a 'run' "
            "method.".format(self.category, self.__class__.__name__))


class SurfaceLayerComponent(Component):

    _cat = 'surfacelayer'
    _ups = ()
    _ins = ()
    _downs = ('subsurface', 'openwater')
    _outs = ('throughfall', 'snowmelt', 'transpiration',
             'evaporation_soil_surface', 'evaporation_ponded_water',
             'evaporation_openwater')

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(SurfaceLayerComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ups, self._ins, self._downs, self._outs)

    def run(self, *args, **kwargs):

        super(SurfaceLayerComponent, self).run(self, *args, **kwargs)


class SubSurfaceComponent(Component):

    _cat = 'subsurface'
    _ups = ('surfacelayer',)
    _ins = ('evaporation_soil_surface', 'evaporation_ponded_water',
            'transpiration', 'throughfall', 'snowmelt')
    _downs = ('openwater',)
    _outs = ('surface_runoff', 'subsurface_runoff')

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(SubSurfaceComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ups, self._ins, self._downs, self._outs)

    def run(self, *args, **kwargs):

        super(SubSurfaceComponent, self).run(self, *args, **kwargs)


class OpenWaterComponent(Component):

    _cat = 'openwater'
    _ups = ('surfacelayer', 'subsurface')
    _ins = ('evaporation_openwater', 'surface_runoff', 'subsurface_runoff')
    _downs = ()
    _outs = ('discharge',)

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(OpenWaterComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ups, self._ins, self._downs, self._outs)

    def run(self, *args, **kwargs):

        super(OpenWaterComponent, self).run(self, *args, **kwargs)


class DataComponent(Component):

    _cat = 'data'
    _ups = ()
    _ins = ()
    _downs = ()
    _outs = ()

    def __init__(self, substituting, database, required):

        super(DataComponent, self).__init__(
            self._cat, None, None,
            None, self._ups, self._ins, self._downs, self._outs)

        self.database = database

        # check that 'required' data is present in 'database'
        for data in required:
            if data not in self.database:
                raise KeyError(
                    "There is no data '{}' available in the database "
                    "used in substitution for the {} component.".format(
                        data, substituting))

    def run(self, *args, **kwargs):

        return {v.standard_name: v.array for v in self.database}


class NoneComponent(Component):

    _cat = 'none'
    _ups = ()
    _ins = ()
    _downs = ()
    _outs = ()

    def __init__(self):

        super(NoneComponent, self).__init__(
            self._cat, None, None,
            None, self._ups, self._ins, self._downs, self._outs)

    def run(self, *args, **kwargs): return {}
