import numpy as np

from cm4twc.components import OpenWaterComponent
from cm4twc.settings import DTYPE_F
from .dummyfortran import dummyfortran
from .dummyc import dummyc


class Dummy(OpenWaterComponent):
    # driving_data_info = {}
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    constants_info = {
        'constant_a': {
            'units': '1'
        }
    },
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):

        state_a[-1][:] = 0

    def run(self,
            # from interface
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
            # to interface
            'discharge': ancillary_a * parameter_a * constant_a
        }

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        pass


class DummyFortran(OpenWaterComponent):
    # driving_data_info = {}
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    constants_info = {
         'constant_a': {
             'units': '1'
         }
     },
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1,
            'order': 'F'
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):
        dummyfortran.initialise(state_a[-1])

    def run(self,
            # from interface
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

        discharge = dummyfortran.run(
            evaporation_openwater, runoff, ancillary_a, parameter_a,
            state_a[-1], state_a[0], constant_a
        )

        return {
            # to interface
            'discharge': discharge
        }

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        dummyfortran.finalise()


class DummyC(OpenWaterComponent):
    # driving_data_info = {}
    ancillary_data_info = {
        'ancillary_a': {
            'units': '1'
        }
    }
    parameters_info = {
        'parameter_a': {
            'units': '1'
        },
    }
    constants_info = {
        'constant_a': {
            'units': '1'
        }
    },
    states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1
        }
    }
    solver_history = 1

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):
        dummyc.initialise(state_a[-1])

    def run(self,
            # from interface
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
            # to interface
            'discharge': discharge
        }

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        dummyc.finalise()
