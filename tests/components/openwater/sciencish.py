import numpy as np

from cm4twc.components import OpenWaterComponent


class Sciencish(OpenWaterComponent):

    # _inputs_info = {}
    _parameters_info = {
        'residence_time': {
            'units': 's'
        }
    }
    # _constants_info = {},
    _states_info = {
        'river_channel': {
            'units': 'kg m-2',
            'divisions': 1
        }
    }
    _outputs_info = {
        'discharge': {
            'units': 'kg m-2 s-1'
        }
    }
    _solver_history = 1

    def initialise(self,
                   # component states
                   river_channel,
                   **kwargs):
        river_channel[-1][:] = 1e3

    def run(self,
            # from exchanger
            evaporation_openwater, runoff,
            # component driving data
            # component ancillary data
            # component parameters
            residence_time,
            # component states
            river_channel,
            # component constants
            **kwargs):

        discharge = river_channel[-1] / residence_time

        channel_water = (river_channel[-1]
                         + (runoff - evaporation_openwater - discharge)
                         * self.timedelta_in_seconds)

        river_channel[0][:] = np.where(channel_water < 0, 0, channel_water)

        return (
            # to exchanger
            {
                'water_level': river_channel[0][:]
            },
            # component outputs
            {
                'discharge': discharge
            }
        )

    def finalise(self,
                 # component states
                 river_channel,
                 **kwargs):
        pass
