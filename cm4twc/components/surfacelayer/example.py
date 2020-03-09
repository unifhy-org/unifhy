import numpy as np

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
            parameters_info={},
            states_info={
                'canopy': 'kg m-2',
                'snowpack': 'kg m-2'
            }
        )

    def initialise(self):

        return {
            'canopy': None,
            'snowpack': None
        }

    def run(self, spaceshape,
            rainfall, snowfall, air_temperature,
            vegetation_fraction,
            canopy, snowpack,
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        return {
            'throughfall': dummy_array,
            'snowmelt': dummy_array,
            'transpiration': dummy_array,
            'evaporation_soil_surface': dummy_array,
            'evaporation_ponded_water': dummy_array,
            'evaporation_openwater': dummy_array,
            'canopy': dummy_array,
            'snowpack': dummy_array
        }

    def finalise(self, canopy, snowpack,
                 **kwargs):

        pass
