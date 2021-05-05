from cm4twc.components import OpenWaterComponent
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


class Dummy(OpenWaterComponent):
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        'transfer_j': {
            'units': '1',
            'from': 'surfacelayer',
            'method': 'mean'
        },
        'transfer_m': {
            'units': '1',
            'from': 'subsurface',
            'method': 'mean'
        }
    }
    _outwards_info = {
        'transfer_l': {
            'units': '1',
            'to': ['surfacelayer'],
            'method': 'mean'
        },
        'transfer_n': {
            'units': '1',
            'to': ['surfacelayer', 'subsurface'],
            'method': 'mean'
        },
        'transfer_o': {
            'units': '1',
            'to': ['ocean'],
            'method': 'mean'
        }
    }
    # define some dummy inputs/parameters/constants/states/outputs
    _inputs_info = {
        'ancillary_b': {
            'units': '1',
            'kind': 'climatologic',
            'frequency': 'monthly',
            'description': 'January to December'
        }
    }
    _parameters_info = {
        'parameter_c': {
            'units': '1'
        },
    }
    _constants_info = {
        'constant_c': {
            'units': '1',
            'default_value': 3
        }
    }
    _states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1
        }
    }
    _outputs_info = {
        'output_x': {
            'units': '1'
        },
        'output_y': {
            'units': '1'
        }
    }
    _solver_history = 1

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):

        state_a[-1][:] = 0

    def run(self,
            # from exchanger
            transfer_j, transfer_m,
            # component driving data
            # component ancillary data
            ancillary_b,
            # component parameters
            parameter_c,
            # component states
            state_a,
            # component constants
            constant_c,
            **kwargs):

        state_a[0][:] = state_a[-1] + 1

        return (
            # to exchanger
            {
                'transfer_l': ancillary_b[11] * transfer_m + state_a[0],
                'transfer_n': parameter_c * transfer_j,
                'transfer_o': constant_c + transfer_j
            },
            # component outputs
            {
                'output_x': parameter_c * transfer_j + constant_c,
                'output_y': ancillary_b[11] * transfer_m - state_a[0],
            }
        )

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        pass


class DummyFortran(Dummy):
    # overwrite states to explicitly set array order
    _states_info = {
        'state_a': {
            'units': '1',
            'divisions': 1,
            'order': 'F'
        }
    }

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):
        dummyfortran.initialise(state_a[-1])

    def run(self,
            # from exchanger
            transfer_j, transfer_m,
            # component driving data
            # component ancillary data
            ancillary_b,
            # component parameters
            parameter_c,
            # component states
            state_a,
            # component constants
            constant_c,
            **kwargs):

        transfer_l, transfer_n, transfer_o, output_x, output_y = (
            dummyfortran.run(
                transfer_j, transfer_m, ancillary_b, parameter_c,
                state_a[-1], state_a[0], constant_c
            )
        )

        return (
            # to exchanger
            {
                'transfer_l': transfer_l,
                'transfer_n': transfer_n,
                'transfer_o': transfer_o
            },
            # component outputs
            {
                'output_x': output_x,
                'output_y': output_y
            }
        )

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        dummyfortran.finalise()


class DummyC(Dummy):

    def initialise(self,
                   # component states
                   state_a,
                   **kwargs):
        dummyc.initialise(state_a[-1])

    def run(self,
            # from exchanger
            transfer_j, transfer_m,
            # component driving data
            # component ancillary data
            ancillary_b,
            # component parameters
            parameter_c,
            # component states
            state_a,
            # component constants
            constant_c,
            **kwargs):

        transfer_l, transfer_n, transfer_o, output_x, output_y = (
            dummyc.run(
                transfer_j, transfer_m, ancillary_b, parameter_c,
                state_a[-1], state_a[0], constant_c
            )
        )

        return (
            # to exchanger
            {
                'transfer_l': transfer_l,
                'transfer_n': transfer_n,
                'transfer_o': transfer_o
            },
            # component outputs
            {
                'output_x': output_x,
                'output_y': output_y
            }
        )

    def finalise(self,
                 # component states
                 state_a,
                 **kwargs):
        dummyc.finalise()
