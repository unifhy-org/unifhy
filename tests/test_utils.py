import unittest
import numpy as np
from datetime import timedelta

import cm4twc._utils


class TestClockAPI(unittest.TestCase):

    def setUp(self):
        # daily
        self.td_a = cm4twc.TimeDomain(
            timestamps=np.array([0, 1, 2, 3, 4, 5, 6,
                                 7, 8, 9, 10, 11, 12]),
            units='days since 1970-01-01 00:00:00',
            calendar='standard'
        )
        # 2-daily
        self.td_b = cm4twc.TimeDomain(
            timestamps=np.array([0, 2, 4, 6, 8, 10, 12]),
            units='days since 1970-01-01 00:00:00',
            calendar='gregorian'
        )
        # 3-daily
        self.td_c = cm4twc.TimeDomain(
            timestamps=np.array([0, 3, 6, 9, 12]),
            units='days since 1970-01-01 00:00:00',
            calendar='gregorian'
        )

        self.d = timedelta(days=6)

        self.exp_bool_a = [True, True, True, True, True, True,
                           True, True, True, True, True, True]
        self.exp_idx_a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        self.exp_bool_b = [False, True, False, True, False, True,
                           False, True, False, True, False, True]
        self.exp_idx_b = [0, 1, 2, 3, 4, 5]

        self.exp_bool_c = [False, False, True, False, False, True,
                           False, False, True, False, False, True]
        self.exp_idx_c = [0, 1, 2, 3]

        self.exp_bool_d = [True, False, False, False, False, False,
                           True, False, False, False, False, False]

    def test_clock_init(self):
        clock = cm4twc._utils.Clock(
            {'surfacelayer': self.td_a,
             'subsurface': self.td_b,
             'openwater': self.td_c},
        )
        clock.set_dumping_frequency(dumping_frequency=self.d)

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


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestClockAPI))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
