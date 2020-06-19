import numpy as np

from cm4twc.components import OpenWaterComponent


class Dummy(OpenWaterComponent):

    # driving_data_info = {}
    ancillary_data_info = {
        'ancillary_a': '1'
    }
    parameters_info = {
        'parameter_a': '1',
    }
    constants_info = {
        'constant_a': '1'
    },
    states_info = {
        'state_a': '1'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'state_a': (
                np.zeros(self.spaceshape, np.float32),  # for t-1
                np.zeros(self.spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            evaporation_openwater, runoff,
            # component driving data
            # component ancillary data
            ancillary_a,
            # component parameters
            parameter_a,
            # component states
            state_a,
            # component constants
            constant_a=1,
            **kwargs):

        dummy_array = np.ones(self.spaceshape, np.float32)

        state_a[0][:] = state_a[-1] + 1

        return {
            # interface fluxes out
            'discharge': ancillary_a * parameter_a * constant_a
        }

    def finalise(self, state_a,
                 **kwargs):

        pass
