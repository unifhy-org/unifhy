import numpy as np

from cm4twc.components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    driving_data_info = {
        'driving_a': '1',
    }
    # ancillary_data_info = {},
    parameters_info = {
        'parameter_a': '1',
    }
    # constants_info = {},
    states_info = {
        'state_a': '1',
        'state_b': '1'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'state_a': (
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            ),
            'state_b': (
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            # component driving data
            driving_a,
            # component ancillary data
            # component parameters
            parameter_a,
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        state_a[0][:] = state_a[-1] + 1
        state_b[0][:] = state_b[-1] + 2

        return {
            # interface fluxes out
            'runoff': driving_a * parameter_a,
            'soil_water_stress': driving_a * parameter_a
        }

    def finalise(self, state_a, state_b,
                 **kwargs):

        pass
