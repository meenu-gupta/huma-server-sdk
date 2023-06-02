from typing import Optional, Union

from flask import Blueprint
from flask_limiter import Limiter

from sdk.auth.callbacks.callbacks import (
    send_password_updated_email,
    send_phone_number_updated_email,
    unregister_device_notifications,
)
from sdk.auth.config.auth_config import AuthConfig
from sdk.auth.di.components import bind_auth_repository
from sdk.auth.events.set_auth_attributes_events import PostSetAuthAttributesEvent
from sdk.auth.router.auth_router import api, api_v1, sign_up, check_auth_attributes
from sdk.auth.events.sign_out_event import SignOutEventV1
from sdk.auth.router.deeplink_router import deeplink_api
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig


class AuthComponent(PhoenixBaseComponent):
    config_class = AuthConfig
    component_type = "sdk"
    tag_name = "auth"

    def __init__(self):
        self.routers = [api, api_v1, deeplink_api]

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_{self.name.lower()}",
            "route": f"/apispec_{self.name.lower()}.json",
            "rule_filter": lambda rule: True
            if rule.rule.startswith(("/api/auth/v1beta", "/api/auth/v1"))
            else False,
            "model_filter": lambda tag: True,  # all in
        }

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_auth_repository(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.routers

    def setup_rate_limiter(self, limiter: Limiter):
        limit_config = self.config.rateLimit
        if limit_config and limit_config.enable:
            # configure whole blueprint if default is present
            if limit_config.default:
                limiter.limit(limit_config.default)(api)

            # routes to be configured by signup parameter
            if limit_config.signup:
                limiter.limit(limit_config.signup)(sign_up)

            if limit_config.checkAuthAttributes:
                limiter.limit(limit_config.checkAuthAttributes)(check_auth_attributes)

    def setup_auth(self):
        pass

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        set_auth_events = [send_password_updated_email, send_phone_number_updated_email]
        for event in set_auth_events:
            event_bus.subscribe(PostSetAuthAttributesEvent, event)

        event_bus.subscribe(SignOutEventV1, unregister_device_notifications)

        super().post_setup()
