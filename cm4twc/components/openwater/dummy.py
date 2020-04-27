import numpy as np

from ..components import OpenWaterComponent


class Dummy(OpenWaterComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={},
            ancil_data_info={},
            parameters_info={
                'residence_time': 's',
            },
            states_info={
                'river_channel': 'kg m-2'
            },
            constants_info={},
            solver_history=1
        )

    def initialise(self, spaceshape, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'river_channel': (
                np.zeros(spaceshape, np.float32),  # for t-1
                np.zeros(spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            evaporation_openwater, runoff,
            # component features
            spaceshape,
            # component driving data
            # component ancillary data
            # component parameters
            residence_time,
            # component states
            river_channel,
            # component constants
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        river_channel[0][:] = river_channel[-1] + 1

        return {
            # interface fluxes out
            'discharge': dummy_array
        }

    def finalise(self, river_channel,
                 **kwargs):

        pass
