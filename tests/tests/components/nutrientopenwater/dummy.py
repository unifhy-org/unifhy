from unifhy.component import NutrientOpenWaterComponent

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


class Dummy(NutrientOpenWaterComponent):
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        "transfer_b": {
            "units": "1",
            "from": "nutrientsurfacelayer",
            "method": "mean",
        },
        "transfer_e": {
            "units": "1",
            "from": "nutrientsubsurface",
            "method": "mean",
        },
        "transfer_p": {"units": "1", "from": "openwater", "method": "mean"},
    }
    _outwards_info = {
        "transfer_d": {
            "units": "1",
            "to": ["nutrientsurfacelayer"],
            "method": "mean",
        },
        "transfer_f": {
            "units": "1",
            "to": ["nutrientsurfacelayer", "nutrientsubsurface"],
            "method": "mean",
        },
        "transfer_g": {"units": "1", "to": ["ocean"], "method": "mean"},
    }
    # define some dummy inputs/parameters/constants/states/outputs
    _inwards = {"transfer_b", "transfer_e", "transfer_p"}
    _outwards = {"transfer_d", "transfer_f", "transfer_g"}
    _inputs_info = {
        "ancillary_d": {
            "units": "1",
            "kind": "climatologic",
            "frequency": "monthly",
            "description": "January to December",
        }
    }
    _parameters_info = {
        "parameter_e": {"units": "1"},
    }
    _constants_info = {"constant_d": {"units": "1", "default_value": 3}}
    _states_info = {"state_a": {"units": "1", "divisions": (4, "constant_d")}}
    _outputs_info = {"output_x": {"units": "1"}, "output_y": {"units": "1"}}
    _solver_history = 1
    _requires_land_sea_mask = False
    _requires_flow_direction = False
    _requires_cell_area = False

    def initialise(
        self,
        # component states
        state_a,
        # component constants
        constant_d,
        **kwargs
    ):
        if not self.initialised_states:
            state_a.set_timestep(-1, 0)

    def run(
        self,
        # from exchanger
        transfer_b,
        transfer_e,
        transfer_p,
        # component driving data
        # component ancillary data
        ancillary_d,
        # component parameters
        parameter_e,
        # component states
        state_a,
        # component constants
        constant_d,
        **kwargs
    ):
        state_a.set_timestep(0, state_a.get_timestep(-1) + 1)

        return (
            # to exchanger
            {
                "transfer_d": ancillary_d[11] * transfer_e
                + state_a.get_timestep(0)[..., 0, 0],
                "transfer_f": parameter_e * transfer_b,
                "transfer_g": constant_d + transfer_b,
            },
            # component outputs
            {
                "output_x": parameter_e * transfer_b + constant_d,
                "output_y": ancillary_d[11][0] * transfer_e
                - state_a.get_timestep(0)[..., 0, 0]
                + transfer_p,
            },
        )

    def finalise(
        self,
        # component states
        state_a,
        **kwargs
    ):
        pass
