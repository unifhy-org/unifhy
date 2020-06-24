import numpy as np

from cm4twc.components import SurfaceLayerComponent


class Dummy(SurfaceLayerComponent):

    driving_data_info = {
        'driving_a': '1',
        'driving_b': '1',
        'driving_c': '1',
    }
    ancillary_data_info = {
        'ancillary_a': '1'
    }
    # parameters_info = {}
    # constants_info = {}
    states_info = {
        'state_a': '1',
        'state_b': '1'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            # component states
            'state_a': (  # in chronological order
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            ),
            'state_b': (  # in chronological order
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            soil_water_stress,
            # component driving data
            driving_a, driving_b, driving_c,
            # component ancillary data
            ancillary_a,
            # component parameters
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        state_a[0][:] = state_a[-1] + 1
        state_b[0][:] = state_b[-1] + 2

        return {
            # interface fluxes out
            'throughfall':
                driving_a + driving_b + driving_c,
            'snowmelt':
                driving_a + driving_b + driving_c,
            'transpiration':
                driving_a + driving_b + driving_c,
            'evaporation_soil_surface':
                driving_a + driving_b + driving_c,
            'evaporation_ponded_water':
                driving_a + driving_b + driving_c,
            'evaporation_openwater':
                driving_a + driving_b + driving_c
        }

    def finalise(self, state_a, state_b,
                 **kwargs):

        pass
