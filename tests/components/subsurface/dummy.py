import numpy as np

from cm4twc.components import SubSurfaceComponent
from cm4twc.settings import DTYPE_F
from .dummyfortran import dummyfortran
from .dummyc import dummyc


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
                np.zeros(self.spaceshape, DTYPE_F()),  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            ),
            'state_b': (
                np.zeros(self.spaceshape, DTYPE_F()),  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
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


class DummyFortran(SubSurfaceComponent):

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
        z, y, x = self.spaceshape
        state_a_m1, state_a_0, state_b_m1, state_b_0 = (
            dummyfortran.dummyfortran.initialise(z, y, x)
        )

        return {
            # component states
            'state_a': (  # in chronological order
                state_a_m1,  # for t-1
                state_a_0  # for t
            ),
            'state_b': (  # in chronological order
                state_b_m1,  # for t-1
                state_b_0  # for t
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

        runoff, soil_water_stress = dummyfortran.dummyfortran.run(
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            driving_a, parameter_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # interface fluxes out
            'runoff': runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self, state_a, state_b,
                 **kwargs):
        dummyfortran.dummyfortran.finalise()


class DummyC(SubSurfaceComponent):

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
        z, y, x = self.spaceshape
        state_a_m1, state_a_0, state_b_m1, state_b_0 = (
            dummyc.initialise(z, y, x)
        )

        return {
            # component states
            'state_a': (  # in chronological order
                state_a_m1,  # for t-1
                state_a_0  # for t
            ),
            'state_b': (  # in chronological order
                state_b_m1,  # for t-1
                state_b_0  # for t
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

        runoff, soil_water_stress = dummyc.run(
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            driving_a, parameter_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # interface fluxes out
            'runoff': runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self, state_a, state_b,
                 **kwargs):
        dummyc.finalise()
