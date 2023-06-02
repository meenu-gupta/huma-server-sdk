"""Patch model"""
from enum import Enum
from typing import Any

from sdk.common.utils.convertible import convertibleclass, required_field, default_field


class OperationType(Enum):
    replace = "replace"
    add = "add"
    remove = "remove"


@convertibleclass
class Patch:
    OP = "op"
    PATH = "path"
    VALUE = "value"

    op: OperationType = required_field()
    path: str = required_field()
    value: Any = default_field()
