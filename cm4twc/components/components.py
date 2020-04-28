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
                 parameters_info, states_info, constants_info, solver_history,
                 inwards, outwards):

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
        self.constants_info = \
            constants_info if constants_info else {}
        self.solver_history = solver_history

        # interface attributes
        self.inwards = inwards
        self.outwards = outwards

        # states attribute
        self.states = {}

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
                        spaceshape=spaceshape, **self.states, **kwargs)

    def initialise_states(self, **kwargs):
        states = self.initialise(**kwargs)
        for s in self.states_info.keys():
            if s in states:
                self.states[s] = State(*states[s])
            else:
                raise KeyError(
                    "The state '{}' of the {} component was "
                    "not initialised.".format(s, self._kind)
                )

    def increment_states(self):
        for s in self.states.keys():
            # determine first index in the State
            # (function of solver's history)
            first_index = -len(self.states[s]) + 1
            # prepare the left-hand side of the name re-binding
            lhs = [t for t in self.states[s]]
            # prepare the right-hand side of the name re-binding
            rhs = [t for t in self.states[s][first_index + 1:]] + \
                [self.states[s][first_index]]
            # carry out the permutation (i.e. name re-binding)
            # to avoid new object creations
            lhs[:] = rhs[:]
            # apply new name bindings to the State
            z = self.states[s][:]
            self.states[s][:] = lhs

            # re-initialise current timestep of State to zero
            self.states[s][0][:] = 0.0

    def finalise_states(self):
        self.finalise(**self.states)

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

    def __init__(self, solver_history, driving_data_info=None,
                 ancil_data_info=None, parameters_info=None, states_info=None,
                 constants_info=None):

        super(SurfaceLayerComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, constants_info, solver_history,
            self._ins, self._outs)


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
        'runoff': 'kg m-2 s-1'
    }

    def __init__(self, solver_history, driving_data_info=None,
                 ancil_data_info=None, parameters_info=None, states_info=None,
                 constants_info=None):

        super(SubSurfaceComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, constants_info, solver_history,
            self._ins, self._outs)


class OpenWaterComponent(_Component, metaclass=abc.ABCMeta):

    _kind = 'openwater'
    _ins = {
        'evaporation_openwater': 'kg m-2 s-1',
        'runoff': 'kg m-2 s-1'
    }
    _outs = {
        'discharge': 'kg m-2 s-1'
    }

    def __init__(self, solver_history, driving_data_info=None,
                 ancil_data_info=None, parameters_info=None, states_info=None,
                 constants_info=None):

        super(OpenWaterComponent, self).__init__(
            self._kind, driving_data_info, ancil_data_info,
            parameters_info, states_info, constants_info, solver_history,
            self._ins, self._outs)


class DataComponent(_Component):

    _kind = 'data'
    _ins = {}
    _outs = {}

    def __init__(self, substituting_class):

        super(DataComponent, self).__init__(
            substituting_class.get_class_kind(),
            substituting_class.get_class_outwards(),
            None, None, None, None, 0, self._ins, self._outs)

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
            substituting_class.get_class_kind(), None, None, None, None, None,
            0, self._ins, substituting_class.get_class_outwards())

    def initialise(self, **kwargs):

        return {}

    def run(self, spaceshape, **kwargs):

        null_array = np.zeros(spaceshape, np.float32)

        return {n: null_array for n in self.outwards}

    def finalise(self, **kwargs):

        pass


class State(object):
    """
    The State class behaves like a list which stores the values of a
    given component state for several consecutive timesteps (in
    chronological order, i.e. the oldest timestep is the first item,
    the most recent is the last item).

    Although, unlike a list, its indexing is shifted so that the last
    item has index 0, and all previous items are accessible via a
    negative integer (e.g. -1 for the 2nd-to-last, -2 for the
    3rd-to-last, etc.). The first item (i.e. the oldest timestep stored)
    is accessible at the index equals to minus the length of the list
    plus one. Since the list remains in chronological order, it means
    that for a given timestep t, index -1 corresponds to timestep t-1,
    index -2 to timestep t-2, etc. Current timestep t is accessible at
    index 0.
    """
    def __init__(self, *args):
        self.history = list(args)

    def __getitem__(self, index):
        index = self.shift_index(index)
        return self.history[index]

    def __setitem__(self, index, item):
        index = self.shift_index(index)
        self.history[index] = item

    def shift_index(self, index):
        if isinstance(index, int):
            index = index + len(self) - 1
        elif isinstance(index, slice):
            start, stop = index.start, index.stop
            if start is not None:
                start = start + len(self) - 1
            if stop is not None:
                stop = stop + len(self) - 1
            index = slice(start, stop, index.step)
        return index

    def __delitem__(self, index):
        index = self.shift_index(index)
        del self.history[index]

    def __len__(self):
        return len(self.history)

    def __iter__(self):
        return iter(self.history)

    def __repr__(self):
        return "%r" % self.history
