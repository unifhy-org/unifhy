from importlib import import_module
from os import sep, path
from glob import glob
from datetime import datetime, timedelta
import yaml

from ._utils import Interface, Clock, Compass
from ._utils.interface import load_transfers_dump
from .components import (SurfaceLayerComponent, SubSurfaceComponent,
                         OpenWaterComponent, DataComponent, NullComponent)
from .time import TimeDomain


class Model(object):
    r"""Model is the core element of the modelling framework.

    It is responsible for configuring the simulation, checking the
    compatibility between `Component`\s, and controlling the simulation
    workflow.
    """
    def __init__(self, identifier, config_directory, output_directory,
                 surfacelayer, subsurface, openwater,
                 _to_yaml=True):
        """**Initialisation**

        :Parameters:

            identifier: `str`
                A name to identify the model output files.

            config_directory: `str`
                The path to the directory where to save the model
                configuration files.

            output_directory: `str`
                The path to the directory where to save the model
                interface dump files and model output files.

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
        # assign components to model if of the correct type
        self.surfacelayer = self._process_component_type(
            surfacelayer, SurfaceLayerComponent)

        self.subsurface = self._process_component_type(
            subsurface, SubSurfaceComponent)

        self.openwater = self._process_component_type(
            openwater, OpenWaterComponent)

        # assign identifier
        self.identifier = identifier
        # propagate id to components
        self.surfacelayer.identifier = identifier
        self.subsurface.identifier = identifier
        self.openwater.identifier = identifier

        # assign directories
        self.config_directory = config_directory
        self.output_directory = output_directory

        # save model configuration in yaml file
        if _to_yaml:
            self.to_yaml()

        # define attribute interface for transfers between components
        self.interface = None

    @staticmethod
    def _process_component_type(component, expected_component):
        if isinstance(component, expected_component):
            # check inwards interface
            # check outwards interface
            return component
        elif isinstance(component, (DataComponent, NullComponent)):
            if component.category != expected_component.get_class_category():
                raise TypeError(
                    "'{}' component given must be substituting type {}".format(
                        expected_component.get_class_category(),
                        expected_component.__name__))
            else:
                return component
        else:
            raise TypeError(
                "'{}' component given must either be of type {}, {}, "
                "or {}".format(
                    expected_component.get_class_category(),
                    expected_component.__name__, DataComponent.__name__,
                    NullComponent.__name__))

    def __str__(self):
        return "\n".join(
            ["{}(".format(self.__class__.__name__)] +
            ["    identifier: {}".format(self.identifier)] +
            ["    config directory: {}".format(self.config_directory)] +
            ["    output directory: {}".format(self.output_directory)] +
            ["    surfacelayer: {}".format(
                self.surfacelayer.__class__.__name__)] +
            ["    subsurface: {}".format(
                self.subsurface.__class__.__name__)] +
            ["    openwater: {}".format(
                self.openwater.__class__.__name__)] +
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
            identifier=cfg['identifier'],
            config_directory=cfg['config_directory'],
            output_directory=cfg['output_directory'],
            surfacelayer=surfacelayer.from_config(
                cfg['surfacelayer']),
            subsurface=subsurface.from_config(
                cfg['subsurface']),
            openwater=openwater.from_config(
                cfg['openwater']),
            _to_yaml=False
        )

    def to_config(self):
        return {
            'identifier': self.identifier,
            'config_directory': self.config_directory,
            'output_directory': self.output_directory,
            'surfacelayer': self.surfacelayer.to_config(),
            'subsurface': self.subsurface.to_config(),
            'openwater': self.openwater.to_config()
        }

    @classmethod
    def from_yaml(cls, yaml_file):
        """Instantiate a `Model` from a YAML configuration file.

        :Parameters:

            yaml_file: `str`
                A string providing the path to the YAML file to be used
                to instantiate `Model`.

                *Parameter example:* ::

                    yaml_file='configurations/dummy.yml'

        **Examples**

        >>> m = Model.from_yaml('configurations/dummy.yml')
        >>> print(m)
        Model(
            identifier: dummy
            config directory: configurations
            output directory: outputs
            surfacelayer: Dummy
            subsurface: Dummy
            openwater: Dummy
        )

        """
        with open(yaml_file, 'r') as f:
            cfg = yaml.load(f, yaml.FullLoader)
        return cls.from_config(cfg)

    def to_yaml(self):
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
        with open(sep.join([self.config_directory,
                            '.'.join([self.identifier, 'yml'])]), 'w') as f:
            yaml.dump(self.to_config(), f, yaml.Dumper, sort_keys=False)

    def initialise_transfers_from_dump(self, dump_file, at=None):
        """Initialise the transfers of the Interface from a dump file.

        :Parameters:

            dump_file: `str`
                A string providing the path to the netCDF dump file
                containing values to be used as initial conditions for
                the transfers of the Interface.

            at: datetime object, optional
                The snapshot in time to be used for the initial
                conditions. Must be any datetime type (except
                `numpy.datetime64`). Must be contained in the 'time'
                variable in *dump_file*. If not provided, the last index
                in the 'time' variable in *dump_file* will be used.

                Note: if a datetime is provided, there is no enforcement
                of the fact that this datetime must correspond to the
                initial datetime in the simulation period for the
                `Component`, and it is only used as a means to select
                a specific snapshot in time amongst the ones available
                in the dump file.

        :Returns:

            datetime object
                The snapshot in time that was used for the initial
                conditions.

        """
        # set up compass responsible for mapping across components
        compass = Compass({'surfacelayer': self.surfacelayer.spacedomain,
                           'subsurface': self.subsurface.spacedomain,
                           'openwater': self.openwater.spacedomain})

        # set up clock responsible for iterating over time
        clock = Clock({'surfacelayer': self.surfacelayer.timedomain,
                       'subsurface': self.subsurface.timedomain,
                       'openwater': self.openwater.timedomain})

        # set up interface responsible for transfers between components
        self.interface = Interface({'surfacelayer': self.surfacelayer,
                                    'subsurface': self.subsurface,
                                    'openwater': self.openwater},
                                   clock, compass, self.identifier,
                                   self.output_directory)

        transfers, at = load_transfers_dump(dump_file, at,
                                            self.interface.transfers)
        for tr in self.interface.transfers:
            if tr in transfers:
                if self.interface.transfers[tr].get('from') is None:
                    continue
                else:
                    self.interface.transfers[tr]['slices'][-1] = transfers[tr]
            else:
                raise KeyError("initial conditions for interface transfer "
                               "'{}' not in dump".format(tr))

        return at

    def spin_up(self, start, end, cycles=1, dumping_frequency=None,
                overwrite=True, _cycle_origin_no=0):
        """Run model spin-up simulation to initialise states of each
        `Component` of the Model.

        :Parameters:

            start, end: `datetime.datetime` object
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

            dumping_frequency: `datetime.timedelta` object, optional
                The frequency at which Components' states must be
                stored in a dump file. These dumps can be used to
                restart a `Component` from a particular point in time.

                Note, the frequency is to be understood in a modelled
                time context, not computational time context.

                *Parameter example:* ::

                    dumping_frequency=datetime.timedelta(weeks=10)

            overwrite: `bool`, optional
                Whether existing files should be overwritten if they
                feature the same name as files about to be written by
                the model. If not provided, set to default True.

        """
        # generate spin-up timedomains for each model component
        surfacelayer_timedomain = (
            self.surfacelayer.get_spin_up_timedomain(start, end)
        )
        subsurface_timedomain = (
            self.subsurface.get_spin_up_timedomain(start, end)
        )
        openwater_timedomain = (
            self.openwater.get_spin_up_timedomain(start, end)
        )

        # store spin up configuration in a separate yaml file
        spin_up_config = {
            'start': start.strftime('%Y-%m-%d %H:%M:%S'),
            'end': end.strftime('%Y-%m-%d %H:%M:%S'),
            'cycles': cycles,
            'dumping_frequency':
                {'seconds': dumping_frequency.total_seconds()}
                if dumping_frequency is not None else None
        }
        with open(sep.join([self.config_directory,
                            '.'.join([self.identifier, 'spin_up', 'yml'])]),
                  'w') as f:
            yaml.dump(spin_up_config, f, yaml.Dumper, sort_keys=False)

        # store main run attributes
        main_sl_td = self.surfacelayer.timedomain
        main_ss_td = self.subsurface.timedomain
        main_ow_td = self.openwater.timedomain

        # assign spin-up run attributes in place of main run's ones
        self.surfacelayer.timedomain = surfacelayer_timedomain
        self.subsurface.timedomain = subsurface_timedomain
        self.openwater.timedomain = openwater_timedomain

        # start the spin up run(s)
        for cycle in range(cycles):
            tag = 'spinup{}'.format(_cycle_origin_no + cycle + 1)
            self._initialise(tag, overwrite)
            self._run(tag, dumping_frequency, overwrite)
            self._finalise()

        # restore main run attributes
        self.surfacelayer.timedomain = main_sl_td
        self.subsurface.timedomain = main_ss_td
        self.openwater.timedomain = main_ow_td

    def simulate(self, dumping_frequency=None, overwrite=True):
        """Run model simulation over period defined in its components'
        timedomains.

        :Parameters:

            dumping_frequency: `datetime.timedelta` object, optional
                The frequency at which Components' states must be
                stored in a dump file. These dumps can be used to
                restart a `Component` from a particular point in time.

                Note, the frequency is to be understood in a modelled
                time context, not computational time context.

                *Parameter example:* ::

                    dumping_frequency=datetime.timedelta(weeks=4)

            overwrite: `bool`, optional
                Whether existing files should be overwritten if they
                feature the same name as files about to be written by
                the model. If not provided, set to default True.

        """
        # store spin up configuration in a separate yaml file
        simulate_config = {
            'dumping_frequency':
                {'seconds': dumping_frequency.total_seconds()}
                if dumping_frequency is not None else None
        }
        with open(sep.join([self.config_directory,
                            '.'.join([self.identifier, 'simulate', 'yml'])]),
                  'w') as f:
            yaml.dump(simulate_config, f, yaml.Dumper, sort_keys=False)

        # initialise, run, finalise model
        self._initialise('run', overwrite)
        self._run('run', dumping_frequency, overwrite)
        self._finalise()

    def _initialise(self, tag, overwrite):
        # initialise components' states
        self.surfacelayer.initialise_(tag, overwrite)
        self.subsurface.initialise_(tag, overwrite)
        self.openwater.initialise_(tag, overwrite)

    def _run(self, tag, dumping_frequency=None, overwrite=True):
        # set up compass responsible for mapping across components
        compass = Compass({'surfacelayer': self.surfacelayer.spacedomain,
                           'subsurface': self.subsurface.spacedomain,
                           'openwater': self.openwater.spacedomain})

        # set up clock responsible for iterating over time
        clock = Clock({'surfacelayer': self.surfacelayer.timedomain,
                       'subsurface': self.subsurface.timedomain,
                       'openwater': self.openwater.timedomain})
        if dumping_frequency is not None:
            clock.set_dumping_frequency(dumping_frequency)

        # set up interface responsible for transfers between components
        if self.interface is None:
            # generate an instance of Interface
            self.interface = Interface({'surfacelayer': self.surfacelayer,
                                        'subsurface': self.subsurface,
                                        'openwater': self.openwater},
                                       clock, compass, self.identifier,
                                       self.output_directory)
        else:
            # no need for a new instance, but need to re-run the setup
            # of the existing instance because time or space information
            # may have been changed for one or more components
            self.interface.set_up({'surfacelayer': self.surfacelayer,
                                   'subsurface': self.subsurface,
                                   'openwater': self.openwater},
                                  clock, compass)
        self.interface.initialise_(tag, overwrite)

        # run components
        for (run_surfacelayer, run_subsurface, run_openwater,
             dumping) in clock:

            to_interface = {}

            if dumping:
                self.surfacelayer.dump_states(
                    clock.get_current_timeindex('surfacelayer')
                )
                self.subsurface.dump_states(
                    clock.get_current_timeindex('subsurface')
                )
                self.openwater.dump_states(
                    clock.get_current_timeindex('openwater')
                )
                self.interface.dump_transfers(
                    clock.get_current_timestamp()
                )

            if run_surfacelayer:
                to_interface.update(
                    self.surfacelayer.run_(
                        clock.get_current_timeindex('surfacelayer'),
                        self.interface
                    )
                )

            if run_subsurface:
                to_interface.update(
                    self.subsurface.run_(
                        clock.get_current_timeindex('subsurface'),
                        self.interface
                    )
                )

            if run_openwater:
                to_interface.update(
                    self.openwater.run_(
                        clock.get_current_timeindex('openwater'),
                        self.interface
                    )
                )

            self.interface.update(to_interface)

    def _finalise(self):
        # finalise components
        self.surfacelayer.finalise_()
        self.subsurface.finalise_()
        self.openwater.finalise_()
        # finalise model
        self.interface.finalise_()

    def resume(self, at=None):
        """Resume model simulation on latest snapshot in dump files or
        at the given snapshot.

        :Parameters:

            at: datetime object, optional
                The particular point in time (snapshot) available in the
                dump files that will be used to resume the model
                simulation.

        """
        ats = []
        cycle_nos = []
        data_or_null = 0
        for component in [self.surfacelayer, self.subsurface, self.openwater]:
            # skip DataComponent and NullComponent
            if isinstance(component, (DataComponent, NullComponent)):
                data_or_null += 1
                continue

            # initialise component states from dump file
            dump_sig = sep.join([component.output_directory,
                                 '_'.join([component.identifier,
                                           component.category,
                                           '*', 'dump.nc'])])

            dump_files = sorted(glob(dump_sig))

            if not dump_files:
                raise RuntimeError(
                    "no dump file found for {} component of model {}".format(
                        component.category, self.identifier)
                )
            elif dump_sig.replace('*', 'run') in dump_files:
                dump_file = dump_sig.replace('*', 'run')
            else:
                # use last dump file, which will be the latest spinup run
                dump_file = dump_files[-1]
                cycle_nos.append(
                    dump_file.split('_dump.nc')[0].split('spinup')[-1]
                )

            ats.append(component.initialise_states_from_dump(dump_file, at))

        # if all components are Data or Null, exit resume
        if data_or_null == 3:
            return

        # initialise model interface transfers from dump file
        dump_sig = sep.join([self.output_directory,
                             '_'.join([self.identifier, 'interface',
                                       '*', 'dump.nc'])])

        dump_files = sorted(glob(dump_sig))

        if not dump_files:
            raise RuntimeError(
                "no dump file found for interface of model {}".format(
                    self.identifier)
            )
        elif dump_sig.replace('*', 'run') in dump_files:
            dump_file = dump_sig.replace('*', 'run')
        else:
            # use last dump file, which will be the latest spinup run
            dump_file = dump_files[-1]
            cycle_nos.append(
                dump_file.split('_dump.nc')[0].split('spinup')[-1]
            )

        ats.append(self.initialise_transfers_from_dump(dump_file, at))

        # check whether snapshots in dumps are for same datetime
        if not len(set(ats)) == 1:
            raise RuntimeError("dump files feature different last "
                               "snapshots in time, cannot resume")
        at = list(set(ats))[0]

        # reload simulate configuration (if it exists)
        yaml_sig = sep.join(
            [self.config_directory,
             '.'.join([self.identifier, '*', 'yml'])]
        )

        if path.exists(yaml_sig.replace('*', 'simulate')):
            # collect simulate arguments stored in yaml file
            with open(yaml_sig.replace('*', 'simulate'), 'r') as f:
                cfg = yaml.load(f, yaml.FullLoader)

            # adjust the component timedomain to reflect remaining period
            for component in [self.surfacelayer, self.subsurface,
                              self.openwater]:
                if at == component.timedomain.bounds.datetime_array[-1, -1]:
                    raise RuntimeError("{} component run already completed "
                                       "successfully, cannot resume".format(
                                            component.category))

                remaining_td = TimeDomain.from_start_end_step(
                    start=at,
                    end=component.timedomain.bounds.datetime_array[-1, -1],
                    step=component.timedomain.timedelta,
                    units=component.timedomain.units,
                    calendar=component.timedomain.calendar
                )
                component.timedomain = remaining_td

            # resume the simulation run
            dump_freq_sec = (None if cfg['dumping_frequency'] is None else
                             cfg['dumping_frequency'].get('seconds', None))
            self.simulate(
                dumping_frequency=timedelta(seconds=dump_freq_sec)
                if dump_freq_sec is not None else None,
                overwrite=False
            )
        elif path.exists(yaml_sig.replace('*', 'spin_up')):
            # collect spin up arguments stored in yaml file
            with open(yaml_sig.replace('*', 'spin_up'), 'r') as f:
                cfg = yaml.load(f, yaml.FullLoader)

            # check whether spin up cycles for components are the same
            if not len(set(cycle_nos)) == 1:
                raise RuntimeError("component cycle numbers are different, "
                                   "cannot resume")
            cycle_no = int(list(set(cycle_nos))[0])

            # resume the spin up run(s)
            start = datetime.strptime(str(cfg['start']), '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(str(cfg['end']), '%Y-%m-%d %H:%M:%S')
            dump_freq_sec = (None if cfg['dumping_frequency'] is None else
                             cfg['dumping_frequency'].get('seconds', None))
            dumping_frequency = (timedelta(seconds=dump_freq_sec)
                                 if dump_freq_sec is not None else None)
            # resume spin up cycle according to the latest dump found
            if at == end:
                if cfg['cycles'] == cycle_no:
                    raise RuntimeError("spin up run(s) already completed "
                                       "successfully, cannot resume")
            else:
                self.spin_up(
                    start=at,
                    end=end,
                    cycles=1,
                    dumping_frequency=dumping_frequency,
                    overwrite=False,
                    _cycle_origin_no=cycle_no - 1
                )
            # start any additional spin up cycle
            if cfg['cycles'] - cycle_no > 0:
                self.spin_up(
                    start=start,
                    end=end,
                    cycles=cfg['cycles'] - cycle_no,
                    dumping_frequency=dumping_frequency,
                    overwrite=False,
                    _cycle_origin_no=cycle_no
                )
        else:
            raise RuntimeError("no spin up nor simulate configuration found, "
                               "cannot resume")
