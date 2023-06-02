from enum import Enum

from sdk.common.utils.convertible import convertibleclass, default_field


@convertibleclass
class KardiaIntegrationConfig:
    apiKey: str = default_field()
    baseUrl: str = default_field()


class Action(Enum):
    CreateKardiaPatient = "CreateKardiaPatient"
