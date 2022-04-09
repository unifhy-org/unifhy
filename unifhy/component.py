import abc
from importlib import import_module
import numpy as np
from os import path, sep
import cf
from cfunits import Units
from numbers import Number
from copy import deepcopy
import yaml

from ._utils.state import (
    State, create_states_dump, update_states_dump, load_states_dump
)
from ._utils.record import (
    StateRecord, OutwardRecord, OutputRecord, RecordStream
)
from .time import TimeDomain
from . import space
from .space import SpaceDomain, Grid
from .data import (
    DataSet, Variable, StaticVariable, ClimatologicVariable, DynamicVariable
)
from .settings import dtype_float, array_order


class MetaComponent(abc.ABCMeta):
    """MetaComponent is a metaclass for `Component`."""
    # intrinsic attributes
    _category = None

    _inwards_info = None
    _outwards_info = None

    _inwards = None
    _outwards = None

    # definition attributes
    _inputs_info = None
    _parameters_info = None
    _constants_info = None
    _states_info = None
    _outputs_info = None

    _solver_history = None

    _requires_land_sea_mask = None
    _requires_flow_direction = None
    _requires_cell_area = None

    @property
    def category(cls):
        return cls._category

    @property
    def inwards_info(cls):
        return {
            k: deepcopy(v) for k, v in cls._inwards_info.items()
            if k in cls._inwards
        }

    @property
    def outwards_info(cls):
        return {
            k: deepcopy(v) for k, v in cls._outwards_info.items()
            if k in cls._outwards
        }

    @property
    def inwards_metadata(cls):
        """Return details on the component inward transfers as a `str`."""
        if cls.inwards_info:
            return yaml.dump(cls.inwards_info)

    @property
    def outwards_metadata(cls):
        """Return details on the component outward transfers as a `str`."""
        if cls.outwards_info:
            return yaml.dump(cls.outwards_info)

    @property
    def inputs_metadata(cls):
        """Return details on the component input data as a `str`."""
        if cls._inputs_info:
            return yaml.dump(cls._inputs_info)

    @property
    def parameters_metadata(cls):
        """Return details on the component parameters as a `str`."""
        if cls._parameters_info:
            return yaml.dump(cls._parameters_info)

    @property
    def constants_metadata(cls):
        """Return details on the component constants as a `str`."""
        if cls._constants_info:
            return yaml.dump(cls._constants_info)

    @property
    def states_metadata(cls):
        """Return details on the component states as a `str`."""
        if cls._states_info:
            return yaml.dump(cls._states_info)

    @property
    def outputs_metadata(cls):
        """Return details on the component outputs as a `str`."""
        if cls._outputs_info:
            return yaml.dump(cls._outputs_info)

    @property
    def solver_history(cls):
        return cls._solver_history

    def requires_flow_direction(cls):
        """Return `True` if flow direction must be available in the
        component spacedomain, otherwise return `False`."""
        return cls._requires_flow_direction

    def requires_land_sea_mask(cls):
        """Return `True` if land sea mask must be available in the
        component spacedomain, otherwise return `False`."""
        return cls._requires_land_sea_mask

    def requires_cell_area(cls):
        """Return `True` if cell area must be available in the
        component spacedomain, otherwise return `False`."""
        return cls._requires_cell_area

    def __str__(cls):
        info_a = [
            "\n".join(
                ([f"    {t.replace('_info', ' metadata').replace('_', '')}:"]
                 + [f"        {n} [{info['units']}]"
                    for n, info in getattr(cls, t).items()])
            )
            for t in ['inwards_info', '_inputs_info']
            if getattr(cls, t)
        ]

        info_b = [
            "\n".join(
                ([f"    {t.replace('_info', ' metadata').replace('_', '')}:"]
                 + [f"        {n} [{info['units']}]"
                    for n, info in getattr(cls, t).items()])
            )
            for t in ['_parameters_info', '_constants_info', '_states_info',
                      'outwards_info', '_outputs_info']
            if getattr(cls, t)
        ]

        return "\n".join(
            [f"{cls.__name__}("]
            + [f"    category: {getattr(cls, '_category')}"]
            + info_a
            + [
                f"    requires land sea mask: "
                f"{getattr(cls, '_requires_land_sea_mask')}"
            ]
            + [
                f"    requires flow direction: "
                f"{getattr(cls, '_requires_flow_direction')}"
            ]
            + [
                f"    requires cell area: "
                f"{getattr(cls, '_requires_cell_area')}"
            ]
            + info_b
            + [")"]
        )


