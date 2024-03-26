# MJB 26/01/24
# Script for calculating the transfers and outputs of dummy components,
# which future tests are verified against in the UNIFHY framework.
# Provided for when further components are added to UNIFHY.
from dummy_components_for_testing import run_dummy_component
import numpy as np

"""
Components can be added as necessary in the 'dummy_nutrient_components_for_testing.py' file.
Each component will have access to all the data in the 'data' dictionary, two state variables:
state_a which increases by 1 each component tstep and state_b which increases by 2 each
component tstep, and two output variables: output_x and output_y.
The key variables to edit here are comptsteps, inmap and outmap.

The script will output two dictionaries, 'outputs' and 'transfers' containg the
output and transfer variables of each component. These can be then be put into
test_record.py in unifhy/test/tests/test_utils for comparison against in tests
that run when future edits to the unifhy code are made.
"""

tsteps = 16  # total number of framework timesteps
# number of framework timesteps that each component
# timestep covers. The framework timestep is the timestep
# of the component with the fatest updating timestep.
# If all components are running on the same timstep, set
# them all to 1.
comptsteps = {"sl": 1, "ss": 4, "ow": 2, "nsl": 2, "nss": 4, "now": 1}

# dictionary containing the names of the transfers that go INTO each component
inmap = {
    "sl": ["transfer_k", "transfer_l", "transfer_n", "transfer_h"],
    "ss": ["transfer_i", "transfer_n"],
    "ow": ["transfer_j", "transfer_m"],
    "nsl": ["transfer_c", "transfer_d", "transfer_f"],
    "nss": ["transfer_a", "transfer_f"],
    "now": ["transfer_b", "transfer_e", "transfer_p"],
}
# dictionary containing the names of the transfers that come OUT OF each component
outmap = {
    "sl": ["transfer_i", "transfer_j"],
    "ss": ["transfer_k", "transfer_m"],
    "ow": ["transfer_l", "transfer_n", "transfer_o", "transfer_p"],
    "nsl": ["transfer_a", "transfer_b", "transfer_h"],
    "nss": ["transfer_c", "transfer_e"],
    "now": ["transfer_d", "transfer_f", "transfer_g"],
}

# initial condition of the states. Each component can have two states.
# state_a increases by 1 each timestep, state_b by 2.
states = {}
for comp in comptsteps.keys():
    states[comp] = {"state_a": 0, "state_b": 0}

# initialise empty dictionary to contain outputs
# Each component can output to two outputs
outputs = {}
for comp in comptsteps.keys():
    outputs[comp] = {"output_x": [], "output_y": []}

# fixed in time data that a component might need to use
# initialise fixed-in-time driving data/ancils/constants/params
# All components will have access to this data.
data = {
    "driving_a": 1,
    "driving_b": 2,
    "driving_c": 3,
    "driving_d": 1,
    "driving_e": 2,
    "driving_f": 3,
    "ancillary_b": 2,
    "ancillary_c": 3,
    "ancillary_d": 2,
    "ancillary_e": 3,
    "parameter_a": 1,
    "parameter_c": 3,
    "parameter_d": 1,
    "parameter_e": 3,
    "constant_c": 3,
    "constant_d": 3,
}

# create empty dictionary to store the transfers
transferlist = []
for comp in inmap.keys():
    for tr in inmap[comp]:
        transferlist.append(tr)
for comp in outmap.keys():
    for tr in outmap[comp]:
        transferlist.append(tr)
transferlist = np.unique(np.asarray(transferlist))
transfers = {}
for tr in transferlist:
    transfers[tr] = []

# each component needs to keep track of it's own timestep, initialise here
comp_cur_tstep = {}
for comp in comptsteps.keys():
    comp_cur_tstep[comp] = 0

clock = clockgen(comptsteps, tsteps)

# Loop through framework timesteps
for tstep in range(1, tsteps + 1):
    print("Timestep " + str(tstep))

    # determines which components run for each framework timestep
    compswitches = next(clock)

    temp_outputs = {}

    # adapt so that all component specific stuff is in a dictionary
    # which can be looped over, to avoid having to code up each
    # individual component here
    for comp in compswitches.keys():
        if compswitches[comp] == 1:
            comp_cur_tstep[comp] += 1
            states[comp]["state_a"] += 1
            states[comp]["state_b"] += 2
            wtransfers = transfer_calc(transfers, inmap, outmap, comp)
            temp_outputs[comp] = run_dummy_component(
                states[comp], wtransfers, data, comp
            )

    # put into a loop over dictionaries with keys the component names
    # to avoid having to write out component specific stuff here
    for comp in compswitches.keys():
        if compswitches[comp] == 1:
            for tr in outmap[comp]:
                transfers[tr].append(temp_outputs[comp][tr])
            try:
                outputs[comp]["output_x"].append(temp_outputs[comp]["output_x"])
            except KeyError:
                pass
            try:
                outputs[comp]["output_y"].append(temp_outputs[comp]["output_y"])
            except KeyError:
                pass

print("transfer_k: " + str(transfers["transfer_k"]))
print("transfer_l: " + str(transfers["transfer_l"]))
print("transfer_n: " + str(transfers["transfer_n"]))
print("transfer_o: " + str(transfers["transfer_o"]))
print("transfer_h: " + str(transfers["transfer_h"]))
print("transfer_i: " + str(transfers["transfer_i"]))
print("transfer_j: " + str(transfers["transfer_j"]))
print("transfer_m: " + str(transfers["transfer_m"]))
print("transfer_c: " + str(transfers["transfer_c"]))
print("transfer_d: " + str(transfers["transfer_d"]))
print("transfer_f: " + str(transfers["transfer_f"]))
print("transfer_a: " + str(transfers["transfer_a"]))
print("transfer_b: " + str(transfers["transfer_b"]))
print("transfer_e: " + str(transfers["transfer_e"]))
print("transfer_p: " + str(transfers["transfer_p"]))
print("transfer_g: " + str(transfers["transfer_g"]))
print("output_x_sl: " + str(outputs["sl"]["output_x"]))
print("output_y_sl: " + str(outputs["sl"]["output_y"]))
print("output_x_ss: " + str(outputs["ss"]["output_x"]))
print("output_x_ow: " + str(outputs["ow"]["output_x"]))
print("output_y_ow: " + str(outputs["ow"]["output_y"]))
print("output_x_nsl: " + str(outputs["nsl"]["output_x"]))
print("output_x_nss: " + str(outputs["nss"]["output_x"]))
print("output_x_now: " + str(outputs["now"]["output_x"]))
print("output_y_now: " + str(outputs["now"]["output_y"]))
