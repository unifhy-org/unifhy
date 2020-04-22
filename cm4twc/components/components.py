import abc
import numpy as np


class _Component(metaclass=abc.ABCMeta):
    """
    DOCSTRING REQUIRED
    """

    _kind = None
    _ins = None
    _outs = None

    def __init__(self, category, driving_data_info, ancil_data_info,
                 parameters_info, states_info, inwards, outwards):

        # category attribute
        self.category = category

        # definition attributes
        self.driving_data_info = \
            driving_data_info if driving_data_info else {}
        self.ancil_data_info = \
            ancil_data_info if ancil_data_info else {}
        self.parameters_info = \
            parameters_info if parameters_info else {}
        self.states_info = \
            states_info if states_info else {}

        # interface attributes
        self.inwards = inwards
        self.outwards = outwards

        # time attributes
        self.timedomain = None

        # space attributes
        self.spacedomain = None

    def __call__(self, timeindex, datetime, timestepinseconds, spaceshape,
                 dataset,
                 **kwargs):

        # collect required ancillary data from dataset
        for data in self.ancil_data_info:
            kwargs[data] = dataset[data].array[...]

        # collect required driving data from dataset
        for data in self.driving_data_info:
            kwargs[data] = dataset[data].array[timeindex, ...]

        # run simulation for the component
        return self.run(datetime=datetime, timestepinseconds=timestepinseconds,
                        spaceshape=spaceshape, **kwargs)

    @classmethod
    def get_class_kind(cls):
        return cls._kind

    @classmethod
    def get_class_inwards(cls):
        return cls._ins

    @classmethod
    def get_class_outwards(cls):
        return cls._outs

    @abc.abstractmethod
    def initialise(self, **kwargs):

        raise NotImplementedError(
            "The {} class '{}' does not feature an 'initialise' "
            "method.".format(self.category, self.__class__.__name__))

    @abc.abstractmethod
    def run(self, **kwargs):

        raise NotImplementedError(
            "The {} class '{}' does not feature a 'run' "
            "method.".format(self.category, self.__class__.__name__))

    @abc.abstractmethod
    def finalise(self, **kwargs):

        raise NotImplementedError(
            "The {} class '{}' does not feature a 'finalise' "
            "method.".format(self.category, self.__class__.__name__))


class SurfaceLayerComponent(_Component, metaclass=abc.ABCMeta):

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
                 parameters_info=None, states_info=None):

        super(SurfaceLayerComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, self._ins, self._outs)


class SubSurfaceComponent(_Component, metaclass=abc.ABCMeta):

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
                 parameters_info=None, states_info=None):

        super(SubSurfaceComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, self._ins, self._outs)


class OpenWaterComponent(_Component, metaclass=abc.ABCMeta):

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
                 parameters_info=None, states_info=None):

        super(OpenWaterComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, self._ins, self._outs)


class DataComponent(_Component):

    _kind = 'data'
    _ins = {}
    _outs = {}

    def __init__(self, substituting_class):

        super(DataComponent, self).__init__(
            substituting_class.get_class_kind(),
            substituting_class.get_class_outwards(),
            None, None, None, self._ins, self._outs)

    def initialise(self, **kwargs):

        return {}

    def run(self, **kwargs):

        return {n: kwargs[n] for n in self.driving_data_info}

    def finalise(self, **kwargs):

        pass


class NullComponent(_Component):

    _kind = 'null'
    _ins = {}
    _outs = {}

    def __init__(self, substituting_class):

        super(NullComponent, self).__init__(
            substituting_class.get_class_kind(), None, None, None, None,
            self._ins, substituting_class.get_class_outwards())

    def initialise(self, **kwargs):

        return {}

    def run(self, spaceshape, **kwargs):

        null_array = np.zeros(spaceshape, np.float32)

        return {n: null_array for n in self.outwards}

    def finalise(self, **kwargs):

        pass
