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
                 openwater_timedomain):
        # determine temporal supermesh properties
        # (supermesh is the fastest component)
        supermesh_timedelta = min(
            surfacelayer_timedomain.timedelta,
            subsurface_timedomain.timedelta,
            openwater_timedomain.timedelta
        )
        supermesh_length = max(
            surfacelayer_timedomain.time.size,
            subsurface_timedomain.time.size,
            openwater_timedomain.time.data.size
        )
        supermesh_timestep = supermesh_timedelta.total_seconds()

        # check that all timesteps are multiple integers of the supermesh step
        surfacelayer_timedomain_timestep = (
            surfacelayer_timedomain.timedelta.total_seconds()
        )
        if not surfacelayer_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the surfacelayer component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(surfacelayer_timedomain_timestep,
                                supermesh_timestep))
        subsurface_timedomain_timestep = (
            subsurface_timedomain.timedelta.total_seconds()
        )
        if not subsurface_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the subsurface component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(subsurface_timedomain_timestep,
                                supermesh_timestep))
        openwater_timedomain_timestep = (
            openwater_timedomain.timedelta.total_seconds()
        )
        if not openwater_timedomain_timestep % supermesh_timestep == 0:
            raise ValueError(
                "The timestep of the openwater component ({}s) is not a "
                "multiple integer of the timestep of the fastest component "
                "({}s).".format(openwater_timedomain_timestep,
                                supermesh_timestep))

        # get boolean arrays (switches) to determine when to run a given
        # component on temporal supermesh
        self._surfacelayer_switch = np.zeros((supermesh_length,), dtype=bool)
        surfacelayer_increment = (
            int(surfacelayer_timedomain_timestep // supermesh_timestep)
        )
        self._surfacelayer_switch[0::surfacelayer_increment] = True
        self._surfacelayer_index_multiple = surfacelayer_increment

        self._subsurface_switch = np.zeros((supermesh_length,), dtype=bool)
        subsurface_increment = (
            int(subsurface_timedomain_timestep // supermesh_timestep)
        )
        self._subsurface_switch[0::subsurface_increment] = True
        self._subsurface_index_multiple = subsurface_increment

        self._openwater_switch = np.zeros((supermesh_length,), dtype=bool)
        openwater_increment = (
            int(openwater_timedomain_timestep // supermesh_timestep)
        )
        self._openwater_switch[0::openwater_increment] = True
        self._openwater_index_multiple = openwater_increment

        # set static time attributes
        self.start_datetime = (
            surfacelayer_timedomain.time.datetime_array[0]
        )
        self.end_datetime = (
            surfacelayer_timedomain.time.datetime_array[-1]
        )
        self.timedelta = supermesh_timedelta
        self.start_timeindex = 0
        self.end_timeindex = supermesh_length - 1

        # initialise 'iterable' time attributes to the point in time just
        # prior the actual specified start of the supermesh because the
        # iterator needs to increment in time prior indexing the switches
        self._current_datetime = self.start_datetime - supermesh_timedelta
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
            raise ValueError("Cannot get current time index: unknown "
                             "component type {}.".format(component_type))

    def __iter__(self):
        return self

    def __next__(self):
        # loop until it hits the second to last index (because the last index
        # corresponds to the end of the last timestep, so that it should not
        # be used as the start of another iteration
        if self._current_timeindex < self.end_timeindex - 1:
            self._current_timeindex += 1
            self._current_datetime += self.timedelta

            switches = (
                self._surfacelayer_switch[self._current_timeindex],
                self._subsurface_switch[self._current_timeindex],
                self._openwater_switch[self._current_timeindex]
            )
            return switches
        else:
            raise StopIteration
