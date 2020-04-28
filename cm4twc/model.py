from .time_ import Clock
from .interface import Interface
from .components import SurfaceLayerComponent, SubSurfaceComponent, \
    OpenWaterComponent, DataComponent, NullComponent


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

        if (self._surfacelayer.timedomain != self._subsurface.timedomain) or \
                (self._surfacelayer.timedomain != self._openwater.timedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeDomains.")

        if (self._surfacelayer.spacedomain != self._subsurface.spacedomain) or \
                (self._surfacelayer.spacedomain != self._openwater.spacedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

    @staticmethod
    def _process_component_type(component, expected_component):

        if isinstance(component, expected_component):
            # check inwards interface
            # check outwards interface
            return component
        elif isinstance(component, (DataComponent, NullComponent)):
            if component.category != expected_component.get_class_kind():
                raise TypeError(
                    "The '{}' component given must be substituting an instance "
                    "of  the class {}.".format(
                        expected_component.get_class_kind(),
                        expected_component.__name__))
            else:
                return component
        else:
            raise TypeError(
                "The '{}' component given must either be an instance of "
                "the class {}, the class {}, or the class {}.".format(
                    expected_component.get_class_kind(),
                    expected_component.__name__, DataComponent.__name__,
                    NullComponent.__name__))

    def simulate(self):
        """
        DOCSTRING REQUIRED
        """
        # set up clock responsible for the time-stepping schemes
        clock = Clock(surfacelayer_timedomain=self._surfacelayer.timedomain,
                      subsurface_timedomain=self._subsurface.timedomain,
                      openwater_timedomain=self._openwater.timedomain)

        # set up interface responsible for exchanges between components
        interface = Interface(
            # fluxes that are both inwards and outwards will exist
            # only once because dictionary keys are unique
            fluxes={
                f: None for c in
                [self._surfacelayer, self._subsurface, self._openwater]
                for f in list(c.inwards.keys()) + list(c.outwards.keys())
            }
        )

        # initialise components
        self._surfacelayer.initialise_states()
        self._subsurface.initialise_states()
        self._openwater.initialise_states()

        # run components
        for run_surfacelayer, run_subsurface, run_openwater in clock:

            timeindex = clock.get_current_timeindex()
            datetime = clock.get_current_datetime()

            if run_surfacelayer:
                interface.update(
                    self._surfacelayer(
                        timeindex=timeindex,
                        datetime=datetime,
                        **interface
                    )
                )

            if run_subsurface:
                interface.update(
                    self._subsurface(
                        timeindex=timeindex,
                        datetime=datetime,
                        **interface
                    )
                )

            if run_openwater:
                interface.update(
                    self._openwater(
                        timeindex=timeindex,
                        datetime=datetime,
                        **interface
                    )
                )

            if run_surfacelayer:
                self._surfacelayer.increment_states()
            if run_subsurface:
                self._subsurface.increment_states()
            if run_openwater:
                self._openwater.increment_states()

        # finalise components
        self._surfacelayer.finalise_states()
        self._subsurface.finalise_states()
        self._openwater.finalise_states()

        return interface
