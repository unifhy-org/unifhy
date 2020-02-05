from ..components import OpenWaterComponent


class Dummy(OpenWaterComponent):

    def __init__(self):
        super().__init__(driving_data_names=(),
                         ancil_data_names=(),
                         parameter_names=('residence_time',))

    def run(self, evaporation_openwater, surface_runoff, subsurface_runoff,
            residence_time,
            **kwargs):

        return {
            'discharge': None
        }
