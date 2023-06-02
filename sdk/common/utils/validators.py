import collections
import hashlib
import json
import logging
import re
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Pattern, Any, Union, Callable

import isodate
import phonenumbers
from pyparsing import empty
import pytz
import validators
from aniso8601 import parse_datetime, parse_time
from boltons.iterutils import remap
from bson import ObjectId
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from packaging import version
from pycountry import countries

from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.localization.utils import Language
from sdk.common.utils.convertible import ConvertibleClassValidationError, meta
from sdk.versioning.models.version_field import VersionField

log = logging.getLogger(__name__)
"""Helper functions"""
RE_COLOR: Pattern[str] = re.compile(r"^0x([A-Fa-f0-9]{6})$")
RE_HEX_COLOR: Pattern[str] = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
RE_MODULE_NAME: Pattern[str] = re.compile(r"^[A-Z][A-Za-z]+$")
RE_PHONE_NUMBER_NAME: Pattern[str] = re.compile(
    r"^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$"
)
RE_URL_SAFE_STRING: Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")

frequency_dict = {
    1: "ONCE",
    2: "TWICE",
    3: "THREE TIMES",
    4: "FOUR TIMES",
    5: "FIVE TIMES",
    6: "SIX TIMES",
    7: "SEVEN TIMES",
    8: "EIGHT TIMES",
    9: "NINE TIMES",
    10: "TEN TIMES",
}
duration_dict = {
    "1Y": "A YEAR",
    "2Y": "EVERY TWO YEARS",
    "1M": "A MONTH",
    "2M": "EVERY 2 MONTHS",
    "3M": "EVERY 3 MONTHS",
    "1W": "A WEEK",
    "2W": "EVERY 2 WEEKS",
    "3W": "EVERY 3 WEEKS",
    "4W": "EVERY 4 WEEKS",
    "1D": "A DAY",
    "2D": "EVERY TWO DAYS",
    "3D": "EVERY THREE DAYS",
    "4D": "EVERY FOUR DAYS",
    "5D": "EVERY FIVE DAYS",
    "6D": "EVERY SIX DAYS",
}


def validate_regex(n):
    if n:
        re.compile(n)
    return True


def validate_duration(iso_duration: str, time_only=False) -> bool:
    isodate.parse_duration(iso_duration)
    match = re.match(r"PT\d{1,2}H\d{1,2}M", iso_duration)
    if time_only and not match:
        raise Exception("value doesn't match time pattern.")
    if match:
        hours, minutes = iso_duration.replace("PT", "").replace("M", "").split("H")
        if len(hours) > 1 and hours.startswith("0"):
            raise Exception("Hours should not have leading zeros.")
        elif len(minutes) > 1 and minutes.startswith("0"):
            raise Exception("Minutes should not have leading zeros.")
    return True


def validate_time_durations_in_list(durations: list[str]) -> bool:
    if not durations:
        return False

    return validate_len(max=6)(durations) and all(
        validate_duration(duration, time_only=True) for duration in durations
    )


def validate_time_duration(iso_duration):
    return validate_duration(iso_duration, time_only=True)


def validate_id(n):
    if type(n) is ObjectId:
        n = str(n)
    return len(n) > 8


def validate_object_id(n: Union[ObjectId, str]):
    if not isinstance(n, str):
        n = str(n)
    return ObjectId.is_valid(n)


def utc_str_date_to_datetime(val: Union[str, datetime, date]) -> datetime:
    if isinstance(val, datetime):
        return val

    date_ = utc_str_to_date(val)
    return datetime(year=date_.year, month=date_.month, day=date_.day)


def utc_str_val_to_field(val: Union[str, datetime]) -> datetime:
    if isinstance(val, datetime):
        return val

    try:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%fZ")
    except TypeError:
        raise ConvertibleClassValidationError(f"{val} is invalid date format")
    except ValueError:
        try:
            return datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ConvertibleClassValidationError(f"{val} is invalid date format")


