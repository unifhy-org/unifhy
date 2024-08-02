from unifhy.component import NutrientSurfaceLayerComponent

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


class Dummy(NutrientSurfaceLayerComponent):
    # supersede existing inwards/outwards for physically meaningless ones
    _inwards_info = {
        "transfer_c": {
            "units": "1",
            "from": "nutrientsubsurface",
            "method": "mean",
        },
        "transfer_d": {
            "units": "1",
            "from": "nutrientopenwater",
            "method": "mean",
        },
        "transfer_f": {
            "units": "1",
            "from": "nutrientopenwater",
            "method": "mean",
        },
    }
    _outwards_info = {
        "transfer_a": {
            "units": "1",
            "to": ["nutrientsubsurface"],
            "method": "mean",
        },
        "transfer_b": {
            "units": "1",
            "to": ["nutrientopenwater"],
            "method": "mean",
        },
        "transfer_h": {"units": "1", "to": ["surfacelayer"], "method": "mean"},
    }
    # define some dummy inputs/parameters/constants/states/outputs
    _inwards = {"transfer_c", "transfer_d", "transfer_f"}
    _outwards = {"transfer_a", "transfer_b", "transfer_h"}
    _inputs_info = {
        "driving_d": {"units": "1", "kind": "dynamic"},
        "driving_e": {"units": "1", "kind": "dynamic"},
        "driving_f": {"units": "1", "kind": "dynamic"},
        "ancillary_e": {"units": "1", "kind": "static"},
    }
    # _parameters_info = {}
    # _constants_info = {}
    _states_info = {
        "state_a": {"units": "1", "divisions": 1},
        "state_b": {"units": "1", "divisions": 1},
    }
    _outputs_info = {"output_x": {"units": "1"}}
    _solver_history = 1
    _requires_land_sea_mask = True
    _requires_flow_direction = True
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
        transfer_c,
        transfer_d,
        transfer_f,
        # component driving data
        driving_d,
        driving_e,
        driving_f,
        # component ancillary data
        ancillary_e,
        # component parameters
        # component states
        state_a,
        state_b,
        # component constants
        **kwargs
    ):
        state_a.set_timestep(0, state_a.get_timestep(-1) + 1)
        state_b.set_timestep(0, state_b.get_timestep(-1) + 2)

        output_x, _ = self.spacedomain.route(
            driving_d + driving_e + driving_f + transfer_f - state_a.get_timestep(0)
        )

        return (
            # to exchanger
            {
                "transfer_a": driving_d
                + driving_e
                + transfer_d
                + ancillary_e * state_a.get_timestep(0),
                "transfer_b": driving_d
                + driving_e
                + driving_f
                + transfer_c
                + state_b.get_timestep(0),
                "transfer_h": state_a.get_timestep(0) * ancillary_e,
            },
            # component outputs
            {"output_x": output_x},
        )

    def finalise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        pass


class DummyFortran(Dummy):
    # overwrite states to explicitly set array order
    _states_info = {
        "state_a": {"units": "1", "divisions": 1, "order": "F"},
        "state_b": {"units": "1", "divisions": 1, "order": "F"},
    }

    def initialise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        if not self.initialised_states:
            dummyfortran.initialise(state_a.get_timestep(-1), state_b.get_timestep(-1))

    def run(
        self,
        # from exchanger
        transfer_c,
        transfer_d,
        transfer_f,
        # component driving data
        driving_d,
        driving_e,
        driving_f,
        # component ancillary data
        ancillary_e,
        # component parameters
        # component states
        state_a,
        state_b,
        # component constants
        **kwargs
    ):
        transfer_a, transfer_b, transfer_h, output_x = dummyfortran.run(
            transfer_c,
            transfer_d,
            transfer_f,
            driving_d,
            driving_e,
            driving_f,
            ancillary_e,
            state_a.get_timestep(-1),
            state_a.get_timestep(0),
            state_b.get_timestep(-1),
            state_b.get_timestep(0),
        )

        output_x, _ = self.spacedomain.route(output_x)

        return (
            # to exchanger
            {
                "transfer_a": transfer_a,
                "transfer_b": transfer_b,
                "transfer_h": transfer_h,
            },
            # component outputs
            {"output_x": output_x},
        )

    def finalise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        dummyfortran.finalise()


class DummyC(Dummy):
    def initialise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        if not self.initialised_states:
            dummyc.initialise(state_a.get_timestep(-1), state_b.get_timestep(-1))

    def run(
        self,
        # from exchanger
        transfer_c,
        transfer_d,
        transfer_f,
        # component driving data
        driving_d,
        driving_e,
        driving_f,
        # component ancillary data
        ancillary_e,
        # component parameters
        # component states
        state_a,
        state_b,
        # component constants
        **kwargs
    ):
        transfer_a, transfer_b, transfer_h, output_x = dummyc.run(
            transfer_c,
            transfer_d,
            transfer_f,
            driving_d,
            driving_e,
            driving_f,
            ancillary_e,
            state_a.get_timestep(-1),
            state_a.get_timestep(0),
            state_b.get_timestep(-1),
            state_b.get_timestep(0),
        )

        output_x, _ = self.spacedomain.route(output_x)

        return (
            # to exchanger
            {
                "transfer_a": transfer_a,
                "transfer_b": transfer_b,
                "transfer_h": transfer_h,
            },
            # component outputs
            {"output_x": output_x},
        )

    def finalise(
        self,
        # component states
        state_a,
        state_b,
        **kwargs
    ):
        dummyc.finalise()
