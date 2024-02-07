import unittest
import doctest
import os
import numpy as np
from copy import deepcopy
from glob import glob

import unifhy
from .test_time import (
    get_dummy_timedomain,
    get_dummy_spin_up_start_end,
    get_dummy_dumping_frequency,
)
from .test_component import get_dummy_component
from .test_utils.test_state import compare_states
from .test_utils.test_record import (
    get_expected_record,
    get_produced_record,
    exp_records_raw,
)


class Simulator(object):
    def __init__(self, time_, space_, model):
        self.time_ = time_
        self.space_ = space_
        self.model = model

    @classmethod
    def from_scratch(
        cls,
        time_,
        space_,
        surfacelayer_kind,
        subsurface_kind,
        openwater_kind,
        nutrient_surfacelayer_kind,
        nutrient_subsurface_kind,
        nutrient_openwater_kind,
        sources=None,
        id_trail=None,
    ):
        return cls(
            time_,
            space_,
            cls._set_up_model(
                time_,
                space_,
                surfacelayer_kind,
                subsurface_kind,
                openwater_kind,
                nutrient_surfacelayer_kind,
                nutrient_subsurface_kind,
                nutrient_openwater_kind,
                sources,
                id_trail,
            ),
        )

    @classmethod
    def from_yaml(cls, time_, space_):
        return cls(
            time_,
            space_,
            unifhy.Model.from_yaml(
                "configurations/dummy_{}_{}.yml".format(time_, space_)
            ),
        )

    @staticmethod
    def _set_up_model(
        time_,
        space_,
        surfacelayer_kind,
        subsurface_kind,
        openwater_kind,
        nutrient_surfacelayer_kind,
        nutrient_subsurface_kind,
        nutrient_openwater_kind,
        sources,
        id_trail,
    ):
        # for surfacelayer component
        category = "surfacelayer"
        surfacelayer = get_dummy_component(
            category,
            surfacelayer_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # for nutrient surfacelayer component
        category = "nutrientsurfacelayer"
        nutrientsurfacelayer = get_dummy_component(
            category,
            nutrient_surfacelayer_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # for subsurface component
        category = "subsurface"
        subsurface = get_dummy_component(
            category,
            subsurface_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # for nutrient subsurface component
        category = "nutrientsubsurface"
        nutrientsubsurface = get_dummy_component(
            category,
            nutrient_subsurface_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # for openwater
        category = "openwater"
        openwater = get_dummy_component(
            category,
            openwater_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # for nutrient openwater
        category = "nutrientopenwater"
        nutrientopenwater = get_dummy_component(
            category,
            nutrient_openwater_kind,
            time_,
            space_,
            "Python" if sources is None else sources.get(category, "Python"),
        )

        # try to get an instance of model with the given combination
        model = unifhy.Model(
            identifier="test-{}-{}-{}{}{}{}{}{}{}".format(
                time_,
                space_,
                surfacelayer_kind,
                subsurface_kind,
                openwater_kind,
                nutrient_surfacelayer_kind,
                nutrient_subsurface_kind,
                nutrient_openwater_kind,
                "" if id_trail is None else id_trail,
            ),
            config_directory="outputs",
            saving_directory="outputs",
            surfacelayer=surfacelayer,
            subsurface=subsurface,
            openwater=openwater,
            nutrientsurfacelayer=nutrientsurfacelayer,
            nutrientsubsurface=nutrientsubsurface,
            nutrientopenwater=nutrientopenwater,
        )

        return model

    def spinup_model(self, cycles=2):
        self.model.spin_up(
            *get_dummy_spin_up_start_end(),
            cycles,
            dumping_frequency=get_dummy_dumping_frequency(self.time_)
        )

    def run_model(self):
        self.model.simulate(dumping_frequency=get_dummy_dumping_frequency(self.time_))

    def resume_model(self, tag="run"):
        if tag == "run":
            at = get_dummy_timedomain("daily").bounds.datetime_array[
                -1, -1
            ] - get_dummy_dumping_frequency(self.time_)
        else:  # tag == 'spinup'
            at = get_dummy_spin_up_start_end()[-1] - get_dummy_dumping_frequency(
                self.time_
            )

        self.model.resume(tag=tag, at=at)

    def clean_up_files(self):
        # clean up configuration files created
        self.clean_up_config_files()
        # clean up dump files potentially created
        self.clean_up_dump_files()
        # clean up record files potentially created
        self.clean_up_record_files()

    def clean_up_config_files(self):
        files = glob(
            os.sep.join([self.model.config_directory, self.model.identifier + "*.yml"])
        )
        # convert config file list to set to avoid potential duplicates
        for f in set(files):
            os.remove(f)

    def clean_up_dump_files(self):
        files = []
        files.extend(
            glob(
                os.sep.join(
                    [
                        self.model.exchanger.saving_directory,
                        self.model.identifier + "*_dump*.nc",
                    ]
                )
            )
        )
        if self.model.surfacelayer.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.surfacelayer.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientsurfacelayer.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientsurfacelayer.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        if self.model.subsurface.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.subsurface.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientsubsurface.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientsubsurface.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        if self.model.openwater.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.openwater.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientopenwater.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientopenwater.saving_directory,
                            self.model.identifier + "*_dump*.nc",
                        ]
                    )
                )
            )
        # convert dumps list to set to avoid potential duplicates
        for f in set(files):
            os.remove(f)

    def clean_up_record_files(self):
        files = []
        if self.model.surfacelayer.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.surfacelayer.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientsurfacelayer.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientsurfacelayer.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        if self.model.subsurface.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.subsurface.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientsubsurface.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientsubsurface.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        if self.model.openwater.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.openwater.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        if self.model.nutrientopenwater.saving_directory is not None:
            files.extend(
                glob(
                    os.sep.join(
                        [
                            self.model.nutrientopenwater.saving_directory,
                            self.model.identifier + "*_records*.nc",
                        ]
                    )
                )
            )
        # convert record file list to set to avoid potential duplicates
        for f in set(files):
            os.remove(f)


class BasicTestModel(object):
    # flag to specify whether components are to run at same temporal resolution
    # or at different temporal resolutions
    t = None
    # flag to specify whether components are to run at same spatial resolution
    # or at different spatial resolutions
    s = None

    def setUp(self):
        self.simulator = None

    def tearDown(self):
        if self.simulator is not None:
            self.simulator.clean_up_files()

    def shortDescription(self):
        return None

    def test_spinup_dump_init_spinup(self):
        """
        The purpose of this test is to check that a workflow going
        dump files, as follows:
        - configure first model;
        - spin-up first model;
        - configure second model;
        - initialise second model with dumps from first model last snapshot;
        - spin-up second model.

        The test only works with a combination of actual components.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values.

        Note, since simulate period is of 16 days, and each spinup cycle
        is of 8 days, and given that the driving data is constant for
        the 16-day period, the final conditions with spinup+spinup
        will be the same as with simulate without spinup, which means
        that correctness of final conditions can be checked, but not
        records because they are scattered across two files of for
        simulation periods 8 days each.
        """
        # set up a model, and spin it up
        simulator_1 = Simulator.from_scratch(
            self.t, self.s, "c", "c", "c", "c", "c", "c"
        )
        simulator_1.spinup_model(cycles=1)

        # set up another model
        simulator_2 = Simulator.from_scratch(
            self.t, self.s, "c", "c", "c", "c", "c", "c", id_trail="bis"
        )

        # use dump of first model as initial conditions for second model
        simulator_2.model.surfacelayer.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.surfacelayer.saving_directory,
                    simulator_1.model.surfacelayer.dump_file,
                ]
            )
        )
        simulator_2.model.nutrientsurfacelayer.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.nutrientsurfacelayer.saving_directory,
                    simulator_1.model.nutrientsurfacelayer.dump_file,
                ]
            )
        )
        simulator_2.model.subsurface.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.subsurface.saving_directory,
                    simulator_1.model.subsurface.dump_file,
                ]
            )
        )
        simulator_2.model.nutrientsubsurface.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.nutrientsubsurface.saving_directory,
                    simulator_1.model.nutrientsubsurface.dump_file,
                ]
            )
        )
        simulator_2.model.openwater.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.openwater.saving_directory,
                    simulator_1.model.openwater.dump_file,
                ]
            )
        )
        simulator_2.model.nutrientopenwater.initialise_states_from_dump(
            os.sep.join(
                [
                    simulator_1.model.nutrientopenwater.saving_directory,
                    simulator_1.model.nutrientopenwater.dump_file,
                ]
            )
        )

        simulator_2.model.initialise_transfers_from_dump(
            os.sep.join(
                [
                    simulator_1.model.exchanger.saving_directory,
                    simulator_1.model.exchanger.dump_file,
                ]
            )
        )

        # spin second model up
        simulator_2.spinup_model(cycles=1)

        # check final state and transfer values
        self.check_final_conditions(simulator_2.model)

    def test_yaml_setup_simulate(self):
        """
        The purpose of this test is to check that the following workflow
        is functional:
        - configure model using a YAML model configuration file;
        - simulate model main run.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values;
        - checking the values in the record files.
        """
        # set up a model from yaml configuration file
        simulator = Simulator.from_yaml(self.t, self.s)

        # start main run
        simulator.run_model()

        # check final state and transfer values
        self.check_final_conditions(simulator.model)
        # check records
        self.check_records(simulator.model)

        # clean up
        simulator.clean_up_files()

    def test_setup_simulate_resume_run(self):
        """
        The purpose of this test is to check that the following workflow
        is functional:
        - configure model;
        - simulate model main run;
        - resume model main run at second-to-last snapshot.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values;
        - checking the values in the record files.
        """
        # set up a model from yaml configuration file
        simulator = Simulator.from_scratch(self.t, self.s, "c", "c", "c", "c", "c", "c")

        # start main run
        simulator.run_model()

        # resume main run
        simulator.resume_model()

        # check final state and transfer values
        self.check_final_conditions(simulator.model)
        # check records
        self.check_records(simulator.model)

        # clean up
        simulator.clean_up_files()

    def test_setup_spinup_yaml_resume_spinup(self):
        """
        The purpose of this test is to check that the following workflow
        is functional:
        - configure first model;
        - spin-up first model (2 cycles);
        - configure second model using YAML configuration file of first model;
        - resume second model first spinup at second-to-last snapshot;
        - configure third model using YAML configuration file of first model;
        - resume third model second spinup at second-to-last snapshot.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values.

        Note, since simulate period is of 16 days, and each spinup cycle
        is of 8 days, and given that the driving data is constant for
        the 16-day period, the final conditions with spinup+spinup
        will be the same as with simulate without spinup, which means
        that correctness of final conditions can be checked, but not
        records because they are scattered across two files of for
        simulation periods 8 days each.
        """
        # set up a model
        simulator_1 = Simulator.from_scratch(
            self.t, self.s, "c", "c", "c", "c", "c", "c"
        )

        # spinup model
        simulator_1.spinup_model()

        # check final state and transfer values
        self.check_final_conditions(simulator_1.model)

        # set up another model using YAML of first model
        simulator_2 = Simulator(
            self.t,
            self.s,
            unifhy.Model.from_yaml(
                os.sep.join(
                    [
                        simulator_1.model.saving_directory,
                        "{}.yml".format(simulator_1.model.identifier),
                    ]
                )
            ),
        )

        # resume first spin-up run
        simulator_2.resume_model(tag="spinup1")

        # check final state and transfer values
        self.check_final_conditions(simulator_2.model)

        # set up yet another model using YAML of first model
        simulator_3 = Simulator(
            self.t,
            self.s,
            unifhy.Model.from_yaml(
                os.sep.join(
                    [
                        simulator_1.model.saving_directory,
                        "{}.yml".format(simulator_1.model.identifier),
                    ]
                )
            ),
        )

        # resume second spin-up run
        simulator_3.resume_model(tag="spinup2")

        # check final state and transfer values
        self.check_final_conditions(simulator_3.model)

        # clean up
        simulator_1.clean_up_files()

    def test_setup_yaml_setup_simulate(self):
        """
        The purpose of this test is to check that the following workflow
        is functional:
        - configure first model;
        - configure second model using YAML configuration file of first model;
        - simulate model main run.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values;
        - checking the values in the record files.
        """
        # set up a model
        simulator_1 = Simulator.from_scratch(
            self.t, self.s, "c", "c", "c", "c", "c", "c"
        )

        # set up another model using YAML of first model
        simulator_2 = Simulator(
            self.t,
            self.s,
            unifhy.Model.from_yaml(
                os.sep.join(
                    [
                        simulator_1.model.saving_directory,
                        "{}.yml".format(simulator_1.model.identifier),
                    ]
                )
            ),
        )

        # start main run of second model
        simulator_2.run_model()

        # check final state and transfer values
        self.check_final_conditions(simulator_2.model)
        # check records
        self.check_records(simulator_2.model)

        # clean up
        simulator_2.clean_up_files()

    def test_setup_spinup_simulate_resume_run(self):
        """
        The purpose of this test is to check that a complete workflow is
        functional, i.e.:
        - configure first model;
        - spin-up first model;
        - simulate first model main run;
        - configure second model using YAML configuration file of first model;
        - resume second model main run at second-to-last snapshot.

        Unlike its "advanced" counterpart, this test considers only one
        combinations of actual `Component`, `DataComponent`, and
        `NullComponent`.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking equality of the final component states at the end of
          simulate and at the end of resume.

        Note, this test does not check for correctness of final
        states and transfers conditions, nor correctness of final
        records because when one or more `NullComponent` is used in the
        combination, the final conditions are not expected to be
        'correct', and even less so 'consistent' from one combination
        to the next.
        """
        # set up, spinup, and run model
        simulator_1 = Simulator.from_scratch(
            self.t, self.s, "d", "c", "n", "d", "c", "n"
        )
        simulator_1.spinup_model()
        simulator_1.run_model()

        # store the last component states
        last_states_sl = deepcopy(simulator_1.model.surfacelayer.states)
        last_states_ss = deepcopy(simulator_1.model.subsurface.states)
        last_states_ow = deepcopy(simulator_1.model.openwater.states)
        last_states_nsl = deepcopy(simulator_1.model.nutrientsurfacelayer.states)
        last_states_nss = deepcopy(simulator_1.model.nutrientsubsurface.states)
        last_states_now = deepcopy(simulator_1.model.nutrientopenwater.states)

        # set up another model using YAML of first model
        simulator_2 = Simulator(
            self.t,
            self.s,
            unifhy.Model.from_yaml(
                os.sep.join(
                    [
                        simulator_1.model.saving_directory,
                        "{}.yml".format(simulator_1.model.identifier),
                    ]
                )
            ),
        )

        # resume model run
        simulator_2.resume_model()

        # check final state values are coherent
        self.assertTrue(
            compare_states(last_states_sl, simulator_2.model.surfacelayer.states)
        )
        self.assertTrue(
            compare_states(
                last_states_nsl, simulator_2.model.nutrientsurfacelayer.states
            )
        )
        self.assertTrue(
            compare_states(last_states_ss, simulator_2.model.subsurface.states)
        )
        self.assertTrue(
            compare_states(last_states_nss, simulator_2.model.nutrientsubsurface.states)
        )
        self.assertTrue(
            compare_states(last_states_ow, simulator_2.model.openwater.states)
        )
        self.assertTrue(
            compare_states(last_states_now, simulator_2.model.nutrientopenwater.states)
        )

        # clean up
        simulator_1.clean_up_files()

    def check_final_conditions(self, model):
        """
        This method checks that the final values of all component states
        values, and the final values of exchanger transfers are correct.
        """
        # check components' final state values
        for comp in [
            model.surfacelayer,
            model.subsurface,
            model.openwater,
            model.nutrientsurfacelayer,
            model.nutrientsubsurface,
            model.nutrientopenwater,
        ]:
            self.check_component_states(comp)

        # check final transfer values
        self.check_exchanger_transfers(model.exchanger)

    def check_component_states(self, component):
        """
        This method checks that the final values of all component states
        are correct.
        """
        cat = component.category
        # if component is "real", otherwise no states
        if not isinstance(component, unifhy.DataComponent):
            for state in ["state_a", "state_b"]:
                if exp_records_raw[self.t][cat].get(state) is None:
                    # some components feature only one state
                    continue
                # retrieve last state values
                arr = component.states[state].get_timestep(-1)
                # compare both min/max, as arrays are homogeneous
                try:
                    val = exp_records_raw[self.t][cat][state][-1]
                    self.assertEqual(np.amin(arr), val)
                    self.assertEqual(np.amax(arr), val)
                except AssertionError as e:
                    raise AssertionError("error for {}, {}".format(cat, state)) from e

    def check_exchanger_transfers(self, exchanger):
        """
        This method checks that the final values of exchanger transfers
        are correct.
        """
        for transfer in [
            "transfer_a",
            "transfer_b",
            "transfer_c",
            "transfer_d",
            "transfer_e",
            "transfer_f",
            "transfer_g",
            "transfer_h",
            "transfer_i",
            "transfer_j",
            "transfer_k",
            "transfer_l",
            "transfer_m",
            "transfer_n",
            "transfer_o",
            "transfer_p",
        ]:
            arr = exchanger.transfers[transfer]["slices"][-1]
            cat = exchanger.transfers[transfer]["src_cat"]
            # compare both min/max, as array should be homogeneous
            val = exp_records_raw[self.t][cat][transfer][-1]
            try:
                self.assertAlmostEqual(np.amin(arr), val)
                self.assertAlmostEqual(np.amax(arr), val)
            except AssertionError as e:
                raise AssertionError("error for {}".format(transfer)) from e

    def check_records(self, model):
        """
        This method checks that all values of all component states
        component transfers, component records are correct, from start
        to end.
        """
        for component in [
            model.surfacelayer,
            model.subsurface,
            model.openwater,
            model.nutrientsurfacelayer,
            model.nutrientsubsurface,
            model.nutrientopenwater,
        ]:
            rtol, atol = unifhy.rtol(), unifhy.atol()

            # if component is "real", otherwise no records requested
            cat = component.category
            if not isinstance(component, unifhy.DataComponent):
                for name, frequencies in component.records.items():
                    for delta, methods in frequencies.items():
                        for method in methods:
                            exp_t, exp_b, exp_o = get_expected_record(
                                self.t, component, name, delta, method
                            )
                            prd_t, prd_b, prd_o = get_produced_record(
                                component, name, delta, method
                            )
                            try:
                                np.testing.assert_array_equal(prd_t, exp_t)
                            except AssertionError as e:
                                raise AssertionError(
                                    "error for {} component output {} time:"
                                    " {}, {}".format(cat, name, delta, method)
                                ) from e
                            try:
                                np.testing.assert_array_equal(prd_b, exp_b)
                            except AssertionError as e:
                                raise AssertionError(
                                    "error for {} component output {} bounds:"
                                    " {}, {}".format(cat, name, delta, method)
                                ) from e
                            try:
                                np.testing.assert_allclose(prd_o, exp_o, rtol, atol)
                            except AssertionError as e:
                                raise AssertionError(
                                    "error for {} component output {} values:"
                                    " {}, {}".format(cat, name, delta, method)
                                ) from e