def utc_str_field_to_val(val: Union[str, datetime]) -> str:
    if isinstance(val, str):
        return val

    try:
        return val.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except AttributeError:
        raise ConvertibleClassValidationError(f"{val} is invalid date format")


def string_or_datetime_to_string(value: Union[str, datetime]):
    """
    Returns iso formatted string datetime from string or datetime object
    :return: str
    """
    utc_tz = pytz.timezone("UTC")
    if isinstance(value, str):
        value = parse(value)

    if not value.tzinfo:
        return value.replace(tzinfo=utc_tz)

    return value.astimezone(utc_tz).isoformat()


def end_datetime_from_str_or_date(value: Union[str, datetime, date]) -> datetime:
    """
    Returns datetime from the end of the day, parsed from date string or object
    or datetime with UTC/provided timezone
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        value = value.strftime("%Y-%m-%d")

    if isinstance(value, str):
        now = datetime.utcnow()
        utc_tz = pytz.timezone("UTC")
        default_dt = now.replace(
            hour=23, minute=59, second=59, microsecond=999, tzinfo=utc_tz
        )
        # missing values (time when only date is passed) will be replaced with default
        value = parse(value, default=default_dt)

    return value


def start_datetime_from_str_or_date(value: Union[str, datetime, date]) -> datetime:
    """
    Returns datetime from the start of the day, parsed from date string or object
    or datetime with UTC/provided timezone
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        value = value.strftime("%Y-%m-%d")

    if isinstance(value, str):
        now = datetime.utcnow()
        utc_tz = pytz.timezone("UTC")
        # missing values (time when only date is passed) will be replaced with default
        default_dt = now.replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=utc_tz
        )
        value = parse(value, default=default_dt)

    return value


def default_datetime_meta():
    return meta(
        field_to_value=utc_str_field_to_val, value_to_field=utc_str_val_to_field
    )


def utc_str_to_date(val: Union[str, date]) -> date:
    if isinstance(val, datetime):
        return val.date()
    elif isinstance(val, date):
        return val
    elif not isinstance(val, str):
        raise ConvertibleClassValidationError(f"{val} is invalid date format")

    val = val.split("T", maxsplit=1)[0]
    try:
        return date.fromisoformat(val)
    except ValueError:
        raise ConvertibleClassValidationError(f"{val} is invalid date format")


def utc_date_to_str(val: Union[str, date, datetime]) -> str:
    if isinstance(val, str):
        return val

    try:
        return val.strftime("%Y-%m-%d")
    except AttributeError:
        raise ConvertibleClassValidationError(f"{val} is invalid date format")


def str_id_to_obj_id(id_string: str) -> ObjectId:
    return ObjectId(id_string)


def object_id_list_to_str_list(object_ids: list[ObjectId]) -> list[str]:
    return [str(obj_id) for obj_id in object_ids]


def str_id_list_to_obj_id_list(id_strings: list[str]) -> list[ObjectId]:
    return [ObjectId(id_string) for id_string in id_strings]


def round_to_half_int(value: Union[float, int, str]):
    return round(float(value) * 2) / 2


def default_email_meta() -> dict[str, Any]:
    return meta(
        validator=validate_email,
        field_to_value=lambda x: x.lower(),
        value_to_field=lambda x: x.lower(),
    )


def id_as_obj_id(func):
    """Used to convert string ids, passing to function into ObjectID. Keyword arguments should be used."""

    def wrapper(instance, **kwargs):
        for key in kwargs:
            if (
                key.endswith("_id")
                and isinstance(kwargs[key], str)
                and ObjectId.is_valid(kwargs[key])
            ):
                kwargs[key] = ObjectId(kwargs[key])
        return func(instance, **kwargs)

    return wrapper


def validate_activation_code(n: str):
    if not isinstance(n, str):
        return False

    return 8 <= len(n) <= 16


