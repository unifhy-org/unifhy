from ..components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={
                'soil_temperature': 'K',
            },
            ancil_data_info={},
            parameter_info={
                'saturated_hydraulic_conductivity': 'kg m-2 s-1',
            }
        )

    def run(self, evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            soil_temperature,
            saturated_hydraulic_conductivity,
            **kwargs):

        return {
            'surface_runoff': None,
            'subsurface_runoff': None
        }
