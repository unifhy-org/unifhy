import unittest

import cm4twc._utils
from tests.test_time import (get_dummy_timedomain, get_dummy_dumping_frequency,
                             get_dummy_timedomain_different_start)


class TestClock(unittest.TestCase):
    # daily
    td_a = get_dummy_timedomain('daily')
    # 2-daily
    td_b = get_dummy_timedomain('2daily')
    # 3-daily
    td_c = get_dummy_timedomain('3daily')

    # dumping frequency
    dumping = get_dummy_dumping_frequency('async')

    # expected switches and indices
    exp_bool_a = [True, True, True, True, True, True,
                  True, True, True, True, True, True]
    exp_idx_a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    exp_bool_b = [False, True, False, True, False, True,
                  False, True, False, True, False, True]
    exp_idx_b = [0, 1, 2, 3, 4, 5]

    exp_bool_c = [False, False, True, False, False, True,
                  False, False, True, False, False, True]
    exp_idx_c = [0, 1, 2, 3]

    exp_bool_d = [True, False, False, False, False, False,
                  True, False, False, False, False, False]

    def test_clock_init(self):
        clock = cm4twc._utils.Clock(
            {'surfacelayer': self.td_a,
             'subsurface': self.td_b,
             'openwater': self.td_c},
        )
        clock.set_dumping_frequency(dumping_frequency=self.dumping)

        self.assertEqual(clock.switches['surfacelayer'].tolist(),
                         self.exp_bool_a)
        self.assertEqual(clock.switches['subsurface'].tolist(),
                         self.exp_bool_b)
        self.assertEqual(clock.switches['openwater'].tolist(),
                         self.exp_bool_c)
        self.assertEqual(clock.switches['dumping'].tolist(),
                         self.exp_bool_d)

    def test_clock_iteration(self):
        clock = cm4twc._utils.Clock(
            {'surfacelayer': self.td_a,
             'subsurface': self.td_b,
             'openwater': self.td_c}
        )

        out_bool_a, out_bool_b, out_bool_c = list(), list(), list()
        out_idx_a, out_idx_b, out_idx_c = list(), list(), list()

        for a, b, c, d in clock:
            out_bool_a.append(a)
            if a:
                out_idx_a.append(clock.get_current_timeindex('surfacelayer'))
            out_bool_b.append(b)
            if b:
                out_idx_b.append(clock.get_current_timeindex('subsurface'))
            out_bool_c.append(c)
            if c:
                out_idx_c.append(clock.get_current_timeindex('openwater'))

        self.assertEqual(out_bool_a, self.exp_bool_a)
        self.assertEqual(out_bool_b, self.exp_bool_b)
        self.assertEqual(out_bool_c, self.exp_bool_c)

        self.assertEqual(out_idx_a, self.exp_idx_a)
        self.assertEqual(out_idx_b, self.exp_idx_b)
        self.assertEqual(out_idx_c, self.exp_idx_c)

    @unittest.expectedFailure
    def test_clock_incompatible_timedomains(self):
        clock = cm4twc._utils.Clock(
            {'surfacelayer': get_dummy_timedomain_different_start('daily'),
             'subsurface': self.td_b,
             'openwater': self.td_c},
        )

    @unittest.expectedFailure
    def test_clock_incompatible_dumping_frequency(self):
        clock = cm4twc._utils.Clock(
            {'surfacelayer': self.td_a,
             'subsurface': self.td_b,
             'openwater': self.td_c},
        )
        clock.set_dumping_frequency(get_dummy_dumping_frequency('sync'))


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestClock))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
