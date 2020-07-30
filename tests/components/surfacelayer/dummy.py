from cm4twc.components import SurfaceLayerComponent
try:
    from .dummyfortran import dummyfortran
except ImportError:
    # since dummyfortran is not defined in this exception catch, it will raise
    # a NameError later if DummyFortran component is used, but other component
    # will remain usable
    pass
try:
    from .dummyc import dummyc
except ImportError:
    # since dummyc is not defined in this exception catch, it will raise
    # a NameError later if DummyC component is used, but other component
    # will remain usable
    pass


class Dummy(SurfaceLayerComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
        'driving_b': {
            'units': '1'
        },
        'driving_c': {
            'units': '1'
        },
    }
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    # parameters_info = {}
    # constants_info = {}
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
            # to interface
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

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        pass


class DummyFortran(SurfaceLayerComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
        'driving_b': {
            'units': '1'
        },
        'driving_c': {
            'units': '1'
        },
    }
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    # parameters_info = {}
    # constants_info = {}
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
         evaporation_openwater) = dummyfortran.run(
            soil_water_stress,
            driving_a, driving_b, driving_c,
            ancillary_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return {
            # to interface
            'throughfall': throughfall,
            'snowmelt': snowmelt,
            'transpiration': transpiration,
            'evaporation_soil_surface': evaporation_soil_surface,
            'evaporation_ponded_water': evaporation_ponded_water,
            'evaporation_openwater': evaporation_openwater
        }

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyfortran.finalise()


class DummyC(SurfaceLayerComponent):
    driving_data_info = {
        'driving_a': {
            'units': '1'
        },
        'driving_b': {
            'units': '1'
        },
        'driving_c': {
            'units': '1'
        },
    }
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    # parameters_info = {}
    # constants_info = {}
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
            # to interface
            'throughfall': throughfall,
            'snowmelt': snowmelt,
            'transpiration': transpiration,
            'evaporation_soil_surface': evaporation_soil_surface,
            'evaporation_ponded_water': evaporation_ponded_water,
            'evaporation_openwater': evaporation_openwater
        }

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyc.finalise()
