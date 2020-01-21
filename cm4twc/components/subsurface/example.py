from ..components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    def __init__(self):
        super().__init__(driving_data_names=('soil_temperature',),
                         ancil_data_names=('permeability',),
                         parameter_names=('hydraulic_conductivity',))

    def run(self, evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            soil_temperature,
            permeability,
            hydraulic_conductivity,
            **kwargs):

        return {
            'surface_runoff': None,
            'subsurface_runoff': None
        }
