from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from dateutil.relativedelta import relativedelta

from extensions.utils import num_of_months_between_two_dates
from sdk.common.utils.common_functions_utils import round_half_up


def fill_month_data_with_zero_qty(data: dict[date, int], key_date: date):
    data_including_zero = {}
    while key_date <= datetime.utcnow().date():
        data_including_zero[key_date] = data.get(key_date, 0)
        key_date += relativedelta(months=1)
    return data_including_zero


def get_earliest_and_latest_dates(data) -> (date, date, date):
    merged_months_data = {k: v for d in data.values() for k, v in d.items()}
    sorted_by_dates = sorted(merged_months_data.keys(), reverse=True)
    if sorted_by_dates:
        latest_date = sorted_by_dates[0]
        earliest_date = sorted_by_dates[-1]
        latest_without_zero = earliest_date
        for month_date in sorted_by_dates:
            if merged_months_data[month_date]:
                latest_without_zero = month_date
                break
        return earliest_date, latest_date, latest_without_zero
    return None, None, None


def fill_missing_data_with_0_and_sort_by_month(data: dict, earliest_date: date) -> dict:
    res_data = defaultdict(dict)
    if not earliest_date:
        return {}

    for deployment, month_data in data.items():
        month_data = fill_month_data_with_zero_qty(month_data, earliest_date)
        for month, amount in month_data.items():
            res_data[month][deployment] = amount
    return dict(sorted(res_data.items(), key=lambda x: x[0]))


def calculate_average_per_month(
    total: int, earliest_date: date, latest_date: date
) -> Optional[int]:
    if earliest_date and latest_date:
        num_of_months = num_of_months_between_two_dates(earliest_date, latest_date) + 1
        return round_half_up(total / num_of_months)
