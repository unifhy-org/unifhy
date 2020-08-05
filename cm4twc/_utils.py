from collections.abc import MutableMapping
import numpy as np


class Interface(MutableMapping):

    def __init__(self, fluxes):
        self.fluxes = {}
        self.update(fluxes)

    def __getitem__(self, key):
        return self.fluxes[key]

    def __setitem__(self, key, value):
        self.fluxes[key] = value

    def __delitem__(self, key):
        del self.fluxes[key]

    def __iter__(self):
        return iter(self.fluxes)

    def __len__(self):
        return len(self.fluxes)

    def __repr__(self):
        return "Interface(\n\tfluxes: %r\n" % \
               {f: self.fluxes[f] for f in self.fluxes}


class Clock(object):

    def __init__(self, surfacelayer_timedomain, subsurface_timedomain,
                 openwater_timedomain, dumping_frequency=None):
        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        supermesh_delta = min(
            surfacelayer_timedomain.timedelta,
            subsurface_timedomain.timedelta,
            openwater_timedomain.timedelta
        )
        supermesh_length = max(
            surfacelayer_timedomain.time.size,
            subsurface_timedomain.time.size,
            openwater_timedomain.time.size
        )
        supermesh_step = supermesh_delta.total_seconds()

        # check that all timesteps are multiple integers of the supermesh step
        sl_step = surfacelayer_timedomain.timedelta.total_seconds()
        if not sl_step % supermesh_step == 0:
            raise ValueError(
                "timestep of surfacelayer component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    sl_step, supermesh_step))

        ss_step = subsurface_timedomain.timedelta.total_seconds()
        if not ss_step % supermesh_step == 0:
            raise ValueError(
                "timestep of subsurface component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    ss_step, supermesh_step))

        ow_step = openwater_timedomain.timedelta.total_seconds()
        if not ow_step % supermesh_step == 0:
            raise ValueError(
                "timestep of openwater component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    ow_step, supermesh_step))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self._sl_switch = np.zeros((supermesh_length,), dtype=bool)
        sl_increment = int(sl_step // supermesh_step)
        self._sl_switch[sl_increment-1::sl_increment] = True
        self._sl_index_multiple = sl_increment

        self._ss_switch = np.zeros((supermesh_length,), dtype=bool)
        ss_increment = int(ss_step // supermesh_step)
        self._ss_switch[ss_increment-1::ss_increment] = True
        self._ss_index_multiple = ss_increment

        self._ow_switch = np.zeros((supermesh_length,), dtype=bool)
        ow_increment = int(ow_step // supermesh_step)
        self._ow_switch[ow_increment-1::ow_increment] = True
        self._ow_index_multiple = ow_increment

        # determine whether model states dumping is required,and if so, when
        self._dumping_switch = np.zeros((supermesh_length,), dtype=bool)
        if dumping_frequency is not None:
            # check that dumpy frequency is a multiple of
            # slowest component's step
            dumping_delta = max(
                surfacelayer_timedomain.timedelta,
                subsurface_timedomain.timedelta,
                openwater_timedomain.timedelta
            )
            dumping_step = dumping_frequency.total_seconds()
            if not dumping_step % dumping_delta.total_seconds() == 0:
                raise ValueError(
                    "dumping frequency ({}s) is not a multiple integer "
                    "of timestep of slowest component ({}s).".format(
                        dumping_step, dumping_delta.total_seconds()))

            # get boolean arrays (switches) to determine when to dump the
            # component states on temporal supermesh
            dumping_increment = int(dumping_step // supermesh_step)
            self._dumping_switch[0::dumping_increment] = True
        else:
            # get only one dump for the initial conditions
            self._dumping_switch[0] = True

        # set some time attributes
        self.start_datetime = surfacelayer_timedomain.time.datetime_array[0]
        self.end_datetime = surfacelayer_timedomain.time.datetime_array[-1]
        self.timedelta = supermesh_delta
        self.start_timeindex = 0
        self.end_timeindex = supermesh_length - 1

        # initialise 'iterable' time attributes to the point in time just
        # prior the actual specified start of the supermesh because the
        # iterator needs to increment in time prior indexing the switches
        self._current_datetime = self.start_datetime - supermesh_delta
        self._current_timeindex = self.start_timeindex - 1

    def get_current_datetime(self):
        return self._current_datetime

    def get_current_timeindex(self, component_type):
        if component_type == 'surfacelayer':
            return (self._current_timeindex //
                    self._sl_index_multiple)
        if component_type == 'subsurface':
            return (self._current_timeindex //
                    self._ss_index_multiple)
        if component_type == 'openwater':
            return (self._current_timeindex //
                    self._ow_index_multiple)
        else:
            raise None

    def __iter__(self):
        return self

    def __next__(self):
        # loop until it hits to last index (because the last index
        # corresponds to the start of the last timestep)
        if self._current_timeindex < self.end_timeindex:
            self._current_timeindex += 1
            index = self._current_timeindex
            self._current_datetime += self.timedelta

            return (
                self._sl_switch[index],
                self._ss_switch[index],
                self._ow_switch[index],
                self._dumping_switch[index]
            )
        else:
            raise StopIteration
