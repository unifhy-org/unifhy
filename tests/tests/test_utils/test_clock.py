import unittest
import doctest

import unifhy._utils
from ..test_time import (
    get_dummy_timedomain,
    get_dummy_dumping_frequency,
    get_dummy_timedomain_different_start,
)


class TestClock(unittest.TestCase):
    # surfacelayer
    td_a = get_dummy_timedomain("daily")
    # subsurface
    td_b = get_dummy_timedomain("4daily")
    # openwater
    td_c = get_dummy_timedomain("2daily")
    # nutrientsurfacelayer
    td_d = get_dummy_timedomain("2daily")
    # nutrientsubsurface
    td_e = get_dummy_timedomain("4daily")
    # nutrientopenwater
    td_f = get_dummy_timedomain("daily")

    # dumping frequency
    dumping = get_dummy_dumping_frequency("async")

    # expected switches and indices
    # surfacelayer
    exp_bool_a = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]
    exp_idx_a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    # subsurface
    exp_bool_b = [
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
    ]
    exp_idx_b = [0, 1, 2, 3]

    # openwater
    exp_bool_c = [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
    ]
    exp_idx_c = [0, 1, 2, 3, 4, 5, 6, 7]

    # nutrientsurfacelayer
    exp_bool_d = [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
    ]
    exp_idx_d = [0, 1, 2, 3, 4, 5, 6, 7]

    # nutrientsubsurface
    exp_bool_e = [
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        True,
    ]
    exp_idx_e = [0, 1, 2, 3]

    # nutrientopenwater
    exp_bool_f = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]
    exp_idx_f = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    # dumping
    exp_bool_g = [
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]

    def test_clock_init(self):
        clock = unifhy._utils.Clock(
            {
                "surfacelayer": self.td_a,
                "subsurface": self.td_b,
                "openwater": self.td_c,
                "nutrientsurfacelayer": self.td_d,
                "nutrientsubsurface": self.td_e,
                "nutrientopenwater": self.td_f,
            },
        )
        clock.set_dumping_frequency(dumping_frequency=self.dumping)

        self.assertEqual(clock.switches["surfacelayer"].tolist(), self.exp_bool_a)
        self.assertEqual(clock.switches["subsurface"].tolist(), self.exp_bool_b)
        self.assertEqual(clock.switches["openwater"].tolist(), self.exp_bool_c)
        self.assertEqual(
            clock.switches["nutrientsurfacelayer"].tolist(), self.exp_bool_d
        )
        self.assertEqual(clock.switches["nutrientsubsurface"].tolist(), self.exp_bool_e)
        self.assertEqual(clock.switches["nutrientopenwater"].tolist(), self.exp_bool_f)
        self.assertEqual(clock.switches["dumping"].tolist(), self.exp_bool_g)

    def test_clock_iteration(self):
        clock = unifhy._utils.Clock(
            {
                "surfacelayer": self.td_a,
                "subsurface": self.td_b,
                "openwater": self.td_c,
                "nutrientsurfacelayer": self.td_d,
                "nutrientsubsurface": self.td_e,
                "nutrientopenwater": self.td_f,
            }
        )

        out_bool_a, out_bool_b, out_bool_c = list(), list(), list()
        out_bool_d, out_bool_e, out_bool_f = list(), list(), list()
        out_idx_a, out_idx_b, out_idx_c = list(), list(), list()
        out_idx_d, out_idx_e, out_idx_f = list(), list(), list()

        for a, b, c, d, e, f, g in clock:
            out_bool_a.append(a)
            if a:
                out_idx_a.append(clock.get_current_timeindex("surfacelayer"))
            out_bool_b.append(b)
            if b:
                out_idx_b.append(clock.get_current_timeindex("subsurface"))
            out_bool_c.append(c)
            if c:
                out_idx_c.append(clock.get_current_timeindex("openwater"))
            out_bool_d.append(d)
            if d:
                out_idx_d.append(clock.get_current_timeindex("nutrientsurfacelayer"))
            out_bool_e.append(e)
            if e:
                out_idx_e.append(clock.get_current_timeindex("nutrientsubsurface"))
            out_bool_f.append(f)
            if f:
                out_idx_f.append(clock.get_current_timeindex("nutrientopenwater"))

        self.assertEqual(out_bool_a, self.exp_bool_a)
        self.assertEqual(out_bool_b, self.exp_bool_b)
        self.assertEqual(out_bool_c, self.exp_bool_c)
        self.assertEqual(out_bool_d, self.exp_bool_d)
        self.assertEqual(out_bool_e, self.exp_bool_e)
        self.assertEqual(out_bool_f, self.exp_bool_f)

        self.assertEqual(out_idx_a, self.exp_idx_a)
        self.assertEqual(out_idx_b, self.exp_idx_b)
        self.assertEqual(out_idx_c, self.exp_idx_c)
        self.assertEqual(out_idx_d, self.exp_idx_d)
        self.assertEqual(out_idx_e, self.exp_idx_e)
        self.assertEqual(out_idx_f, self.exp_idx_f)

    @unittest.expectedFailure
    def test_clock_incompatible_timedomains(self):
        clock = unifhy._utils.Clock(
            {
                "surfacelayer": get_dummy_timedomain_different_start("daily"),
                "subsurface": self.td_b,
                "openwater": self.td_c,
                "nutrientsurfacelayer": self.td_d,
                "nutrientsubsurface": self.td_e,
                "nutrientopenwater": self.td_f,
            },
        )

    @unittest.expectedFailure
    def test_clock_incompatible_dumping_frequency(self):
        clock = unifhy._utils.Clock(
            {
                "surfacelayer": self.td_a,
                "subsurface": self.td_b,
                "openwater": self.td_c,
                "nutrientsurfacelayer": self.td_d,
                "nutrientsubsurface": self.td_e,
                "nutrientopenwater": self.td_f,
            },
        )
        clock.set_dumping_frequency(get_dummy_dumping_frequency("same_t"))


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestClock))

    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.clock))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
