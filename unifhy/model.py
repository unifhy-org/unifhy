from importlib import import_module
from os import sep
from datetime import datetime, timedelta
import re
import yaml

from ._utils import Exchanger, Clock, Compass
from ._utils.exchanger import load_transfers_dump
from .component import (SurfaceLayerComponent, SubSurfaceComponent,
                        OpenWaterComponent, DataComponent, NullComponent)
from .time import TimeDomain


class Model(object):
    r"""Model is the core element of the modelling framework.

    It is responsible for configuring the simulation, checking the
    compatibility between `Component`\s, and controlling the simulation
    workflow.
    """
    def __init__(self, identifier, config_directory, saving_directory,
                 surfacelayer, subsurface, openwater,
                 _to_yaml=True):
        """**Instantiation**

        :Parameters:

            identifier: `str`
                A name to identify the model files.

            config_directory: `str`
                The path to the directory where to save the model
                configuration files.

            saving_directory: `str`
                The path to the directory where to save the model
                exchanger dump files and model record files.

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
        #: Return the surface layer component of the model.
        self.surfacelayer = self._process_component_type(
            surfacelayer, SurfaceLayerComponent)
        #: Return the sub-surface component of the model.
        self.subsurface = self._process_component_type(
            subsurface, SubSurfaceComponent)
        #: Return the open water component of the model.
        self.openwater = self._process_component_type(
            openwater, OpenWaterComponent)

        self._check_components_plugging()

        # assign identifier
        self.identifier = identifier

        # assign directories
        #: Return the directory used to store the model configurations.
        self.config_directory = config_directory
        #: Return the directory used to store the model output files.
        self.saving_directory = saving_directory

        # save model configuration in yaml file
        if _to_yaml:
            self.to_yaml()

        # define attribute exchanger for transfers between components
        self.exchanger = None

    @property
    def identifier(self):
        """Return the name used to identify the model files."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = identifier
        # propagate id to components
        self.surfacelayer.identifier = identifier
        self.subsurface.identifier = identifier
        self.openwater.identifier = identifier

    @staticmethod
    def _process_component_type(component, expected_type):
        if isinstance(component, expected_type):
            return component
        elif isinstance(component, (DataComponent, NullComponent)):
            if component.category != expected_type.category:
                raise TypeError(
                    f"'{expected_type.category}' component given must be "
                    f"substituting type {expected_type.__name__}"
                )
            else:
                return component
        else:
            raise TypeError(
                f"'{expected_type.category}' component given must either be "
                f"of type {expected_type.__name__}, {DataComponent.__name__}, "
                f"or {NullComponent.__name__}"
            )

    def _check_components_plugging(self):
        # check that each component inward is available as an outward
        # from the expected component
        for cat in ['surfacelayer', 'subsurface', 'openwater']:
            dst = getattr(self, cat)
            for trf, info in dst.inwards_info.items():
                src = getattr(self, info['from'])
                if (trf not in src.outwards_info
                        or cat not in src.outwards_info[trf]['to']):
                    raise RuntimeError(
                        f"{cat} component inward transfer '{trf}' "
                        f"not available from {src.category} component"
                    )

    def __str__(self):
        return "\n".join(
            [f"{self.__class__.__name__}("]
            + [f"    identifier: {self._identifier}"]
            + [f"    config directory: {self.config_directory}"]
            + [f"    saving directory: {self.saving_directory}"]
            + [f"    surfacelayer: {self.surfacelayer.__module__}"]
            + [f"    subsurface: {self.subsurface.__module__}"]
            + [f"    openwater: {self.openwater.__module__}"]
            + [")"]
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
            saving_directory=cfg['saving_directory'],
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
            'identifier': self._identifier,
            'config_directory': self.config_directory,
            'saving_directory': self.saving_directory,
            'surfacelayer': self.surfacelayer.to_config(),
            'subsurface': self.subsurface.to_config(),
            'openwater': self.openwater.to_config()
        }

    @staticmethod
    def _set_up_yaml_loader():
        # configure yaml for loading datetime.timedelta
        yaml.add_constructor(
            u'!timedelta',
            lambda loader, node: timedelta(
                **{match[1]: float(match[2]) for match in
                   re.findall(r"(([a-z]+) *= *([0-9]+\.?[0-9]*))",
                              loader.construct_scalar(node))}
            ),
            Loader=yaml.FullLoader
        )
        yaml.add_implicit_resolver(
            u'!timedelta',
            re.compile(r"timedelta\(( *([a-z]+) *= *([0-9]+\.?[0-9]*) *,?)+\)")
        )

    @staticmethod
    def _set_up_yaml_dumper():
        # configure the dumping format for sequences
        for type_ in (list, tuple, set):
            yaml.add_representer(
                type_,
                lambda dumper, data:
                dumper.represent_sequence(u'tag:yaml.org,2002:seq',
                                          data, flow_style=True),
                Dumper=yaml.Dumper
            )
        # configure the dumping format for datetime.timedelta
        yaml.add_representer(
            timedelta,
            lambda dumper, data:
            dumper.represent_scalar(
                u'!timedelta', 'timedelta(seconds=%s)' % data.total_seconds()
            ),
            Dumper=yaml.Dumper
        )
        yaml.add_implicit_resolver(
            u'!timedelta',
            re.compile(r"timedelta\(( *([a-z]+) *= *([0-9]+\.?[0-9]*) *,?)+\)")
        )

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

        >>> m = Model.from_yaml('configurations/dummy_same_t_same_s.yml')
        >>> print(m)
        Model(
            identifier: test-dummy-same_t-same_s
            config directory: outputs
            saving directory: outputs
            surfacelayer: tests.components.surfacelayer.dummy
            subsurface: tests.components.subsurface.dummy
            openwater: tests.components.openwater.dummy
        )

        """
        cls._set_up_yaml_loader()

        with open(yaml_file, 'r') as f:
            cfg = yaml.load(f, yaml.FullLoader)
        return cls.from_config(cfg)

    def to_yaml(self):
        """Store configuration of `Model` as a YAML file in the
        configuration directory."""
        self._set_up_yaml_dumper()

        # dump configuration in yaml file
        with open(sep.join([self.config_directory, f'{self._identifier}.yml']),
                  'w') as f:
            yaml.dump(self.to_config(), f, yaml.Dumper, sort_keys=False)

    def initialise_transfers_from_dump(self, dump_file, at=None):
        """Initialise the transfers of the `Exchanger` from a dump file.

        :Parameters:

            dump_file: `str`
                A string providing the path to the netCDF dump file
                containing values to be used as initial conditions for
                the transfers of the Exchanger.

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

        # set up exchanger responsible for transfers between components
        self.exchanger = Exchanger({'surfacelayer': self.surfacelayer,
                                    'subsurface': self.subsurface,
                                    'openwater': self.openwater},
                                   clock, compass, self._identifier,
                                   self.saving_directory)

        transfers, at = load_transfers_dump(dump_file, at,
                                            self.exchanger.transfers)
        for tr in self.exchanger.transfers:
            if tr in transfers:
                if self.exchanger.transfers[tr].get('from') is None:
                    continue
                else:
                    self.exchanger.transfers[tr]['slices'][-1] = transfers[tr]
            else:
                raise KeyError(
                    f"initial conditions for exchanger transfer '{tr}' "
                    f"not in dump"
                )

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
                The frequency at which model snapshots must be stored
                in a dump file. These snapshots can be used to restart
                a `Model` from a particular point in time. If not
                provided, set to default None (i.e. no snapshot stored).

                Note, the frequency is to be understood in a simulation
                time context, not in a computational time context.

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
            'dumping_frequency': dumping_frequency
            if dumping_frequency is not None else None
        }
        self._set_up_yaml_dumper()
        with open(sep.join([self.config_directory,
                            f"{self._identifier}.spin_up.yml"]),
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
            tag = f'spinup{_cycle_origin_no + cycle + 1}'
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
                The frequency at which model snapshots must be stored
                in a dump file. These snapshots can be used to restart
                a `Model` from a particular point in time. If not
                provided, set to default None (i.e. no snapshot stored).

                Note, the frequency is to be understood in a simulation
                time context, not in a computational time context.

                *Parameter example:* ::

                    dumping_frequency=datetime.timedelta(weeks=4)


            overwrite: `bool`, optional
                Whether existing files should be overwritten if they
                feature the same name as files about to be written by
                the model. If not provided, set to default True.

        """
        # store spin up configuration in a separate yaml file
        simulate_config = {
            'dumping_frequency': dumping_frequency
            if dumping_frequency is not None else None
        }
        self._set_up_yaml_dumper()
        with open(sep.join([self.config_directory,
                            f"{self._identifier}.simulate.yml"]),
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

        # set up exchanger responsible for transfers between components
        if self.exchanger is None:
            # generate an instance of Exchanger
            self.exchanger = Exchanger({'surfacelayer': self.surfacelayer,
                                        'subsurface': self.subsurface,
                                        'openwater': self.openwater},
                                       clock, compass, self._identifier,
                                       self.saving_directory)
        else:
            # no need for a new instance, but need to re-run the setup
            # of the existing instance because time or space information
            # may have been changed for one or more components
            self.exchanger.set_up(clock, compass)
        self.exchanger.initialise_(tag, overwrite)

        # run components
        for (run_surfacelayer, run_subsurface, run_openwater,
             dumping) in clock:

            to_exchanger = {}

            if dumping:
                ti = clock.get_current_timeindex('surfacelayer')
                self.surfacelayer.dump_states(ti)
                self.surfacelayer.dump_record_streams(ti)
                ti = clock.get_current_timeindex('subsurface')
                self.subsurface.dump_states(ti)
                self.subsurface.dump_record_streams(ti)
                ti = clock.get_current_timeindex('openwater')
                self.openwater.dump_states(ti)
                self.openwater.dump_record_streams(ti)
                self.exchanger.dump_transfers(
                    clock.get_current_timestamp()
                )

            if run_surfacelayer:
                to_exchanger.update(
                    self.surfacelayer.run_(
                        clock.get_current_timeindex('surfacelayer'),
                        self.exchanger
                    )
                )

            if run_subsurface:
                to_exchanger.update(
                    self.subsurface.run_(
                        clock.get_current_timeindex('subsurface'),
                        self.exchanger
                    )
                )

            if run_openwater:
                to_exchanger.update(
                    self.openwater.run_(
                        clock.get_current_timeindex('openwater'),
                        self.exchanger
                    )
                )

            self.exchanger.update_transfers(to_exchanger)

    def _finalise(self):
        # finalise components
        self.surfacelayer.finalise_()
        self.subsurface.finalise_()
        self.openwater.finalise_()
        # finalise model
        self.exchanger.finalise_()

    def resume(self, tag, at=None):
        """Resume model spin up or main simulation run on latest
        snapshot in dump files or at the given snapshot.

        :Parameters:

            tag: `str`
                The tag for the run to resume. For a main simulation
                run, this is simply *run*. For a given cycle of a spin
                up run, this is *spinup#*, where *#* is the integer
                corresponding to the given spin up cycle (e.g. *1* for
                first cycle, *2* for second cycle, etc.).

            at: datetime object, optional
                The particular point in time (snapshot) available in the
                dump files that will be used to resume the model
                simulation.

        """
        # check validity of tag
        if tag == 'run':
            method = 'simulate'
        elif 'spinup' in tag:
            method = 'spin_up'
            res = re.compile(r"spinup[0-9]+").match(tag)
            if not res or ((res.end() - res.start()) != len(tag)):
                raise ValueError(f"tag '{tag}' for resume is invalid")
        else:
            raise ValueError(f"tag '{tag}' for resume is invalid")

        # collect simulate arguments stored in yaml file
        yaml_sig = sep.join([self.config_directory,
                             f"{self._identifier}.*.yml"])
        self._set_up_yaml_loader()
        try:
            with open(yaml_sig.replace('*', method), 'r') as f:
                cfg = yaml.load(f, yaml.FullLoader)
        except FileNotFoundError:
            raise FileNotFoundError("no configuration file found")

        # initialise list to hold snapshot retrieved from each dump file
        ats = []

        # initialise component states and record streams from dump files
        data_or_null = 0
        for component in [self.surfacelayer, self.subsurface, self.openwater]:
            # skip DataComponent and NullComponent
            if isinstance(component, (DataComponent, NullComponent)):
                data_or_null += 1
                continue

            # initialise component states from dump file
            dump_file = sep.join([self.saving_directory,
                                  '_'.join([component.identifier,
                                            component.category,
                                            tag, 'dump_states.nc'])])

            ats.append(component.initialise_states_from_dump(dump_file, at))

            # revive component record streams from dump file
            dump_file = sep.join([self.saving_directory,
                                  '_'.join([component.identifier,
                                            component.category,
                                            tag, 'dump_record_stream_{}.nc'])])

            timedomain = None
            if method == 'spin_up':
                # need to generate and use spin-up timedomain, because
                # until 'spin_up' is invoked, the component has the
                # timedomain corresponding to the main run (which, if
                # used, would result in improper initialisation of
                # record steams)
                start = datetime.strptime(str(cfg['start']), '%Y-%m-%d %H:%M:%S')
                end = datetime.strptime(str(cfg['end']), '%Y-%m-%d %H:%M:%S')
                timedomain = component.get_spin_up_timedomain(start, end)

            ats.extend(
                component.revive_record_streams_from_dump(
                    dump_file, timedomain, at
                )
            )

        # if all components are Data or Null, exit resume
        if data_or_null == 3:
            return

        # initialise model exchanger transfers from dump file
        dump_file = sep.join([self.saving_directory,
                              '_'.join([self._identifier, 'exchanger',
                                        tag, 'dump_transfers.nc'])])

        ats.append(self.initialise_transfers_from_dump(dump_file, at))

        # check whether snapshots in dumps are for same datetime
        if not len(set(ats)) == 1:
            raise RuntimeError("dump files feature different last "
                               "snapshots in time, cannot resume")
        at = list(set(ats))[0]

        # proceed with call to spin_up or simulate method of self
        if method == 'spin_up':
            cycle_no = int(tag.split('spinup')[-1])

            # resume the spin up run(s)
            start = datetime.strptime(str(cfg['start']), '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(str(cfg['end']), '%Y-%m-%d %H:%M:%S')
            dumping_frequency = cfg['dumping_frequency']

            # resume spin up cycle according to the latest dump found
            if at == end:
                if cfg['cycles'] == cycle_no:
                    raise RuntimeError("(all) spin up run(s) already completed "
                                       "successfully, cannot resume")
            else:
                # resume spin up cycle
                self.spin_up(
                    start=at,
                    end=end,
                    cycles=1,
                    dumping_frequency=dumping_frequency,
                    overwrite=False,
                    _cycle_origin_no=cycle_no - 1
                )
            # start any potential additional spin up cycle
            if cfg['cycles'] - cycle_no > 0:
                self.spin_up(
                    start=start,
                    end=end,
                    cycles=cfg['cycles'] - cycle_no,
                    dumping_frequency=dumping_frequency,
                    overwrite=False,
                    _cycle_origin_no=cycle_no
                )
        else:  # method == 'simulate'
            # adjust the component timedomain to reflect remaining period
            for component in [self.surfacelayer, self.subsurface,
                              self.openwater]:
                if at == component.timedomain.bounds.datetime_array[-1, -1]:
                    raise RuntimeError(
                        f"{component.category} component run already completed "
                        f"successfully, cannot resume"
                    )

                remaining_td = TimeDomain.from_start_end_step(
                    start=at,
                    end=component.timedomain.bounds.datetime_array[-1, -1],
                    step=component.timedomain.timedelta,
                    units=component.timedomain.units,
                    calendar=component.timedomain.calendar
                )
                component.timedomain = remaining_td

            # resume simulation run
            self.simulate(
                dumping_frequency=cfg['dumping_frequency'],
                overwrite=False
            )
