from dataclasses import field

from sdk import convertibleclass
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class AuthorizationConfig(BasePhoenixConfig):
    checkAdminIpAddress: bool = field(default=True)
