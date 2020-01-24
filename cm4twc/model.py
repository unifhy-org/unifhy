from inspect import isclass

from .time_ import TimeFrame
from .space_ import _SpaceDomain
from .data_ import DataBase
from .components import SurfaceComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NoneComponent, Component


class Model(object):
    """
    DOCSTRING REQUIRED
    """

    def __init__(self, surface, subsurface, openwater):

        self._surface = self._check_component_dependencies(
            'surface', SurfaceComponent, surface,
            self._infer_component_class(surface),
            (
                (SubSurfaceComponent, self._infer_component_class(subsurface)),
                (OpenWaterComponent, self._infer_component_class(openwater)),
            )
        )

        self._subsurface = self._check_component_dependencies(
            'subsurface', SubSurfaceComponent, subsurface,
            self._infer_component_class(subsurface),
            (
                (OpenWaterComponent, self._infer_component_class(openwater)),
            )
        )

        self._openwater = self._check_component_dependencies(
            'openwater', OpenWaterComponent, openwater,
            self._infer_component_class(openwater),
            ()
        )

    def simulate(self, surface_context, surface_parameters,
                 subsurface_context, subsurface_parameters,
                 openwater_context, openwater_parameters):

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

    @staticmethod
    def _infer_component_class(given_object):

        """
        The purpose of this method is to return a class not matter what
        is given in the instantiation of the Model object.

        Only three objects can be used to instantiate a Component of Model:
            - a subclass of Component,
            - an instance of DataBase,
            - None.

        If something else is given, the method returns a type class.

        :param given_object: object given during instantiation of Model
        :return: a subclass of Component or type if object given is unsupported
        :rtype: class
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
    def _check_component_dependencies(category, expected_class, given_object,
                                      inferred_class, dep_comp_classes):
        """

        :param category: name of the component category
        :param given_object: object given during instantiation of Model
        :param inferred_class: class previously inferred from given_object
        :param dep_comp_classes: components depending on this component
        :type dep_comp_classes: tuple((class, class))

        :return: None
        """

        if issubclass(inferred_class, DataComponent):
            # not expecting to get data for this component
            # if not required by its dependencies
            if not all([issubclass(given, (DataComponent, NoneComponent))
                        for expected, given in dep_comp_classes]):

                required_data = (
                    data_ for expected, given in dep_comp_classes
                    if not issubclass(given, (DataComponent, NoneComponent))
                    for data_ in expected.get_inwards()
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
            if all([issubclass(given, (DataComponent, NoneComponent))
                    for expected, given in dep_comp_classes]):
                return NoneComponent()
            else:
                raise TypeError(
                    "The given {} component is None but other components "
                    "depending on it are not None.".format(category)
                )
        elif issubclass(inferred_class, expected_class):
            # matching types, proceed with instantiation without further ado
            return inferred_class()
        else:
            raise TypeError(
                "The {} component given must either be a subclass of the "
                "class {}, an instance of DataBase (if relevant), or None "
                "(if possible).".format(category, expected_class.__name__)
            )

    @staticmethod
    def _check_modelling_context(category, timeframe, spacedomain, database):

        if not isinstance(timeframe, TimeFrame):
            raise TypeError("The 1st contextual item for the '{}' component "
                            "must be an instance of TimeFrame.".format(category))

        if not isinstance(spacedomain, _SpaceDomain):
            raise TypeError("The 2nd contextual item for the '{}' component "
                            "must be an instance of SpaceDomain.".format(category))

        if not isinstance(database, DataBase):
            raise TypeError("The 3rd contextual item for the '{}' component "
                            "must be an instance of DataBase.".format(category))
