import numpy as np

from cm4twc.components import SurfaceLayerComponent
from cm4twc.settings import DTYPE_F
from .dummyfortran import dummyfortran
from .dummyc import dummyc


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
                np.zeros(self.spaceshape, DTYPE_F()),  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            ),
            'state_b': (  # in chronological order
                np.zeros(self.spaceshape, DTYPE_F()),  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
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


class DummyFortran(SurfaceLayerComponent):

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

        (throughfall, snowmelt, transpiration,
         evaporation_soil_surface, evaporation_ponded_water,
         evaporation_openwater) = dummyfortran.dummyfortran.run(
            soil_water_stress,
            driving_a, driving_b, driving_c,
            ancillary_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # interface fluxes out
            'throughfall': throughfall,
            'snowmelt': snowmelt,
            'transpiration': transpiration,
            'evaporation_soil_surface': evaporation_soil_surface,
            'evaporation_ponded_water': evaporation_ponded_water,
            'evaporation_openwater': evaporation_openwater
        }

    def finalise(self, **kwargs):
        dummyfortran.dummyfortran.finalise()


class DummyC(SurfaceLayerComponent):

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

        (throughfall, snowmelt, transpiration,
         evaporation_soil_surface, evaporation_ponded_water,
         evaporation_openwater) = dummyc.run(
            soil_water_stress,
            driving_a, driving_b, driving_c,
            ancillary_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # interface fluxes out
            'throughfall': throughfall,
            'snowmelt': snowmelt,
            'transpiration': transpiration,
            'evaporation_soil_surface': evaporation_soil_surface,
            'evaporation_ponded_water': evaporation_ponded_water,
            'evaporation_openwater': evaporation_openwater
        }

    def finalise(self, **kwargs):
        dummyc.finalise()
