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
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        'transfer_k': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        },
        'transfer_l': {
            'units': '1',
            'from': 'openwater',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'transfer_i': {
            'units': '1',
            'to': 'subsurface',
            'method': 'mean'
        },
        'transfer_j': {
            'units': '1',
            'to': 'openwater',
            'method': 'mean'
        }
    }
    # define some dummy inputs/parameters/constants/states/outputs
    inputs_info = {
        'driving_a': {
            'units': '1',
            'kind': 'dynamic'
        },
        'driving_b': {
            'units': '1',
            'kind': 'dynamic'
        },
        'driving_c': {
            'units': '1',
            'kind': 'dynamic'
        },
        'ancillary_c': {
            'units': '1',
            'kind': 'static'
        }
    }
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
        'ancillary_c': {
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
    outputs_info = {
        'output_x': {
            'units': '1'
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
            # from exchanger
            transfer_k, transfer_l,
            # component driving data
            driving_a, driving_b, driving_c,
            # component ancillary data
            ancillary_c,
            # component parameters
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        state_a[0][:] = state_a[-1] + 1
        state_b[0][:] = state_b[-1] + 2

        return (
            # to exchanger
            {
                'transfer_i':
                    driving_a + driving_b + transfer_l + ancillary_c * state_a[0],
                'transfer_j':
                    driving_a + driving_b + driving_c + transfer_k + state_b[0]
            },
            # component outputs
            {
                'output_x':
                    driving_a + driving_b + driving_c + transfer_k - state_a[0]
            }
        )

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        pass


class DummyFortran(Dummy):
    # overwrite states to explicitly set array order
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

    def initialise(self,
                   # component states
                   state_a, state_b,
                   **kwargs):
        dummyfortran.initialise(state_a[-1], state_b[-1])

    def run(self,
            # from exchanger
            transfer_k, transfer_l,
            # component driving data
            driving_a, driving_b, driving_c,
            # component ancillary data
            ancillary_c,
            # component parameters
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        transfer_i, transfer_j, output_x = dummyfortran.run(
            transfer_k, transfer_l,
            driving_a, driving_b, driving_c,
            ancillary_c,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return (
            # to exchanger
            {
                'transfer_i': transfer_i,
                'transfer_j': transfer_j
            },
            # component outputs
            {
                'output_x': output_x
            }
        )

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyfortran.finalise()


class DummyC(Dummy):

    def initialise(self,
                   # component states
                   state_a, state_b,
                   **kwargs):
        dummyc.initialise(state_a[-1], state_b[-1])

    def run(self,
            # from exchanger
            transfer_k, transfer_l,
            # component driving data
            driving_a, driving_b, driving_c,
            # component ancillary data
            ancillary_c,
            # component parameters
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        transfer_i, transfer_j, output_x = dummyc.run(
            transfer_k, transfer_l,
            driving_a, driving_b, driving_c,
            ancillary_c,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return (
            # to exchanger
            {
                'transfer_i': transfer_i,
                'transfer_j': transfer_j
            },
            # component outputs
            {
                'output_x': output_x
            }
        )

    def finalise(self,
                 # component states
                 state_a, state_b,
                 **kwargs):
        dummyc.finalise()
