from ..components import OpenWaterComponent


class JULES(OpenWaterComponent):

    def __init__(self):
        super().__init__(driving_data_names=('air_temperature',),
                         ancil_data_names=('roughness',),
                         parameter_names=('residence_time',))

    def run(self, evaporation_openwater, surface_runoff, subsurface_runoff,
            air_temperature,
            roughness,
            residence_time,
            **kwargs):

        return {
            'discharge': None
        }
