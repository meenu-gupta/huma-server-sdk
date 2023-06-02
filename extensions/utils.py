import random
from datetime import datetime
from typing import Union

import exrex
from pymongo import DESCENDING, ASCENDING

from extensions.common.exceptions import InvalidSortFieldsException
from extensions.common.sort import SortField


def generate_code(length: int, include_characters: bool = False) -> str:
    chars = "0123456789"
    if include_characters:
        chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    password = ""

    for i in range(length):
        password += random.choice(chars)

    return password


def generate_code_from_regex(pattern: str) -> str:
    return exrex.getone(pattern)


def format_sort_fields(
    sort_fields: list[SortField], valid_sort_fields: list[str]
) -> list[tuple[str, int]]:
    formatted_sort_fields = []
    invalid_sort_fields = []

    for sort_field in sort_fields:
        field = sort_field
        if field.field not in valid_sort_fields:
            invalid_sort_fields.append(field.field)
            continue
        order = DESCENDING if field.direction == SortField.Direction.DESC else ASCENDING
        formatted_sort_fields.append((field.field, order))

    if invalid_sort_fields:
        raise InvalidSortFieldsException(invalid_sort_fields)

    return formatted_sort_fields


def string_to_range(str_range: str) -> list[int]:
    """
    @param str_range: Any string value with 2 numbers connected with dash.
    Example: 1-25, 400-812, 13-16
    @return: list of numbers in provided range
    """
    step = 1
    try:
        start, end = str_range.split("-")
        start, end = int(start), int(end)
        if start > end:
            step = -1
        return list(range(start, end + step, step))
    except Exception:
        return []


def get_full_list(question_numbers: list) -> list[Union[int, str]]:
    """
    @param question_numbers a list containing str_range : Any string value with 2 numbers connected with dash.
    Example: ["1-25", "400-812"]
    @return: list of numbers in provided ranges
    """
    numbers = []
    for item in question_numbers:
        if isinstance(item, int):
            numbers.append(item)
            continue
        numbers += list(string_to_range(item))

    return numbers


def build_date(record: dict[str, dict[str, int]]):
    year = record["_id"]["year"]
    month = record["_id"]["month"]
    return datetime.strptime(f"{year}{month}", "%Y%m").date()


def num_of_months_between_two_dates(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


def format_text_to_bold(value: Union[int, str]):
    if value:
        return f"<strong>{value}</strong>"


def remove_trailing_zero_in_decimal(num: Union[int, float]) -> str:
    return ("%i" if num == int(num) else "%s") % num
