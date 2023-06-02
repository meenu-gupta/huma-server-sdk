import dataclasses
from dataclasses import fields
from datetime import datetime, date
from enum import EnumMeta, Enum
from typing import Any, Type, Union, Callable

from bson import ObjectId, SON
from mongoengine import Document
from pymongo.database import Database

from sdk.common.utils import inject
from sdk.common.utils.convertible import is_from_generic_list
from sdk.common.utils.validators import (
    utc_str_val_to_field,
    utc_str_to_date,
    utc_str_field_to_val,
)


def convert_values(d):
    d.pop("_cls", None)
    if "_id" in d:
        d["id"] = d.pop("_id", None)
    for key, value in d.items():
        if isinstance(value, ObjectId):
            d[key] = str(value)
        elif isinstance(value, datetime):
            d[key] = utc_str_field_to_val(value)
        elif isinstance(value, list):
            d[key] = []
            for item in value:
                # converting nested list of Embedded documents into correct dict
                if isinstance(item, SON):
                    item = convert_values(item.to_dict())
                elif isinstance(item, ObjectId):
                    item = str(item)
                d[key].append(item)
        elif isinstance(value, SON):
            d[key] = convert_values(value.to_dict())
    return d


class MongoPhoenixDocument(Document):
    ID_ = "_id"
    meta = {"allow_inheritance": True, "abstract": True, "strict": False}

    def __init__(self, **kwargs):
        if self.ID_ in kwargs:
            kwargs.update({"id": kwargs.pop("_id")})
        super().__init__(**kwargs)

    @classmethod
    def _get_db(cls):
        return inject.instance(Database)

    def to_dict(self):
        return convert_values(self.to_mongo())

    @classmethod
    def fields(cls):
        return cls._fields_ordered


def obj_to_model(obj: Any, model: Union[type, Type[MongoPhoenixDocument]]):
    if dataclasses.is_dataclass(model):
        return _mongo_to_dataclass(obj, model)

    return _data_class_to_mongo(obj, model)


def _data_class_to_mongo(obj, model: Type[MongoPhoenixDocument]):
    init_args = {}
    for field in fields(obj):
        val = getattr(obj, field.name, None)
        if val is None:
            continue

        if is_from_generic_list(field.type) or field.type == list:
            inner_type = field.type.__args__[0]

            if dataclasses.is_dataclass(inner_type):
                val = [obj_to_model(v, dict) for v in val]

        init_args[field.name] = val

    return model(**init_args)


def _mongo_to_dataclass(obj: MongoPhoenixDocument, model: type):
    new = model()
    for field in fields(new):
        val = getattr(obj, field.name, None)
        if val is None:
            continue

        if is_from_generic_list(field.type) or field.type == list:
            inner_type = field.type.__args__[0]
            val = [obj_to_model(v, inner_type) for v in val]

        elif type(val) != field.type:
            val = _DataclassFieldEncoder.load(val, field)
        setattr(new, field.name, val)
    if hasattr(new, "post_init"):
        new.post_init()
    return new


class _DataclassFieldEncoder:
    types_mapping: dict[type, Callable[[Any], Any]] = {
        date: utc_str_to_date,
        datetime: utc_str_val_to_field,
    }
    generic_types = (bool, int, float, str, dict)

    @classmethod
    def load(cls, val: Any, field_type: type):
        if isinstance(field_type, EnumMeta):
            return cls._load_enum(val, field_type)

        load_func = cls.types_mapping.get(field_type)
        if not load_func:
            if field_type not in cls.generic_types:
                return obj_to_model(val, field_type)
            return field_type(val)

        return load_func(val)

    @staticmethod
    def _load_enum(val: Any, enum: Type[Enum]) -> Enum:
        # For backward compatibility to match both attr name and value
        try:
            return enum(val)
        except ValueError:
            return enum[val]


def convert_date_to_datetime(user_dict: dict, cls: type):
    """
    MongoDB doesn't support date objects, only datetime.
    So before saving to DB we need to convert all dates to datetime.
    This is temporary solution until we create MongoUserModels.
    """
    if not dataclasses.is_dataclass(cls):
        return

    for f in dataclasses.fields(cls):
        if f.name not in user_dict:
            continue

        if not _field_is_date_field(f):
            continue

        user_date = user_dict[f.name]
        if isinstance(user_date, datetime):
            continue
        elif isinstance(user_date, date):
            user_dict[f.name] = datetime.combine(user_date, datetime.min.time())


def _field_is_date_field(f: dataclasses.Field):
    return f.type == date or (hasattr(f.type, "__name__") and f.type.__name__ == "date")
