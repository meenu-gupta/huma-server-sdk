from enum import Enum


class Status(Enum):
    DRAFT = "DRAFT"
    DEPLOYED = "DEPLOYED"
    ARCHIVED = "ARCHIVED"


class EnableStatus(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
