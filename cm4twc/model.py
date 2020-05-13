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

        self._check_timedomain_compatibilities()
        self._check_spacedomain_compatibilities()

        self._span_up = False

    @staticmethod
    def _process_component_type(component, expected_component):
        if isinstance(component, expected_component):
            # check inwards interface
            # check outwards interface
            return component
        elif isinstance(component, (DataComponent, NullComponent)):
            if component.category != expected_component.get_class_kind():
                raise TypeError(
                    "The '{}' component given must be substituting an "
                    "instance of the class {}.".format(
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

    def _check_timedomain_compatibilities(self):
        # check that components' timedomains start/end on same datetime
        if (not self._surfacelayer.timedomain.spans_same_period_as(
                self._subsurface.timedomain)) or \
            (not self._surfacelayer.timedomain.spans_same_period_as(
                self._openwater.timedomain)):
            raise ValueError(
                "The Timedomains of the Components do not span "
                "the same period.")
        # check that components' timedomains are equal
        # (to stay until temporal supermesh supported)
        if (self._surfacelayer.timedomain != self._subsurface.timedomain) or \
                (self._surfacelayer.timedomain != self._openwater.timedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeDomains.")

    def _check_spacedomain_compatibilities(self):
        # check that components' spacedomains are equal
        # (to stay until spatial supermesh supported)
        if (self._surfacelayer.spacedomain != self._subsurface.spacedomain) or \
                (self._surfacelayer.spacedomain != self._openwater.spacedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

    def spin_up(self, start, end, cycles=1):
        """
        DOCSTRING REQUIRED
        """
        self._initialise()

        surfacelayer_timedomain = \
            self._surfacelayer.get_spin_up_timedomain(start, end)
        subsurface_timedomain = \
            self._subsurface.get_spin_up_timedomain(start, end)
        openwater_timedomain = \
            self._openwater.get_spin_up_timedomain(start, end)

        for cycle in range(cycles):
            self._run(surfacelayer_timedomain,
                      subsurface_timedomain,
                      openwater_timedomain)

        self._span_up = True

    def simulate(self):
        """
        DOCSTRING REQUIRED
        """
        if not self._span_up:
            self._initialise()

        interface = self._run(self._surfacelayer.timedomain,
                              self._subsurface.timedomain,
                              self._openwater.timedomain)

        self._finalise()

        return interface

    def _initialise(self):
        # initialise components' states
        self._surfacelayer.initialise_states()
        self._subsurface.initialise_states()
        self._openwater.initialise_states()

    def _run(self, surfacelayer_timedomain, subsurface_timedomain,
             openwater_timedomain):
        # set up clock responsible for the time-stepping schemes
        clock = Clock(surfacelayer_timedomain,
                      subsurface_timedomain,
                      openwater_timedomain)

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

        # run components
        for run_surfacelayer, run_subsurface, run_openwater in clock:

            datetime = clock.get_current_datetime()

            if run_surfacelayer:
                interface.update(
                    self._surfacelayer(
                        timeindex=clock.get_current_timeindex('surfacelayer'),
                        datetime=datetime,
                        **interface
                    )
                )

            if run_subsurface:
                interface.update(
                    self._subsurface(
                        timeindex=clock.get_current_timeindex('subsurface'),
                        datetime=datetime,
                        **interface
                    )
                )

            if run_openwater:
                interface.update(
                    self._openwater(
                        timeindex=clock.get_current_timeindex('openwater'),
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

        return interface

    def _finalise(self):
        # finalise components
        self._surfacelayer.finalise_states()
        self._subsurface.finalise_states()
        self._openwater.finalise_states()
