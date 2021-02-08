import numpy as np

from cm4twc.components import SubSurfaceComponent


class Sciencish(SubSurfaceComponent):

    _inputs_info = {
        'soil_temperature': {
            'units': 'K',
            'kind': 'dynamic'
        }
    }
    _parameters_info = {
        'saturation_capacity': {
            'units': 'kg m-2'
        }
    }
    _constants_info = {
        'freezing_temperature': {
            'units': 'K'
        }
    },
    _states_info = {
        'soil_moisture': {
            'units': 'kg m-2',
            'divisions': 1
        },
        'aquifer': {
            'units': 'kg m-2',
            'divisions': 1
        }
    }
    _solver_history = 1

    def initialise(self,
                   # component states
                   soil_moisture, aquifer,
                   **kwargs):
        soil_moisture[-1][:] = 3e2
        aquifer[-1][:] = 1e3

    def run(self,
            # from exchanger
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
                      + (throughfall + snowmelt) * self.timedelta_in_seconds)
        surface_runoff = np.where(
            soil_water > saturation_capacity,
            (soil_water - saturation_capacity) / self.timedelta_in_seconds,
            0
        )
        soil_water = np.where(
            soil_water > saturation_capacity,
            saturation_capacity,
            soil_water
        )
        soil_runoff = np.where(
            soil_temperature > freezing_temperature,
            soil_water / self.timedelta_in_seconds * 0.1,
            0
        )
        soil_moisture[0][:] = (soil_water
                               - soil_runoff * self.timedelta_in_seconds)

        soil_water_stress = soil_moisture[0] / saturation_capacity

        groundwater_runoff = aquifer[-1] / self.timedelta_in_seconds * 0.05
        aquifer[0][:] = (soil_moisture[-1]
                         - groundwater_runoff * self.timedelta_in_seconds)

        return (
            # to exchanger
            {
                'surface_runoff': surface_runoff,
                'subsurface_runoff': soil_runoff + groundwater_runoff,
                'soil_water_stress': soil_water_stress
            },
            # component outputs
            {}
        )

    def finalise(self,
                 # component states
                 soil_moisture, aquifer,
                 **kwargs):
        pass
