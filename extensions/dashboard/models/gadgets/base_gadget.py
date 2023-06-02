from typing import Any

from extensions.dashboard.exceptions import InvalidGadgetException
from sdk.common.utils.convertible import meta, required_field, default_field, get_class
from sdk.common.utils.validators import (
    validate_object_id,
    validate_entity_name,
)


class GadgetConfig:
    _configured: bool = required_field(default=False)

    @property
    def configured(self):
        return self._configured


class InfoField:
    NAME = "name"
    VALUE = "value"

    name: str = required_field(metadata=meta(validate_entity_name))
    value: str = default_field(metadata=meta(validate_entity_name))


class Gadget:
    type: str = None

    ID = "id"
    ID_ = "_id"
    CONFIGURATION = "configuration"
    METADATA = "metadata"
    TOOLTIP = "tooltip"
    TITLE = "title"
    INFO_FIELDS = "infoFields"
    DATA = "data"

    IGNORED_FIELDS = (ID_,)

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    tooltip: str = default_field(metadata=meta(validate_entity_name))
    title: str = default_field(metadata=meta(validate_entity_name))
    infoFields: list[InfoField] = default_field()

    configuration: GadgetConfig = required_field()
    data: Any = default_field()

    metadata: dict = default_field()

    def validate(self):
        from extensions.dashboard.models.gadgets import existing_gadgets

        gadget_types = [gadget.type for gadget in existing_gadgets]
        if self.type not in gadget_types:
            raise InvalidGadgetException

    def update_data(self):
        self.builder().execute(self)

    @classmethod
    def create_from_dict(cls, data: dict, gadget_type: str, validate: bool = True):
        _cls = get_class(f"{gadget_type}Gadget", cls)
        return _cls.from_dict(data, use_validator_field=validate)

    @property
    def builder(self):
        raise NotImplementedError
