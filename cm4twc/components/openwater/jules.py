from ..components import OpenWaterComponent


class JULES(OpenWaterComponent):

    def __init__(self):
        super().__init__(driving_data_names=('air_temperature',),
                         ancil_data_names=('roughness',))

    def run(self, evaporation_openwater, surface_runoff, subsurface_runoff,
            air_temperature,
            roughness,
            **kwargs):

        return {
            'discharge': None
        }
