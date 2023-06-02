from datetime import date

from extensions.dashboard.models.gadget import GadgetId
from extensions.dashboard.models.gadgets import Gadget
from extensions.dashboard.models.gadgets.base_gadget import GadgetConfig
from extensions.deployment.models.key_action_config import validate_duration_iso
from sdk.common.utils.convertible import (
    required_field,
    default_field,
    meta,
    positive_integer_field,
    convertibleclass,
)
from sdk.common.utils.validators import (
    validate_entity_name,
    utc_date_to_str,
    utc_str_to_date,
    validate_object_ids,
    validate_object_id,
)


@convertibleclass
class ConsentedGadgetConfig(GadgetConfig):
    ORGANIZATION_ID = "organizationId"

    durationIso: str = default_field(metadata=meta(validate_duration_iso))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )


@convertibleclass
class ConsentedData:
    # Date (first day of month)
    x: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date)
    )
    # Consented amount
    y: int = positive_integer_field(default=None)
    # Name of the deployment
    d: str = default_field(metadata=meta(validate_entity_name))


@convertibleclass
class ConsentedGadget(Gadget):
    AVG = "avg"

    IGNORED_FIELDS = (
        f"{Gadget.CONFIGURATION}.{ConsentedGadgetConfig.ORGANIZATION_ID}",
        Gadget.ID_,
    )

    type = GadgetId.CONSENTED.value

    configuration: ConsentedGadgetConfig = required_field()
    avg: int = default_field()
    data: list[ConsentedData] = default_field()

    @property
    def builder(self):
        from extensions.dashboard.builders.consented_data_builder import (
            ConsentedDataBuilder,
        )

        return ConsentedDataBuilder
