from .time_ import TimeFrame
from .space_ import _SpaceDomain
from .data_ import DataBase
from .components import SurfaceComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NoneComponent


class Model(object):
    """
    DOCSTRING REQUIRED
    """

    def __init__(self, surface, subsurface, openwater):

        if openwater is None:
            self._openwater = NoneComponent()
        elif issubclass(openwater, OpenWaterComponent):
            self._openwater = openwater()
        else:
            raise TypeError("The openwater component given must either be "
                            "a sublass of the class SurfaceComponent, "
                            "or None.")

        if subsurface is None:
            if openwater is None:
                self._subsurface = NoneComponent()
            else:
                raise TypeError("The subsurface component cannot be None "
                                "because the openwater component is not None.")
        elif issubclass(subsurface, SubSurfaceComponent):
            self._subsurface = subsurface()
        elif isinstance(subsurface, DataBase):
            self._surface = DataComponent(subsurface, self._openwater.inwards)
        else:
            raise TypeError("The subsurface component given must either be "
                            "a sublass of the class SurfaceComponent, "
                            "or an instance of Variable, or None.")

        if issubclass(surface, SurfaceComponent):
            self._surface = surface()
        elif isinstance(surface, DataBase):
            self._surface = DataComponent(
                surface, self._openwater.inwards + self._subsurface.inwards)
        else:
            raise TypeError("The surface component given must either be "
                            "a sublass of the class SurfaceComponent, "
                            "or an instance of Variable.")





    def simulate(self, surface_context, subsurface_context, openwater_context, **kwargs):

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
            **kwargs
        )

        out_subsurface = self._subsurface(
            *subsurface_context,
            **out_surface, **kwargs
        )

        out_openwater = self._openwater(
            *openwater_context,
            **out_surface, **out_subsurface, **kwargs
        )

        return out_surface, out_subsurface, out_openwater

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