def validate_timezone(n):
    return n in pytz.all_timezones


def validate_phone_number(n):
    return phonenumbers.is_valid_number(phonenumbers.parse(n))


def validate_color(n):
    return RE_COLOR.match(n)


def validate_hex_color(n):
    return RE_HEX_COLOR.match(n)


def validate_json(n):
    try:
        json.loads(n)
    except ValueError:
        return False
    return True


def validate_url(n):
    return validators.url(n)


def validate_url_https(n):
    return validators.url(n) and n.startswith("https:")


def validate_url_safe_string(n: str):
    return RE_URL_SAFE_STRING.match(n)


def validate_shortened_invitation_code(n: str):
    # since admin invitations do not have shortened_code, it can be None
    if n is None:
        return True

    if not isinstance(n, str):
        return False

    return validate_url_safe_string(n)


def validate_country(n):
    return countries.get(name=n)


def validate_country_code(n):
    return countries.get(alpha_2=n)


def validate_datetime(n):
    parse_datetime(n)
    return True


def validate_time(n):
    parse_time(n)
    return True


def validate_email(n):
    return validators.email(n)


def validate_email_list(emails: list):
    if not emails:
        return False
    for email in emails:
        if not validators.email(email):
            return False
    return True


def replace_spaces(email: str) -> str:
    """Used to replace spaces which appears in emails with "+" sing in url"""
    return email.replace(" ", "+").lower()


def validate_entity_name(name):
    return 0 < len(name) < 256


def validate_len(min: int = None, max: int = None):
    """Returns function that validates len of the given object within given min/max params inclusive."""

    def validator(value):
        if min and max:
            return min <= len(value) <= max
        elif min:
            return min <= len(value)
        elif max:
            return len(value) <= max
        else:
            raise TypeError(
                "At least one of arguments should be provided: 'min_len', 'max_len'"
            )

    return validator


def validate_list_elements_len(min: int = None, max: int = None):
    """
    Returns a function that validates the length of each element of a list to
    be within a given range of min/max params inclusive.
    """

    def validator(values):
        if min and max:
            return all(min <= len(value) <= max for value in values)
        elif min:
            return all(min <= len(value) for value in values)
        elif max:
            return all(len(value) <= max for value in values)
        else:
            raise TypeError(
                "At least one of these arguments should be provided: 'min_len', 'max_len'"
            )

    return validator


def validate_range(min_: Union[int, float] = None, max_: Union[int, float] = None):
    def validator(value):
        if min_ is not None and max_ is not None:
            msg = f"value must be between {min_} and {max_}"
            valid = min_ <= value <= max_
        elif min_ is not None:
            msg = f"value must be above or equal to {min_}"
            valid = min_ <= value
        elif max_ is not None:
            msg = f"value must be below or equal to {max_}"
            valid = value <= max_
        else:
            raise TypeError(
                "At least one of arguments should be provided: 'min_number', 'max_number'"
            )

        if not valid:
            raise Exception(msg)

        return True

    return validator


def not_empty(value):
    return validate_len(1)(value)


def not_empty_list(values: list):
    return all([not_empty(value) for value in values])


def validate_date_range(
    start: Union[str, Callable[[], str]] = None,
    end: Union[str, Callable[[], str]] = None,
):
    def validator(date_):
        start_value = start
        end_value = end
        if isinstance(start, Callable):
            start_value = start()
        if isinstance(end, Callable):
            end_value = end()

        if start_value and end_value:
            msg = f"date must be between {start_value} and {end_value}"
            valid = (
                utc_str_to_date(start_value)
                <= utc_str_to_date(date_)
                <= utc_str_to_date(end_value)
            )
        elif start_value:
            msg = f"date must be after or equal to {start_value}"
            valid = utc_str_to_date(start_value) <= utc_str_to_date(date_)
        elif end_value:
            msg = f"date must be before or equal to {end_value}"
            valid = utc_str_to_date(date_) <= utc_str_to_date(end_value)
        else:
            raise TypeError(
                "At least one of arguments should be provided: 'start', 'end'"
            )

        if not valid:
            raise Exception(msg)

        return True

    return validator


