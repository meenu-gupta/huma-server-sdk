import ipaddress
import re
from dataclasses import fields, is_dataclass
from typing import Any, Iterable

from extensions.common.exceptions import (
    InvalidGenderOptionValueException,
    InvalidMeasureUnitException,
    InvalidEthnicityOptionValueException,
)
from sdk.common.utils.convertible import (
    ConvertibleClassValidationError,
    convert_ignored_fields_to_dict,
    get_field,
)


def validate_ip(ip_address: str):
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    return True


def validate_tag(tag: dict):
    if not isinstance(tag, dict):
        return False
    for value in tag.values():
        if not isinstance(value, str):
            return False
    return True


def validate_user_profile_field(key: str, value: str, field_config):
    try:
        _validate_user_profile_field(value, field_config)
    except Exception as e:
        raise ConvertibleClassValidationError(
            f"Validation function error for [{key}] field with error [{e}]"
        )


def _validate_user_profile_field(value: str, field_config):
    if not field_config:
        raise Exception("Field is not recognized")

    regex_pattern = field_config.validation
    if not regex_pattern:
        return

    if not re.match(regex_pattern, value):
        raise Exception(f"value {value} does not match pattern {regex_pattern}")


def validate_gender_options(gender_options: list):
    from extensions.authorization.models.user import User

    for gender_option in gender_options:
        if not User.Gender.has_value(gender_option.value):
            raise InvalidGenderOptionValueException(gender_option.value)


def validate_ethnicity_options(ethnicity_options: list):
    from extensions.authorization.models.user import User

    for ethnicity_option in ethnicity_options:
        if not User.Ethnicity.has_value(ethnicity_option.value):
            raise InvalidEthnicityOptionValueException(ethnicity_option.value)


def validate_fields_for_cls(fields_: Iterable, cls: type):
    """cls represents the class to be validated against"""

    if fields_ and not is_dataclass(cls):
        raise ConvertibleClassValidationError(
            message=f"{cls.__name__} does not have attributes {list(fields_)}"
        )

    nested_fields = []
    simple_fields = []
    for key in fields_:
        if "." in key:
            nested_fields.append(key)
            simple_fields.append(key.split(".", maxsplit=1)[0])
        else:
            simple_fields.append(key)

    fields_name_set = {f.name for f in fields(cls)}
    nested_fields = convert_ignored_fields_to_dict(nested_fields)
    non_existent_fields = [v for v in simple_fields if v not in fields_name_set]
    non_existent_fields.sort()
    if non_existent_fields:
        non_existent_fields = ",".join(non_existent_fields)
        raise ConvertibleClassValidationError(
            message=f"{non_existent_fields} does not exist in {cls.__name__}"
        )

    for field, values in nested_fields.items():
        validate_fields_for_cls(values, get_field(cls, field).type)
    return True


def validate_custom_unit(custom_unit):
    from extensions.module_result.models.primitives.primitive import MeasureUnit

    if custom_unit not in MeasureUnit.get_value_list():
        raise InvalidMeasureUnitException(custom_unit)
