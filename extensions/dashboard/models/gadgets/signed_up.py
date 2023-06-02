from datetime import date

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
    validate_object_ids,
    validate_object_id,
    utc_date_to_str,
    utc_str_to_date,
    validate_entity_name,
)


@convertibleclass
class SignUpGadgetConfig(GadgetConfig):
    ORGANIZATION_ID = "organizationId"

    durationIso: str = default_field(metadata=meta(validate_duration_iso))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )


@convertibleclass
class SignedUpData:
    # Date (first day of month)
    x: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date)
    )
    # Signups amount
    y: int = positive_integer_field(default=None)
    # Name of the deployment
    d: str = default_field(metadata=meta(validate_entity_name))


@convertibleclass
class SignedUpGadget(Gadget):
    IGNORED_FIELDS = (
        f"{Gadget.CONFIGURATION}.{SignUpGadgetConfig.ORGANIZATION_ID}",
        Gadget.ID_,
    )
    AVG = "avg"

    type = GadgetId.SIGNED_UP.value

    configuration: SignUpGadgetConfig = required_field()
    avg: int = default_field()
    data: list[SignedUpData] = default_field()

    @property
    def builder(self):
        from extensions.dashboard.builders.signed_up_data_builder import (
            SignedUpDataBuilder,
        )

        return SignedUpDataBuilder
