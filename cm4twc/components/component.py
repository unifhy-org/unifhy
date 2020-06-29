import abc
import numpy as np
from datetime import datetime
from os import sep
import cf
from cfunits import Units

from ._state import State
from ._io import create_dump_file, update_dump_file, load_dump_file
from ..time import TimeDomain
from .. import space
from ..space import SpaceDomain, Grid
from ..data import DataSet


class MetaComponent(abc.ABCMeta):
    """MetaComponent is a metaclass for `Component` which provides a
    custom method `__str__` to display its class attributes.
    """
    def __str__(self):
        info = [
            "\n".join(
                (["    {}:".format(t.replace('_', ' '))] +
                 ["        {} [{}]".format(
                     n, getattr(self, t + '_info')[n])
                     for n in getattr(self, t + '_info')]
                 if getattr(self, t + '_info') else [])
            )
            for t in ['_inwards', '_outwards', 'driving_data',
                      'ancillary_data', 'parameters', 'constants', 'states']
            if getattr(self, t + '_info')
        ]
        return "\n".join(
            ["{}(".format(self.__name__)]
            + ["    category: {}".format(getattr(self, '_category'))]
            + info
            + ["    solver history: {}".format(getattr(self, 'solver_history'))]
            + [")"]
        )


class Component(metaclass=MetaComponent):

    _category = None
    _inwards_info = None
    _outwards_info = None

    # definition attributes (set to default)
    driving_data_info = {}
    ancillary_data_info = {}
    parameters_info = {}
    constants_info = {}
    states_info = {}
    solver_history = 0

    def __init__(self, output_directory, timedomain, spacedomain,
                 dataset=None, parameters=None, constants=None):
        """**Initialisation**

        :Parameters:

            output_directory: `str`
                The path to the directory where to save the component
                output files.

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
        # time attributes
        self.timedomain = timedomain

        # space attributes
        self.spacedomain = spacedomain

        # data attributes
        # # dataset to keep whole data period pristine
        self.dataset = dataset
        # # dataset to subset whole data for given period
        self.datasubset = DataSet()

        # parameters attribute
        self.parameters = parameters

        # constants attribute
        self.constants = constants

        # states attribute
        self.states = {}

        # identifier
        self.identifier = None

        # directories and files
        self.output_directory = output_directory
        self.dump_file = None

        # flag to check whether spin_up/initialise_states_from_dump used
        self.is_initialised = False

    @property
    def timedomain(self):
        """Return the temporal configuration of the Component as a
        `TimeDomain` object."""
        return self._timedomain

    @timedomain.setter
    def timedomain(self, timedomain):
        self._check_timedomain(timedomain)
        self._timedomain = timedomain

    @property
    def timestepinseconds(self):
        """Return the number of seconds separating two consecutive
        timestamps in the temporal configuration of the Component
        as a float."""
        return self.timedomain.timedelta.total_seconds()

    @property
    def spacedomain(self):
        """Return the spatial configuration of the Component as a
        `SpaceDomain` object."""
        return self._spacedomain

    @spacedomain.setter
    def spacedomain(self, spacedomain):
        self._check_spacedomain(spacedomain)
        self._spacedomain = spacedomain

    @property
    def spaceshape(self):
        """Return the length of each dimension in the spatial
        configuration of the Component as a `tuple` of `int`."""
        return self.spacedomain.shape

    @property
    def dataset(self):
        """Return the collection of variables forming the dataset for
        the Component as a `DataSet` object."""
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        dataset = DataSet() if dataset is None else dataset
        self._check_dataset(dataset)
        self._check_dataset_space(dataset, self.spacedomain)
        self._dataset = dataset

    @property
    def parameters(self):
        """Return the collection of parameter values for the Component
        as a `dict`."""
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        parameters = {} if parameters is None else parameters
        self._check_parameters(parameters)
        self._parameters = parameters

    @property
    def constants(self):
        """Return the collection of adjusted constant values for the
        Component as a `dict`. Potentially returning an empty dictionary
        if no default constant value is adjusted."""
        return self._constants

    @constants.setter
    def constants(self, constants):
        constants = {} if constants is None else constants
        # # no check because they are optional
        self._constants = constants

    def _check_timedomain(self, timedomain):
        """The purpose of this method is to check that the timedomain is
        of the right type.
        """
        if not isinstance(timedomain, TimeDomain):
            raise TypeError("not an instance of {} for {}".format(
                TimeDomain.__name__, self._category))

    def _check_spacedomain(self, spacedomain):
        """The purpose of this method is to check that the spacedomain is
        of the right type.
        """
        if not isinstance(spacedomain, SpaceDomain):
            raise TypeError("not an instance of {} for {}".format(
                SpaceDomain.__name__, self._category))

        if not isinstance(spacedomain, Grid):
            raise NotImplementedError(
                "only {} currently supported by framework "
                "for spacedomain".format(Grid.__name__))

    def _check_dataset(self, dataset):
        # checks for both driving and ancillary data

        # check that the dataset is an instance of DataSet
        if not isinstance(dataset, DataSet):

            raise TypeError(
                "object given for dataset argument of {} component '{}' "
                "not of type {}".format(
                    self._category, self.__class__.__name__,
                    DataSet.__name__))

        # check data units compatibility with component
        for data_name, data_unit in {**self.driving_data_info,
                                     **self.ancillary_data_info}.items():
            # check that all driving data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "no data '{}' available in {} for {} component '{}'".format(
                        data_name, DataSet.__name__, self._category,
                        self.__class__.__name__))
            # check that driving data units are compliant with component units
            if hasattr(dataset[data_name], 'units'):
                if not Units(data_unit).equals(
                        Units(dataset[data_name].units)):
                    raise ValueError(
                        "units of variable '{}' in {} {} not equal to units "
                        "required by {} component '{}': {} required".format(
                            data_name, self._category, DataSet.__name__,
                            self._category, self.__class__.__name__,
                            data_unit))
            else:
                raise AttributeError("variable '{}' in {} for {} component "
                                     "missing 'units' attribute".format(
                                         data_name, DataSet.__name__,
                                         self._category))

    def _check_dataset_space(self, dataset, spacedomain):
        # check space compatibility for both driving and ancillary data
        for data_name, data_unit in {**self.driving_data_info,
                                     **self.ancillary_data_info}.items():
            # check that the data and component space domains are compatible
            if not spacedomain.is_space_equal_to(dataset[data_name]):
                raise ValueError(
                    "spacedomain of data '{}' not compatible with "
                    "spacedomain of {} component '{}'".format(
                        data_name, self._category, self.__class__.__name__))

    def check_dataset_time(self, timedomain):
        # check time compatibility for driving data
        for data_name in self.driving_data_info:
            error = ValueError(
                "timedomain of data '{}' not compatible with "
                "timedomain of {} component '{}'".format(
                    data_name, self._category, self.__class__.__name__)
            )
            # try to subspace in time
            if self.dataset[data_name].subspace(
                    'test', T=cf.wi(*timedomain.time.datetime_array[[0, -1]])):
                # subspace in time
                self.datasubset[data_name] = self.dataset[data_name].subspace(
                    T=cf.wi(*timedomain.time.datetime_array[[0, -1]]))
            else:
                raise error

            # check that the data and component time domains are compatible
            if not timedomain.is_time_equal_to(self.datasubset[data_name]):
                raise error
        # copy reference for ancillary data
        for data_name in self.ancillary_data_info:
            self.datasubset[data_name] = self.dataset[data_name]

    def _check_parameters(self, parameters):
        """The purpose of this method is to check that parameter values
        are given for the corresponding component.
        """
        # check that all parameters are provided
        if not all([i in parameters for i in self.parameters_info]):
            raise RuntimeError(
                "one or more parameters are missing in {} component '{}': "
                "{} all required".format(
                    self._category, self.__class__.__name__,
                    self.parameters_info))

    @property
    def category(self):
        """Return the part of the water cycle the `Component` represents."""
        return self._category

    @property
    def inwards_info(self):
        """Return the incoming information expected by the `Component`."""
        return self._inwards_info

    @property
    def outwards_info(self):
        """Return the outgoing information provided by the `Component`."""
        return self._outwards_info

    @classmethod
    def get_class_category(cls):
        return cls._category

    @classmethod
    def get_class_inwards_info(cls):
        return cls._inwards_info

    @classmethod
    def get_class_outwards_info(cls):
        return cls._outwards_info

    @classmethod
    def from_config(cls, cfg):
        spacedomain = getattr(space, cfg['spacedomain']['class'])
        return cls(
            output_directory=cfg['output_directory'],
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
            'output_directory': self.output_directory,
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
        shape = ', '.join(['{}: {}'.format(ax, ln) for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])
        parameters = ["        {}: {} {}".format(
            p, self.parameters[p], self.parameters_info[p])
            for p in self.parameters] if self.parameters else []
        constants = ["        {}: {} {}".format(
            p, self.constants[p], self.constants_info[p])
            for p in self.constants] if self.constants else []
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    category: {}".format(self._category)]
            + ["    output directory: {}".format(self.output_directory)]
            + ["    timedomain: period: {}".format(self.timedomain.period)]
            + ["    spacedomain: shape: ({})".format(shape)]
            + ["    dataset: {} variable(s)".format(len(self.dataset))]
            + (["    parameters:"] if parameters else []) + parameters
            + (["    constants:"] if constants else []) + constants
            + [")"]
        )

    def __call__(self, timeindex, datetime_, **kwargs):
        # collect required ancillary data from dataset
        for data in self.ancillary_data_info:
            kwargs[data] = self.datasubset[data].array[...]

        # collect required driving data from dataset
        for data in self.driving_data_info:
            kwargs[data] = self.datasubset[data].array[timeindex, ...]

        # run simulation for the component
        outwards = self.run(datetime=datetime_, **self.parameters,
                            **self.constants, **self.states, **kwargs)

        # increment the component's states by one timestep
        self.increment_states()

        return outwards

    def _instantiate_states(self, states):
        # get a State object for each state and give it its initial conditions
        for s in self.states_info:
            if s in states:
                self.states[s] = State(*states[s])
            else:
                raise KeyError("initial conditions for {} component state "
                               "'{}' not provided".format(self._category, s))

    def _initialise_dump(self):
        self.dump_file = '_'.join([self.identifier, self.category,
                                   datetime.now().strftime('%Y%m%d%H%M%S%f'),
                                   'dump.nc'])
        create_dump_file(sep.join([self.output_directory, self.dump_file]),
                         self.states_info, self.solver_history,
                         self.timedomain, self.spacedomain)

    def initialise_states(self):
        # if not already initialised, get default state values
        if not self.is_initialised:
            states = self.initialise(**self.constants)
            self._instantiate_states(states)
            self.is_initialised = True
        # create the dump file for this given run
        self._initialise_dump()

    def initialise_states_from_dump(self, dump_file, at=None):
        """Initialise the states of the Component from a dump file.

        :Parameters:

            dump_file: `str`
                A string providing the path to the netCDF dump file
                containing values to be used as initial conditions for
                the states of the Component.

            at: datetime object, optional
                The snapshot in time to be used for the initial
                conditions. Must be any datetime type (except
                `numpy.datetime64`). Must be contained in the 'time'
                variable in *dump_file*. If not provided, the last index
                in the 'time' variable in *dump_file* will be used.

                Note: if a datetime is provided, there is no enforcement
                of the fact that this datetime must correspond to the
                initial datetime in the simulation period for the
                `Component`, and it is only used as a means to select
                a specific snapshot in time amongst the ones available
                in the dump file.

        """
        states = load_dump_file(dump_file, at, self.states_info)
        self._instantiate_states(states)
        self.is_initialised = True

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

    def dump_states(self, timeindex):
        timestamp = self.timedomain.bounds.array[timeindex, 1]
        update_dump_file(sep.join([self.output_directory, self.dump_file]),
                         self.states, timestamp, self.solver_history)

    def finalise_states(self):
        self.dump_states(-1)
        self.finalise(**self.states)

    @abc.abstractmethod
    def initialise(self, **kwargs):
        raise NotImplementedError(
            "{} class '{}' missing an 'initialise' method".format(
                self._category, self.__class__.__name__))

    @abc.abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError(
            "{} class '{}' missing a 'run' method".format(
                self._category, self.__class__.__name__))

    @abc.abstractmethod
    def finalise(self, **kwargs):
        raise NotImplementedError(
            "{} class '{}' missing a 'finalise' method".format(
                self._category, self.__class__.__name__))


class SurfaceLayerComponent(Component, metaclass=abc.ABCMeta):
    """The SurfaceLayerComponent is simulating the hydrological
    processes in the surface layer compartment of the hydrological
    cycle.
    """
    _category = 'surfacelayer'
    _inwards_info = {
        'soil_water_stress': '1'
    }
    _outwards_info = {
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
    _category = 'subsurface'
    _inwards_info = {
        'evaporation_soil_surface': 'kg m-2 s-1',
        'evaporation_ponded_water': 'kg m-2 s-1',
        'transpiration': 'kg m-2 s-1',
        'throughfall': 'kg m-2 s-1',
        'snowmelt': 'kg m-2 s-1'
    }
    _outwards_info = {
        'runoff': 'kg m-2 s-1',
        'soil_water_stress': '1'
    }


class OpenWaterComponent(Component, metaclass=abc.ABCMeta):
    """The OpenWaterComponent is simulating the hydrological processes
    in the open water compartment of the hydrological cycle.
    """
    _category = 'openwater'
    _inwards_info = {
        'evaporation_openwater': 'kg m-2 s-1',
        'runoff': 'kg m-2 s-1'
    }
    _outwards_info = {
        'discharge': 'kg m-2 s-1'
    }


class DataComponent(Component):
    """The DataComponent is a `Component` substituting simulations with
    data.

    Its intended use is to replace a compartment of the hydrological
    cycle with measurements or with previous simulation runs.
    """
    _category = 'data'
    _inwards_info = {}
    _outwards_info = {}

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
        super(DataComponent, self).__init__(None, timedomain, spacedomain,
                                            dataset)

        # override category to the one of substituting component
        self._category = substituting_class.get_class_category()

    def __str__(self):
        shape = ', '.join(['{}: {}'.format(ax, ln) for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    category: {}".format(self._category)]
            + ["    timedomain: period: {}".format(self.timedomain.period)]
            + ["    spacedomain: shape: ({})".format(shape)]
            + ["    dataset: {} variable(s)".format(len(self.dataset))]
            + [")"]
        )

    def _initialise_dump(self):
        pass

    def dump_states(self, timeindex):
        pass

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
    _category = 'null'
    _inwards_info = {}
    _outwards_info = {}

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
        super(NullComponent, self).__init__(None, timedomain, spacedomain)

        # override category with the one of component being substituted
        self._category = substituting_class.get_class_category()

        # override outwards with the ones of component being substituted
        self._outwards_info = substituting_class.get_class_outwards_info()

    def __str__(self):
        shape = ', '.join(['{}: {}'.format(ax, ln) for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    category: {}".format(self._category)]
            + ["    timedomain: period: {}".format(self.timedomain.period)]
            + ["    spacedomain: shape: ({})".format(shape)]
            + [")"]
        )

    def _initialise_dump(self):
        pass

    def dump_states(self, timeindex):
        pass

    def initialise(self, **kwargs):
        return {}

    def run(self, **kwargs):
        null_array = np.zeros(self.spaceshape, np.float32)
        return {n: null_array for n in self._outwards_info}

    def finalise(self, **kwargs):
        pass
