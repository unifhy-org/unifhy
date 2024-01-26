def run_dummy_component(states, transfers, data, component):
    # waterenergy surface layer dummy component
    if component == "sl":
        # transfer_k,
        # transfer_l,
        # transfer_n,
        # transfer_h,
        # component driving data
        # driving_a,
        # driving_b,
        # driving_c,
        # component ancillary data
        # ancillary_c,
        # component parameters
        # component states
        # state_a,
        # state_b):

        outputs = {}
        outputs["transfer_i"] = (
            data["driving_a"]
            + data["driving_b"]
            + transfers["transfer_l"]
            + data["ancillary_c"] * states["state_a"]
        )
        outputs["transfer_j"] = (
            data["driving_a"]
            + data["driving_b"]
            + data["driving_c"]
            + transfers["transfer_k"]
            + states["state_b"]
        )

        outputs["output_x"] = (
            data["driving_a"]
            + data["driving_b"]
            + data["driving_c"]
            + transfers["transfer_n"]
            - states["state_a"]
        )
        outputs["output_y"] = transfers["transfer_h"] * states["state_a"]

        return outputs

    # waterenergy subsurface dummy component
    elif component == "ss":
        # transfer_i,
        # transfer_n,
        # driving_a,
        # parameter_a,
        # state_a,
        # state_b):

        outputs = {}
        outputs["transfer_k"] = (
            data["driving_a"] * data["parameter_a"]
            + transfers["transfer_n"]
            + states["state_a"]
        )
        outputs["transfer_m"] = (
            data["driving_a"] * data["parameter_a"]
            + transfers["transfer_i"]
            + states["state_b"]
        )
        outputs["output_x"] = (
            data["driving_a"] * data["parameter_a"]
            + transfers["transfer_n"]
            - states["state_a"]
        )

        return outputs

    # waterenergy openwater dummy component
    elif component == "ow":
        # transfer_j,
        # transfer_m,
        # ancillary_b,
        # parameter_c,
        # state_a,
        # constant_c):

        outputs = {}
        outputs["transfer_l"] = (
            data["ancillary_b"] * transfers["transfer_m"] + states["state_a"]
        )
        outputs["transfer_n"] = data["parameter_c"] * transfers["transfer_j"]
        outputs["transfer_o"] = data["constant_c"] + transfers["transfer_j"]
        outputs["transfer_p"] = states["state_a"]

        outputs["output_x"] = (
            data["parameter_c"] * transfers["transfer_j"] + data["constant_c"]
        )
        outputs["output_y"] = (
            data["ancillary_b"] * transfers["transfer_m"] - states["state_a"]
        )

        return outputs

    # nutrient surface layer dummy component
    elif component == "nsl":
        # transfer_c,
        # transfer_d,
        # transfer_f,
        # driving_d,
        # driving_e,
        # driving_f,
        # ancillary_e,
        # state_a,
        # state_b):

        outputs = {}
        outputs["transfer_a"] = (
            data["driving_d"]
            + data["driving_e"]
            + transfers["transfer_d"]
            + data["ancillary_e"] * states["state_a"]
        )
        outputs["transfer_b"] = (
            data["driving_d"]
            + data["driving_e"]
            + data["driving_f"]
            + transfers["transfer_c"]
            + states["state_b"]
        )
        outputs["transfer_h"] = states["state_a"] * data["ancillary_e"]

        outputs["output_x"] = (
            data["driving_d"]
            + data["driving_e"]
            + data["driving_f"]
            + transfers["transfer_f"]
            - states["state_a"]
        )

        return outputs

    # nutrient subsurface dummy component
    elif component == "nss":
        # transfer_a,
        # transfer_f,
        # driving_d,
        # parameter_d,
        # state_a,
        # state_b):

        outputs = {}
        outputs["transfer_c"] = (
            data["driving_d"] * data["parameter_d"]
            + transfers["transfer_f"]
            + states["state_a"]
        )
        outputs["transfer_e"] = (
            data["driving_d"] * data["parameter_d"]
            + transfers["transfer_a"]
            + states["state_b"]
        )

        outputs["output_x"] = (
            data["driving_d"] * data["parameter_d"]
            + transfers["transfer_f"]
            - states["state_a"]
        )

        return outputs

    # nutrient openwater dummy component
    elif component == "now":
        # transfer_b,
        # transfer_e,
        # transfer_p,
        # ancillary_d,
        # parameter_e,
        # state_a,
        # constant_d):

        outputs = {}
        outputs["transfer_d"] = (
            data["ancillary_d"] * transfers["transfer_e"] + states["state_a"]
        )
        outputs["transfer_f"] = data["parameter_e"] * transfers["transfer_b"]
        outputs["transfer_g"] = data["constant_d"] + transfers["transfer_b"]

        outputs["output_x"] = (
            data["parameter_e"] * transfers["transfer_b"] + data["constant_d"]
        )
        outputs["output_y"] = (
            data["ancillary_d"] * transfers["transfer_e"]
            - states["state_a"]
            + transfers["transfer_p"]
        )

        return outputs

    else:
        raise Error("Component" + str(component) + " not found")
