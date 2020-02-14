

class _Component(object):
    """
    DOCSTRING REQUIRED
    """

    _kind = None
    _ins = None
    _outs = None

    def __init__(self, category, driving_data_info, ancil_data_info,
                 parameter_info, inwards, outwards):

        self.category = category
        self.driving_data_info = \
            driving_data_info if driving_data_info else {}
        self.ancil_data_info = \
            ancil_data_info if ancil_data_info else {}
        self.parameter_info = \
            parameter_info if parameter_info else {}
        self.inwards = inwards
        self.outwards = outwards

    def __call__(self, td, sd, db, **kwargs):

        # collect required driving data from database
        for data in self.driving_data_info:
            kwargs[data] = db[data].array
        # collect required ancillary data from database
        for data in self.ancil_data_info:
            kwargs[data] = db[data].array

        # run simulation for the component
        return self.run(**kwargs)

    @classmethod
    def get_kind(cls):
        return cls._kind

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

    _kind = 'surfacelayer'
    _ins = {}
    _outs = {
        'throughfall': 'kg m-2 s-1',
        'snowmelt': 'kg m-2 s-1',
        'transpiration': 'kg m-2 s-1',
        'evaporation_soil_surface': 'kg m-2 s-1',
        'evaporation_ponded_water': 'kg m-2 s-1',
        'evaporation_openwater': 'kg m-2 s-1',
    }

    def __init__(self, driving_data_info=None, ancil_data_info=None,
                 parameter_info=None):

        super(SurfaceLayerComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameter_info, self._ins, self._outs)

    def run(self, **kwargs):

        super(SurfaceLayerComponent, self).run(**kwargs)


class SubSurfaceComponent(_Component):

    _kind = 'subsurface'
    _ins = {
        'evaporation_soil_surface': 'kg m-2 s-1',
        'evaporation_ponded_water': 'kg m-2 s-1',
        'transpiration': 'kg m-2 s-1',
        'throughfall': 'kg m-2 s-1',
        'snowmelt': 'kg m-2 s-1'
    }
    _outs = {
        'surface_runoff': 'kg m-2 s-1',
        'subsurface_runoff': 'kg m-2 s-1'
    }

    def __init__(self, driving_data_info=None, ancil_data_info=None,
                 parameter_info=None):

        super(SubSurfaceComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameter_info, self._ins, self._outs)

    def run(self, **kwargs):

        super(SubSurfaceComponent, self).run(**kwargs)


class OpenWaterComponent(_Component):

    _kind = 'openwater'
    _ins = {
        'evaporation_openwater': 'kg m-2 s-1',
        'surface_runoff': 'kg m-2 s-1',
        'subsurface_runoff': 'kg m-2 s-1'
    }
    _outs = {
        'discharge': 'kg m-2 s-1'
    }

    def __init__(self, driving_data_info=None, ancil_data_info=None,
                 parameter_info=None):

        super(OpenWaterComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameter_info, self._ins, self._outs)

    def run(self, **kwargs):

        super(OpenWaterComponent, self).run(**kwargs)


class DataComponent(_Component):

    _kind = 'data'
    _ins = {}
    _outs = {}

    def __init__(self, substituting_class):

        super(DataComponent, self).__init__(
            substituting_class.get_kind(), substituting_class.get_outwards(),
            None, None, self._ins, self._outs)

    def run(self, **kwargs):

        return {n: kwargs[n] for n in self.driving_data_info}


class NullComponent(_Component):

    _kind = 'null'
    _ins = {}
    _outs = {}

    def __init__(self, substituting_class):

        super(NullComponent, self).__init__(
            substituting_class.get_kind(), None, None, None,
            self._ins, substituting_class.get_outwards())

    def run(self, **kwargs):

        return {n: 0.0 for n in self.outwards}
