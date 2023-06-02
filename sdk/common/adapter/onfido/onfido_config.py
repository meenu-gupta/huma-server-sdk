from dataclasses import field
from onfido.regions import Region

from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class OnfidoConfig:
    apiToken: str = required_field()
    region: Region = required_field(default=Region.EU)
    tokenExpiresAfterMinutes: int = field(default=90)
    webhookToken: str = required_field()
