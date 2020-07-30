import numpy as np

from cm4twc.components import SubSurfaceComponent


class Sciencish(SubSurfaceComponent):

    driving_data_info = {
        'soil_temperature': {
            'units': 'K'
        },
    }
    # ancillary_data_info = {},
    parameters_info = {
        'saturation_capacity': {
            'units': 'kg m-2'
        }
    }
    constants_info = {
        'freezing_temperature': {
            'units': 'K'
        }
    },
    states_info = {
        'soil_moisture': {
            'units': 'kg m-2',
            'divisions': 1
        },
        'aquifer': {
            'units': 'kg m-2',
            'divisions': 1
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   soil_moisture, aquifer,
                   **kwargs):
        soil_moisture[-1][:] = 3e2
        aquifer[-1][:] = 1e3

    def run(self,
            # from interface
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
            # to interface
            'runoff': soil_runoff + surface_runoff + groundwater_runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self,
                 # component states
                 soil_moisture, aquifer,
                 **kwargs):
        pass
