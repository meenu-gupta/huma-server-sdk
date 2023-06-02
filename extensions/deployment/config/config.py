from dataclasses import field

from sdk import convertibleclass
from sdk.common.utils.convertible import default_field
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class DeploymentConfig(BasePhoenixConfig):
    encryptionSecret: str = default_field()
    flagsEnabled: bool = field(default=False)
    userProfileValidation: bool = field(default=True)
    onBoarding: bool = field(default=True)
    offBoarding: bool = field(default=True)
