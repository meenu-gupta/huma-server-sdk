from typing import Optional, Union
from flask import Blueprint

from extensions.config.config import KardiaConfig
from extensions.kardia.di.components import bind_kardia_integration_client
from extensions.kardia.router.kardia_router import api
from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig


class KardiaComponent(PhoenixBaseComponent):
    config_class = KardiaConfig
    tag_name = "kardia"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_kardia_integration_client(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api
