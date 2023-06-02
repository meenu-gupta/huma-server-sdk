import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.config.config import RevereTestConfig
from extensions.revere.di.components import bind_revere_repository
from extensions.revere.router.revere_router import api
from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class RevereComponent(PhoenixBaseComponent):
    config_class = RevereTestConfig
    tag_name = "revereTest"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_revere_repository(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api
