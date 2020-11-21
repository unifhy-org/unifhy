import unittest
import doctest
import os
import numpy as np
from copy import deepcopy
from glob import glob

import cm4twc
from tests.test_time import (get_dummy_timedomain,
                             get_dummy_spin_up_start_end,
                             get_dummy_dumping_frequency)
from tests.test_component import get_dummy_component
from tests.test_states import compare_states
from tests.test_outputs import (get_expected_output, get_produced_output,
                                exp_outputs_raw)


class Simulator(object):
    def __init__(self, time_, space_, model):
        self.time_ = time_
        self.space_ = space_
        self.model = model

    @classmethod
    def from_scratch(cls, time_, space_, surfacelayer_kind, subsurface_kind,
                     openwater_kind, sources=None, id_trail=None):
        return cls(
            time_, space_,
            cls._set_up_model(
                time_, space_,
                surfacelayer_kind, subsurface_kind, openwater_kind,
                sources, id_trail
            )
        )

    @classmethod
    def from_yaml(cls, time_, space_):
        return cls(
            time_, space_,
            cm4twc.Model.from_yaml(
                'configurations/dummy_{}_{}.yml'.format(time_, space_)
            )
        )

    @staticmethod
    def _set_up_model(time_, space_, surfacelayer_kind, subsurface_kind,
                      openwater_kind, sources, id_trail):
        # for surfacelayer component
        category = 'surfacelayer'
        surfacelayer = get_dummy_component(
            category, surfacelayer_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )
        # for subsurface component
        category = 'subsurface'
        subsurface = get_dummy_component(
            category, subsurface_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )
        # for openwater
        category = 'openwater'
        openwater = get_dummy_component(
            category, openwater_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )

        # try to get an instance of model with the given combination
        model = cm4twc.Model(
            identifier='test-{}-{}-{}{}{}{}'.format(
                time_, space_,
                surfacelayer_kind, subsurface_kind, openwater_kind,
                '' if id_trail is None else id_trail
            ),
            config_directory='outputs',
            output_directory='outputs',
            surfacelayer=surfacelayer,
            subsurface=subsurface,
            openwater=openwater
        )

        return model

    def spinup_model(self, cycles=2):
        self.model.spin_up(
            *get_dummy_spin_up_start_end(), cycles,
            dumping_frequency=get_dummy_dumping_frequency(self.time_)
        )

    def run_model(self):
        self.model.simulate(
            dumping_frequency=get_dummy_dumping_frequency(self.time_)
        )

    def resume_model(self):
        self.model.resume(
            tag='run',
            at=(get_dummy_timedomain('daily').bounds.datetime_array[-1, -1]
                - get_dummy_dumping_frequency(self.time_))
        )

    def clean_up_files(self):
        files = []
        # clean up dump files potentially created
        files.extend(
            glob(os.sep.join([self.model.interface.output_directory,
                              self.model.identifier + '*_dump*.nc']))
        )
        # clean up output files potentially created
        files.extend(
            glob(os.sep.join([self.model.interface.output_directory,
                              self.model.identifier + '*_out*.nc']))
        )
        # clean up configuration files created
        files.extend(
            glob(os.sep.join([self.model.config_directory,
                              self.model.identifier + '*.yml']))
        )
        # convert dumps list to set to avoid potential duplicates
        for f in set(files):
            os.remove(f)