class Component(metaclass=MetaComponent):
    # intrinsic attributes (set to default)
    _category = ''

    _inwards_info = {}
    _outwards_info = {}

    _inwards = {}
    _outwards = {}

    # definition attributes (set to default)
    _inputs_info = {}
    _parameters_info = {}
    _constants_info = {}
    _states_info = {}
    _outputs_info = {}

    _solver_history = 1

    _requires_land_sea_mask = False
    _requires_flow_direction = False
    _requires_cell_area = False

    def __init__(self, saving_directory, timedomain, spacedomain,
                 dataset=None, parameters=None, constants=None, records=None,
                 io_slice=None):
        """**Instantiation**

        :Parameters:

            saving_directory: `str`
                The path to the directory where to save the component
                dump and record files.

            timedomain: `TimeDomain` object
                The temporal dimension of the `Component`.

            spacedomain: `SpaceDomain` object
                The spatial dimension of the `Component`.

            dataset: `DataSet` object, optional
                The collection of input data required by the `Component`
                (i.e. 'dynamic' and/or 'static' and/or 'climatologic').
                The input data must always be compatible in space with
                *spacedomain*, and compatible in time with *timedomain*
                for the 'dynamic' kind, and with the 'frequency' for
                the 'climatologic' kind (see :ref:`Tab. 2<tab_frequencies>`
                for details).

            parameters: `dict`, optional
                The parameter values for the `Component`. Each key must
                correspond to a parameter name, and each value can be
                a `cf.Field` (with units), a `cf.Data` (with units),
                or a sequence of 2 items data and units (in this order).

                If it is a `cf.Field`, it must contains data for all
                spatial elements in the region covered by the component's
                spacedomain. If it is a `cf.Data` or sequence of 2 items,
                underlying data can be a scalar or an array (of the same
                shape as the component's spacedomain).

                *Parameter example:* ::

                    parameters={
                        'parameter_a': (120, 'm s-1')
                    }

                *Parameter example:* ::

                    parameters={
                        'parameter_a': cf.Data(120, 'm s-1')
                    }

                *Parameter example:* ::

                    parameters={
                        'parameter_a': ([130, 110, 120], 'm s-1')
                    }

                *Parameter example:* ::

                    parameters={
                        'parameter_a': (numpy.array([130, 110, 120]), 'm s-1')
                    }

                *Parameter example:* ::

                    parameters={
                        'parameter_a': cf.Data([130, 110, 120], 'm s-1')
                    }

            constants: `dict`, optional
                The constant values for the `Component` for which
                adjustment is desired. Each key must correspond to a
                constant name, and each value must either be a `cf.Data`
                (with units, where data must be a scalar) or a sequence
                of 2 items data and units (in this order, where data
                must be a scalar).

                *Parameter example:* ::

                    constants={
                        'constant_a': (1000, 'kg m-3')
                    }

                *Parameter example:* ::

                    constants={
                        'constant_a': cf.Data(1000, 'kg m-3')
                    }

            records: `dict`, optional
                The desired records from the `Component`. Each key
                must be a valid variable recordable for the component
                chosen (i.e. outwards, outputs, and states), each value
                is a `dict` of recording temporal resolutions as
                `datetime.timedelta` for keys and aggregation methods
                as a sequence of `str` for values.

                *Parameter example:* ::

                    records={
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

                The recording temporal resolutions must be multiples
                of the component temporal resolution, and they must be
                divisors of the component simulation period.

            io_slice: `int`, optional
                The length of the time slice to use for input/output
                operations. This corresponds to the number of component
                timesteps to read/write at once. If not set, its default
                value is 100 (arbitrary).

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

        # time attribute
        self._io_slice = 100 if io_slice is None else int(io_slice)
        self._timedelta_in_seconds = None
        self._current_datetime = None
        self._datetime_array = None
        self.timedomain = timedomain

        # parameters attribute
        self._pristine_parameters = None
        self.parameters = parameters

        # constants attribute
        self.constants = constants

        # records attributes
        self._record_objects = None
        self._record_streams = None
        self.records = records

        # states attribute
        self.states = {}

        # identifier
        self.identifier = None

        # directories and files
        self.saving_directory = saving_directory
        self.dump_file = None

        # special attribute to store information that can be communicated
        # between component methods (typically between `initialise` and `run`)
        self.shelf = {}

        # flag to check whether states / streams have been initialised
        self._initialised_states = False
        self._revived_streams = False

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
        self._timedelta_in_seconds = timedomain.timedelta.total_seconds()
        self._current_datetime = timedomain.time.datetime_array[0]
        self._datetime_array = timedomain.time.datetime_array[:]

    @property
    def timedelta_in_seconds(self):
        """Return the number of seconds separating two consecutive
        timestamps in the temporal configuration of the Component
        as a `float`."""
        return self._timedelta_in_seconds

    @property
    def current_datetime(self):
        """Return the current datetime at any stage during the
        simulation as a datetime object."""
        return self._current_datetime

    @property
    def spacedomain(self):
        """Return the spatial configuration of the Component as a
        `SpaceDomain` object."""
        return self._spacedomain

    @spacedomain.setter
    def spacedomain(self, spacedomain):
        self._check_spacedomain(spacedomain)
        self._spaceshape = spacedomain.shape
        self._spacedomain = spacedomain

    @property
    def spaceshape(self):
        """Return the length of each dimension in the spatial
        configuration of the Component as a `tuple` of `int`."""
        return self._spaceshape

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
        self._pristine_parameters = parameters
        self._parameters = self._check_parameters(parameters, self.spacedomain)

    @property
    def constants(self):
        """Return the collection of adjusted constant values for the
        Component as a `dict`. Potentially returning an empty dictionary
        if no default constant value is adjusted."""
        return self._constants

    @constants.setter
    def constants(self, constants):
        constants = {} if constants is None else constants
        self._constants = self._check_constants(constants)
        self._use_constants_to_replace_state_divisions()

    @property
    def records(self):
        """Return the collection of desired records to be saved for the
        Component as a `dict`. Potentially returning an empty dictionary
        if no record are desired."""
        return self._records

    @records.setter
    def records(self, records):
        records = {} if records is None else records
        records_ = {}
        for name, frequencies in records.items():
            # check type and eliminate duplicates in methods
            records_[name] = {}
            for delta, methods in frequencies.items():
                if isinstance(methods, (list, tuple, set)):
                    records_[name][delta] = set(methods)
                else:
                    raise TypeError(
                        f"recording methods for {name} at {delta} "
                        f"must be a sequence of strings"
                    )

        self._records = records_

        # create record objects, record stream objects
        self._record_objects = {}
        self._record_streams = {}

        for name, frequencies in self.records.items():
            # create instance of appropriate Record subclass
            if name in self._outputs_info:
                self._record_objects[name] = OutputRecord(
                    name, **self._outputs_info[name]
                )
            elif name in self._outwards_info:
                self._record_objects[name] = OutwardRecord(
                    name, **self._outwards_info[name]
                )
            elif name in self._states_info:
                self._record_objects[name] = StateRecord(
                    name, **self._states_info[name]
                )
            else:
                raise ValueError(
                    f"{name} not available for {self._category} component"
                )

            for delta, methods in frequencies.items():
                # instantiate RecordStream if none for given timedelta yet
                if delta not in self._record_streams:
                    self._record_streams[delta] = RecordStream(
                        delta, writing_slice=self._io_slice
                    )
                # hold reference to record object in stream
                self._record_streams[delta].add_record(
                    self._record_objects[name], methods
                )

    @property
    def initialised_states(self):
        """Return whether initial conditions for component states have
        already been set as a `bool`."""
        return self._initialised_states

    def _check_definition(self):
        # check inwards/outwards are relevant for the component category
        for lead in ['inwards', 'outwards']:
            info = {}
            def_attr = getattr(self, f'_{lead}')
            cls_attr = getattr(self, f'_{lead}_info')
            for name in def_attr:
                if name in cls_attr:
                    info[name] = cls_attr[name]
                else:
                    raise RuntimeError(
                        f"{lead[:-1]} {name} in component definition is "
                        f"not compatible with component category"
                    )
            setattr(self, f'_{lead}_info', info)

        # check for units
        for lead in ['inputs', 'parameters', 'constants',
                     'outputs', 'states']:
            attr = getattr(self, f'_{lead}_info')
            if attr:
                for name, info in attr.items():
                    if 'units' not in info:
                        raise RuntimeError(
                            f"units missing for {name} in {self._category} "
                            f"component definition"
                        )

        # check for presence of input kind, if not assume 'dynamic'
        if self._inputs_info:
            for name, info in self._inputs_info.items():
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
                            f"invalid type for {name} in {self._category} "
                            f"component definition"
                        )
                    if info['kind'] == 'climatologic':
                        if 'frequency' not in info:
                            raise RuntimeError(
                                f"frequency missing for {name} in "
                                f"{self._category} component definition"
                            )
                        freq = info['frequency']
                        if not isinstance(freq, int):
                            if (isinstance(freq, str) and freq
                                    not in ['seasonal', 'monthly', 'daily']):
                                raise TypeError(
                                    f"invalid frequency for {name} in "
                                    f"{self._category} component definition"
                                )

        # check for presence of constant default_value
        if self._constants_info:
            for name, info in self._constants_info.items():
                if 'default_value' not in info:
                    raise RuntimeError(
                        f"default_value missing for constant {name} in "
                        f"{self._category} component definition"
                    )

        # check for presence of state divisions, if not assume scalar
        if self._states_info:
            for name, info in self._states_info.items():
                d = info.get('divisions', None)

                if d is None:
                    # assign default value (i.e. state is a scalar)
                    d = [1]
                else:
                    if isinstance(d, (Number, str)):
                        # convert to list of one item
                        d = [d]
                    elif isinstance(d, (list, tuple)):
                        # make sure it is a mutable sequence
                        d = [*d]
                    else:
                        raise TypeError(
                            f"invalid divisions for {name} in "
                            f"{self._category} component definition"
                        )

                for v in d:
                    # check it has a valid type
                    if not isinstance(v, (Number, str)):
                        raise TypeError(
                            f"invalid divisions for {name} in "
                            f"{self._category} component definition"
                        )
                    # check that, if string used, constant exists
                    if isinstance(v, str):
                        if v not in self._constants_info:
                            raise ValueError(
                                f"no constant {v} to use for divisions of "
                                f"state {name} in {self._category} component "
                                f"definition"
                            )

                info['divisions'] = d

    def _check_timedomain(self, timedomain):
        """The purpose of this method is to check that the timedomain is
        of the right type.
        """
        if not isinstance(timedomain, TimeDomain):
            raise TypeError(
                f"not an instance of {TimeDomain.__name__} for {self._category}"
            )

    def _check_spacedomain(self, spacedomain):
        """The purpose of this method is to check that the spacedomain
        is of the right type and that special properties land_sea_mask,
        flow_direction, and cell_area are set if required by component.
        """
        if not isinstance(spacedomain, SpaceDomain):
            raise TypeError(
                f"not an instance of {SpaceDomain.__name__} for {self._category}"
            )

        if not isinstance(spacedomain, Grid):
            raise NotImplementedError(
                f"only {Grid.__name__} currently supported by framework "
                f"for spacedomain"
            )

        for extra in ['land_sea_mask', 'flow_direction', 'cell_area']:
            if getattr(self, '_requires_{}'.format(extra)):
                if getattr(spacedomain, extra) is None:
                    raise RuntimeError(
                        f"'{extra}' must be set in {SpaceDomain.__name__} of "
                        f"{self._category} component '{self.__class__.__name__}'"
                    )

    def _check_dataset(self, dataset):
        # checks for input data

        # check that the dataset is an instance of DataSet
        if not isinstance(dataset, DataSet):

            raise TypeError(
                f"object given for dataset argument of {self._category} "
                f"component '{self.__class__.__name__}' not of type "
                f"{DataSet.__name__}"
            )

        # check data units compatibility with component
        for data_name, data_info in self._inputs_info.items():
            # check that all input data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    f"no data '{data_name}' available in {DataSet.__name__} "
                    f"for {self._category} component '{self.__class__.__name__}'"
                )
            # check that input data units are compliant with component units
            if hasattr(dataset[data_name].field, 'units'):
                if not Units(data_info['units']).equals(
                        Units(dataset[data_name].field.units)):
                    raise ValueError(
                        f"units of variable '{data_name}' in {DataSet.__name__} "
                        f"not equal to units required by {self._category} "
                        f"component '{self.__class__.__name__}': "
                        f"{data_info['units']} required"
                    )
            else:
                raise AttributeError(
                    f"variable '{data_name}' in {DataSet.__name__} for "
                    f"{self._category} component missing 'units' attribute"
                )

    def _check_dataset_space(self, dataset, spacedomain):
        # check space compatibility for input data
        for data_name, data_unit in self._inputs_info.items():
            try:
                dataset[data_name] = Variable(
                    spacedomain.subset_and_compare(dataset[data_name].field),
                    dataset[data_name].filenames
                )
            except RuntimeError:
                raise ValueError(
                    f"spacedomain of data '{data_name}' not compatible with "
                    f"spacedomain of {self._category} component "
                    f"'{self.__class__.__name__}'"
                )

    def _check_dataset_time(self, timedomain):
        # check time compatibility for 'dynamic' input data
        for data_name in self._inputs_info:
            error = ValueError(
                f"timedomain of data '{data_name}' not compatible with "
                f"timedomain of {self._category} component "
                f"'{self.__class__.__name__}'"
            )

            self.datasubset[data_name] = self._check_time(
                self.dataset[data_name], timedomain,
                self._inputs_info[data_name]['kind'], error, self._io_slice,
                frequency=self._inputs_info[data_name].get('frequency')
            )

    @staticmethod
    def _check_time(variable, timedomain, kind, error, reading_slice,
                    frequency=None):
        field = variable.field
        filenames = variable.filenames

        if kind == 'dynamic':
            try:
                variable_subset = DynamicVariable(
                    timedomain.subset_and_compare(field), filenames,
                    reading_slice
                )
            except RuntimeError:
                raise error

        elif kind == 'climatologic':
            lengths = {
                'seasonal': 4,  # DJF-MAM-JJA-SON
                'monthly': 12,  # January to December
                'day_of_year': 366  # Jan 1st to Dec 31st (with Feb 29th)
            }
            if isinstance(frequency, str):
                length = lengths[frequency]
            else:  # isinstance(freq, int):
                length = int(frequency)

            # check that time dimension is of expected length
            if field.construct('time').size != length:
                raise error

            # copy reference for climatologic input data
            variable_subset = ClimatologicVariable(field, filenames)

        else:  # kind == 'static':
            # copy reference for static input data
            if field.has_construct('time'):
                if field.construct('time').size == 1:
                    variable_subset = StaticVariable(field.squeeze('time'),
                                                     filenames)
                else:
                    raise error
            else:
                variable_subset = StaticVariable(field, filenames)

        return variable_subset

    def _check_parameters(self, parameters, spacedomain):
        """Check that parameter values are (convertible to) `cf.Data`
        with right units. Return dictionary with values in place of
        `cf.Data`.
        """
        parameters_ = {}

        if self._parameters_info:
            for name, info in self._parameters_info.items():
                # check presence of value for parameter
                if name not in parameters:
                    raise RuntimeError(
                        f"value missing for parameter {name}"
                    )
                parameter = parameters[name]

                # check parameter type
                if isinstance(parameter, cf.Data):
                    pass
                elif isinstance(parameter, cf.Field):
                    try:
                        parameter = spacedomain.subset_and_compare(parameter)
                    except RuntimeError:
                        raise RuntimeError(
                            f"parameter {name} spatially incompatible"
                        )
                    parameter = parameter.data
                elif isinstance(parameter, (tuple, list)) and len(parameter) == 2:
                    try:
                        parameter = cf.Data(*parameter)
                    except ValueError:
                        raise ValueError(
                            f"parameter {name} not convertible to cf.Data"
                        )
                else:
                    raise TypeError(
                        f"invalid type for parameter {name}"
                    )

                # check parameter units
                if not parameter.get_units(False):
                    raise ValueError(
                        f"missing units for parameter {name}"
                    )
                if not parameter.Units.equals(
                        Units(self._parameters_info[name]['units'])
                ):
                    raise ValueError(
                        f"invalid units for parameter {name}"
                    )

                # check parameter shape (and reshape if scalar-like)
                if parameter.shape == spacedomain.shape:
                    parameter = parameter.array
                else:
                    # check if parameter evaluate as a scalar
                    try:
                        p = parameter.array.item()
                    except ValueError:
                        raise ValueError(
                            f"incompatible shape for parameter {name}"
                        )
                    # assign scalar to newly created array of spacedomain shape
                    parameter = np.zeros(spacedomain.shape, dtype_float())
                    parameter[:] = p

                # assign parameter value in place of cf.Data
                parameters_[name] = parameter

        return parameters_

    def _check_constants(self, constants):
        """If given, check that constant values are (convertible to)
        `cf.Data` with right units. If not given, use constant default
        value from component definition. Return dictionary with values
        in place of `cf.Data`.
        """
        constants_ = {}

        # check if constant value provided, otherwise use default_value
        if self._constants_info:
            for name, info in self._constants_info.items():
                if name not in constants:
                    constants_[name] = info['default_value']
                else:
                    constant = constants[name]

                    # check parameter type
                    if isinstance(constant, cf.Data):
                        pass
                    elif isinstance(constant, (tuple, list)) and len(constant) == 2:
                        try:
                            constant = cf.Data(*constant)
                        except ValueError:
                            raise ValueError(
                                f"constant {name} not convertible to cf.Data"
                            )
                    else:
                        raise TypeError(
                            f"invalid type for constant {name}"
                        )

                    # check parameter units
                    if not constant.get_units(False):
                        raise ValueError(
                            f"missing units for constant {name}"
                        )
                    if not constant.Units.equals(
                            Units(self._constants_info[name]['units'])
                    ):
                        raise ValueError(
                            f"invalid units for constant {name}"
                        )

                    # assign parameter value in place of cf.Data
                    try:
                        constants_[name] = constant.array.item()
                    except ValueError:
                        raise ValueError(
                            f"constant {name} not a scalar"
                        )

        return constants_

    def _use_constants_to_replace_state_divisions(self):
        """Replace component state divisions if specified as a string
        by an integer using component constants.
        """
        for s in self._states_info:
            d = self._states_info[s]['divisions']

            new_d = []
            for v in d:
                if v and isinstance(v, str):
                    # replace string with constant value, cast to integer
                    new_v = int(self.constants[v])
                else:
                    # keep existing value, cast to integer
                    new_v = int(v)

                if new_v <= 0:
                    # cannot have negative dimension for array, also rule out 0
                    raise ValueError(
                        f"{s} divisions dimension must be greater than zero"
                    )
                elif new_v > 1:
                    # do not add dimension if it is 1
                    new_d.append(new_v)

            self._states_info[s]['divisions'] = tuple(new_d)

    @property
    def category(self):
        """Return the part of the water cycle the `Component` represents."""
        return self._category

    @property
    def inwards_info(self):
        """Return the incoming information expected by the `Component`."""
        return deepcopy(self._inwards_info)

    @property
    def outwards_info(self):
        """Return the outgoing information provided by the `Component`."""
        return deepcopy(self._outwards_info)

    @classmethod
    def from_config(cls, cfg):
        # get relevant spacedomain subclass
        spacedomain = getattr(space, cfg['spacedomain']['class'])

        # convert parameters to cf.Field or cf.Data
        parameters = {}
        if cfg.get('parameters'):
            for name, info in cfg['parameters'].items():
                error = ValueError(
                    f"invalid information in YAML for parameter {name}"
                )
                if isinstance(info, (tuple, list)):
                    parameters[name] = cf.Data(*info)
                elif isinstance(info, dict):
                    if info.get('files') and info.get('select'):
                        parameters[name] = (
                            cf.read(info['files']).select_field(info['select'])
                        )
                    else:
                        raise error
                else:
                    raise error

        return cls(
            saving_directory=cfg['saving_directory'],
            timedomain=TimeDomain.from_config(cfg['timedomain']),
            spacedomain=spacedomain.from_config(cfg['spacedomain']),
            dataset=DataSet.from_config(cfg.get('dataset')),
            parameters=parameters,
            constants=cfg.get('constants'),
            records=cfg.get('records'),
            io_slice=cfg.get('io_slice', None)
        )

    def to_config(self):
        # get parameters and constants as tuple (value, unit)
        parameters = {}
        if self.parameters:
            for name, value in self.parameters.items():
                original = self._pristine_parameters[name]
                if isinstance(original, cf.Field):
                    if original.data.get_filenames():
                        # comes from a file, point to it
                        parameters[name] = {
                            'files': original.data.get_filenames(),
                            'select': original.identity()
                        }
                    else:
                        # create a new file for it
                        filename = sep.join(
                            [self.saving_directory,
                             '_'.join([self.identifier, self._category, name])
                             + ".nc"]
                        )
                        cf.write(original, filename)
                        # point to it
                        parameters[name] = {
                            'files': [filename],
                            'select': original.identity()
                        }
                else:
                    if np.amin(value) == np.amax(value):
                        # can be stored as a scalar
                        parameters[name] = (np.mean(value).item(),
                                            self._parameters_info[name]['units'])
                    else:
                        # must be stored as a cf.Field in new file
                        field = self.spacedomain.to_field()
                        field.data[:] = original
                        field.long_name = name
                        # create a new file for it
                        filename = sep.join(
                            [self.saving_directory,
                             '_'.join([self.identifier, self._category, name])
                             + ".nc"]
                        )
                        cf.write(original, filename)
                        # point to it
                        parameters[name] = {
                            'files': [filename],
                            'select': field.identity()
                        }

        constants = {}
        if self.constants:
            for name, value in self.constants.items():
                constants[name] = (value, self._constants_info[name]['units'])

        cfg = {
            'module': self.__module__,
            'class': self.__class__.__name__,
            'saving_directory': self.saving_directory,
            'timedomain': self.timedomain.to_config(),
            'spacedomain': self.spacedomain.to_config(),
            'dataset': self.dataset.to_config(),
            'parameters': parameters if parameters else None,
            'constants': constants if constants else None,
            'records': self.records if self.records else None,
            'io_slice': self._io_slice
        }
        return cfg

    def get_spin_up_timedomain(self, start, end):
        if ((end - start)
                % self.timedomain.timedelta).total_seconds() != 0:
            raise RuntimeError(
                f"spin up start-end incompatible with {self._category} "
                f"component timedelta"
            )

        timedomain = TimeDomain.from_start_end_step(
            start, end, self.timedomain.timedelta,
            self.timedomain.units,
            self.timedomain.calendar
        )

        return timedomain

    def __str__(self):
        shape = ', '.join([f"{ax}: {ln}" for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])

        records = [f"        {o}: {d} {m}"
                   for o, f in self.records.items()
                   for d, m in f.items()] if self.records else []

        return "\n".join(
            [f"{self.__class__.__name__}("]
            + [f"    category: {self._category}"]
            + [f"    saving directory: {self.saving_directory}"]
            + [f"    timedomain: period: {self.timedomain.period}"]
            + [f"    spacedomain: shape: ({shape})"]
            + (["    records:"] if records else []) + records
            + [")"]
        )

    def initialise_(self, tag, overwrite):
        # if states not already initialised, instantiate them
        if not self._initialised_states:
            self._instantiate_states()

        # reset time for data slices
        # (because component may have already be run, the slices in
        #  the data would not point to the beginning of the array, and
        #  they need to for this new run)
        for d in self._inputs_info:
            self.datasubset[d].reset_time()

        # collect inputs for first time step (i.e. time index 0)
        inputs = {d: self.datasubset[d][0] for d in self._inputs_info}

        # reset time for data slices
        # (because of the input collection just above, the slices
        #  iterator in the data has been triggered, so it needs to be
        #  reset for the actual run to follow)
        for d in self._inputs_info:
            self.datasubset[d].reset_time()

        # initialise component
        self.initialise(
            **inputs, **self.parameters, **self.constants, **self.states
        )
        self._initialised_states = True

        # create dump file for given run
        self._initialise_states_dump(tag, overwrite)

        if self.records:
            if not self._revived_streams:
                self._initialise_record_streams()
            # need to reset flag to False because Component may be
            # re-used for another spin cycle / simulation run and
            # it needs for its streams to be properly re-initialised
            # (its trackers in particular)
            self._revived_streams = False
            # optionally create files and dump files
            self._create_stream_files_and_dumps(tag, overwrite)

    def run_(self, timeindex, exchanger):
        data = {}
        # collect required input data from dataset
        for d in self._inputs_info:
            data[d] = self.datasubset[d][timeindex]

        # determine current datetime in simulation
        self._current_datetime = self._datetime_array[timeindex]

        # collect required transfers from exchanger
        for d in self._inwards_info:
            data[d] = exchanger.get_transfer(d, self._category)

        # run simulation for the component
        to_exchanger, outputs = self.run(
            **self.parameters, **self.constants, **self.states, **data
        )

        # store variables to record
        for name in self._records:
            self._record_objects[name](self.states, to_exchanger, outputs)

        # increment the component's states by one timestep
        self.increment_states()

        return to_exchanger

    def finalise_(self):
        timestamp = self.timedomain.bounds.array[-1, -1]
        update_states_dump(sep.join([self.saving_directory, self.dump_file]),
                           self.states, timestamp, self._solver_history)
        self.finalise(**self.parameters, **self.constants, **self.states)

    def _instantiate_states(self):
        # get a State object for each state and initialise to zero
        for s in self._states_info:
            d = self._states_info[s].get('divisions')
            o = self._states_info[s].get('order', array_order())
            self.states[s] = State(
                np.zeros(
                    (self._solver_history + 1, *self.spaceshape, *d),
                    dtype_float(), order=o
                ),
                order=o
            )

    def _initialise_states_dump(self, tag, overwrite):
        self.dump_file = '_'.join([self.identifier, self._category,
                                   tag, 'dump_states.nc'])
        if (overwrite or not path.exists(sep.join([self.saving_directory,
                                                   self.dump_file]))):
            create_states_dump(sep.join([self.saving_directory, self.dump_file]),
                               self._states_info, self._solver_history,
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
        states, at = load_states_dump(dump_file, at, self._states_info)
        for s in self._states_info:
            if s in states:
                o = self._states_info[s].get('order', array_order())
                self.states[s] = State(states[s], order=o)
            else:
                raise KeyError(f"initial conditions for {self._category} "
                               f"component state '{s}' not in dump")
        self._initialised_states = True

        return at

    def increment_states(self):
        for s in self.states:
            self.states[s].increment()

    def dump_states(self, timeindex):
        timestamp = self.timedomain.bounds.array[timeindex, 0]
        update_states_dump(sep.join([self.saving_directory, self.dump_file]),
                           self.states, timestamp, self._solver_history)

    def _initialise_record_streams(self):
        for delta, stream in self._record_streams.items():
            # (re)initialise record stream time attributes
            stream.initialise(self.timedomain, self.spacedomain)

    def _create_stream_files_and_dumps(self, tag, overwrite):
        for delta, stream in self._record_streams.items():
            # initialise record files
            filename = '_'.join([self.identifier, self._category, tag,
                                 'records', stream.frequency_tag])
            file_ = sep.join([self.saving_directory, filename + '.nc'])

            if overwrite or not path.exists(file_):
                stream.create_record_stream_file(file_)
            else:
                stream.file = file_

            # initialise stream dumps
            filename = '_'.join([self.identifier, self._category, tag,
                                 'dump_record_stream', stream.frequency_tag])
            file_ = sep.join([self.saving_directory, filename + '.nc'])

            if overwrite or not path.exists(file_):
                stream.create_record_stream_dump(file_)
            else:
                stream.dump_file = file_

    def revive_record_streams_from_dump(self, dump_file_pattern,
                                        timedomain=None, at=None):
        """Revive the record streams of the Component from a dump file.

        :Parameters:

            dump_filepath_pattern: `str`
                A string providing the path to the netCDF dump file
                containing values to be used as initial conditions for
                the record streams of the Component. Note, curly
                brackets {} should be used where the record stream delta
                should be used.

                *Parameter example:* ::

                    dump_file_pattern='out/dummy_surfacelayer_run_'
                                      'dump_record_stream_{}.nc'

            timedomain: `TimeDomain`, optional
                This is required if the run to be revived is a spin-up
                one. Indeed, until the `spin_up` method is called, the
                `TimeDomain` of the `Component` is the one of its main
                run.

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
                The snapshot in time that was used for reviving the
                record streams.

        """
        ats = []

        if self.records:
            for delta, stream in self._record_streams.items():
                file_ = dump_file_pattern.format(stream.frequency_tag)
                ats.append(stream.load_record_stream_dump(
                    file_, at, timedomain or self.timedomain, self.spacedomain
                ))
        self._revived_streams = True

        return ats

    def dump_record_streams(self, timeindex):
        timestamp = self.timedomain.bounds.array[timeindex, 0]
        if self.records:
            for delta, stream in self._record_streams.items():
                stream.update_record_stream_dump(timestamp)

    @abc.abstractmethod
    def initialise(self, **kwargs):
        raise NotImplementedError(
            f"{self._category} class '{self.__class__.__name__}' "
            f"missing an 'initialise' method"
        )

    @abc.abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError(
            f"{self._category} class '{self.__class__.__name__}' "
            f"missing a 'run' method"
        )

    @abc.abstractmethod
    def finalise(self, **kwargs):
        raise NotImplementedError(
            f"{self._category} class '{self.__class__.__name__}' "
            f"missing a 'finalise' method"
        )


class SurfaceLayerComponent(Component, metaclass=abc.ABCMeta):
    """The SurfaceLayerComponent is simulating the hydrological
    processes in the surface layer compartment of the hydrological
    cycle.
    """
    _category = 'surfacelayer'
    _inwards_info = {
        'soil_water_stress_for_transpiration': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        },
        'soil_water_stress_for_direct_soil_evaporation': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        },
        'standing_water_area_fraction': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        },
        'total_water_area_fraction': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'canopy_liquid_throughfall_and_snow_melt_flux': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'transpiration_flux_from_root_uptake': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'direct_water_evaporation_flux_from_soil': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'water_evaporation_flux_from_standing_water': {
            'units': 'kg m-2 s-1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'water_evaporation_flux_from_open_water': {
            'units': 'kg m-2 s-1',
            'to': ['openwater'],
            'method': 'mean'
        },
        'direct_throughfall_flux': {
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
        'canopy_liquid_throughfall_and_snow_melt_flux': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'transpiration_flux_from_root_uptake': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'direct_water_evaporation_flux_from_soil': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'water_evaporation_flux_from_standing_water': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'open_water_area_fraction': {
            'units': '1',
            'from': 'openwater',
            'method': 'mean'
        },
        'open_water_surface_height': {
            'units': 'm',
            'from': 'openwater',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'soil_water_stress_for_transpiration': {
            'units': '1',
            'to': ['surfacelayer'],
            'method': 'mean'
        },
        'soil_water_stress_for_direct_soil_evaporation': {
            'units': '1',
            'to': ['surfacelayer'],
            'method': 'mean'
        },
        'standing_water_area_fraction': {
            'units': '1',
            'to': ['surfacelayer'],
            'method': 'mean'
        },
        'total_water_area_fraction': {
            'units': '1',
            'to': ['surfacelayer'],
            'method': 'mean'
        },
        'surface_runoff_flux_delivered_to_rivers': {
            'units': 'kg m-2 s-1',
            'to': ['openwater'],
            'method': 'mean'
        },
        'net_groundwater_flux_to_rivers': {
            'units': 'kg m-2 s-1',
            'to': ['openwater'],
            'method': 'mean'
        }
    }


class OpenWaterComponent(Component, metaclass=abc.ABCMeta):
    """The OpenWaterComponent is simulating the hydrological processes
    in the open water compartment of the hydrological cycle.
    """
    _category = 'openwater'
    _inwards_info = {
        'water_evaporation_flux_from_open_water': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'direct_throughfall_flux': {
            'units': 'kg m-2 s-1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'surface_runoff_flux_delivered_to_rivers': {
            'units': 'kg m-2 s-1',
            'from': 'subsurface',
            'method': 'mean'
        },
        'net_groundwater_flux_to_rivers': {
            'units': 'kg m-2 s-1',
            'from': 'subsurface',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'open_water_area_fraction': {
            'units': '1',
            'to': ['subsurface'],
            'method': 'mean'
        },
        'open_water_surface_height': {
            'units': 'm',
            'to': ['subsurface'],
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
    _solver_history = 0

    def __init__(self, timedomain, spacedomain, dataset, substituting_class,
                 io_slice=None):
        """**Instantiation**

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

            io_slice: `int`, optional
                The length of the time slice to use for input/output
                operations. This corresponds to the number of component
                timesteps to read/write at once. If not set, its default
                value is 100 (arbitrary).

        """
        # store class being substituted for config
        self._substituting_class = substituting_class

        # override category to the one of substituting component
        self._category = substituting_class.category

        # override outwards with the ones of component being substituted
        self._outwards = set(substituting_class.outwards_info.keys())
        self._outwards_info = substituting_class.outwards_info

        # override inputs info with the outwards of component being
        # substituted (so that the dataset is checked for time and space
        # compatibility as a 'standard' dataset would be)
        self._inputs_info = substituting_class.outwards_info

        # initialise as a Component
        super(DataComponent, self).__init__(None, timedomain, spacedomain,
                                            dataset, io_slice=io_slice)

    def __str__(self):
        shape = ', '.join([f"{ax}: {ln}" for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])
        return "\n".join(
            [f"{self.__class__.__name__}("]
            + [f"    category: {self._category}"]
            + [f"    timedomain: period: {self.timedomain.period}"]
            + [f"    spacedomain: shape: ({shape})"]
            + [f"    dataset: {len(self.dataset)} variable(s)"]
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
            substituting_class=substituting_class,
            io_slice=cfg.get('io_slice', None)
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
            },
            'io_slice': self._io_slice
        }
        return cfg

    def initialise_(self, *args, **kwargs):
        # reset time for data slices
        for d in self._inputs_info:
            self.datasubset[d].reset_time()

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
    _solver_history = 0

    def __init__(self, timedomain, spacedomain, substituting_class):
        """**Instantiation**

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
        self._category = substituting_class.category

        # override inwards and outwards with the ones of component
        # being substituted
        self._outwards = set(substituting_class.outwards_info.keys())
        self._outwards_info = substituting_class.outwards_info

        # initialise as a Component
        super(NullComponent, self).__init__(None, timedomain, spacedomain)

    def __str__(self):
        shape = ', '.join([f"{ax}: {ln}" for ax, ln in
                           zip(self.spacedomain.axes, self.spaceshape)])
        return "\n".join(
            [f"{self.__class__.__name__}("]
            + [f"    category: {self._category}"]
            + [f"    timedomain: period: {self.timedomain.period}"]
            + [f"    spacedomain: shape: ({shape})"]
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
