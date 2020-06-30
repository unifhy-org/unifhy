import numpy as np

from cm4twc.components import OpenWaterComponent
from cm4twc.settings import DTYPE_F


class Sciencish(OpenWaterComponent):

    # driving_data_info = {}
    # ancillary_data_info = {}
    parameters_info = {
        'residence_time': 's',
    }
    # constants_info = {},
    states_info = {
        'river_channel': 'kg m-2'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'river_channel': (
                np.ones(self.spaceshape, DTYPE_F()) * 1e3,  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            )
        }

    def run(self,
            # interface fluxes in
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
                         * self.timestepinseconds)

        river_channel[0][:] = np.where(channel_water < 0, 0, channel_water)

        return {
            # interface fluxes out
            'discharge': discharge
        }

    def finalise(self, river_channel,
                 **kwargs):

        pass
