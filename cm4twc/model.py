from inspect import isclass

from .time_ import TimeDomain
from .space_ import SpaceDomain, Grid
from .data_ import DataBase
from .components import SurfaceComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NoneComponent, Component


class Model(object):
    """
    DOCSTRING REQUIRED
    """

    _cat_to_class = {
        'surface': SurfaceComponent,
        'subsurface': SubSurfaceComponent,
        'openwater': OpenWaterComponent,
    }

    def __init__(self, surface, subsurface, openwater):

        given = {
            'surface': surface,
            'subsurface': subsurface,
            'openwater': openwater,
        }

        # check if any component is actually meant to simulate anything
        if all([comp is None for cat, comp in given.items()]):
            raise UserWarning("Trying to instantiate a Model without any "
                              "meaningful component (i.e. all are None).")

        inferred = {
            'surface': self._infer_component_class(surface),
            'subsurface': self._infer_component_class(subsurface),
            'openwater': self._infer_component_class(openwater),
        }

        self._surface = self._instantiate_component_with_depend_checks(
            'surface', given, inferred
        )

        self._subsurface = self._instantiate_component_with_depend_checks(
            'subsurface', given, inferred
        )

        self._openwater = self._instantiate_component_with_depend_checks(
            'openwater', given, inferred
        )

    def simulate(self, surface_domain, surface_data, surface_parameters,
                 subsurface_domain, subsurface_data, subsurface_parameters,
                 openwater_domain, openwater_data, openwater_parameters):
        """
        DOCSTRING REQUIRED
        """

        # check that the context given for each component is a tuple
        # (TimeDomain instance, SpaceDomain instance)
        self._check_component_domain(self._surface, *surface_domain)
        self._check_component_domain(self._subsurface, *subsurface_domain)
        self._check_component_domain(self._openwater, *openwater_domain)

        if (surface_domain[0] != subsurface_domain[0]) \
                or (surface_domain[0] != openwater_domain[0]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeDomains.")

        if (surface_domain[1] != subsurface_domain[1]) \
                or (surface_domain[1] != openwater_domain[1]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

        # check that the required parameters are provided
        self._check_component_parameters(self._surface, surface_parameters)
        self._check_component_parameters(self._subsurface, subsurface_parameters)
        self._check_component_parameters(self._openwater, openwater_parameters)

        # check that the required data is available in a DataBase instance
        self._check_component_data(self._surface, surface_data,
                                   *surface_domain)
        self._check_component_data(self._subsurface, subsurface_data,
                                   *subsurface_domain)
        self._check_component_data(self._openwater, openwater_data,
                                   *openwater_domain)

        interface_ = {}

        interface_.update(
            self._surface(
                *surface_domain,
                db=surface_data,
                **surface_parameters,
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

    def _instantiate_component_with_depend_checks(self, category,
                                                  given, inferred):
        """
        The purpose of this method is to instantiate a given component
        after some checks on its compatibility with other components:
            - if a subclass of [Component] is given for the component,
            check that this is a subclass of the relevant class (e.g.
            [SurfaceComponent] if given for the [surface] argument) ;
            - if a [DataBase] is given for the component, check that the
            components depending on it require data (i.e. they are not
            all [DataComponent] or [NoneComponent]) ;
            - if [None] is given for the component, check that the
            components depending on it do not require data (i.e. they
            are all [NoneComponent]).

        Once these checks are done, an instance of [DataComponent],
        [NoneComponent], or a "genuine" [Component] (e.g.
        [SurfaceComponent], [SubSurfaceComponent], etc.) is returned.

        :param category: name of the component category
        :type category: str
        :param given: dictionary of objects given during instantiation
        of [Model] - keys: component category / values: object
        :type given: dict
        :param inferred: dictionary of classes previously inferred from
        given objects - keys: component category /
                        values: subclass of [Component]
        :type inferred: dict

        :return: instance of Component
        :rtype: Component
        """
        given_object = given[category]
        inferred_class = inferred[category]
        expected_class = self._cat_to_class[category]

        if issubclass(inferred_class, DataComponent):
            # not expecting to get data for this component
            # if not required by its dependencies
            if not all([issubclass(inferred[down_],
                                   (DataComponent, NoneComponent))
                        for down_ in expected_class.get_downwards()]):

                required_data = (
                    data_ for down_ in inferred_class.get_downwards()
                    if not issubclass(inferred[down_],
                                      (DataComponent, NoneComponent))
                    for data_ in self._cat_to_class[down_].get_inwards()
                    if data_ in expected_class.get_outwards())
                # return an instance of DataComponent which will only be
                # instantiated successfully if the data required its
                # dependencies are available in the DataBase
                return DataComponent(category, given_object, required_data)
            else:
                raise UserWarning(
                    "The given {} component is a DataBase, "
                    "but no other component depending on it "
                    "requires any data.".format(category)
                )
        elif issubclass(inferred_class, NoneComponent):
            # can only be a NoneComponent if any component which depends
            # on this component is a NoneComponent or a DataComponent
            if all([issubclass(inferred[down_],
                               (DataComponent, NoneComponent))
                    for down_ in expected_class.get_downwards()]):
                return NoneComponent()
            else:
                raise TypeError(
                    "The given {} component is None but other components "
                    "depending on it are not None.".format(category)
                )
        elif issubclass(inferred_class, expected_class):
            # matching types, proceed with instantiation without further ado
            return given_object()
        else:
            raise TypeError(
                "The {} component given must either be a subclass of the "
                "class {}, an instance of DataBase (if relevant), or None "
                "(if possible).".format(category, expected_class.__name__)
            )

    @staticmethod
    def _infer_component_class(given_object):
        """
        The purpose of this method is to return a class not matter what
        is given during the instantiation of the [Model] object.

        Only three objects are supported for instantiating a [Component]
        of [Model]:
            - a subclass of [Component] (e.g. [SurfaceComponent],
            [SubSurfaceComponent], etc.) ;
            - an instance of [DataBase] ;
            - [None].

        If anything else is given, the method returns the class [type].

        :param given_object: object given during instantiation of [Model]
        :return: a subclass of [Component] or type if object given
        is unsupported
        :rtype: type
        """
        if given_object is None:
            return NoneComponent
        elif isclass(given_object):
            if issubclass(given_object, Component):
                return given_object
            else:
                return type
        elif isinstance(given_object, DataBase):
            return DataComponent
        else:
            return type

    @staticmethod
    def _check_component_domain(component, timedomain, spacedomain):
        """
        The purpose of this method is to check that the elements in the
        tuple given for a given component category are of the right type
        (i.e. ([TimeDomain] instance and [SpaceDomain] instance)

        :param component: instance of the component whose domain is
        being checked
        :type component: Component
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
        :type component: Component
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
        :type component: Component
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
