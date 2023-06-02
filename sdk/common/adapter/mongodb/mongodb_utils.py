import logging

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import AutoReconnect

from sdk.common.constants import (
    VALUE_IN,
    LESS_OR_EQUAL_TO,
    LESS_THAN,
    GREATER_OR_EQUAL_TO,
    GREATER_THAN,
    VALUE_NOT_IN,
    VALUE_EQUALS_TO,
    NOT_EQUAL,
)

MONGO_MAPPING = {
    LESS_OR_EQUAL_TO: "$lte",
    LESS_THAN: "$lt",
    GREATER_OR_EQUAL_TO: "$gte",
    GREATER_THAN: "$gt",
    VALUE_IN: "$in",
    VALUE_NOT_IN: "$nin",
    VALUE_EQUALS_TO: "$eq",
    NOT_EQUAL: "$ne",
}

logger = logging.getLogger(__name__)


def db_is_accessible(db: Database):
    try:
        result = db.command("ping").get("ok")
    except AutoReconnect as e:
        r"""Maybe because of certificate problem.
        Run certificate command of python '/Applications/Python\ 3.9/Install\ Certificates.command'
        Look at this:
        https://stackoverflow.com/questions/40684543/how-to-make-python-use-ca-certificates-from-mac-os-truststore"""

        logger.exception(e)
        result = 0

    return result == 1.0


def kwargs_to_obj_id(kwargs) -> dict:
    result = {}
    for key, value in kwargs.items():
        if "." not in key and key.endswith("Id"):
            if isinstance(value, str) and ObjectId.is_valid(value):
                value = ObjectId(value)
            elif isinstance(value, dict) and "$in" in value:
                value = {"$in": [ObjectId(val) for val in value["$in"]]}
            elif isinstance(value, dict) and VALUE_IN in value:
                value = {VALUE_IN: [ObjectId(val) for val in value[VALUE_IN]]}
        result[key] = value
    return result


def convert_mongo_comparison_operators(filter_data: dict) -> dict:
    mapping = MONGO_MAPPING
    new = {}
    for k, v in filter_data.items():
        if isinstance(v, dict):
            v = convert_mongo_comparison_operators(v)
        matched_value = mapping.get(k)
        if matched_value:
            new[k.replace(k, matched_value)] = v
        else:
            new[k] = v
    return new


def convert_kwargs(f):
    def wrapper(*args, **kwargs):
        kwargs = kwargs_to_obj_id(kwargs)
        return f(*args, **kwargs)

    return wrapper


def map_mongo_comparison_operators(f):
    def wrapper(*args, **kwargs):
        kwargs = convert_mongo_comparison_operators(kwargs)
        return f(*args, **kwargs)

    return wrapper
