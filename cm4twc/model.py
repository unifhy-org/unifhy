from importlib import import_module

from .time_ import Clock
from .interface import Interface
from .components import (SurfaceLayerComponent, SubSurfaceComponent,
                         OpenWaterComponent, DataComponent, NullComponent)


class Model(object):
    """
    DOCSTRING REQUIRED
    """
    def __init__(self, surfacelayer, subsurface, openwater):
        self.surfacelayer = self._process_component_type(
            surfacelayer, SurfaceLayerComponent)

        self.subsurface = self._process_component_type(
            subsurface, SubSurfaceComponent)

        self.openwater = self._process_component_type(
            openwater, OpenWaterComponent)

        self._check_timedomain_compatibilities()
        self._check_spacedomain_compatibilities()

        self._spun_up = False

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
        if (not self.surfacelayer.timedomain.spans_same_period_as(
                self.subsurface.timedomain)) or \
            (not self.surfacelayer.timedomain.spans_same_period_as(
                self.openwater.timedomain)):
            raise ValueError(
                "The Timedomains of the Components do not span "
                "the same period.")
        # check that components' timedomains are equal
        # (to stay until temporal supermesh supported)
        if (self.surfacelayer.timedomain != self.subsurface.timedomain) or \
                (self.surfacelayer.timedomain != self.openwater.timedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different TimeDomains.")

    def _check_spacedomain_compatibilities(self):
        # check that components' spacedomains are equal
        # (to stay until spatial supermesh supported)
        if (self.surfacelayer.spacedomain != self.subsurface.spacedomain) or \
                (self.surfacelayer.spacedomain != self.openwater.spacedomain):
            raise NotImplementedError(
                "Currently, the modelling framework does not allow "
                "for components to work on different SpaceDomains.")

    @classmethod
    def from_config(cls, cfg):
        surfacelayer = (
            getattr(
                import_module(cfg['surfacelayer']['module']),
                cfg['surfacelayer']['class']
            )
        )
        subsurface = (
            getattr(
                import_module(cfg['subsurface']['module']),
                cfg['subsurface']['class']
            )
        )
        openwater = (
            getattr(
                import_module(cfg['openwater']['module']),
                cfg['openwater']['class']
            )
        )

        return cls(
            surfacelayer=surfacelayer.from_config(
                cfg['surfacelayer']),
            subsurface=subsurface.from_config(
                cfg['subsurface']),
            openwater=openwater.from_config(
                cfg['openwater'])
        )

    def to_config(self):
        return {
            'surfacelayer': self.surfacelayer.to_config(),
            'subsurface': self.subsurface.to_config(),
            'openwater': self.openwater.to_config()
            }

    def spin_up(self, start, end, cycles=1):
        """
        DOCSTRING REQUIRED
        """
        self._initialise()

        surfacelayer_timedomain = \
            self.surfacelayer.get_spin_up_timedomain(start, end)
        subsurface_timedomain = \
            self.subsurface.get_spin_up_timedomain(start, end)
        openwater_timedomain = \
            self.openwater.get_spin_up_timedomain(start, end)

        for cycle in range(cycles):
            self._run(surfacelayer_timedomain,
                      subsurface_timedomain,
                      openwater_timedomain)

        self._spun_up = True

    def simulate(self):
        """
        DOCSTRING REQUIRED
        """
        if not self._spun_up:
            self._initialise()

        interface = self._run(self.surfacelayer.timedomain,
                              self.subsurface.timedomain,
                              self.openwater.timedomain)

        self._finalise()

        return interface

    def _initialise(self):
        # initialise components' states
        self.surfacelayer.initialise_states()
        self.subsurface.initialise_states()
        self.openwater.initialise_states()

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
                [self.surfacelayer, self.subsurface, self.openwater]
                for f in list(c.inwards.keys()) + list(c.outwards.keys())
            }
        )

        # run components
        for run_surfacelayer, run_subsurface, run_openwater in clock:

            datetime = clock.get_current_datetime()

            if run_surfacelayer:
                interface.update(
                    self.surfacelayer(
                        timeindex=clock.get_current_timeindex('surfacelayer'),
                        datetime=datetime,
                        **interface
                    )
                )

            if run_subsurface:
                interface.update(
                    self.subsurface(
                        timeindex=clock.get_current_timeindex('subsurface'),
                        datetime=datetime,
                        **interface
                    )
                )

            if run_openwater:
                interface.update(
                    self.openwater(
                        timeindex=clock.get_current_timeindex('openwater'),
                        datetime=datetime,
                        **interface
                    )
                )

            if run_surfacelayer:
                self.surfacelayer.increment_states()
            if run_subsurface:
                self.subsurface.increment_states()
            if run_openwater:
                self.openwater.increment_states()

        return interface

    def _finalise(self):
        # finalise components
        self.surfacelayer.finalise_states()
        self.subsurface.finalise_states()
        self.openwater.finalise_states()
