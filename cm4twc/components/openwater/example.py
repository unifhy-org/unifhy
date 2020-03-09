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
            }
        )

    def initialise(self):

        return {
            'river_channel': None
        }

    def run(self, spaceshape,
            evaporation_openwater, surface_runoff, subsurface_runoff,
            residence_time, river_channel,
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        return {
            'discharge': dummy_array,
            'river_channel': dummy_array
        }

    def finalise(self, river_channel,
                 **kwargs):

        pass
