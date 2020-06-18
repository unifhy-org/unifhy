import numpy as np

from cm4twc.components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    driving_data_info = {
        'soil_temperature': 'K',
    }
    # ancillary_data_info = {},
    parameters_info = {
        'saturated_hydraulic_conductivity': 'kg m-2 s-1',
    }
    # constants_info = {},
    states_info = {
        'soil_moisture': 'kg m-2',
        'aquifer': 'kg m-2'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'soil_moisture': (
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            ),
            'aquifer': (
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            # component driving data
            soil_temperature,
            # component ancillary data
            # component parameters
            saturated_hydraulic_conductivity,
            # component states
            soil_moisture, aquifer,
            # component constants
            **kwargs):

        dummy_array = np.ones(self.spaceshape, np.float32)

        soil_moisture[0][:] = soil_moisture[-1] + 1
        aquifer[0][:] = soil_moisture[-1] + 1

        return {
            # interface fluxes out
            'runoff': dummy_array,
            'soil_water_stress': dummy_array
        }

    def finalise(self, soil_moisture, aquifer,
                 **kwargs):

        pass
