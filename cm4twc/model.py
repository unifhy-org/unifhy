from cfunits import Units

from .time_ import TimeDomain, Clock
from .space_ import SpaceDomain, Grid
from .data_ import DataSet
from .components import SurfaceLayerComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NullComponent, _Component


class Model(object):
    """
    DOCSTRING REQUIRED
    """

    def __init__(self, surfacelayer, subsurface, openwater):

        self._surfacelayer = self._process_component_type(
            surfacelayer, SurfaceLayerComponent)

        self._subsurface = self._process_component_type(
            subsurface, SubSurfaceComponent)

        self._openwater = self._process_component_type(
            openwater, OpenWaterComponent)

    def simulate(self, surfacelayer_domain, subsurface_domain,
                 openwater_domain, surfacelayer_data=None,
                 subsurface_data=None, openwater_data=None,
                 surfacelayer_parameters=None, subsurface_parameters=None,
                 openwater_parameters=None):
        """
        DOCSTRING REQUIRED
        """

        # check that the context given for each component is a tuple
        # (TimeDomain instance, SpaceDomain instance)
        self._check_component_domain(self._surfacelayer, *surfacelayer_domain)
        self._check_component_domain(self._subsurface, *subsurface_domain)
        self._check_component_domain(self._openwater, *openwater_domain)

        if (surfacelayer_domain[0] != subsurface_domain[0]) \
                or (surfacelayer_domain[0] != openwater_domain[0]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeDomains.")

        if (surfacelayer_domain[1] != subsurface_domain[1]) \
                or (surfacelayer_domain[1] != openwater_domain[1]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

        # assign the domains to the components
        self._surfacelayer.timedomain, self._surfacelayer.spacedomain = \
            surfacelayer_domain
        self._subsurface.timedomain, self._subsurface.spacedomain = \
            subsurface_domain
        self._openwater.timedomain, self._openwater.spacedomain = \
            openwater_domain

        # check that the required parameters are provided
        if not surfacelayer_parameters:
            surfacelayer_parameters = {}
        self._check_component_parameters(self._surfacelayer, surfacelayer_parameters)
        if not subsurface_parameters:
            subsurface_parameters = {}
        self._check_component_parameters(self._subsurface, subsurface_parameters)
        if not openwater_parameters:
            openwater_parameters = {}
        self._check_component_parameters(self._openwater, openwater_parameters)

        # check that the required data is available in a DataSet instance
        if not surfacelayer_data:
            surfacelayer_data = DataSet()
        self._check_component_data(self._surfacelayer, surfacelayer_data,
                                   *surfacelayer_domain)
        if not subsurface_data:
            subsurface_data = DataSet()
        self._check_component_data(self._subsurface, subsurface_data,
                                   *subsurface_domain)
        if not openwater_data:
            openwater_data = DataSet()
        self._check_component_data(self._openwater, openwater_data,
                                   *openwater_domain)

        # set up clock responsible for the time-stepping schemes
        clock = Clock(surfacelayer_timedomain=surfacelayer_domain[0],
                      subsurface_timedomain=subsurface_domain[0],
                      openwater_timedomain=openwater_domain[0])

        # set up interface responsible for exchanges between components
        interface = {}

        # initialise components
        interface.update(
            self._surfacelayer.initialise()
        )

        interface.update(
            self._subsurface.initialise()
        )

        interface.update(
            self._openwater.initialise()
        )

        # run components
        for run_surfacelayer, run_subsurface, run_openwater in clock:

            timeindex = clock.get_current_timeindex()
            datetime = clock.get_current_datetime()

            if run_surfacelayer:
                interface.update(
                    self._surfacelayer(
                        timeindex=timeindex,
                        datetime=datetime,
                        dataset=surfacelayer_data,
                        **surfacelayer_parameters,
                        **interface
                    )
                )

            if run_subsurface:
                interface.update(
                    self._subsurface(
                        timeindex=timeindex,
                        datetime=datetime,
                        dataset=subsurface_data,
                        **subsurface_parameters,
                        **interface
                    )
                )

            if run_openwater:
                interface.update(
                    self._openwater(
                        timeindex=timeindex,
                        datetime=datetime,
                        dataset=openwater_data,
                        **openwater_parameters,
                        **interface
                    )
                )

        # finalise components
        self._surfacelayer.finalise(**interface)

        self._subsurface.finalise(**interface)

        self._openwater.finalise(**interface)

        return interface

    @staticmethod
    def _process_component_type(component, expected_component):

        if issubclass(component, expected_component):
            # check inwards interface
            # check outwards interface
            return component()
        elif issubclass(component, (DataComponent, NullComponent)):
            return component(expected_component)
        else:
            raise TypeError(
                "The '{}' component given must either be a subclass of the "
                "class {}, the class {}, or the class {}.".format(
                    expected_component.category,
                    SurfaceLayerComponent.__name__, DataComponent.__name__,
                    NullComponent.__name__)
            )

    @staticmethod
    def _check_component_domain(component, timedomain, spacedomain):
        """
        The purpose of this method is to check that the elements in the
        tuple given for a given component category are of the right type
        (i.e. ([TimeDomain] instance and [SpaceDomain] instance)

        :param component: instance of the component whose domain is
        being checked
        :type component: _Component
        :param timedomain: object being given as 1st element of the domain
        tuple during the call of the [simulate] method for the given component
        :type timedomain: object
        :param spacedomain: object being given as 2nd element of the domain
        tuple during the call of the [simulate] method for the given component
        :type spacedomain: object

        :return: None
        """
        if not isinstance(timedomain, TimeDomain):
            raise TypeError("The 1st domain item for the '{}' component "
                            "must be an instance of {}.".format(
                                component.category, TimeDomain.__name__))

        if not isinstance(spacedomain, SpaceDomain):
            raise TypeError("The 2nd domain item for the '{}' component "
                            "must be an instance of {}.".format(
                                component.category, TimeDomain.__name__))
        else:
            if not isinstance(spacedomain, Grid):
                raise NotImplementedError("The only {} subclass currently "
                                          "supported by the framework is "
                                          "{}.".format(SpaceDomain.__name__,
                                                       Grid.__name__))

    @staticmethod
    def _check_component_parameters(component, parameters):
        """
        The purpose of this method is to check that parameter values are given
        for the corresponding component.

        :param component: instance of the component whose domain is
        being checked
        :type component: _Component
        :param parameters: a dictionary containing the parameter values given
        during the call of the [simulate] method for the given component
        :type parameters: dict

        :return: None
        """

        # check that all parameters are provided
        if not all([i in parameters for i in component.parameters_info]):
            raise RuntimeError(
                "One or more parameters are missing in {} component '{}': "
                "{} are all required.".format(
                    component.category, component.__class__.__name__,
                    component.parameters_info)
            )

    @staticmethod
    def _check_component_data(component, dataset, timedomain, spacedomain):
        """
        The purpose of this method is to check that:
            - the object given for the dataset is an instance of [DataSet]
            - the dataset contains [Variable] instances for all the driving
            and ancillary data the component requires
            - the domain of each variable complies with the component's domain

        :param component: instance of the component whose data is being checked
        :type component: _Component
        :param dataset: object being given as the dataset for the given
        component category
        :type dataset: object
        :param timedomain: instance of [TimeDomain] for the given
        component category
        :type timedomain: TimeDomain
        :param spacedomain: instance of [SpaceDomain] for the given
        component category
        :type spacedomain: SpaceDomain

        :return: None
        """

        # check that the data is an instance of DataSet
        if not isinstance(dataset, DataSet):
            raise TypeError(
                "The dataset object given for the {} component '{}' must "
                "be an instance of {}.".format(
                    component.category, component.__class__.__name__,
                    DataSet.__name__))

        # check driving data for time and space compatibility with component
        for data_name, data_unit in component.driving_data_info.items():
            # check that all driving data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "There is no data '{}' available in the {} "
                    "for the {} component '{}'.".format(
                        data_name, DataSet.__name__, component.category,
                        component.__class__.__name__))
            # check that driving data units are compliant with component units
            if hasattr(dataset[data_name], 'units'):
                if not Units(data_unit).equals(
                        Units(dataset[data_name].units)):
                    raise ValueError(
                        "The units of the variable '{}' in the {} {} "
                        "are not equal to the units required by the {} "
                        "component '{}': {} are required.".format(
                            data_name, component.category, DataSet.__name__,
                            component.category, component.__class__.__name__,
                            data_unit))
            else:
                raise AttributeError("The variable '{}' in the {} for "
                                     "the {} component is missing a 'units' "
                                     "attribute.".format(data_name,
                                                         DataSet.__name__,
                                                         component.category))

            # check that the data and component time domains are compatible
            # using _truncation=-1 to remove requirement for last datetime
            # of TimeDomain to be available which is not required
            if not timedomain.is_time_equal_to(dataset[data_name],
                                               _trailing_truncation_idx=-1):
                raise ValueError(
                    "The time domain of the data '{}' is not compatible with "
                    "the time domain of the {} component '{}'.".format(
                        data_name, component.category,
                        component.__class__.__name__))
            # check that the data and component space domains are compatible
            if not spacedomain.is_matched_in(dataset[data_name]):
                raise ValueError(
                    "The space domain of the data '{}' is not compatible with "
                    "the space domain of the {} component '{}'.".format(
                        data_name, component.category,
                        component.__class__.__name__))

        # check ancillary data for space compatibility with component
        for data_name, data_unit in component.ancil_data_info.items():
            # check that all ancillary data are available in DataSet
            if data_name not in dataset:
                raise KeyError(
                    "There is no data '{}' available in the {} "
                    "for the {} component '{}'.".format(
                        data_name, DataSet.__name__, component.category,
                        component.__class__.__name__))
            # check that driving data units are compliant with component units
            if hasattr(dataset[data_name], 'units'):
                if not Units(data_unit).equals(
                        Units(dataset[data_name].units)):
                    raise ValueError(
                        "The units of the variable '{}' in the {} {} "
                        "are not equal to the units required by the {} "
                        "component '{}': {} are required.".format(
                            data_name, component.category, DataSet.__name__,
                            component.category, component.__class__.__name__,
                            data_unit))
            else:
                raise AttributeError("The variable '{}' in the {} for "
                                     "the {} component is missing a 'units' "
                                     "attribute.".format(data_name,
                                                         DataSet.__name__,
                                                         component.category))
            # check that the data and component space domains are compatible
            if not spacedomain.is_matched_in(dataset[data_name]):
                raise ValueError(
                    "The space domain of the data '{}' is not compatible with "
                    "the space domain of the {} component '{}'.".format(
                        data_name, component.category,
                        component.__class__.__name__))
