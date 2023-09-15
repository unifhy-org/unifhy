import unittest
import doctest
from datetime import datetime, timedelta
import numpy as np
import cf
import cftime

import unifhy


def get_dummy_timedomain(resolution):
    if resolution == "daily":
        return unifhy.TimeDomain(
            timestamps=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            units="days since 2019-01-01 09:00:00Z",
            calendar="gregorian",
        )
    elif resolution == "2daily":
        return unifhy.TimeDomain(
            timestamps=[0, 2, 4, 6, 8, 10, 12, 14, 16],
            units="days since 2019-01-01 09:00:00Z",
            calendar="gregorian",
        )
    elif resolution == "4daily":
        return unifhy.TimeDomain(
            timestamps=[0, 4, 8, 12, 16],
            units="days since 2019-01-01 09:00:00Z",
            calendar="gregorian",
        )
    else:
        raise ValueError("timedomain resolution '{}' not supported".format(resolution))


def get_dummy_timedomain_different_start(resolution):
    return unifhy.TimeDomain.from_datetime_sequence(
        get_dummy_timedomain(resolution).bounds.datetime_array[1, :]
    )


def get_dummy_spin_up_start_end():
    return (
        cftime.DatetimeGregorian(2019, 1, 1, 9),
        cftime.DatetimeGregorian(2019, 1, 9, 9),
    )


def get_dummy_dumping_frequency(tag):
    if tag == "same_t":
        return timedelta(days=1)
    else:
        return timedelta(days=8)


def get_dummy_output_time_and_bounds(resolution, delta):
    timedomain = get_dummy_timedomain(resolution)
    timedomain = unifhy.TimeDomain.from_start_end_step(
        start=timedomain.bounds.datetime_array[0, 0],
        end=timedomain.bounds.datetime_array[-1, -1] + delta,
        step=delta,
        calendar=timedomain.calendar,
        units=timedomain.units,
    )
    return timedomain.time.array[1:], timedomain.bounds.array[:-1, :]


