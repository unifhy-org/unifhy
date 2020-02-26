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

    def initialise(self):

        return {
            'soil_moisture': None,
            'aquifer': None
        }

    def run(self, evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            soil_temperature,
            saturated_hydraulic_conductivity,
            soil_moisture, aquifer,
            **kwargs):

        return {
            'surface_runoff': None,
            'subsurface_runoff': None,
            'soil_moisture': None,
            'aquifer': None
        }

    def finalise(self, soil_moisture, aquifer,
                 **kwargs):

        pass
