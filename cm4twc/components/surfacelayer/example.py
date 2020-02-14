from ..components import SurfaceLayerComponent


class Dummy(SurfaceLayerComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={
                'rainfall': 'kg m-2 s-1',
                'snowfall': 'kg m-2 s-1',
                'air_temperature': 'K',
            },
            ancil_data_info={
                'vegetation_fraction': '1'
            },
            parameter_info={}
        )

    def run(self, rainfall, snowfall, air_temperature,
            vegetation_fraction,
            **kwargs):

        return {
            'throughfall': None,
            'snowmelt': None,
            'transpiration': None,
            'evaporation_soil_surface': None,
            'evaporation_ponded_water': None,
            'evaporation_openwater': None
        }
