from enum import Enum

from extensions.dashboard.models.gadget import GadgetId
from extensions.dashboard.models.gadgets import Gadget
from extensions.dashboard.models.gadgets.base_gadget import GadgetConfig
from extensions.deployment.models.key_action_config import validate_duration_iso
from sdk import convertibleclass
from sdk.common.utils.convertible import (
    default_field,
    meta,
    positive_integer_field,
    required_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
    validate_object_ids,
)


@convertibleclass
class OverallViewGadgetConfig(GadgetConfig):
    ORGANIZATION_ID = "organizationId"

    durationIso: str = default_field(metadata=meta(validate_duration_iso))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )


@convertibleclass
class OverallViewData:
    X = "x"
    Y = "y"
    Y2 = "y2"
    Y3 = "y3"
    Y4 = "y4"

    x: str = default_field()  # name of tab
    y: str = default_field()
    y2: int = default_field()
    y3: str = default_field()
    y4: int = default_field()


@convertibleclass
class OverallViewGadget(Gadget):
    IGNORED_FIELDS = (
        f"{Gadget.CONFIGURATION}.{OverallViewGadgetConfig.ORGANIZATION_ID}",
        Gadget.ID_,
    )

    type = GadgetId.OVERALL_VIEW.value

    configuration: OverallViewGadgetConfig = required_field()
    data: list[OverallViewData] = default_field()

    @property
    def builder(self):
        from extensions.dashboard.builders.overall_view_data_builder import (
            OverallViewDataBuilder,
        )

        return OverallViewDataBuilder
