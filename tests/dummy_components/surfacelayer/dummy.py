import numpy as np

from cm4twc.components import SurfaceLayerComponent


class Dummy(SurfaceLayerComponent):

    driving_data_info = {
        'rainfall': 'kg m-2 s-1',
        'snowfall': 'kg m-2 s-1',
        'air_temperature': 'K',
    }
    ancillary_data_info = {
        'vegetation_fraction': '1'
    }
    # parameters_info = {}
    # constants_info = {}
    states_info = {
        'canopy': 'kg m-2',
        'snowpack': 'kg m-2'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            # component states
            'canopy': (  # in chronological order
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            ),
            'snowpack': (  # in chronological order
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            soil_water_stress,
            # component driving data
            rainfall, snowfall, air_temperature,
            # component ancillary data
            vegetation_fraction,
            # component parameters
            # component states
            canopy, snowpack,
            # component constants
            **kwargs):

        dummy_array = np.ones(self.spaceshape, np.float32)

        canopy[0][:] = canopy[-1] + 1
        snowpack[0][:] = snowpack[-1] + 1

        return {
            # interface fluxes out
            'throughfall': dummy_array,
            'snowmelt': dummy_array,
            'transpiration': dummy_array,
            'evaporation_soil_surface': dummy_array,
            'evaporation_ponded_water': dummy_array,
            'evaporation_openwater': dummy_array
        }

    def finalise(self, canopy, snowpack,
                 **kwargs):

        pass
