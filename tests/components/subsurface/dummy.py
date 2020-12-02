from cm4twc.components import SubSurfaceComponent
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


class Dummy(SubSurfaceComponent):
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        'transfer_i': {
            'units': '1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'transfer_n': {
            'units': '1',
            'from': 'openwater',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'transfer_k': {
            'units': '1',
            'to': 'surfacelayer',
            'method': 'mean'
        },
        'transfer_m': {
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
        }
    }
    parameters_info = {
        'parameter_a': {
            'units': '1'
        }
    }
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
            # from interface
            transfer_i, transfer_n,
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

        return (
            # to interface
            {
                'transfer_k': driving_a * parameter_a + transfer_n + state_a[0],
                'transfer_m': driving_a * parameter_a + transfer_i + state_b[0]
            },
            # component outputs
            {
                'output_x': driving_a * parameter_a + transfer_n - state_a[0]
            }
        )

    def finalise(self,
                 # to interface
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
            # from interface
            transfer_i, transfer_n,
            # component driving data
            driving_a,
            # component ancillary data
            # component parameters
            parameter_a,
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        transfer_k, transfer_m, output_x = dummyfortran.run(
            transfer_i, transfer_n,
            driving_a, parameter_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return (
            # to interface
            {
                'transfer_k': transfer_k,
                'transfer_m': transfer_m
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
            # from interface
            transfer_i, transfer_n,
            # component driving data
            driving_a,
            # component ancillary data
            # component parameters
            parameter_a,
            # component states
            state_a, state_b,
            # component constants
            **kwargs):

        transfer_k, transfer_m, output_x = dummyc.run(
            transfer_i, transfer_n,
            driving_a, parameter_a,
            state_a[-1], state_a[0], state_b[-1], state_b[0]
        )

        return (
            # to interface
            {
                'transfer_k': transfer_k,
                'transfer_m': transfer_m
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
