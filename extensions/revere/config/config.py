from sdk import convertibleclass
from sdk.common.utils.convertible import default_field
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class RevereTestConfig(BasePhoenixConfig):
    clientId: str = default_field()
    clientKey: str = default_field()
