import datetime
import unittest

from freezegun import freeze_time

from extensions.dashboard.builders.utils import (
    get_earliest_and_latest_dates,
    calculate_average_per_month,
    fill_missing_data_with_0_and_sort_by_month,
    fill_month_data_with_zero_qty,
)
from extensions.utils import format_text_to_bold


class DashboardUtilsTestCase(unittest.TestCase):
    @staticmethod
    def _sample_deployment_data():
        return {
            "5fde855f12db509a2785d899": {
                datetime.date(2022, 2, 1): 1,
                datetime.date(2022, 3, 1): 1,
                datetime.date(2022, 4, 1): 0,
                datetime.date(2022, 5, 1): 0,
                datetime.date(2022, 6, 1): 0,
            },
            "629e30cdf3dcc4921092c7f8": {},
        }

    def test_get_earliest_and_latest_dates(self):
        earliest, latest, latest_without_zero = get_earliest_and_latest_dates(
            self._sample_deployment_data()
        )
        self.assertEqual(datetime.date(2022, 2, 1), earliest)
        self.assertEqual(datetime.date(2022, 6, 1), latest)
        self.assertEqual(datetime.date(2022, 3, 1), latest_without_zero)

    def test_get_earliest_and_latest_dates__empty_data(self):
        earliest, latest, latest_without_zero = get_earliest_and_latest_dates({})
        for value in [earliest, latest, latest_without_zero]:
            self.assertEqual(None, value)

    def test_calculate_average_per_month(self):
        res = calculate_average_per_month(
            10, datetime.date(2022, 2, 1), datetime.date(2022, 6, 1)
        )
        self.assertEqual(2, res)

    def test_calculate_average_per_month__one_month(self):
        res = calculate_average_per_month(
            10, datetime.date(2022, 2, 1), datetime.date(2022, 2, 1)
        )
        self.assertEqual(10, res)

    @freeze_time("2022-06-30")
    def test_fill_and_sort_gadget_data(self):
        res = fill_missing_data_with_0_and_sort_by_month(
            self._sample_deployment_data(), datetime.date(2022, 2, 1)
        )
        expected_res = {
            datetime.date(2022, 2, 1): {
                "5fde855f12db509a2785d899": 1,
                "629e30cdf3dcc4921092c7f8": 0,
            },
            datetime.date(2022, 3, 1): {
                "5fde855f12db509a2785d899": 1,
                "629e30cdf3dcc4921092c7f8": 0,
            },
            datetime.date(2022, 4, 1): {
                "5fde855f12db509a2785d899": 0,
                "629e30cdf3dcc4921092c7f8": 0,
            },
            datetime.date(2022, 5, 1): {
                "5fde855f12db509a2785d899": 0,
                "629e30cdf3dcc4921092c7f8": 0,
            },
            datetime.date(2022, 6, 1): {
                "5fde855f12db509a2785d899": 0,
                "629e30cdf3dcc4921092c7f8": 0,
            },
        }
        self.assertEqual(expected_res, res)

    @freeze_time("2022-06-30")
    def test_fill_month_data_with_zero_qty__more_then_year_data(self):
        data = {
            datetime.date(2022, 2, 1): 1,
            datetime.date(2022, 3, 1): 1,
            datetime.date(2022, 4, 1): 0,
            datetime.date(2022, 5, 1): 0,
            datetime.date(2022, 6, 1): 0,
        }
        res = fill_month_data_with_zero_qty(data, datetime.date(2021, 2, 1))
        expected_res = {
            datetime.date(2021, 2, 1): 0,
            datetime.date(2021, 3, 1): 0,
            datetime.date(2021, 4, 1): 0,
            datetime.date(2021, 5, 1): 0,
            datetime.date(2021, 6, 1): 0,
            datetime.date(2021, 7, 1): 0,
            datetime.date(2021, 8, 1): 0,
            datetime.date(2021, 9, 1): 0,
            datetime.date(2021, 10, 1): 0,
            datetime.date(2021, 11, 1): 0,
            datetime.date(2021, 12, 1): 0,
            datetime.date(2022, 1, 1): 0,
            datetime.date(2022, 2, 1): 1,
            datetime.date(2022, 3, 1): 1,
            datetime.date(2022, 4, 1): 0,
            datetime.date(2022, 5, 1): 0,
            datetime.date(2022, 6, 1): 0,
        }
        self.assertEqual(expected_res, res)

    def test_format_text_to_bold__accepted_values(self):
        value = "Huma is awesome"
        res = format_text_to_bold(value)
        self.assertEqual(f"<strong>{value}</strong>", res)

    def test_format_text_to_bold__should_be_set_to_None(self):
        values = [0, None]
        for value in values:
            res = format_text_to_bold(value)
            self.assertEqual(None, res)


if __name__ == "__main__":
    unittest.main()
