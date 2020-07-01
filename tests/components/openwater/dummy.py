import numpy as np

from cm4twc.components import OpenWaterComponent
from cm4twc.settings import DTYPE_F
from .dummyfortran import dummyfortran
from .dummyc import dummyc


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
                np.zeros(self.spaceshape, DTYPE_F()),  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
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

        state_a[0][:] = state_a[-1] + 1

        return {
            # interface fluxes out
            'discharge': ancillary_a * parameter_a * constant_a
        }

    def finalise(self, state_a,
                 **kwargs):
        pass


class DummyFortran(OpenWaterComponent):

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
        z, y, x = self.spaceshape
        state_a_m1, state_a_0 = dummyfortran.dummyfortran.initialise(z, y, x)

        return {
            'state_a': (
                state_a_m1,  # for t-1
                state_a_0  # for t
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
            constant_a=1.,
            **kwargs):

        discharge = dummyfortran.dummyfortran.run(
            evaporation_openwater, runoff, ancillary_a, parameter_a,
            state_a[-1], state_a[0], constant_a
        )

        return {
            # interface fluxes out
            'discharge': discharge
        }

    def finalise(self, state_a,
                 **kwargs):
        dummyfortran.dummyfortran.finalise()


class DummyC(OpenWaterComponent):

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
        z, y, x = self.spaceshape
        state_a_m1, state_a_0 = dummyc.initialise(z, y, x)

        return {
            'state_a': (
                state_a_m1,  # for t-1
                state_a_0  # for t
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
            constant_a=1.,
            **kwargs):

        discharge = dummyc.run(evaporation_openwater, runoff,
                               ancillary_a, parameter_a, state_a[-1],
                               state_a[0], constant_a)

        return {
            # interface fluxes out
            'discharge': discharge
        }

    def finalise(self, state_a,
                 **kwargs):
        dummyc.finalise()
