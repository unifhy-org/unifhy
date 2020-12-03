import abc
from importlib import import_module
import numpy as np
from os import path, sep
from datetime import timedelta
import cf
from cfunits import Units

from ._utils.states import (State, create_states_dump, update_states_dump,
                            load_states_dump)
from ._utils.outputs import (StateOutput, InterfaceOutput, OtherOutput,
                             OutputStream)
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
                (["    {}:".format(t[1:] if t[0] == '_' else t).replace('_', ' ')]
                 + ["        {} [{}]".format(n, info['units'])
                    for n, info in getattr(self, t + '_info').items()]
                 if getattr(self, t + '_info') else [])
            )
            for t in ['_inwards', '_outwards',
                      'inputs', 'parameters', 'constants', 'outputs', 'states']
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
    inputs_info = {}
    parameters_info = {}
    constants_info = {}
    states_info = {}
    outputs_info = {}
    solver_history = 1

    def __init__(self, output_directory, timedomain, spacedomain,
                 dataset=None, parameters=None, constants=None, outputs=None):
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
                The collection of input data required by the `Component`
                (i.e. 'dynamic' and/or 'static' and/or 'climatologic').
                The input data must be compatible in space with
                *spacedomain*, and compatible in time with *timedomain*
                for the 'dynamic' type, and with the 'frequency' for
                the 'climatologic' type (see table below for details).

                ======================  ================================
                climatologic frequency  length of time dimension in data
                ======================  ================================
                ``'seasonal'``          Length of 4, corresponding to
                                        the meteorological seasons (i.e.
                                        Winter [DJF], Spring [MAM],
                                        Summer [JJA], Autumn [SON], in
                                        this order).

                ``'monthly'``           Length of 12, corresponding to
                                        the months in the calendar year
                                        (i.e. from January to December).

                ``'day_of_year'``       Length of 366, corresponding to
                                        the days in the calendar year
                                        (i.e. from January 1st to
                                        December 31st, including value
                                        for February 29th).

                `int`                   Length according to the integer
                                        value (e.g. a value of 6 means
                                        6 climatologic values for the
                                        calendar year).
                ======================  ================================

            parameters: `dict`, optional
                The parameter values for the `Component`. Must be
                provided in the units expected by the `Component`.

            constants: `dict`, optional
                The parameter values for the `Component`. Must be
                provided in the required units.

            outputs: `dict`, optional
                The desired outputs from the `Component`. Each key
                must an output available for the component chosen,
                each value is a `dict` of `datetime.timedelta` for keys
                and aggregation methods as a sequence of `str` for
                values.

                *Parameter example:* ::

                    outputs={
                        'output_a': {
                            timedelta(days=1): ['sum'],
                            timedelta(weeks=1): ['min', 'max']
                        },
                        'output_b': {
                            timedelta(days=1): ['mean']
                        }
                    }

                The aggregation methods supported are listed in the
                table below.

                ===============  =======================================
                method           description
                ===============  =======================================
                ``'point'``      The instantaneous value at the given
                                 elapsed timedelta.

                ``'sum'``        The accumulation of the values during
                                 the given elapsed timedelta.

                ``'mean'``       The average of the values during the
                                 given elapsed timedelta.

                ``'min'``        The minimum amongst the values during
                                 the elapsed timedelta.

                ``'max'``        The maximum amongst the values during
                                 the elapsed timedelta.
                ===============  =======================================

        """
        # check class definition attributes
        self._check_definition()

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

        # outputs attributes
        self._output_objects = None
        self._output_streams = None
        self.outputs = outputs

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

    @property
    def outputs(self):
        """Return the collection of desired `Output`s to be saved for the
        Component as a `dict`. Potentially returning an empty dictionary
        if no outputs are desired."""
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        outputs = {} if outputs is None else outputs
        outputs_ = {}
        for name, frequencies in outputs.items():
            # check type and eliminate duplicates in methods
            outputs_[name] = {}
            for delta, methods in frequencies.items():
                if isinstance(methods, (list, tuple, set)):
                    outputs_[name][delta] = set(methods)
                else:
                    raise TypeError('output methods for {} at {} must be a '
                                    'sequence of strings'.format(name, delta))

        self._outputs = outputs_

    def _check_definition(self):
        # check for units
        for lead in ['inputs', 'parameters', 'constants',
                     'outputs', 'states']:
            attr = getattr(self, '_'.join([lead, 'info']))
            if attr:
                for name, info in attr.items():
                    if 'units' not in info:
                        raise RuntimeError(
                            "units missing for {} in {} component "
                            "definition".format(name, self._category)
                        )
        # check for kind
        if self.inputs_info:
            for name, info in self.inputs_info.items():
                if 'kind' not in info:
                    # assume it is a 'standard' input, i.e. dynamic
                    # (this is also useful for a `DataComponent` which
                    #  will not have a 'kind' since inputs are inherited
                    #  from outwards of the component being substituted)
                    info['kind'] = 'dynamic'
                else:
                    if info['kind'] not in ['dynamic', 'static',
                                            'climatologic']:
                        raise ValueError(
                            "invalid type for {} in {} component "
                            "definition".format(name, self._category)
                        )
                    if info['kind'] == 'climatologic':
                        if 'frequency' not in info:
                            raise RuntimeError(
                                "frequency missing for {} in {} component "
                                "definition".format(name, self._category)
                            )
                        freq = info['frequency']
                        if not isinstance(freq, int):
                            if (isinstance(freq, str) and freq
                                    not in ['seasonal', 'monthly', 'daily']):
                                raise TypeError(
                                    "invalid frequency for {} in {} component "
                                    "definition".format(name, self._category)
                                )

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
        # checks for input data

        # check that the dataset is an instance of DataSet
        if not isinstance(dataset, DataSet):

            raise TypeError(
                "object given for dataset argument of {} component '{}' "
                "not of type {}".format(
                    self._category, self.__class__.__name__,
                    DataSet.__name__))

        # check data units compatibility with component
        for data_name, data_info in self.inputs_info.items():
            # check that all input data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "no data '{}' available in {} for {} component '{}'".format(
                        data_name, DataSet.__name__, self._category,
                        self.__class__.__name__))
            # check that input data units are compliant with component units
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
        # check space compatibility for input data
        for data_name, data_unit in self.inputs_info.items():
            # check that the data and component space domains are compatible
            if not spacedomain.is_space_equal_to(dataset[data_name]):
                raise ValueError(
                    "spacedomain of data '{}' not compatible with "
                    "spacedomain of {} component '{}'".format(
                        data_name, self._category, self.__class__.__name__))

    def _check_dataset_time(self, timedomain):
        # check time compatibility for 'dynamic' input data
        for data_name in self.inputs_info:
            error = ValueError(
                "timedomain of data '{}' not compatible with "
                "timedomain of {} component '{}'".format(
                    data_name, self._category, self.__class__.__name__)
            )

            kind = self.inputs_info[data_name]['kind']
            if kind == 'dynamic':
                # try to subspace in time
                if self.dataset[data_name].subspace(
                        'test',
                        T=cf.wi(*timedomain.time.datetime_array[[0, -1]])):
                    # subspace in time and assign to data subset
                    self.datasubset[data_name] = (
                        self.dataset[data_name].subspace(
                            T=cf.wi(
                                *timedomain.time.datetime_array[[0, -1]]
                            )
                        )
                    )
                else:
                    raise error

                # check that data and component time domains are compatible
                if not timedomain.is_time_equal_to(
                        self.datasubset[data_name]):
                    raise error

            elif kind == 'climatologic':
                lengths = {
                    'seasonal': 4,  # DJF-MAM-JJA-SON
                    'monthly': 12,  # January to December
                    'day_of_year': 366  # Jan 1st to Dec 31st (with Feb 29th)
                }
                freq = self.inputs_info[data_name]['frequency']
                if isinstance(freq, str):
                    length = lengths[freq]
                else:  # isinstance(freq, int):
                    length = int(freq)

                # check that time dimension is of expected length
                if self.dataset[data_name].construct('time').size != length:
                    raise error

                # copy reference for climatologic input data
                self.datasubset[data_name] = self.dataset[data_name]

            else:  # type_ == 'static':
                # copy reference for static input data
                if self.dataset[data_name].has_construct('time'):
                    if self.dataset[data_name].construct('time').size == 1:
                        self.datasubset[data_name] = (
                            self.dataset[data_name].squeeze('time')
                        )
                    else:
                        raise error
                else:
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
            constants=cfg.get('constants'),
            outputs=cfg.get('outputs')
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
            'constants': self.constants if self.constants else None,
            'outputs': self.outputs if self.outputs else None
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
            p, self.parameters[p], self.parameters_info[p]['units'])
            for p in self.parameters] if self.parameters else []
        constants = ["        {}: {} {}".format(
            c, self.constants[c], self.constants_info[c]['units'])
            for c in self.constants] if self.constants else []
        outputs = ["        {}: {} {}".format(
            o, d, m) for o, f in self.outputs.items()
            for d, m in f.items()] if self.outputs else []
        return "\n".join(
            ["{}(".format(self.__class__.__name__)]
            + ["    category: {}".format(self._category)]
            + ["    output directory: {}".format(self.output_directory)]
            + ["    timedomain: period: {}".format(self.timedomain.period)]
            + ["    spacedomain: shape: ({})".format(shape)]
            + ["    dataset: {} variable(s)".format(len(self.dataset))]
            + (["    parameters:"] if parameters else []) + parameters
            + (["    constants:"] if constants else []) + constants
            + (["    outputs:"] if outputs else []) + outputs
            + [")"]
        )

    def initialise_(self, tag, overwrite):
        # if not already initialised, get default state values
        if not self.is_initialised:
            self._instantiate_states()
            self.initialise(**self.states)
            self.is_initialised = True
        # create dump file for given run
        self._initialise_states_dump(tag, overwrite)

        if self.outputs:
            # create outputs, output streams, and output stream files
            self._instantiate_output_objects_and_streams(tag, overwrite)
            # create dumps for output streams
            self._initialise_output_streams_dumps(tag, overwrite)

    def run_(self, timeindex, exchanger):
        data = {}
        # collect required ancillary data from dataset
        for d in self.inputs_info:
            kind = self.inputs_info[d]['kind']
            if kind == 'dynamic':
                data[d] = self.datasubset[d].array[timeindex, ...]
            else:
                data[d] = self.datasubset[d].array[...]

        # collect required transfers from exchanger
        for d in self._inwards_info:
            data[d] = exchanger.get_transfer(d, self._category)

        # run simulation for the component
        to_exchanger, outputs = self.run(**self.parameters, **self.constants,
                                         **self.states, **data)

        # store outputs
        for name in self._outputs:
            self._output_objects[name](self.states, to_exchanger, outputs)

        # increment the component's states by one timestep
        self.increment_states()

        return to_exchanger

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

    def _initialise_states_dump(self, tag, overwrite):
        self.dump_file = '_'.join([self.identifier, self.category,
                                   tag, 'dump.nc'])
        if (overwrite or not path.exists(sep.join([self.output_directory,
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

    def _instantiate_output_objects_and_streams(self, tag, overwrite):
        self._output_objects = {}
        self._output_streams = {}

        for name, frequencies in self.outputs.items():
            # create instance of appropriate Output subclass
            if name in self.outputs_info:
                self._output_objects[name] = OtherOutput(
                    name, **self.outputs_info[name]
                )
            elif name in self._outwards_info:
                self._output_objects[name] = InterfaceOutput(
                    name, **self._outwards_info[name]
                )
            elif name in self.states_info:
                self._output_objects[name] = StateOutput(
                    name, **self.states_info[name]
                )
            else:
                raise ValueError("{} not available for {} component".format(
                    name, self._category))

            for delta, methods in frequencies.items():
                # instantiate OutputStream if none for given timedelta yet
                if delta not in self._output_streams:
                    self._output_streams[delta] = OutputStream(
                        delta, self.timedomain, self.spacedomain
                    )
                # hold reference to output object in stream
                self._output_streams[delta].add_output(
                    self._output_objects[name], methods
                )

        for delta, stream in self._output_streams.items():
            filename = '_'.join([self.identifier, self._category, tag,
                                 'out', stream.frequency])
            file_ = sep.join([self.output_directory, filename + '.nc'])

            if overwrite or not path.exists(file_):
                stream.create_output_stream_file(file_)
            else:
                stream.file = file_

    def _initialise_output_streams_dumps(self, tag, overwrite):
        for delta, stream in self._output_streams.items():
            filename = '_'.join([self.identifier, self._category, tag,
                                 'dump_stream', stream.frequency])
            file_ = sep.join([self.output_directory, filename + '.nc'])

            if overwrite or not path.exists(file_):
                stream.create_output_stream_dump(file_)
            else:
                stream.dump_file = file_

    def initialise_output_streams_from_dump(self, dump_file_pattern,
                                            at=None):
        """Initialise the states of the Component from a dump file.

        :Parameters:

            dump_filepath_pattern: `str`
                A string providing the path to the netCDF dump file
                containing values to be used as initial conditions for
                the output streams of the Component. Note, curly
                brackets {} should be used where the output stream delta
                should be used.

                *Parameter example:* ::

                    dump_file_pattern='out/dummy_surfacelayer_run_dump_stream_{}.nc'

            at: datetime object, optional
                The snapshot in time to be used for the initial
                conditions. Must be any datetime type (except
                `numpy.datetime64`). Must be contained in the 'time'
                variable in dump file. If not provided, the last index
                in the 'time' variable in dump file will be used.

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
        ats = []

        if self.outputs:
            for delta, stream in self._output_streams.items():
                file_ = dump_file_pattern.format(stream.frequency)
                ats.append(stream.load_output_stream_dump(file_, at))

        return ats

    def dump_output_streams(self, timeindex):
        timestamp = self.timedomain.bounds.array[timeindex, 0]
        if self.outputs:
            for delta, stream in self._output_streams.items():
                stream.update_output_stream_dump(timestamp)

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
        },
        'water_level': {
            'units': 'kg m-2',
            'from': 'openwater',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'throughfall': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'snowmelt': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'transpiration': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'evaporation_soil_surface': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'evaporation_ponded_water': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'evaporation_openwater': {
            'units': 'kg m-2 s-1',
            'to': ['openwater'],
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
        },
        'water_level': {
            'units': 'kg m-2',
            'from': 'openwater',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'runoff': {
            'units': 'kg m-2 s-1',
            'to': ['openwater'],
            'method': 'mean'
        },
        'soil_water_stress': {
            'units': '1',
            'to': ['surfacelayer'],
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
        'water_level': {
            'units': 'kg m-2',
            'to': ['surfacelayer', 'subsurface'],
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

    # definition attributes
    solver_history = 0

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

        # override inputs info with the outwards of component being
        # substituted (so that the dataset is checked for time and space
        # compatibility as a 'standard' dataset would be)
        self.inputs_info = substituting_class.get_class_outwards_info()

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
        return {n: kwargs[n] for n in self._outwards_info}, {}

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

    # definition attributes
    solver_history = 0

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
        return {n: null_array for n in self._outwards_info}, {}

    def finalise(self, *args, **kwargs):
        pass