def validate_min_max_month_days_list(n):
    """Validates if values inside month days are in range of 1-31"""
    if not n:
        return False

    for val in n:
        if (val < 1) or (val > 31):
            raise Exception("Values in list are not in range of [1-31]")

    return True


def validate_rate_limit(limit: str):
    matched = re.match(r"\d+( per |/)(second|minute|hour|day|month|year)", limit)
    if not matched:
        raise Exception(
            f"Rate limit should have format like '2/minute, 15 per hour', not {limit}"
        )
    return True


def validate_rate_limit_strategy(strategy: str) -> bool:
    allowed_strategies = [
        "fixed-window",
        "fixed-window-elastic-expiry",
        "moving-window",
    ]
    if strategy not in allowed_strategies:
        raise Exception(
            f"""Incorrect rate limit strategy. Should be one of "{'", '.join(allowed_strategies)}" """
        )
    return True


def must_be_present(custom_message=None, **kwargs):
    """Raising an exception when none parameter"""
    errors = list()
    for key, value in kwargs.items():
        if value is None:
            errors.append(key)
    if len(errors) == 0:
        return

    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    else:
        raise ConvertibleClassValidationError("Missing keys: " + ",".join(errors))


def must_not_be_present(custom_message=None, **kwargs):
    """Raising an exception when parameter exists"""
    errors = list()
    for key, value in kwargs.items():
        if value is not None:
            errors.append(key)
    if len(errors) == 0:
        return

    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    else:
        raise ConvertibleClassValidationError(
            "Keys should not exist: " + ",".join(errors)
        )


def must_be_only_one_of(custom_message=None, could_be_none=False, **kwargs):
    """Raising an exception when more than one of parameters present"""
    present_values = remove_none_values(kwargs)
    if len(present_values) == 1:
        return

    elif len(present_values) == 0 and could_be_none:
        return

    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    elif not present_values and not could_be_none:
        raise ConvertibleClassValidationError(
            f"One of {','.join(kwargs.keys())} should be present."
        )
    else:
        raise ConvertibleClassValidationError(
            f"Only one of {','.join(kwargs.keys())} should be present"
        )


def must_be_at_least_one_of(custom_message=None, **kwargs):
    """Raising an exception when none of parameters present"""
    present_values = remove_none_values(kwargs)
    if len(present_values) >= 1:
        return

    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    else:
        raise ConvertibleClassValidationError(
            f"At least one of {','.join(kwargs.keys())} should be present"
        )


# todo move to questionnaire validation when unlocked
def must_be_int(custom_message=None, **kwargs):
    """Raising an exception when parameter not int"""
    errors = list()
    for key, value in kwargs.items():
        if not isinstance(value, int):
            errors.append(key)

    if len(errors) == 0:
        return
    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    else:
        raise ConvertibleClassValidationError(
            "Keys value should be an int: " + ",".join(errors)
        )


def must_not_be_empty_list(custom_message=None, **kwargs):
    """Raising an exception when list parameter is empty"""
    errors = list()
    for key, value in kwargs.items():
        if not value:
            errors.append(key)
    if len(errors) == 0:
        return

    if custom_message is not None:
        raise ConvertibleClassValidationError(custom_message)

    else:
        raise ConvertibleClassValidationError("Empty items: " + ",".join(errors))


def read_json_file(path, loc):
    p = Path(loc).joinpath(path)
    text = p.read_text()
    return json.loads(text) or {}


def datetime_now() -> str:
    """Return current UTC time as an ISO 8601 formatted string.
    Only give millisecond resolution, and use Z rather than +00:00
    """
    dt = datetime.now(timezone.utc)
    return f'{dt.strftime("%Y-%m-%dT%H:%M:%S")}.{dt.microsecond // 1000:03}Z'


