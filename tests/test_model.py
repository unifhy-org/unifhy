import unittest
import doctest

import cm4twc
from tests.test_time import (get_dummy_timedomain_different_end,
                             get_dummy_spin_up_start_end)
from tests.test_components import (get_dummy_subsurface_component,
                                   get_dummy_surfacelayer_component,
                                   get_dummy_openwater_component)


class TestModelAPI(unittest.TestCase):
    # dictionary to store the model once initialised
    doe_models = {}

    def setUp(self):
        # full factorial design of experiment
        # (i.e. all possible combinations of components)
        self.doe = (
            # tuple(surfacelayer_component, subsurface_component, openwater_component)
            # with 'c' for _Component, 'd' for DataComponent, 'n' for NullComponent
            ('c', 'c', 'c'),
            ('d', 'c', 'c'),
            ('n', 'c', 'c'),
            ('c', 'd', 'c'),
            ('d', 'd', 'c'),
            ('n', 'd', 'c'),
            ('c', 'n', 'c'),
            ('d', 'n', 'c'),
            ('n', 'n', 'c'),
            ('c', 'c', 'd'),
            ('d', 'c', 'd'),
            ('n', 'c', 'd'),
            ('c', 'd', 'd'),
            ('d', 'd', 'd'),
            ('n', 'd', 'd'),
            ('c', 'n', 'd'),
            ('d', 'n', 'd'),
            ('n', 'n', 'd'),
            ('c', 'c', 'n'),
            ('d', 'c', 'n'),
            ('n', 'c', 'n'),
            ('c', 'd', 'n'),
            ('d', 'd', 'n'),
            ('n', 'd', 'n'),
            ('c', 'n', 'n'),
            ('d', 'n', 'n'),
            ('n', 'n', 'n')
        )

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
                self.doe_models[(surfacelayer_kind, subsurface_kind,
                                 openwater_kind)] = cm4twc.Model(
                    surfacelayer=surfacelayer,
                    subsurface=subsurface,
                    openwater=openwater
                )

    def test_1_model_spin_up(self):
        # loop through all the possible combinations of components
        start, end = get_dummy_spin_up_start_end()
        for surfacelayer_kind, subsurface_kind, openwater_kind in \
                self.doe_models:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # try to run the model for the given combination
                self.doe_models[(surfacelayer_kind, subsurface_kind,
                                 openwater_kind)].spin_up(start, end, cycles=2)

    def test_2_model_simulate(self):
        # loop through all the possible combinations of components
        for surfacelayer_kind, subsurface_kind, openwater_kind in \
                self.doe_models:
            with self.subTest(surfacelayer=surfacelayer_kind,
                              subsurface=subsurface_kind,
                              openwater=openwater_kind):
                # try to run the model for the given combination
                self.doe_models[(surfacelayer_kind, subsurface_kind,
                                 openwater_kind)].simulate()

    @unittest.expectedFailure
    def test_init_with_different_component_timedomains(self):
        # use NullComponents to test this
        surfacelayer = get_dummy_surfacelayer_component('n')
        subsurface = get_dummy_subsurface_component('n')
        openwater = get_dummy_openwater_component(
            'n', timedomain=get_dummy_timedomain_different_end())

        cm4twc.Model(
            surfacelayer=surfacelayer,
            subsurface=subsurface,
            openwater=openwater
        )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelAPI))

    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
