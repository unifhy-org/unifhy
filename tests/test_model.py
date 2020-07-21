import unittest
import doctest
import os
from glob import glob

import cm4twc
from tests.test_time import (get_dummy_timedomain_different_start,
                             get_dummy_spin_up_start_end,
                             get_dummy_dumping_frequency)
from tests.test_components import (get_dummy_subsurface_component,
                                   get_dummy_surfacelayer_component,
                                   get_dummy_openwater_component)


class TestModelAPI(unittest.TestCase):
    # dictionary to store the model once initialised
    doe_models = {}

    # full factorial design of experiment
    # (i.e. all possible combinations of components)

    # with 'c' for Component, 'd' for DataComponent, 'n' for NullComponent
    kinds = ('c', 'd', 'n')

    # generator of component combinations
    # tuple(surfacelayer_component, subsurface_component, openwater_component)
    doe = ((sl, ss, ow) for sl in kinds for ss in kinds for ow in kinds)

    def setUp(self):
        self.model = None

    def tearDown(self):
        if self.model is not None:
            # clean up dump files potentially created
            dumps = []
            if self.model.surfacelayer.dump_file is not None:
                dumps.extend(
                    glob(os.sep.join([self.model.surfacelayer.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            if self.model.subsurface.dump_file is not None:
                dumps.extend(
                    glob(os.sep.join([self.model.subsurface.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            if self.model.openwater.dump_file is not None:
                dumps.extend(
                    glob(os.sep.join([self.model.openwater.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
            # convert dumps list to set to avoid potential duplicates
            for d in set(dumps):
                os.remove(d)

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