class TestTimeDomainAPI(unittest.TestCase):
    def test_timedomain_init_variants_standard_on_leap_year(self):
        # create a spacedomain using default instantiation
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="standard",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=datetime(2020, 2, 28, 9, 0, 0),
            end=datetime(2020, 3, 2, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                datetime(2020, 2, 28, 9, 0, 0),
                datetime(2020, 2, 29, 9, 0, 0),
                datetime(2020, 3, 1, 9, 0, 0),
                datetime(2020, 3, 2, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "standard",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    def test_timedomain_init_variants_gregorian_cal_on_leap_year(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="gregorian",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=cftime.DatetimeGregorian(2020, 2, 28, 9, 0, 0),
            end=cftime.DatetimeGregorian(2020, 3, 2, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                cftime.DatetimeGregorian(2020, 2, 28, 9, 0, 0),
                cftime.DatetimeGregorian(2020, 2, 29, 9, 0, 0),
                cftime.DatetimeGregorian(2020, 3, 1, 9, 0, 0),
                cftime.DatetimeGregorian(2020, 3, 2, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "gregorian",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    def test_timedomain_init_variants_julian_cal_on_leap_year(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="julian",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=cftime.DatetimeJulian(2020, 2, 28, 9, 0, 0),
            end=cftime.DatetimeJulian(2020, 3, 2, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                cftime.DatetimeJulian(2020, 2, 28, 9, 0, 0),
                cftime.DatetimeJulian(2020, 2, 29, 9, 0, 0),
                cftime.DatetimeJulian(2020, 3, 1, 9, 0, 0),
                cftime.DatetimeJulian(2020, 3, 2, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "julian",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    def test_timedomain_init_variants_noleap_cal_on_leap_year(self):
        # test on a leap year (e.g. 2020)
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="noleap",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=cftime.DatetimeNoLeap(2020, 2, 28, 9, 0, 0),
            end=cftime.DatetimeNoLeap(2020, 3, 3, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                cftime.DatetimeNoLeap(2020, 2, 28, 9, 0, 0),
                cftime.DatetimeNoLeap(2020, 3, 1, 9, 0, 0),
                cftime.DatetimeNoLeap(2020, 3, 2, 9, 0, 0),
                cftime.DatetimeNoLeap(2020, 3, 3, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "noleap",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    def test_timedomain_init_variants_all_leap_cal_on_leap_year(self):
        # test on a leap year (e.g. 2020)
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="all_leap",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=cftime.DatetimeAllLeap(2020, 2, 28, 9, 0, 0),
            end=cftime.DatetimeAllLeap(2020, 3, 2, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                cftime.DatetimeAllLeap(2020, 2, 28, 9, 0, 0),
                cftime.DatetimeAllLeap(2020, 2, 29, 9, 0, 0),
                cftime.DatetimeAllLeap(2020, 3, 1, 9, 0, 0),
                cftime.DatetimeAllLeap(2020, 3, 2, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "all_leap",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    def test_timedomain_init_variants_360_day_cal_on_leap_year(self):
        # test on a leap year (e.g. 2020)
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="360_day",
        )

        td2 = unifhy.TimeDomain.from_start_end_step(
            start=cftime.Datetime360Day(2020, 2, 28, 9, 0, 0),
            end=cftime.Datetime360Day(2020, 3, 1, 9, 0, 0),
            step=timedelta(days=1),
        )

        td3 = unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                cftime.Datetime360Day(2020, 2, 28, 9, 0, 0),
                cftime.Datetime360Day(2020, 2, 29, 9, 0, 0),
                cftime.Datetime360Day(2020, 2, 30, 9, 0, 0),
                cftime.Datetime360Day(2020, 3, 1, 9, 0, 0),
            )
        )

        f = cf.Field()
        f.set_construct(
            cf.DimensionCoordinate(
                properties={
                    "standard_name": "time",
                    "units": "days since 2020-02-28 09:00:00Z",
                    "calendar": "360_day",
                    "axis": "T",
                },
                data=cf.Data([0, 1, 2]),
                bounds=cf.Bounds(data=cf.Data([[0, 1], [1, 2], [2, 3]])),
            ),
            axes=f.set_construct(cf.DomainAxis(size=3)),
        )
        td4 = unifhy.TimeDomain.from_field(f)

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td1, td4)

    @unittest.expectedFailure
    def test_timedomain_init_irregular_timestep_in_timestamp_sequence(self):
        # should fail because last timestep is shorter
        unifhy.TimeDomain(
            timestamps=np.array([0, 2, 4, 5]),
            units="days since 2020-02-28 09:00:00Z",
            calendar="standard",
        )

    @unittest.expectedFailure
    def test_timedomain_init_irregular_timestep_in_datetime_sequence(self):
        # should fail because first timestep is longer
        unifhy.TimeDomain.from_datetime_sequence(
            datetimes=(
                datetime(2020, 1, 1, 9, 0, 0),
                datetime(2020, 1, 3, 9, 0, 0),
                datetime(2020, 1, 4, 9, 0, 0),
                datetime(2020, 1, 5, 9, 0, 0),
            )
        )


class TestTimeDomainComparison(unittest.TestCase):
    def test_timedomain_with_different_reference_dates(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([1, 2, 3, 4]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2019-01-02 09:00:00Z",
            calendar="standard",
        )

        self.assertEqual(td1, td2)

        td3 = unifhy.TimeDomain(
            timestamps=np.array([1, 2, 3, 4]),
            units="days since 2019-01-02 09:00:00Z",
            calendar="standard",
        )

        self.assertNotEqual(td1, td3)

    def test_timedomain_with_different_units_of_time(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]) * 86400,
            units="seconds since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]) * 24,
            units="hours since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td3 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td2, td3)

    def test_timedomain_with_different_alias_calendars(self):
        for cal, alias in unifhy.time._supported_calendar_mapping.items():
            if not cal == alias:
                td1 = unifhy.TimeDomain(
                    timestamps=np.array([0, 1, 2, 3]),
                    units="days since 2019-01-01 09:00:00Z",
                    calendar=cal,
                )

                td2 = unifhy.TimeDomain(
                    timestamps=np.array([0, 1, 2, 3]),
                    units="days since 2019-01-01 09:00:00Z",
                    calendar=alias,
                )

                try:
                    self.assertEqual(td1, td2)
                except AssertionError as e:
                    raise AssertionError(
                        "The calendar '{}' and its alias '{}' are not "
                        "found equal.".format(cal, alias)
                    ) from e

    def test_timedomain_with_different_dtypes(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3], dtype=np.float64),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td3 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3], dtype=np.int),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        self.assertEqual(td1, td2)
        self.assertEqual(td1, td3)
        self.assertEqual(td2, td3)

    def test_timedomain_with_different_lengths(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3, 4]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="standard",
        )

        self.assertNotEqual(td1, td2)

    @unittest.expectedFailure
    def test_timedomain_with_different_non_alias_calendars(self):
        # should fail because it cannot compare across different calendars
        td1 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="gregorian",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([0, 1, 2, 3]),
            units="days since 2019-01-01 09:00:00Z",
            calendar="julian",
        )

        self.assertEqual(td1, td2)

    def test_timedomain_spanned_periods(self):
        td1 = unifhy.TimeDomain(
            timestamps=np.array([1, 2, 3, 4, 5]),
            units="days since 1970-01-01 00:00:00",
            calendar="gregorian",
        )

        td2 = unifhy.TimeDomain(
            timestamps=np.array([1, 3, 5]),
            units="days since 1970-01-01 00:00:00",
            calendar="gregorian",
        )

        td3 = unifhy.TimeDomain(
            timestamps=np.array([1, 2, 3, 4]),
            units="days since 1970-01-01 00:00:00",
            calendar="gregorian",
        )

        td4 = unifhy.TimeDomain(
            timestamps=np.array([2, 3, 4, 5]),
            units="days since 1970-01-01 00:00:00",
            calendar="gregorian",
        )
        # same start/end, different timesteps, should be True
        self.assertTrue(td1.spans_same_period_as(td2))
        # same start, different ends, should be False
        self.assertFalse(td1.spans_same_period_as(td3))
        # different starts, same end, should be False
        self.assertFalse(td1.spans_same_period_as(td4))


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestTimeDomainAPI))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestTimeDomainComparison))

    test_suite.addTests(doctest.DocTestSuite(unifhy.time))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
