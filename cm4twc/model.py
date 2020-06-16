from importlib import import_module
import yaml

from .time_ import Clock
from .interface import Interface
from .components import (SurfaceLayerComponent, SubSurfaceComponent,
                         OpenWaterComponent, DataComponent, NullComponent)


class Model(object):
    r"""Model is the core element of the modelling framework.

    It is responsible for configuring the simulating, checking the
    compatibility between `Component`\s, and controlling the simulation
    workflow.
    """
    def __init__(self, surfacelayer, subsurface, openwater):
        """**Initialisation**

        :Parameters:

            surfacelayer: `SurfaceLayerComponent` object
                The `Component` responsible for the surface layer
                compartment of the hydrological cycle.

            subsurface: `SubSurfaceComponent` object
                The `Component` responsible for the subsurface
                compartment of the hydrological cycle.

            openwater: `OpenWaterComponent` object
                The `Component` responsible for the open water
                compartment of the hydrological cycle.

        """
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

    def __str__(self):
        return "\n".join(
            ["Model(".format(self.__class__.__name__)] +
            ["    surfacelayer: %s" % self.surfacelayer.__class__.__name__] +
            ["    subsurface: %s" % self.subsurface.__class__.__name__] +
            ["    openwater: %s" % self.openwater.__class__.__name__] +
            [")"]
        )

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

    @classmethod
    def from_yaml(cls, yaml_file):
        """Initialise a `Model` from a YAML configuration file.

        :Parameters:

            yaml_file: `str`
                A string providing the path to the YAML file to be used
                to initialise `Model`.

                *Parameter example:* ::

                    yaml_file='dummy_config/dummy.yaml'

        **Examples**

        >>> m = Model.from_yaml('dummy_config/dummy.yaml')
        >>> print(m)
        Model(
            surfacelayer: Dummy
            subsurface: Dummy
            openwater: Dummy
        )

        """
        with open(yaml_file, 'r') as f:
            cfg = yaml.load(f, yaml.FullLoader)
        return cls.from_config(cfg)

    def to_yaml(self, yaml_file):
        # configure the dumping format for sequences
        for type_ in (list, tuple, set):
            yaml.add_representer(
                type_,
                lambda dumper, data:
                dumper.represent_sequence(u'tag:yaml.org,2002:seq',
                                          data, flow_style=True),
                Dumper=yaml.Dumper
            )
        # dump configuration in yaml file
        with open(yaml_file, 'w') as f:
            yaml.dump(self.to_config(), f, yaml.Dumper, sort_keys=False)

    def spin_up(self, start, end, cycles=1):
        """Run model spin-up simulation to initialise model states.

        :Parameters:

            start, end: datetime object
                The start and the end of the spin-up simulation. Their
                calendar and units are assumed to be the ones of the
                model `Components` that will be spun up. Note, the *end*
                parameter refers to the end of the last timestep in the
                spin-up period.

                *Parameter example:* ::

                    start=datetime.datetime(2019, 1, 1)

                *Parameter example:* ::

                    end=datetime.datetime(2020, 1, 1)

            cycles: `int`, optional
                The number of repetitions of the spin-up simulation. If
                not provided, set to default 1 (cycle).

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
        """Run model simulation over period defined in its components'
        timedomains.
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
                for f in list(c.inwards_info) + list(c.outwards_info)
            }
        )

        # check time compatibility with data and subspace data in time
        self.surfacelayer.check_dataset_time(surfacelayer_timedomain)
        self.subsurface.check_dataset_time(subsurface_timedomain)
        self.openwater.check_dataset_time(openwater_timedomain)

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
