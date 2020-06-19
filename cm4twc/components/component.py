import abc
import numpy as np
import cf
from cfunits import Units

from ._state import State
from ..time import TimeDomain
from .. import space
from ..space import SpaceDomain, Grid
from ..data import DataSet


class Component(metaclass=abc.ABCMeta):

    _kind = None
    _ins = None
    _outs = None

    # definition attributes (set to default)
    driving_data_info = {}
    ancillary_data_info = {}
    parameters_info = {}
    constants_info = {}
    states_info = {}
    solver_history = 0

    def __init__(self, timedomain, spacedomain, dataset=None,
                 parameters=None, constants=None):
        """**Initialisation**

        :Parameters:

            timedomain: `TimeDomain` object
                The temporal dimension of the `Component`.

            spacedomain: `SpaceDomain` object
                The spatial dimension of the `Component`.

            dataset: `DataSet` object, optional
                The dataset containing the substitute data substituting
                the `Component`\'s simulated time series. The data is
                dataset must be compatible in time with *timedomain* and
                compatible in space with *spacedomain*.

            parameters: `dict`, optional
                The parameter values for the `Component`. Must be
                provided in the units expected by the `Component`.

            constants: `dict`, optional
                The parameter values for the `Component`. Must be
                provided in the required units.

        """
        # category attribute
        self.category = self._kind

        # interface attributes
        self.inwards_info = self._ins
        self.outwards_info = self._outs

        # time attributes
        self._check_timedomain(timedomain)
        self.timedomain = timedomain
        self.timestepinseconds = self.timedomain.timedelta.total_seconds()

        # space attributes
        self._check_spacedomain(spacedomain)
        self.spacedomain = spacedomain
        self.spaceshape = self.spacedomain.shape

        # data attributes
        dataset = DataSet() if dataset is None else dataset
        self._check_dataset(dataset)
        self._check_dataset_space(dataset, spacedomain)
        # # dataset to keep whole data period pristine
        self.dataset = dataset
        # # dataset to subset whole data for given period
        self._dataset = DataSet()

        # parameters attribute
        parameters = {} if parameters is None else parameters
        self._check_parameters(parameters)
        self.parameters = parameters

        # constants attribute
        constants = {} if constants is None else constants
        self.constants = constants  # no check because they are optional

        # states attribute
        self.states = {}

    def _check_timedomain(self, timedomain):
        """The purpose of this method is to check that the timedomain is
        of the right type.
        """
        if not isinstance(timedomain, TimeDomain):
            raise TypeError("not an instance of {} for {}".format(
                TimeDomain.__name__, self.category))

    def _check_spacedomain(self, spacedomain):
        """The purpose of this method is to check that the spacedomain is
        of the right type.
        """
        if not isinstance(spacedomain, SpaceDomain):
            raise TypeError("not an instance of {} for {}".format(
                SpaceDomain.__name__, self.category))

        if not isinstance(spacedomain, Grid):
            raise NotImplementedError(
                "only {} currently supported by the framework "
                "for spacedomain".format(Grid.__name__))

    def _check_dataset(self, dataset):
        # checks for both driving and ancillary data

        # check that the dataset is an instance of DataSet
        if not isinstance(dataset, DataSet):

            raise TypeError(
                "The dataset object given for the {} component '{}' must "
                "be an instance of {}.".format(
                    self.category, self.__class__.__name__,
                    DataSet.__name__))

        # check data units compatibility with component
        for data_name, data_unit in {**self.driving_data_info,
                                     **self.ancillary_data_info}.items():
            # check that all driving data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "There is no data '{}' available in the {} "
                    "for the {} component '{}'.".format(
                        data_name, DataSet.__name__, self.category,
                        self.__class__.__name__))
            # check that driving data units are compliant with component units
            if hasattr(dataset[data_name], 'units'):
                if not Units(data_unit).equals(
                        Units(dataset[data_name].units)):
                    raise ValueError(
                        "The units of the variable '{}' in the {} {} "
                        "are not equal to the units required by the {} "
                        "component '{}': {} are required.".format(
                            data_name, self.category, DataSet.__name__,
                            self.category, self.__class__.__name__,
                            data_unit))
            else:
                raise AttributeError("The variable '{}' in the {} for "
                                     "the {} component is missing a 'units' "
                                     "attribute.".format(
                                         data_name, DataSet.__name__,
                                         self.category))

    def _check_dataset_space(self, dataset, spacedomain):
        # check space compatibility for both driving and ancillary data
        for data_name, data_unit in {**self.driving_data_info,
                                     **self.ancillary_data_info}.items():
            # check that the data and component space domains are compatible
            if not spacedomain.is_space_equal_to(dataset[data_name]):
                raise ValueError(
                    "The space domain of the data '{}' is not compatible with "
                    "the space domain of the {} component '{}'.".format(
                        data_name, self.category, self.__class__.__name__))

    def check_dataset_time(self, timedomain):
        # check time compatibility for driving data
        for data_name in self.driving_data_info:
            # subspace in time
            self._dataset[data_name] = self.dataset[data_name].subspace(
                T=cf.wi(
                    *timedomain.time.datetime_array[[0, -2]]
                )
            )

            # check that the data and component time domains are compatible
            # using _truncation=-1 to remove requirement for last datetime
            # of TimeDomain to be available which is not required
            if not timedomain.is_time_equal_to(self._dataset[data_name],
                                               _trailing_truncation_idx=-1):
                raise ValueError(
                    "The time domain of the data '{}' is not compatible with "
                    "the time domain of the {} component '{}'.".format(
                        data_name, self.category, self.__class__.__name__))
        # copy reference for ancillary data
        for data_name in self.ancillary_data_info:
            self._dataset[data_name] = self.dataset[data_name]

    def _check_parameters(self, parameters):
        """The purpose of this method is to check that parameter values
        are given for the corresponding component.
        """
        # check that all parameters are provided
        if not all([i in parameters for i in self.parameters_info]):
            raise RuntimeError(
                "One or more parameters are missing in {} component '{}': "
                "{} are all required.".format(
                    self.category, self.__class__.__name__,
                    self.parameters_info))

    @classmethod
    def from_config(cls, cfg):
        spacedomain = getattr(space, cfg['spacedomain']['class'])
        return cls(
            timedomain=TimeDomain.from_config(cfg['timedomain']),
            spacedomain=spacedomain.from_config(cfg['spacedomain']),
            dataset=DataSet.from_config(cfg.get('dataset')),
            parameters=cfg.get('parameters'),
            constants=cfg.get('constants')
        )

    def to_config(self):
        cfg = {
            'module': self.__module__,
            'class': self.__class__.__name__,
            'timedomain': self.timedomain.to_config(),
            'spacedomain': self.spacedomain.to_config(),
            'dataset': self.dataset.to_config(),
            'parameters': self.parameters if self.parameters else None,
            'constants': self.constants if self.constants else None
        }
        return cfg

    def get_spin_up_timedomain(self, start, end):
        timedomain = TimeDomain.from_start_end_step(
            start, end, self.timedomain.timedelta,
            self.timedomain.units,
            self.timedomain.calendar
        )
        return timedomain

    def __str__(self):
        info = [
            "\n".join(
                (["    {}:".format(t.replace('_', ' '))] +
                 ["        {} [{}]".format(
                     n, getattr(self, t + '_info')[n])
                  for n in getattr(self, t + '_info')]
                 if getattr(self, t + '_info') else [])
            )
            for t in ['inwards', 'outwards', 'driving_data', 'ancillary_data',
                      'parameters', 'constants', 'states']
            if getattr(self, t + '_info')
        ]
        return "\n".join(
            ["{}(".format(self.__class__.__name__)] +
            ["    category: {}".format(self.category)] +
            info +
            ["    solver history: {}".format(self.solver_history)] +
            [")"]
        )

    def __call__(self, timeindex, datetime, **kwargs):
        # collect required ancillary data from dataset
        for data in self.ancillary_data_info:
            kwargs[data] = self._dataset[data].array[...]

        # collect required driving data from dataset
        for data in self.driving_data_info:
            kwargs[data] = self._dataset[data].array[timeindex, ...]

        # run simulation for the component
        return self.run(datetime=datetime, **self.parameters, **self.constants,
                        **self.states, **kwargs)

    def initialise_states(self):
        states = self.initialise(**self.constants)
        for s in self.states_info:
            if s in states:
                self.states[s] = State(*states[s])
            else:
                raise KeyError(
                    "The state '{}' of the {} component was "
                    "not initialised.".format(s, self._kind)
                )

    def increment_states(self):
        for s in self.states:
            # determine first index in the State
            # (function of solver's history)
            first_index = -len(self.states[s]) + 1
            # prepare the left-hand side of the name re-binding
            lhs = [t for t in self.states[s]]
            # prepare the right-hand side of the name re-binding
            rhs = [t for t in self.states[s][first_index+1:]] + \
                [self.states[s][first_index]]
            # carry out the permutation (i.e. name re-binding)
            # to avoid new object creations
            lhs[:] = rhs[:]
            # apply new name bindings to the State
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