def datetime_now_int() -> int:
    """Return current UTC time as an int."""
    return int(datetime.utcnow().timestamp())


def remove_none_values(d: Union[dict, list], ignore_keys: set = None) -> dict:
    """
    Return Dict that has the none values removed except ignoring certain keys.
    Recursively descend through any embedded Dicts/Lists doing the same
    Returns new Dict if inplace is false. Otherwise modifies given Dict
    """
    if ignore_keys:
        if not isinstance(ignore_keys, set):
            ignore_keys = set(ignore_keys)
        return remap(d, lambda p, k, v: v is not None or k in ignore_keys)
    return remap(d, lambda p, k, v: v is not None)


def remove_duplicates(array: list):
    """Removes duplicates from given list"""
    if not array or not isinstance(array, list):
        return array

    if isinstance(array[0], dict):
        return [dict(t) for t in {tuple(d.items()) for d in array}]
    return list(set(array))


def dict_merge(dct, merge_dct):
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.Mapping)
        ):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def iso_duration_to_friendly_text(iso_duration: str, frequency: int) -> str:
    # check if iso_duration passed is valid
    isodate.parse_duration(iso_duration)
    year = re.search(r"[1-2]Y", iso_duration)
    month = re.search(r"[1-3]M", iso_duration)
    week = re.search(r"[1-4]W", iso_duration)
    day = re.search(r"[1-9]?[1-9]D", iso_duration)
    frequency_text = frequency_dict.get(frequency)
    if year:
        return frequency_text + " " + duration_dict.get(year.group())

    elif month:
        return frequency_text + " " + duration_dict.get(month.group())

    elif week:
        return frequency_text + " " + duration_dict.get(week.group())

    elif day:
        return frequency_text + " " + duration_dict.get(day.group())

    else:
        raise ValueError("Invalid duration passed.")


def hash_value(value, secret=None):
    """
    User to hash values using sha-256
    """
    return hashlib.sha256(f"{value}{secret}".encode("utf-8")).hexdigest()


def password_validator(password):
    if len(password) < 8:
        raise Exception("Password must be at least 8 symbols")
    if not any(s.isupper() for s in password):
        raise Exception("Password must contain at least 1 upper letter")
    if not any(s.islower() for s in password):
        raise Exception("Password must contain at least 1 lower letter")
    if not any(s.isdigit() for s in password):
        raise Exception("Password must contain at least 1 digit")
    return True


def is_valid_semantic_version(v: str):
    match = re.match(r"\d{1,3}[.]\d{1,3}[.]\d{1,3}", v)
    return True if match else False


def check_if_only_one_default(arr: list, key: str):
    if len(arr) == 0:
        raise Exception(f"Array can not be empty")

    count = 0
    for item in arr:
        count += 1 if getattr(item, key, None) else 0
    if not count == 1:
        raise Exception(f"Must have one [{key}] = true but currently you have {count} ")
    return True


def check_unique_values(arr: list, keys: list[str]):
    if len(arr) == 0:
        raise Exception(f"Array can not be empty")

    for key in keys:
        all_keys = [getattr(el, key) for el in arr]
        if not len(set(all_keys)) == len(arr):
            raise Exception(f"[{key}] must be unique")
    return True


def validate_care_plan_activation_code(n: str):
    if not isinstance(n, str):
        return False

    return 2 == len(n)


def validate_language(language: str):
    languages = Language.get_valid_languages()
    if language not in languages:
        raise Exception(f'"{language}" is not a valid language')
    return True


def incorrect_language_to_default(language: str):
    valid_languages = Language.get_valid_languages()
    if language not in valid_languages:
        language = Language.EN
    return language


def validate_object_ids(object_ids: list[str]):
    return all([validate_object_id(object_id) for object_id in object_ids])


