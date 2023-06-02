import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.autocomplete.config.config import AutocompleteConfig
from extensions.autocomplete.di.components import (
    bind_autocomplete_repository,
    bind_autocomplete_manager,
)
from extensions.autocomplete.router.autocomplete_router import api
from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class AutocompleteComponent(PhoenixBaseComponent):
    config_class = AutocompleteConfig
    tag_name = "autocomplete"

    def __init__(self):
        self.routers = [api]

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.routers

    def setup_auth(self):
        blueprint = self.blueprint[0]

        @blueprint.before_request
        def _setup_auth():
            self.default_auth()

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_autocomplete_manager(binder)
        bind_autocomplete_repository(binder)
