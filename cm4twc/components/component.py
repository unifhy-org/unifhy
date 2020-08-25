import abc
from importlib import import_module
import numpy as np
from os import path, sep
import cf
from cfunits import Units

from ._utils.states import (State, create_states_dump, update_states_dump,
                            load_states_dump)
from ..time import TimeDomain
from .. import space
from ..space import SpaceDomain, Grid
from ..data import DataSet
from ..settings import dtype_float, array_order


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
                dump and output files.

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
        # space attributes
        self.spacedomain = spacedomain

        # data attributes
        # # dataset to keep whole data period pristine
        self.dataset = dataset
        # # dataset to subset whole data for given period
        self.datasubset = DataSet()

        # time attributes
        self.timedomain = timedomain

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
        self._check_dataset_time(timedomain)
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
        for data_name, data_info in {**self.driving_data_info,
                                     **self.ancillary_data_info}.items():
            # check that all driving data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "no data '{}' available in {} for {} component '{}'".format(
                        data_name, DataSet.__name__, self._category,
                        self.__class__.__name__))
            # check that driving data units are compliant with component units
            if hasattr(dataset[data_name], 'units'):
                if not Units(data_info['units']).equals(
                        Units(dataset[data_name].units)):
                    raise ValueError(
                        "units of variable '{}' in {} {} not equal to units "
                        "required by {} component '{}': {} required".format(
                            data_name, self._category, DataSet.__name__,
                            self._category, self.__class__.__name__,
                            data_info['units']))
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

    def _check_dataset_time(self, timedomain):
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
        if ((end - start)
                % self.timedomain.timedelta).total_seconds() != 0:
            raise RuntimeError("spin up start-end incompatible with {} "
                               "component timedelta".format(self._category))

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

    def initialise_(self, tag, overwrite):
        # if not already initialised, get default state values
        if not self.is_initialised:
            self._instantiate_states()
            self.initialise(**self.states)
            self.is_initialised = True
        # create the dump file for this given run
        self._initialise_states_dump(tag, overwrite)

    def run_(self, timeindex, from_interface):
        data = {}
        # collect required ancillary data from dataset
        for d in self.ancillary_data_info:
            data[d] = self.datasubset[d].array[...]
        # collect required driving data from dataset
        for d in self.driving_data_info:
            data[d] = self.datasubset[d].array[timeindex, ...]
        # collect required transfers from interface
        for d in self._inwards_info:
            data[d] = from_interface[d]

        # run simulation for the component
        to_interface = self.run(**self.parameters, **self.constants,
                                **self.states, **data)

        # increment the component's states by one timestep
        self.increment_states()

        return to_interface

    def finalise_(self):
        timestamp = self.timedomain.bounds.array[-1, -1]
        update_states_dump(sep.join([self.output_directory, self.dump_file]),
                           self.states, timestamp, self.solver_history)
        self.finalise(**self.states)

    def _instantiate_states(self):
        # get a State object for each state and initialise to zero
        for s in self.states_info:
            d = self.states_info[s].get('divisions', 1)
            o = self.states_info[s].get('order', array_order())
            self.states[s] = State(
                np.zeros(
                    (self.solver_history+1, *self.spaceshape, d) if d > 1
                    else (self.solver_history+1, *self.spaceshape),
                    dtype_float(), order=o
                ),
                order=o
            )

    def _initialise_states_dump(self, tag, overwrite_dump):
        self.dump_file = '_'.join([self.identifier, self.category,
                                   tag, 'dump.nc'])
        if (overwrite_dump or not path.exists(sep.join([self.output_directory,
                                                        self.dump_file]))):
            create_states_dump(sep.join([self.output_directory, self.dump_file]),
                               self.states_info, self.solver_history,
                               self.timedomain, self.spacedomain)

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

        :Returns:

            datetime object
                The snapshot in time that was used for the initial
                conditions.

        """
        states, at = load_states_dump(dump_file, at, self.states_info)
        for s in self.states_info:
            if s in states:
                o = self.states_info[s].get('order', array_order())
                self.states[s] = State(states[s], order=o)
            else:
                raise KeyError("initial conditions for {} component state "
                               "'{}' not in dump".format(self._category, s))
        self.is_initialised = True

        return at

    def increment_states(self):
        for s in self.states:
            self.states[s].increment()

    def dump_states(self, timeindex):
        timestamp = self.timedomain.bounds.array[timeindex, 0]
        update_states_dump(sep.join([self.output_directory, self.dump_file]),
                           self.states, timestamp, self.solver_history)

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
        'soil_water_stress': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'throughfall': {
            'units': 'kg m-2 s-1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'snowmelt': {
            'units': 'kg m-2 s-1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'transpiration': {
            'units': 'kg m-2 s-1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'evaporation_soil_surface': {
            'units': 'kg m-2 s-1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'evaporation_ponded_water': {
            'units': 'kg m-2 s-1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'evaporation_openwater': {
            'units': 'kg m-2 s-1',
            'to': 'openwater',
            'method': 'mean'
        }
    }


class SubSurfaceComponent(Component, metaclass=abc.ABCMeta):
    """The SubSurfaceComponent is simulating the hydrological processes
    in the subsurface compartment of the hydrological cycle.
    """
    _category = 'subsurface'
    _inwards_info = {
        'evaporation_soil_surface': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'evaporation_ponded_water': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'transpiration': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'throughfall': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'snowmelt': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'runoff': {
            'units': 'kg m-2 s-1',
            'to': 'openwater',
            'method': 'mean'
        },
        'soil_water_stress': {
            'units': '1',
            'to': 'surfacelayer',
            'method': 'mean'
        }
    }


class OpenWaterComponent(Component, metaclass=abc.ABCMeta):
    """The OpenWaterComponent is simulating the hydrological processes
    in the open water compartment of the hydrological cycle.
    """
    _category = 'openwater'
    _inwards_info = {
        'evaporation_openwater': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'runoff': {
            'units': 'kg m-2 s-1',
            'from': 'subsurface',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'discharge': {
            'units': 'kg m-2 s-1',
            'to': 'ocean',
            'method': 'mean'
        }
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
                the `Component`\'s simulated time series. The data in
                dataset must be compatible in time with *timedomain* and
                compatible in space with *spacedomain*.

            substituting_class: `Component` object
                The subclass of `Component` that the DataComponent is
                substituting its simulated time series with the ones in
                *dataset*.

        """
        # store class being substituted for config
        self._substituting_class = substituting_class

        # override category to the one of substituting component
        self._category = substituting_class.get_class_category()

        # override outwards with the ones of component being substituted
        self._outwards_info = substituting_class.get_class_outwards_info()

        # override driving data info with the outwards of component
        # being substituted (so that the dataset is checked for time
        # and space compatibility as a 'standard' dataset would be)
        self.driving_data_info = substituting_class.get_class_outwards_info()

        # initialise as a Component
        super(DataComponent, self).__init__(None, timedomain, spacedomain,
                                            dataset)

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

    @classmethod
    def from_config(cls, cfg):
        spacedomain = getattr(space, cfg['spacedomain']['class'])
        substituting_class = (
            getattr(
                import_module(cfg['substituting']['module']),
                cfg['substituting']['class']
            )
        )
        return cls(
            timedomain=TimeDomain.from_config(cfg['timedomain']),
            spacedomain=spacedomain.from_config(cfg['spacedomain']),
            dataset=DataSet.from_config(cfg.get('dataset')),
            substituting_class=substituting_class
        )

    def to_config(self):
        cfg = {
            'module': self.__module__,
            'class': self.__class__.__name__,
            'timedomain': self.timedomain.to_config(),
            'spacedomain': self.spacedomain.to_config(),
            'dataset': self.dataset.to_config(),
            'substituting': {
                'module': self._substituting_class.__module__,
                'class': self._substituting_class.__name__
            }
        }
        return cfg

    def initialise_(self, *args, **kwargs):
        pass

    def dump_states(self, *args, **kwargs):
        pass

    def finalise_(self, *args, **kwargs):
        pass

    def initialise(self, *args, **kwargs):
        return {}

    def run(self, *args, **kwargs):
        return {n: kwargs[n] for n in self._outwards_info}

    def finalise(self, *args, **kwargs):
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

    def __init__(self, timedomain, spacedomain, substituting_class, **kwargs):
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
        # store class being substituted for config
        self._substituting_class = substituting_class

        # override category with the one of component being substituted
        self._category = substituting_class.get_class_category()

        # override inwards and outwards with the ones of component
        # being substituted
        self._outwards_info = substituting_class.get_class_outwards_info()

        # initialise as a Component
        super(NullComponent, self).__init__(None, timedomain, spacedomain)

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

    @classmethod
    def from_config(cls, cfg):
        spacedomain = getattr(space, cfg['spacedomain']['class'])
        substituting_class = (
            getattr(
                import_module(cfg['substituting']['module']),
                cfg['substituting']['class']
            )
        )
        return cls(
            timedomain=TimeDomain.from_config(cfg['timedomain']),
            spacedomain=spacedomain.from_config(cfg['spacedomain']),
            substituting_class=substituting_class
        )

    def to_config(self):
        cfg = {
            'module': self.__module__,
            'class': self.__class__.__name__,
            'timedomain': self.timedomain.to_config(),
            'spacedomain': self.spacedomain.to_config(),
            'substituting': {
                'module': self._substituting_class.__module__,
                'class': self._substituting_class.__name__
            }
        }
        return cfg

    def initialise_(self, *args, **kwargs):
        pass

    def dump_states(self, *args, **kwargs):
        pass

    def finalise_(self, *args, **kwargs):
        pass

    def initialise(self, *args, **kwargs):
        return {}

    def run(self, *args, **kwargs):
        null_array = np.zeros(self.spaceshape, np.float32)
        return {n: null_array for n in self._outwards_info}

    def finalise(self, *args, **kwargs):
        pass
