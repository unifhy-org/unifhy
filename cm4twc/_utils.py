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
        surfacelayer_step = surfacelayer_timedomain.timedelta.total_seconds()
        if not surfacelayer_step % supermesh_step == 0:
            raise ValueError(
                "timestep of surfacelayer component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    surfacelayer_step, supermesh_step))

        subsurface_step = subsurface_timedomain.timedelta.total_seconds()
        if not subsurface_step % supermesh_step == 0:
            raise ValueError(
                "timestep of subsurface component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    subsurface_step, supermesh_step))

        openwater_step = openwater_timedomain.timedelta.total_seconds()
        if not openwater_step % supermesh_step == 0:
            raise ValueError(
                "timestep of openwater component ({}s) not a multiple "
                "integer of timestep of fastest component ({}s).".format(
                    openwater_step, supermesh_step))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self._surfacelayer_switch = np.zeros((supermesh_length,), dtype=bool)
        surfacelayer_increment = int(surfacelayer_step // supermesh_step)
        self._surfacelayer_switch[0::surfacelayer_increment] = True
        self._surfacelayer_index_multiple = surfacelayer_increment

        self._subsurface_switch = np.zeros((supermesh_length,), dtype=bool)
        subsurface_increment = int(subsurface_step // supermesh_step)
        self._subsurface_switch[0::subsurface_increment] = True
        self._subsurface_index_multiple = subsurface_increment

        self._openwater_switch = np.zeros((supermesh_length,), dtype=bool)
        openwater_increment = int(openwater_step // supermesh_step)
        self._openwater_switch[0::openwater_increment] = True
        self._openwater_index_multiple = openwater_increment

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
                    self._surfacelayer_index_multiple)
        if component_type == 'subsurface':
            return (self._current_timeindex //
                    self._subsurface_index_multiple)
        if component_type == 'openwater':
            return (self._current_timeindex //
                    self._openwater_index_multiple)
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
                self._surfacelayer_switch[index],
                self._subsurface_switch[index],
                self._openwater_switch[index],
                self._dumping_switch[index]
            )
        else:
            raise StopIteration
