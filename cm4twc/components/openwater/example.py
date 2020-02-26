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

    def run(self, evaporation_openwater, surface_runoff, subsurface_runoff,
            residence_time, river_channel,
            **kwargs):

        return {
            'discharge': None,
            'river_channel': None
        }

    def finalise(self, river_channel,
                 **kwargs):

        pass
