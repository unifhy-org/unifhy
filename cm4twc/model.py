from inspect import isclass

from .time_ import TimeFrame
from .space_ import SpaceDomain, Network
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

        # check if any component is actually meant to simulate something
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

    def simulate(self, surface_context, surface_parameters,
                 subsurface_context, subsurface_parameters,
                 openwater_context, openwater_parameters):
        """
        DOCSTRING REQUIRED
        """

        # check that the context given for each component is a tuple
        # (TimeFrame instance, SpaceDomain instance, DataBase instance)
        self._check_modelling_context('surface', *surface_context)
        self._check_modelling_context('subsurface', *subsurface_context)
        self._check_modelling_context('openwater', *openwater_context)

        if (surface_context[0] != subsurface_context[0]) \
                or (surface_context[0] != openwater_context[0]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeFrames.")

        if (surface_context[1] != subsurface_context[1]) \
                or (surface_context[1] != openwater_context[1]):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

        out_surface = self._surface(
            *surface_context,
            **surface_parameters
        )

        out_subsurface = self._subsurface(
            *subsurface_context,
            **subsurface_parameters,
            **out_surface
        )

        out_openwater = self._openwater(
            *openwater_context,
            **openwater_parameters,
            **out_surface, **out_subsurface
        )

        return out_surface, out_subsurface, out_openwater

    def _instantiate_component_with_depend_checks(self, category,
                                                  given, inferred):
        """
        The purpose of this method is to instantiate a given component
        after some checks on its compatibility with other components:
            - if a subclass of |Component| is given for the component,
            check that this is a subclass of the relevant class (e.g.
            |SurfaceComponent| if given for the |surface| argument) ;
            - if a |DataBase| is given for the component, check that the
            components depending on it require data (i.e. they are not
            all |DataComponent| or |NoneComponent|) ;
            - if |None| is given for the component, check that the
            components depending on it do not require data (i.e. they
            are all |NoneComponent|).

        Once these checks are done, an instance of |DataComponent|,
        |NoneComponent|, or a "genuine" |Component| (e.g.
        |SurfaceComponent|, |SubSurfaceComponent|, etc.) is returned.

        :param category: name of the component category
        :type category: str
        :param given: dictionary of objects given during instantiation
        of |Model| - keys: component category / values: object
        :type given: dict
        :param inferred: dictionary of classes previously inferred from
        given objects - keyrs: component category / values: subclass of Component
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
            if not all([issubclass(inferred[down_], (DataComponent, NoneComponent))
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
        is given during the instantiation of the |Model| object.

        Only three objects are supported for instantiating a Component of Model:
            - a subclass of |Component| (e.g. |SurfaceComponent|,
            |SubSurfaceComponent|, etc.) ;
            - an instance of |DataBase| ;
            - |None|.

        If something else is given, the method returns the class |type|.

        :param given_object: object given during instantiation of |Model|
        :return: a subclass of |Component| or type if object given is unsupported
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
    def _check_modelling_context(category, timeframe, spacedomain, database):
        """
        The purpose of this method is to check that the elements in the
        tuple given for a given component category are if the right type
        (i.e. (TimeFrame instance, SpaceDomain instance, DataBase instance))

        :param category: name of the component category being checked
        (e.g. 'surface', 'subsurface', etc.)
        :type category: str
        :param timeframe: object being given as 1st argument during the
        call of the |simulate| method for the given component category
        :type timeframe: object being given as 2nd argument during the
        call of the |simulate| method for the given component category
        :param spacedomain: object being given as 3rd argument during the
        call of the |simulate| method for the given component category
        :type spacedomain: object
        :param database:
        :type database: object

        :return: None
        """

        if not isinstance(timeframe, TimeFrame):
            raise TypeError("The 1st contextual item for the '{}' component "
                            "must be an instance of TimeFrame.".format(category))

        if not isinstance(spacedomain, SpaceDomain):
            raise TypeError("The 2nd contextual item for the '{}' component "
                            "must be an instance of SpaceDomain.".format(category))
        else:
            if isinstance(spacedomain, Network):
                raise NotImplementedError("The SpaceDomain subclass Network is "
                                          "not currently supported by the "
                                          "framework.")

        if not isinstance(database, DataBase):
            raise TypeError("The 3rd contextual item for the '{}' component "
                            "must be an instance of DataBase.".format(category))
