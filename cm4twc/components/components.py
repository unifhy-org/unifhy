

class _Component(object):
    """
    DOCSTRING REQUIRED
    """

    _cat = None
    _ins = None
    _outs = None

    def __init__(self, category, driving_data_names, ancil_data_names,
                 parameter_names, inwards, outwards):

        self.category = category
        self.driving_data_names = \
            driving_data_names if driving_data_names else ()
        self.ancil_data_names = \
            ancil_data_names if ancil_data_names else ()
        self.parameter_names = \
            parameter_names if parameter_names else ()
        self.inwards = inwards
        self.outwards = outwards

    def __call__(self, td, sd, db, **kwargs):

        # collect required data from database
        for data in self.driving_data_names + self.ancil_data_names:
            kwargs[data] = db[data].array

        # run simulation for the component
        return self.run(**kwargs)

    @classmethod
    def get_inwards(cls):
        return cls._ins

    @classmethod
    def get_outwards(cls):
        return cls._outs

    def run(self, **kwargs):

        raise NotImplementedError(
            "The {} class '{}' does not feature a 'run' "
            "method.".format(self.category, self.__class__.__name__))


class SurfaceLayerComponent(_Component):

    _cat = 'surfacelayer'
    _ins = ()
    _outs = ('throughfall', 'snowmelt', 'transpiration',
             'evaporation_soil_surface', 'evaporation_ponded_water',
             'evaporation_openwater')

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(SurfaceLayerComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ins, self._outs)

    def run(self, **kwargs):

        super(SurfaceLayerComponent, self).run(**kwargs)


class SubSurfaceComponent(_Component):

    _cat = 'subsurface'
    _ins = ('evaporation_soil_surface', 'evaporation_ponded_water',
            'transpiration', 'throughfall', 'snowmelt')
    _outs = ('surface_runoff', 'subsurface_runoff')

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(SubSurfaceComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ins, self._outs)

    def run(self, **kwargs):

        super(SubSurfaceComponent, self).run(**kwargs)


class OpenWaterComponent(_Component):

    _cat = 'openwater'
    _ins = ('evaporation_openwater', 'surface_runoff', 'subsurface_runoff')
    _outs = ('discharge',)

    def __init__(self, driving_data_names=None, ancil_data_names=None,
                 parameter_names=None):

        super(OpenWaterComponent, self).__init__(
            self._cat, driving_data_names, ancil_data_names,
            parameter_names, self._ins, self._outs)

    def run(self, **kwargs):

        super(OpenWaterComponent, self).run(**kwargs)


class DataComponent(_Component):

    _cat = 'data'
    _ins = ()
    _outs = ()

    def __init__(self, substituting_class):

        super(DataComponent, self).__init__(
            self._cat, substituting_class.get_outwards(), None, None,
            self._ins, self._outs)

    def run(self, **kwargs):

        return {n: kwargs[n] for n in self.driving_data_names}


class NullComponent(_Component):

    _cat = 'null'
    _ins = ()
    _outs = ()

    def __init__(self, substituting_class):

        super(NullComponent, self).__init__(
            self._cat, None, None, None,
            self._ins, substituting_class.get_outwards())

    def run(self, **kwargs):

        return {n: 0.0 for n in self.outwards}
