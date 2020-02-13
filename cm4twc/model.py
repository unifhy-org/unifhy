from inspect import isclass

from .time_ import TimeDomain
from .space_ import SpaceDomain, Grid
from .data_ import DataBase
from .components import SurfaceLayerComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NullComponent, _Component


class Model(object):
    """
    DOCSTRING REQUIRED
    """

    _cat_to_class = {
        'surfacelayer': SurfaceLayerComponent,
        'subsurface': SubSurfaceComponent,
        'openwater': OpenWaterComponent,
    }

    def __init__(self, surfacelayer, subsurface, openwater):

        self._surfacelayer = self._process_component_type(
            surfacelayer, SurfaceLayerComponent)

        self._subsurface = self._process_component_type(
            subsurface, SubSurfaceComponent)

        self._openwater = self._process_component_type(
            openwater, OpenWaterComponent)

    def simulate(self, surfacelayer_domain, surfacelayer_data,
                 surfacelayer_parameters, subsurface_domain, subsurface_data,
                 subsurface_parameters, openwater_domain, openwater_data,
                 openwater_parameters):
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

        # check that the required parameters are provided
        self._check_component_parameters(self._surfacelayer, surfacelayer_parameters)
        self._check_component_parameters(self._subsurface, subsurface_parameters)
        self._check_component_parameters(self._openwater, openwater_parameters)

        # check that the required data is available in a DataBase instance
        self._check_component_data(self._surfacelayer, surfacelayer_data,
                                   *surfacelayer_domain)
        self._check_component_data(self._subsurface, subsurface_data,
                                   *subsurface_domain)
        self._check_component_data(self._openwater, openwater_data,
                                   *openwater_domain)

        interface_ = {}

        interface_.update(
            self._surfacelayer(
                *surfacelayer_domain,
                db=surfacelayer_data,
                **surfacelayer_parameters,
                **interface_
            )
        )

        interface_.update(
            self._subsurface(
                *subsurface_domain,
                db=subsurface_data,
                **subsurface_parameters,
                **interface_
            )
        )

        interface_.update(
            self._openwater(
                *openwater_domain,
                db=openwater_data,
                **openwater_parameters,
                **interface_
            )
        )

        return interface_

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
        if not all([i in parameters for i in component.parameter_names]):
            raise RuntimeError(
                "One or more parameters are missing in {} component '{}': "
                "{} are all required.".format(
                    component.category, component.__class__.__name__,
                    component.parameter_names)
            )

    @staticmethod
    def _check_component_data(component, database, timedomain, spacedomain):
        """
        The purpose of this method is to check that:
            - the object given for the database is an instance of [DataBase]
            - the database contains [Variable] instances for all the driving
            and ancillary data the component requires
            - the domain of each variable complies with the component's domain

        :param component: instance of the component whose data is being checked
        :type component: _Component
        :param database: object being given as the database for the given
        component category
        :type database: object
        :param timedomain: instance of [TimeDomain] for the given
        component category
        :type timedomain: TimeDomain
        :param spacedomain: instance of [SpaceDomain] for the given
        component category
        :type spacedomain: SpaceDomain

        :return: None
        """

        # check that the data is an instance of DataBase
        if not isinstance(database, DataBase):
            raise TypeError("The database object given for the '{}' component "
                            "must be an instance of {}.".format(
                                component.category, DataBase.__name__))

        # check driving data for time and space compatibility with component
        for data in component.driving_data_names:
            # check that all driving data are available in DataBase
            if data not in database:
                raise KeyError(
                    "There is no data '{}' available in the database "
                    "for the {} component '{}'.".format(
                        data, component.category,
                        component.__class__.__name__))
            # check that the data and component time domains are compatible
            if not timedomain.is_matched_in(database[data]):
                raise ValueError(
                    "The time domain of the data '{}' is not compatible with "
                    "the time domain of the {} component '{}'.".format(
                        data, component.category,
                        component.__class__.__name__))
            # check that the data and component space domains are compatible
            if not spacedomain.is_matched_in(database[data]):
                raise ValueError(
                    "The space domain of the data '{}' is not compatible with "
                    "the space domain of the {} component '{}'.".format(
                        data, component.category,
                        component.__class__.__name__))

        # check ancillary data for space compatibility with component
        for data in component.ancil_data_names:
            # check that all ancillary data are available in DataBase
            if data not in database:
                raise KeyError(
                    "There is no data '{}' available in the database "
                    "for the {} component '{}'.".format(
                        data, component.category,
                        component.__class__.__name__))
            # check that the data and component space domains are compatible
            if not spacedomain.is_matched_in(database[data]):
                raise ValueError(
                    "The space domain of the data '{}' is not compatible with "
                    "the space domain of the {} component '{}'.".format(
                        data, component.category,
                        component.__class__.__name__))
