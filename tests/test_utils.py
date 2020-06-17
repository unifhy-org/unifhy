import unittest
import numpy as np

import cm4twc._utils


class TestClockAPI(unittest.TestCase):

    def setUp(self):
        self.td_a = cm4twc.TimeDomain(
            timestamps=(np.array([0, 1, 2, 3, 4, 5, 6]) * 86400.),
            units='seconds since 1970-01-02 00:00:00',
            calendar='standard'
        )

        self.td_b = cm4twc.TimeDomain(
            timestamps=(np.array([1, 3, 5, 7]) * 86400),
            units='seconds since 1970-01-01 00:00:00',
            calendar='gregorian'
        )

        self.td_c = cm4twc.TimeDomain(
            timestamps=np.array([1, 4, 7]),
            units='days since 1970-01-01 00:00:00',
            calendar='gregorian'
        )

        self.exp_bool_a = [True, True, True, True, True, True, True]
        self.exp_idx_a = [0, 1, 2, 3, 4, 5]

        self.exp_bool_b = [True, False, True, False, True, False, True]
        self.exp_idx_b = [0, 1, 2]

        self.exp_bool_c = [True, False, False, True, False, False, True]
        self.exp_idx_c = [0, 1]

    def test_clock_init(self):
        clock = cm4twc._utils.Clock(surfacelayer_timedomain=self.td_a,
                                    subsurface_timedomain=self.td_b,
                                    openwater_timedomain=self.td_c)

        self.assertEqual(clock._surfacelayer_switch.tolist(), self.exp_bool_a)
        self.assertEqual(clock._subsurface_switch.tolist(), self.exp_bool_b)
        self.assertEqual(clock._openwater_switch.tolist(), self.exp_bool_c)

    def test_clock_iteration(self):
        clock = cm4twc._utils.Clock(surfacelayer_timedomain=self.td_a,
                                    subsurface_timedomain=self.td_b,
                                    openwater_timedomain=self.td_c)

        out_bool_a, out_bool_b, out_bool_c = list(), list(), list()
        out_idx_a, out_idx_b, out_idx_c = list(), list(), list()

        for a, b, c in clock:
            out_bool_a.append(a)
            if a:
                out_idx_a.append(clock.get_current_timeindex('surfacelayer'))
            out_bool_b.append(b)
            if b:
                out_idx_b.append(clock.get_current_timeindex('subsurface'))
            out_bool_c.append(c)
            if c:
                out_idx_c.append(clock.get_current_timeindex('openwater'))

        self.assertEqual(out_bool_a, self.exp_bool_a[:-1])
        self.assertEqual(out_bool_b, self.exp_bool_b[:-1])
        self.assertEqual(out_bool_c, self.exp_bool_c[:-1])

        self.assertEqual(out_idx_a, self.exp_idx_a)
        self.assertEqual(out_idx_b, self.exp_idx_b)
        self.assertEqual(out_idx_c, self.exp_idx_c)


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestClockAPI))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
