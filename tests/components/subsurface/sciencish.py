import numpy as np

from cm4twc.components import SubSurfaceComponent
from cm4twc.settings import DTYPE_F


class Sciencish(SubSurfaceComponent):

    driving_data_info = {
        'soil_temperature': 'K',
    }
    # ancillary_data_info = {},
    parameters_info = {
        'saturation_capacity': 'kg m-2'
    }
    constants_info = {
        'freezing_temperature': 'K'
    },
    states_info = {
        'soil_moisture': 'kg m-2',
        'aquifer': 'kg m-2'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'soil_moisture': (
                np.ones(self.spaceshape, DTYPE_F()) * 3e2,  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            ),
            'aquifer': (
                np.ones(self.spaceshape, DTYPE_F()) * 1e3,  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
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
            saturation_capacity,
            # component states
            soil_moisture, aquifer,
            # component constants,
            freezing_temperature=273,
            **kwargs):

        soil_water = (soil_moisture[-1]
                      + (throughfall + snowmelt) * self.timestepinseconds)
        surface_runoff = np.where(
            soil_water > saturation_capacity,
            (soil_water - saturation_capacity) / self.timestepinseconds,
            0
        )
        soil_water = np.where(
            soil_water > saturation_capacity,
            saturation_capacity,
            soil_water
        )
        soil_runoff = np.where(
            soil_temperature > freezing_temperature,
            soil_water / self.timestepinseconds * 0.1,
            0
        )
        soil_moisture[0][:] = (soil_water
                               - soil_runoff * self.timestepinseconds)

        soil_water_stress = soil_moisture[0] / saturation_capacity

        groundwater_runoff = aquifer[-1] / self.timestepinseconds * 0.05
        aquifer[0][:] = (soil_moisture[-1]
                         - groundwater_runoff * self.timestepinseconds)

        return {
            # interface fluxes out
            'runoff': soil_runoff + surface_runoff + groundwater_runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self, soil_moisture, aquifer,
                 **kwargs):

        pass
