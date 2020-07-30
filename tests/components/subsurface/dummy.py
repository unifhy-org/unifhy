from cm4twc.components import SubSurfaceComponent
from .dummyfortran import dummyfortran
from .dummyc import dummyc


class Dummy(SubSurfaceComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
    }
    # ancillary_data_info = {},
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    # constants_info = {},
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1
        },
        'state_b': {
            'units': '1',
            'divisions': 1
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a, state_b,
                   **kwargs):

        state_a[-1][:] = 0
        state_b[-1][:] = 0

    def run(self,
            # from interface
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
            # to interface
            'runoff': driving_a * parameter_a,
            'soil_water_stress': driving_a * parameter_a
        }

    def finalise(self,
                 # to interface
                 state_a, state_b,
                 **kwargs):
        pass


class DummyFortran(SubSurfaceComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
    }
    # ancillary_data_info = {},
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    # constants_info = {},
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1,
            'order': 'F'
        },
        'state_b': {
            'units': '1',
            'divisions': 1,
            'order': 'F'
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a, state_b,
                   **kwargs):
        dummyfortran.initialise(state_a[-1], state_b[-1])

    def run(self,
            # from interface
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

        runoff, soil_water_stress = dummyfortran.run(
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            driving_a, parameter_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # to interface
            'runoff': runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyfortran.finalise()


class DummyC(SubSurfaceComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
    }
    # ancillary_data_info = {},
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    # constants_info = {},
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1
        },
        'state_b': {
            'units': '1',
            'divisions': 1
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a, state_b,
                   **kwargs):
        dummyc.initialise(state_a[-1], state_b[-1])

    def run(self,
            # from interface
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
            # to interface
            'runoff': runoff,
            'soil_water_stress': soil_water_stress
        }

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyc.finalise()
