import numpy as np

from ..components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={
                'soil_temperature': 'K',
            },
            ancil_data_info={},
            parameters_info={
                'saturated_hydraulic_conductivity': 'kg m-2 s-1',
            },
            states_info={
                'soil_moisture': 'kg m-2',
                'aquifer': 'kg m-2'
            }
        )

    def initialise(self, **kwargs):

        return {
            'soil_moisture': None,
            'aquifer': None
        }

    def run(self, spaceshape,
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            soil_temperature,
            saturated_hydraulic_conductivity,
            soil_moisture, aquifer,
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        return {
            'surface_runoff': dummy_array,
            'subsurface_runoff': dummy_array,
            'soil_moisture': dummy_array,
            'aquifer': dummy_array
        }

    def finalise(self, soil_moisture, aquifer,
                 **kwargs):

        pass
