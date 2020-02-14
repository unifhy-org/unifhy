from ..components import OpenWaterComponent


class Dummy(OpenWaterComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={},
            ancil_data_info={},
            parameter_info={
                'residence_time': 's',
            }
        )

    def run(self, evaporation_openwater, surface_runoff, subsurface_runoff,
            residence_time,
            **kwargs):

        return {
            'discharge': None
        }
