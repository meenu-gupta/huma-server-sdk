import logging
from typing import Optional, Union

from flask import Blueprint

from extensions.config.config import IdentityVerificationConfig
from extensions.identity_verification.di.components import (
    bind_onfido_adapter,
    bind_identity_verification_repository,
    bind_email_verification_result_email,
)
from extensions.identity_verification.router.identity_verification_router import api
from extensions.identity_verification.router.identity_verification_public_router import (
    api as public_api,
)

from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class IdentityVerificationComponent(PhoenixBaseComponent):
    config_class = IdentityVerificationConfig
    tag_name = "identityVerification"

    def __init__(self):
        self.routers = [api, public_api]

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_onfido_adapter(binder, config)
        bind_identity_verification_repository(binder, config)
        bind_email_verification_result_email(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.routers

    def setup_auth(self):
        blueprint = self.blueprint[0]

        @blueprint.before_request
        def _setup_auth():
            self.default_auth()
