from extensions.dashboard.models.gadget import GadgetLink
from sdk import convertibleclass
from sdk.common.utils.convertible import meta, required_field
from sdk.common.utils.validators import (
    validate_entity_name,
)
from enum import Enum


class DashboardId(Enum):
    ORGANIZATION_OVERVIEW = "OrganizationOverview"


class DashboardResourceType(Enum):
    ORGANIZATION = "ORGANIZATION"
    DEPLOYMENT = "DEPLOYMENT"


@convertibleclass
class Dashboard:
    ID = "id"
    NAME = "name"
    GADGETS = "gadgets"

    id: DashboardId = required_field()
    name: str = required_field(metadata=meta(validator=validate_entity_name))
    gadgets: list[GadgetLink] = required_field()
