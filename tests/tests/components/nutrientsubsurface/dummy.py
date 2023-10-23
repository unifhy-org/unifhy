from unifhy.component import NutrientSubSurfaceComponent

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


class Dummy(NutrientSubSurfaceComponent):
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        "transfer_a": {
            "units": "1",
            "from": "nutrientsurfacelayer",
            "method": "mean",
        },
        "transfer_f": {
            "units": "1",
            "from": "nutrientopenwater",
            "method": "mean",
        },
    }
    _outwards_info = {
        "transfer_c": {
            "units": "1",
            "to": ["nutrientsurfacelayer"],
            "method": "mean",
        },
        "transfer_e": {
            "units": "1",
            "to": ["nutrientopenwater"],
            "method": "mean",
        },
    }
    # define some dummy inputs/parameters/constants/states/outputs
    _inwards = {"transfer_a", "transfer_f"}
    _outwards = {"transfer_c", "transfer_e"}
    _inputs_info = {"driving_d": {"units": "1", "kind": "dynamic"}}
    _parameters_info = {"parameter_d": {"units": "1"}}
    # _constants_info = {}
    _states_info = {
        "state_a": {"units": "1", "divisions": 1},
        "state_b": {"units": "1", "divisions": 1},
    }
    _outputs_info = {"output_x": {"units": "1"}}
    _solver_history = 1
    _requires_land_sea_mask = False
    _requires_flow_direction = False
    _requires_cell_area = False

    def initialise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        if not self.initialised_states:
            state_a.set_timestep(-1, 0)
            state_b.set_timestep(-1, 0)

    def run(
        self,
        # from exchanger
        transfer_a,
        transfer_f,
        # component driving data
        driving_d,
        # component ancillary data
        # component parameters
        parameter_d,
        # component states
        state_a,
        state_b,
        # component constants
        **kwargs
    ):
        state_a.set_timestep(0, state_a.get_timestep(-1) + 1)
        state_b.set_timestep(0, state_b.get_timestep(-1) + 2)

        return (
            # to exchanger
            {
                "transfer_c": driving_d * parameter_d
                + transfer_f
                + state_a.get_timestep(0),
                "transfer_e": driving_d * parameter_d
                + transfer_a
                + state_b.get_timestep(0),
            },
            # component outputs
            {
                "output_x": driving_d * parameter_d
                + transfer_f
                - state_a.get_timestep(0)
            },
        )

    def finalise(
        self,
        # to exchanger
        state_a,
        state_b,
        **kwargs
    ):
        pass