class AdvancedTestModel(BasicTestModel):
    def test_setup_spinup_simulate_resume_run(self):
        """
        The purpose of this test is to check that a complete workflow is
        functional, i.e.:
        - configure first model;
        - spin-up first model;
        - simulate first model main run;
        - configure second model using YAML configuration file of first model;
        - resume second model main run at second-to-last snapshot.

        The test generates a 'design of experiment' (doe) to consider
        all possible combinations of actual `Component`, `DataComponent`,
        and `NullComponent`. Then, each experiment (i.e. each
        combination) is used as a subtest.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking equality of the final component states at the end of
          simulate and at the end of resume.

        Note, this test does not check for correctness of final
        states and transfers conditions, nor correctness of final
        records because when one or more `NullComponent` is used in the
        combination, the final conditions are not expected to be
        'correct', and even less so 'consistent' from one combination
        to the next.
        """
        # generator of all possible component combinations
        # (i.e. full factorial design of experiment) as
        # tuple(surfacelayer kind, subsurface kind, openwater kind)
        # with 'c' for Component, 'd' for DataComponent, 'n' for NullComponent
        doe = (
            (sl, ss, ow, nsl, nss, now)
            for sl in ("c", "d", "n")
            for ss in ("c", "d", "n")
            for ow in ("c", "d", "n")
            for nsl in ("c", "d", "n")
            for nss in ("c", "d", "n")
            for now in ("c", "d", "n")
        )

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind, nsl_kind, nss_kind, now_kind in doe:
            with self.subTest(
                surfacelayer=sl_kind,
                subsurface=ss_kind,
                openwater=ow_kind,
                nutrientsurfacelayer=nsl_kind,
                nutrientsubsurface=nss_kind,
                nutrientopenwater=now_kind,
            ):
                # set up, spinup, and run model
                simulator_1 = Simulator.from_scratch(
                    self.t,
                    self.s,
                    sl_kind,
                    ss_kind,
                    ow_kind,
                    nsl_kind,
                    nss_kind,
                    now_kind,
                )
                simulator_1.spinup_model()
                simulator_1.run_model()

                # store the last component states
                last_states_sl = deepcopy(simulator_1.model.surfacelayer.states)
                last_states_ss = deepcopy(simulator_1.model.subsurface.states)
                last_states_ow = deepcopy(simulator_1.model.openwater.states)
                last_states_nsl = deepcopy(
                    simulator_1.model.nutrientsurfacelayer.states
                )
                last_states_nss = deepcopy(simulator_1.model.nutrientsubsurface.states)
                last_states_now = deepcopy(simulator_1.model.nutrientopenwater.states)

                # set up another model using YAML of first model
                simulator_2 = Simulator(
                    self.t,
                    self.s,
                    unifhy.Model.from_yaml(
                        os.sep.join(
                            [
                                simulator_1.model.saving_directory,
                                "{}.yml".format(simulator_1.model.identifier),
                            ]
                        )
                    ),
                )

                # resume model run
                simulator_2.resume_model()

                # check final state values are coherent
                self.assertTrue(
                    compare_states(
                        last_states_sl, simulator_2.model.surfacelayer.states
                    )
                )
                self.assertTrue(
                    compare_states(
                        last_states_nsl,
                        simulator_2.model.nutrientsurfacelayer.states,
                    )
                )
                self.assertTrue(
                    compare_states(last_states_ss, simulator_2.model.subsurface.states)
                )
                self.assertTrue(
                    compare_states(
                        last_states_nss,
                        simulator_2.model.nutrientsubsurface.states,
                    )
                )
                self.assertTrue(
                    compare_states(last_states_ow, simulator_2.model.openwater.states)
                )
                self.assertTrue(
                    compare_states(
                        last_states_now,
                        simulator_2.model.nutrientopenwater.states,
                    )
                )

                # clean up
                simulator_1.clean_up_files()

    def test_setup_simulate(self):
        """
        The purpose of this test is to check that a standard workflow
        is functional, i.e.:
        - configure model;
        - simulate model main run.

        The test generates a 'design of experiment' (doe) to consider
        all possible combinations of actual `Component` and
        `DataComponent`. Then, each experiment (i.e. each combination)
        is used as a subtest.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values;
        - checking the correctness of the all component records (i.e.
          all component states, all component transfers, and all
          component outputs).
        """
        doe = (
            (sl, ss, ow, nsl, nss, now)
            for sl in ("c", "d")
            for ss in ("c", "d")
            for ow in ("c", "d")
            for nsl in ("c", "d")
            for nss in ("c", "d")
            for now in ("c", "d")
        )

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind, nsl_kind, nss_kind, now_kind in doe:
            with self.subTest(
                surfacelayer=sl_kind,
                subsurface=ss_kind,
                openwater=ow_kind,
                nutrientsurfacelayer=nsl_kind,
                nutrientsubsurface=nss_kind,
                nutrientopenwater=now_kind,
            ):
                # set up, and run model
                simulator = Simulator.from_scratch(
                    self.t,
                    self.s,
                    sl_kind,
                    ss_kind,
                    ow_kind,
                    nsl_kind,
                    nss_kind,
                    now_kind,
                )
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)
                # check records
                self.check_records(simulator.model)

                # clean up
                simulator.clean_up_files()

    def test_setup_simulate_various_sources(self):
        """
        The purpose of this test is to check that, no matter the
        language of the component source code, a standard workflow
        is functional, i.e.:
        - configure model;
        - simulate model main run.

        The test generates a 'design of experiment' (doe) to consider
        all possible combinations of source code in Python, Fortran, and
        C. Then, each experiment (i.e. each combination)  is used as a
        subtest.

        The test only works with one combination of actual components.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final exchanger transfer values;
        - checking the correctness of the all component records (i.e.
          all component states, all component transfers, and all
          component outputs).
        """
        doe = (
            (sl, ss, ow, nsl, nss, now)
            for sl in ("Python", "Fortran", "C")
            for ss in ("Python", "Fortran", "C")
            for ow in ("Python", "Fortran", "C")
            for nsl in ("Python", "Fortran", "C")
            for nss in ("Python", "Fortran", "C")
            for now in ("Python", "Fortran", "C")
        )

        # loop through all possible combinations of component sources
        for sl_src, ss_src, ow_src, nsl_src, nss_src, now_src in doe:
            with self.subTest(
                surfacelayer=sl_src,
                subsurface=ss_src,
                openwater=ow_src,
                nutrientsurfacelayer=nsl_src,
                nutrientsubsurface=nss_src,
                nutrientopenwater=now_src,
            ):
                # set up, and run model
                simulator = Simulator.from_scratch(
                    self.t,
                    self.s,
                    "c",
                    "c",
                    "c",
                    "c",
                    "c",
                    "c",
                    {
                        "surfacelayer": sl_src,
                        "subsurface": ss_src,
                        "openwater": ow_src,
                        "nutrientsurfacelayer": nsl_src,
                        "nutrientsubsurface": nss_src,
                        "nutrientopenwater": now_src,
                    },
                )
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)
                # check records
                self.check_records(simulator.model)

                # clean up
                simulator.clean_up_files()


class TestModelSameTimeSameSpace(AdvancedTestModel, unittest.TestCase):
    # flag to specify that components are to run at same temporal resolutions
    t = "same_t"
    # flag to specify that components are to run at same spatial resolution
    s = "same_s"


class TestModelDiffTimeSameSpace(AdvancedTestModel, unittest.TestCase):
    # flag to specify that components are to run at different temporal resolutions
    t = "diff_t"
    # flag to specify that components are to run at same spatial resolution
    s = "same_s"


class TestModelSameTimeDiffSpace(AdvancedTestModel, unittest.TestCase):
    # flag to specify that components are to run at same temporal resolutions
    t = "same_t"
    # flag to specify that components are to run at different spatial resolutions
    s = "diff_s"


class TestModelDiffTimeDiffSpace(AdvancedTestModel, unittest.TestCase):
    # flag to specify that components are to run at different temporal resolutions
    t = "diff_t"
    # flag to specify that components are to run at different spatial resolutions
    s = "diff_s"


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeSameSpace))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelSameTimeDiffSpace))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))

    test_suite.addTests(doctest.DocTestSuite(unifhy.model))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