class TestModel(unittest.TestCase):
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

    def test_setup_spinup_simulate_resume(self):
        """
        The purpose of this test is to check that a complete workflow is
        functional, i.e.:
        - configure model;
        - spin-up model;
        - simulate model main run;
        - resume model main run at second-to-last snapshot.

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
        outputs because when one or more `NullComponent` is used in the
        combination, the final conditions are not expected to be
        'correct', and even less so 'consistent' from one combination
        to the next.
        """
        # generator of all possible component combinations
        # (i.e. full factorial design of experiment) as
        # tuple(surfacelayer kind, subsurface kind, openwater kind)
        # with 'c' for Component, 'd' for DataComponent, 'n' for NullComponent
        doe = ((sl, ss, ow)
               for sl in ('c', 'd', 'n')
               for ss in ('c', 'd', 'n')
               for ow in ('c', 'd', 'n'))

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind in doe:
            with self.subTest(surfacelayer=sl_kind,
                              subsurface=ss_kind,
                              openwater=ow_kind):
                # set up, spinup, and run model
                simulator = Simulator.from_scratch(self.t, self.s,
                                                   sl_kind, ss_kind, ow_kind)
                simulator.spinup_model()
                simulator.run_model()

                # store the last component states
                last_states_sl = deepcopy(simulator.model.surfacelayer.states)
                last_states_ss = deepcopy(simulator.model.subsurface.states)
                last_states_ow = deepcopy(simulator.model.openwater.states)

                # resume model
                simulator.resume_model()

                # check final state values are coherent
                self.assertTrue(
                    compare_states(last_states_sl,
                                   simulator.model.surfacelayer.states)
                )
                self.assertTrue(
                    compare_states(last_states_ss,
                                   simulator.model.subsurface.states)
                )
                self.assertTrue(
                    compare_states(last_states_ow,
                                   simulator.model.openwater.states)
                )

                # clean up
                simulator.clean_up_files()

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
        - checking the correctness of the final interface transfer values;
        - checking the correctness of the all component outputs (i.e.
          all component states, all component transfers, and all
          component outputs).
        """
        doe = ((sl, ss, ow)
               for sl in ('c', 'd')
               for ss in ('c', 'd')
               for ow in ('c', 'd'))

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind in doe:
            with self.subTest(surfacelayer=sl_kind,
                              subsurface=ss_kind,
                              openwater=ow_kind):

                # set up, and run model
                simulator = Simulator.from_scratch(self.t, self.s,
                                                   sl_kind, ss_kind, ow_kind)
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)
                # check outputs
                self.check_outputs(simulator.model)

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
        - checking the correctness of the final interface transfer values;
        - checking the correctness of the all component outputs (i.e.
          all component states, all component transfers, and all
          component outputs).
        """
        doe = ((sl, ss, ow)
               for sl in ('Python', 'Fortran', 'C')
               for ss in ('Python', 'Fortran', 'C')
               for ow in ('Python', 'Fortran', 'C'))

        # loop through all possible combinations of component sources
        for sl_src, ss_src, ow_src in doe:
            with self.subTest(surfacelayer=sl_src,
                              subsurface=ss_src,
                              openwater=ow_src):
                # set up, and run model
                simulator = Simulator.from_scratch(self.t, self.s,
                                                   'c', 'c', 'c',
                                                   {'surfacelayer': sl_src,
                                                    'subsurface': ss_src,
                                                    'openwater': ow_src})
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)
                # check outputs
                self.check_outputs(simulator.model)

                # clean up
                simulator.clean_up_files()

    def test_spinup_dump_init_spinup(self):
        """
        The purpose of this test is to check that a workflow going
        dump files, as follows:
        - configure first model;
        - spin-up first model;
        - configure second model;
        - initialise second model with dumps from first model last snapshot;
        - spin-up second model.

        The test only works with one combination of actual components.

        The functional character of the workflow is tested through:
        - completing with no error;
        - checking the correctness of the final component state values;
        - checking the correctness of the final interface transfer values.

        Note, since simulate period is of 12 days, and each spinup cycle
        is of 6 days, and given that the driving data is constant for
        the 12-day period, the final conditions with spinup+spinup
        will be the same as with simulate without spinup, which means
        that correctness of final conditions can be checked, but not
        outputs because they are scattered across two files of for
        simulation periods 6 days each.
        """
        # set up a model, and spin it up
        simulator_1 = Simulator.from_scratch(self.t, self.s, 'c', 'c', 'c')
        simulator_1.spinup_model(cycles=1)

        # set up another model
        simulator_2 = Simulator.from_scratch(self.t, self.s, 'c', 'c', 'c',
                                             id_trail='bis')

        # use dump of first model as initial conditions for second model
        simulator_2.model.surfacelayer.initialise_states_from_dump(
            os.sep.join([simulator_1.model.surfacelayer.output_directory,
                         simulator_1.model.surfacelayer.dump_file])
        )
        simulator_2.model.subsurface.initialise_states_from_dump(
            os.sep.join([simulator_1.model.subsurface.output_directory,
                         simulator_1.model.subsurface.dump_file])
        )
        simulator_2.model.openwater.initialise_states_from_dump(
            os.sep.join([simulator_1.model.openwater.output_directory,
                         simulator_1.model.openwater.dump_file])
        )

        simulator_2.model.initialise_transfers_from_dump(
            os.sep.join([simulator_1.model.interface.output_directory,
                         simulator_1.model.interface.dump_file])
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
        - checking the correctness of the final interface transfer values.
        """
        # set up a model from yaml configuration file
        simulator = Simulator.from_yaml(self.t, self.s)

        # start main run
        simulator.run_model()

        # check final state and transfer values
        self.check_final_conditions(simulator.model)
        # check outputs
        self.check_outputs(simulator.model)

        # clean up
        simulator.clean_up_files()

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
        - checking the correctness of the final interface transfer values.
        """
        # set up a model
        simulator_1 = Simulator.from_scratch(self.t, self.s, 'c', 'c', 'c')

        # set up another model using YAML of first model
        simulator_2 = Simulator(
            self.t, self.s,
            cm4twc.Model.from_yaml(
                os.sep.join([simulator_1.model.output_directory,
                             '{}.yml'.format(simulator_1.model.identifier)])
            )
        )

        # start main run of second model
        simulator_2.run_model()

        # check final state and transfer values
        self.check_final_conditions(simulator_2.model)
        # check outputs
        self.check_outputs(simulator_2.model)

        # clean up
        simulator_2.clean_up_files()

    def check_final_conditions(self, model):
        """
        This method checks that the final values of all component states
        values, and the final values of interface transfers are correct.
        """
        # check components' final state values
        for comp in [model.surfacelayer,
                     model.subsurface,
                     model.openwater]:
            self.check_component_states(comp)

        # check final transfer values
        self.check_interface_transfers(model.interface)

    def check_component_states(self, component):
        """
        This method checks that the final values of all component states
        are correct.
        """
        cat = component.category
        # if component is "real", otherwise no states
        if not isinstance(component, cm4twc.DataComponent):
            for state in ['state_a', 'state_b']:
                if exp_outputs_raw[self.t][cat].get(state) is None:
                    # some components feature only one state
                    continue
                # retrieve last state values
                arr = component.states[state][-1]
                # compare both min/max, as arrays are homogeneous
                try:
                    val = exp_outputs_raw[self.t][cat][state][-1]
                    self.assertEqual(np.amin(arr), val)
                    self.assertEqual(np.amax(arr), val)
                except AssertionError as e:
                    raise AssertionError(
                        "error for {}, {}".format(cat, state)
                    ) from e

    def check_interface_transfers(self, interface):
        """
        This method checks that the final values of interface transfers
        are correct.
        """
        for transfer in ['transfer_i', 'transfer_j', 'transfer_k',
                         'transfer_l', 'transfer_m', 'transfer_n',
                         'transfer_o']:
            arr = interface.transfers[transfer]['slices'][-1]
            cat = interface.transfers[transfer]['src_cat']
            # compare both min/max, as array should be homogeneous
            val = exp_outputs_raw[self.t][cat][transfer][-1]
            try:
                self.assertAlmostEqual(np.amin(arr), val)
                self.assertAlmostEqual(np.amax(arr), val)
            except AssertionError as e:
                raise AssertionError(
                    "error for {}".format(transfer)) from e

    def check_outputs(self, model):
        """
        This method checks that all values of all component states
        component transfers, component outputs are correct, from start
        to end.
        """
        for component in [model.surfacelayer,
                          model.subsurface,
                          model.openwater]:
            rtol, atol = cm4twc.rtol(), cm4twc.atol()

            # if component is "real", otherwise no outputs requested
            cat = component.category
            if not isinstance(component, cm4twc.DataComponent):
                for name, frequencies in component.outputs.items():
                    for delta, methods in frequencies.items():
                        for method in methods:
                            exp_t, exp_b, exp_o = get_expected_output(
                                self.t, component, name, delta, method
                            )
                            prd_t, prd_b, prd_o = get_produced_output(
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
                                np.testing.assert_allclose(prd_o, exp_o,
                                                           rtol, atol)
                            except AssertionError as e:
                                raise AssertionError(
                                    "error for {} component output {} values:"
                                    " {}, {}".format(cat, name, delta, method)
                                ) from e


class TestModelSameTimeSameSpace(TestModel):
    # flag to specify that components are to run at same temporal resolutions
    t = 'sync'
    # flag to specify that components are to run at same spatial resolution
    s = 'match'


class TestModelDiffTimeSameSpace(TestModel):
    # flag to specify that components are to run at different temporal resolutions
    t = 'async'
    # flag to specify that components are to run at same spatial resolution
    s = 'match'


class TestModelSameTimeDiffSpace(TestModel):
    # flag to specify that components are to run at same temporal resolutions
    t = 'sync'
    # flag to specify that components are to run at different spatial resolutions
    s = 'remap'


class TestModelDiffTimeDiffSpace(TestModel):
    # flag to specify that components are to run at different temporal resolutions
    t = 'async'
    # flag to specify that components are to run at different spatial resolutions
    s = 'remap'


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeSameSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeDiffSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))

    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
