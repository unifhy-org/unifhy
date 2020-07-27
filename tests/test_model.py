import unittest
import doctest
import os
from copy import deepcopy
from glob import glob

import cm4twc
from tests.test_time import (get_dummy_timedomain,
                             get_dummy_timedomain_different_start,
                             get_dummy_spin_up_start_end,
                             get_dummy_dumping_frequency)
from tests.test_component import (get_dummy_subsurface_component,
                                  get_dummy_surfacelayer_component,
                                  get_dummy_openwater_component)
from tests.test_state import compare_states


class TestModelAPI(unittest.TestCase):
    # dictionary to store the model once initialised
    doe_models = {}

    # generator of all possible component combinations
    # (i.e. full factorial design of experiment) as
    # tuple(surfacelayer kind, subsurface kind, openwater kind)
    # with 'c' for Component, 'd' for DataComponent, 'n' for NullComponent
    doe = ((sl, ss, ow)
           for sl in ('c', 'd', 'n')
           for ss in ('c', 'd', 'n')
           for ow in ('c', 'd', 'n'))

    def setUp(self):
        self.model = None

    def tearDown(self):
        if self.model is not None:
            # clean up dump files potentially created
            files = []
            if self.model.surfacelayer.dump_file is not None:
                files.extend(
                    glob(os.sep.join([self.model.surfacelayer.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            if self.model.subsurface.dump_file is not None:
                files.extend(
                    glob(os.sep.join([self.model.subsurface.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            if self.model.openwater.dump_file is not None:
                files.extend(
                    glob(os.sep.join([self.model.openwater.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            files.extend(
                glob(os.sep.join([self.model.config_directory,
                                  self.model.identifier + '*.yml']))
            )
            # convert dumps list to set to avoid potential duplicates
            for f in set(files):
                os.remove(f)

    def test_0_model_init(self):
        # loop through all the possible combinations of components
        for surfacelayer_kind, subsurface_kind, openwater_kind in self.doe:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # for surfacelayer component
                surfacelayer = get_dummy_surfacelayer_component(
                    surfacelayer_kind)
                # for subsurface component
                subsurface = get_dummy_subsurface_component(
                    subsurface_kind)
                # for openwater
                openwater = get_dummy_openwater_component(
                    openwater_kind)

                # try to get an instance of model with the given combination
                self.model = cm4twc.Model(
                    identifier='test_{}{}{}'.format(
                        surfacelayer_kind, subsurface_kind, openwater_kind),
                    config_directory='outputs',
                    surfacelayer=surfacelayer,
                    subsurface=subsurface,
                    openwater=openwater
                )

                # store the model instance for reuse in other tests
                self.doe_models[(surfacelayer_kind, subsurface_kind,
                                 openwater_kind)] = self.model

                self.tearDown()

    def test_1_model_spin_up(self):
        # loop through all the possible combinations of components
        start, end = get_dummy_spin_up_start_end()
        for surfacelayer_kind, subsurface_kind, openwater_kind in \
                self.doe_models:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # try to run the model for the given combination
                self.model = self.doe_models[(surfacelayer_kind,
                                              subsurface_kind,
                                              openwater_kind)]
                self.model.spin_up(
                    start, end, cycles=2,
                    dumping_frequency=get_dummy_dumping_frequency()
                )

                self.tearDown()

    def test_2_model_simulate(self):
        # loop through all the possible combinations of components
        for surfacelayer_kind, subsurface_kind, openwater_kind in \
                self.doe_models:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # try to run the model for the given combination
                self.model = self.doe_models[(surfacelayer_kind,
                                              subsurface_kind,
                                              openwater_kind)]
                self.model.simulate(
                    dumping_frequency=get_dummy_dumping_frequency()
                )

                self.tearDown()

    def test_3_model_resume(self):
        # loop through all the possible combinations of components
        for surfacelayer_kind, subsurface_kind, openwater_kind in \
                self.doe_models:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # try to run the model for the given combination
                self.model = self.doe_models[(surfacelayer_kind,
                                              subsurface_kind,
                                              openwater_kind)]
                self.model.simulate(
                    dumping_frequency=get_dummy_dumping_frequency()
                )

                # store the last component states
                last_states_sl = deepcopy(self.model.surfacelayer.states)
                last_states_ss = deepcopy(self.model.subsurface.states)
                last_states_ow = deepcopy(self.model.openwater.states)

                # resume the model using dumps at the second to last snapshot
                last = get_dummy_timedomain().bounds.datetime_array[-1, -1]
                self.model.resume(at=last - get_dummy_dumping_frequency())

                # compare the component final states compared to stored ones
                self.assertTrue(
                    compare_states(last_states_sl,
                                   self.model.surfacelayer.states)
                )
                self.assertTrue(
                    compare_states(last_states_ss,
                                   self.model.subsurface.states)
                )
                self.assertTrue(
                    compare_states(last_states_ow,
                                   self.model.openwater.states)
                )

                self.tearDown()

    @unittest.expectedFailure
    def test_init_with_different_component_timedomains(self):
        # use NullComponents to test this
        surfacelayer = get_dummy_surfacelayer_component('n')
        subsurface = get_dummy_subsurface_component('n')
        openwater = get_dummy_openwater_component(
            'n', timedomain=get_dummy_timedomain_different_start())

        self.model = cm4twc.Model(
            identifier='test_different_timedomains',
            config_directory='outputs',
            surfacelayer=surfacelayer,
            subsurface=subsurface,
            openwater=openwater
        )

        self.model.simulate()


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelAPI))

    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
