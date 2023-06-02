from enum import Enum
from typing import Type


def enum_values(enum_class: Type[Enum]) -> list:
    return [member.value for member in enum_class]