def validate_non_empty_object_ids(object_ids: list[str]):
    if not validate_len(1)(object_ids):
        raise ValueError(f"{object_ids}" is empty)
    return validate_object_ids(object_ids=object_ids)


def validate_twilio_media_region(region: str):
    from sdk.common.adapter.twilio.twilio_video_config import MediaRegion

    if region not in MediaRegion.get_valid_regions():
        raise Exception(f'"{region}" is not a valid region')
    return True


def validate_days_took_medication_before_vaccination(days: int):
    return 0 <= days <= 5


def validate_days_took_medication_after_vaccination(days: int):
    return 0 <= days <= 5


def validate_days_took_medication(days: int):
    return 0 <= days <= 365 * 2


def validate_pregnancy_weeks(number_of_weeks: int):
    return 22 <= number_of_weeks <= 45


def validate_past_pregnancies_elective_termination(number_of_pregnancies: int):
    return 0 <= number_of_pregnancies <= 40


def validate_past_pregnancies_miscarriage(number_of_pregnancies: int):
    return 0 <= number_of_pregnancies <= 40


def validate_past_pregnancies_ectopic(number_of_pregnancies: int):
    return 0 <= number_of_pregnancies <= 20


def validate_past_pregnancies_stillborn_baby(number_of_pregnancies: int):
    return 0 <= number_of_pregnancies <= 20


def validate_past_pregnancies_live_birth(number_of_pregnancies: int):
    return 0 <= number_of_pregnancies <= 20


def validate_pregnancy_count(number_of_pregnancies: int):
    return 1 <= number_of_pregnancies <= 40


def validate_number_of_babies_multiple_birth(number_of_babies: int):
    return 1 <= number_of_babies <= 10


def validate_expected_due_date(date_: str):
    return (
        utc_str_to_date(str(date.today()))
        <= utc_str_to_date(date_)
        <= utc_str_to_date(str(date.today() + relativedelta(months=10)))
    )


def validate_second_vaccine_schedule_date(date_: str):
    return (
        utc_str_to_date(str(date.today()))
        <= utc_str_to_date(date_)
        <= utc_str_to_date(str(date.today() + relativedelta(years=1)))
    )


def parse_phone_number(phone_number):
    parsed_phone_number = phonenumbers.parse(phone_number)
    return f"+{parsed_phone_number.country_code}{parsed_phone_number.national_number}"


def default_phone_number_meta():
    return meta(validator=validate_phone_number, value_to_field=parse_phone_number)


def validate_serializable(value: Any):
    json.dumps(value)
    return True


def str_to_bool(value: str) -> bool:
    if isinstance(value, bool):
        return value

    true_values = ["true", "yes"]
    false_values = ["false", "no"]

    if value.lower() in true_values:
        return True

    if value.lower() in false_values:
        return False

    raise ValueError("Invalid boolean string passed")


def str_to_int(value: Union[str, int]) -> int:
    if isinstance(value, int):
        return value
    try:
        value = int(value)
    except ValueError:
        msg = f"value: {value} should be convertable to an integer"
        raise ConvertibleClassValidationError(msg)
    return value


def str_to_version(val: Union[str, VersionField]) -> VersionField:
    if isinstance(val, VersionField):
        return val
    try:
        return VersionField(val)
    except version.InvalidVersion:
        raise ConvertibleClassValidationError(f"[{val}] is invalid version format")


def default_version_meta():
    return meta(field_to_value=str, value_to_field=str_to_version)


def validate_no_duplicate_keys_value_in_list(keys: set[str]):
    def validate_no_duplicate_value(values: list[dict[str, Any]]):
        for key in keys:
            key_values = [data.get(key) for data in values]
            if len(key_values) != len(set(key_values)):
                raise ValueError(f"{key} has a duplicate values in the list")
        return True

    return validate_no_duplicate_value


def validate_resource(resource):
    try:
        (_, _) = resource.split("/")
    except Exception:
        raise InvalidRequestException("Invalid resource")
    return True