class SurfaceLayerComponent(Component, metaclass=abc.ABCMeta):
    """The SurfaceLayerComponent is simulating the hydrological
    processes in the surface layer compartment of the hydrological
    cycle.
    """
    _kind = 'surfacelayer'
    _ins = {
        'soil_water_stress': '1'
    }
    _outs = {
        'throughfall': 'kg m-2 s-1',
        'snowmelt': 'kg m-2 s-1',
        'transpiration': 'kg m-2 s-1',
        'evaporation_soil_surface': 'kg m-2 s-1',
        'evaporation_ponded_water': 'kg m-2 s-1',
        'evaporation_openwater': 'kg m-2 s-1'
    }


class SubSurfaceComponent(Component, metaclass=abc.ABCMeta):
    """The SubSurfaceComponent is simulating the hydrological processes
    in the subsurface compartment of the hydrological cycle.
    """
    _kind = 'subsurface'
    _ins = {
        'evaporation_soil_surface': 'kg m-2 s-1',
        'evaporation_ponded_water': 'kg m-2 s-1',
        'transpiration': 'kg m-2 s-1',
        'throughfall': 'kg m-2 s-1',
        'snowmelt': 'kg m-2 s-1'
    }
    _outs = {
        'runoff': 'kg m-2 s-1',
        'soil_water_stress': '1'
    }


