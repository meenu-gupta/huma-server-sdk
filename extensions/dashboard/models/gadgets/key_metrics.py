from extensions.dashboard.models.gadget import GadgetId
from extensions.dashboard.models.gadgets import Gadget
from extensions.dashboard.models.gadgets.base_gadget import GadgetConfig, InfoField
from sdk.common.utils.convertible import (
    required_field,
    default_field,
    meta,
    positive_integer_field,
    convertibleclass,
)
from sdk.common.utils.validators import (
    validate_entity_name,
    validate_object_ids,
    validate_object_id,
)


@convertibleclass
class KeyMetricsGadgetConfig(GadgetConfig):
    ORGANIZATION_ID = "organizationId"

    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )


@convertibleclass
class KeyMetricsData:
    X = "x"
    Y = "y"
    D = "d"

    x: str = default_field(metadata=meta(validate_entity_name))
    y: int = positive_integer_field(default=None)
    d: str = default_field(metadata=meta(validate_entity_name))


@convertibleclass
class KeyMetricsGadget(Gadget):

    IGNORED_FIELDS = (
        f"{Gadget.CONFIGURATION}.{KeyMetricsGadgetConfig.ORGANIZATION_ID}",
        Gadget.ID_,
    )

    type = GadgetId.KEY_METRICS.value

    configuration: KeyMetricsGadgetConfig = required_field()
    data: list[KeyMetricsData] = default_field()
    infoFields: list[InfoField] = default_field()

    @property
    def builder(self):
        from extensions.dashboard.builders.key_metrics_data_builder import (
            KeyMetricsDataBuilder,
        )

        return KeyMetricsDataBuilder
