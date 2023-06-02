import functools
import re
import warnings
from decimal import Decimal, ROUND_HALF_UP
from itertools import groupby
from typing import Any, Type, Callable, Iterable, Optional, Union


def get_full_name_for_signature(given_name, family_name):
    return ((given_name or "") + " " + (family_name or "")).strip()


def deprecated(message: str = None):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    def wrapper(func):
        error = f"Call to deprecated function {func.__name__}."
        if message:
            error += f" {message}"

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(error, category=DeprecationWarning, stacklevel=2)
            warnings.simplefilter("default", DeprecationWarning)
            return func(*args, **kwargs)

        return new_func

    return wrapper


def get_all_subclasses(parent_class: Type[Any], results: list = None) -> list:
    results = results or [parent_class]
    total = [cls() for cls in parent_class.__subclasses__()]
    results.extend(total)
    # extending the list with modules which are subclasses
    for module in list(total):
        get_all_subclasses(module.__class__, results)
    return results


def find(condition: Callable[[Any], bool], iterable: Iterable) -> Optional[Any]:
    return next(filter(condition, iterable), None)


def escape(string: Union[str, None]) -> Union[str, None]:
    """Escapes string value or returns empty string/None"""
    return re.escape(string) if string else string


def mute_error(error):
    def wrapper(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error:
                return

        return _wrapper

    return wrapper


def is_all_items_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def round_half_up(value: float, decimal_places: int = 0) -> Union[int, float]:
    value = Decimal(str(value))
    decimals = Decimal(f"1.{'0'*decimal_places}")
    result = value.quantize(decimals, rounding=ROUND_HALF_UP)
    if decimal_places == 0:
        return int(result)
    return float(result)


def find_last_less_or_equal_element_index(item: int, items: list[int]) -> int:
    """Returns index of the last element in array that is less or equal to item"""
    if not items:
        return -1
    items = sorted(items)
    for last_index, e in enumerate(items):
        if item >= e:
            continue
        return last_index - 1

    return last_index