class OpenWaterComponent(Component, metaclass=abc.ABCMeta):
    """The OpenWaterComponent is simulating the hydrological processes
    in the open water compartment of the hydrological cycle.
    """
    _kind = 'openwater'
    _ins = {
        'evaporation_openwater': 'kg m-2 s-1',
        'runoff': 'kg m-2 s-1'
    }
    _outs = {
        'discharge': 'kg m-2 s-1'
    }


class DataComponent(Component):
    """The DataComponent is a `Component` substituting simulations with
    data.

    Its intended use is to replace a compartment of the hydrological
    cycle with measurements or with previous simulation runs.
    """
    _kind = 'data'
    _ins = {}
    _outs = {}

    def __init__(self, timedomain, spacedomain, dataset, substituting_class):
        """**Initialisation**

        :Parameters:

            timedomain: `TimeDomain` object
                The temporal dimension of the `Component`.

            spacedomain: `SpaceDomain` object
                The spatial dimension of the `Component`.

            dataset: `DataSet` object
                The dataset containing the substitute data substituting
                the `Component`\'s simulated time series. The data is
                dataset must be compatible in time with *timedomain* and
                compatible in space with *spacedomain*.

            substituting_class: `Component` object
                The subclass of `Component` that the DataComponent is
                substituting its simulated time series with the ones in
                *dataset*.

        """
        super(DataComponent, self).__init__(timedomain, spacedomain, dataset)

        # override category to the one of substituting component
        self.category = substituting_class.get_class_kind()

    def __str__(self):
        return "\n".join(
            ["{}(".format(self.__class__.__name__)] +
            ["    category: %s" % self.category] +
            ["    outwards:"] +
            ["        %s [%s]" % (n, self.driving_data_info[n])
             for n in self.driving_data_info] +
            [")"]
        )

    def initialise(self, **kwargs):
        return {}

    def run(self, **kwargs):
        return {n: kwargs[n] for n in self.driving_data_info}

    def finalise(self, **kwargs):
        pass


class NullComponent(Component):
    """The NullComponent mimics a `Component` and returns time series of
    zeros.

    Its intended use is to ignore a compartment of the hydrological
    cycle.
    """
    _kind = 'null'
    _ins = {}
    _outs = {}

    def __init__(self, timedomain, spacedomain, substituting_class):
        """**Initialisation**

        :Parameters:

            timedomain: `TimeDomain` object
                The temporal dimension of the `Component`.

            spacedomain: `SpaceDomain` object
                The spatial dimension of the `Component`.

            substituting_class: `Component` object
                The subclass of `Component` that the NullComponent is
                substituting its simulated time series with time series
                of zeros.

        """
        super(NullComponent, self).__init__(timedomain, spacedomain)

        # override category with the one of component being substituted
        self.category = substituting_class.get_class_kind()

        # override outwards with the ones of component being substituted
        self.outwards_info = substituting_class.get_class_outwards()

    def __str__(self):
        return "\n".join(
            ["{}(".format(self.__class__.__name__)] +
            ["    category: %s" % self.category] +
            ["    outwards:"] +
            ["        %s [%s]" % (n, self.outwards_info[n])
             for n in self.outwards_info] +
            [")"]
        )

    def initialise(self, **kwargs):
        return {}

    def run(self, **kwargs):
        null_array = np.zeros(self.spaceshape, np.float32)
        return {n: null_array for n in self.outwards_info}

    def finalise(self, **kwargs):
        pass
