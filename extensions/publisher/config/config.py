from dataclasses import field

from sdk import convertibleclass
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class PublisherConfig(BasePhoenixConfig):
    enable: bool = field(default=False)
