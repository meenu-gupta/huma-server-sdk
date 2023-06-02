import statistics

from sdk.common.utils.common_functions_utils import round_half_up


def build_deviation_dict(scores: list, min_=None, max_=None):
    mean = statistics.mean(scores)
    standard_deviation = round_half_up(statistics.stdev(scores), 2)
    start = deviation_start = mean - standard_deviation
    end = (mean - deviation_start) * 2
    if min_ is not None:
        start = max((deviation_start, min_))
    if max_ is not None:
        end = min(end, max_)
    if start < 0:
        end = end + start
        start = 0
    return {"deviationStart": start, "deviationEnd": end}


def get_date_range_str(start, end) -> str:
    return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"
