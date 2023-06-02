from typing import Optional, Union, Callable, Iterable, Type

from flask import Blueprint

from extensions.config.config import DeploymentConfig
from extensions.deployment.callbacks import (
    validate_extra_custom_fields_on_user_update,
    PreUserProfileUpdateEvent,
    validate_user_surgery_details_on_user_update,
    check_onboarding_is_required,
    check_off_boarding,
    validate_user_surgery_date_on_user_update,
    validate_profile_fields_on_user_update,
    custom_message_check,
    deployment_mfa_required,
    pre_deployment_update,
    post_deployment_update_event,
)
from extensions.deployment.di.components import (
    bind_deployment_repository,
    bind_consent_repository,
    bind_modules_manager,
    bind_econsent_repository,
)
from extensions.deployment.events import (
    PreDeploymentUpdateEvent,
    PostDeploymentUpdateEvent,
)
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.router.deployment_public_router import (
    api as deployment_public_router,
)
from extensions.deployment.router.deployment_router import api as deployment_router
from sdk.auth.events.mfa_required_event import MFARequiredEvent
from sdk.auth.events.token_extraction_event import TokenExtractionEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter, BaseEvent
from sdk.common.utils.inject import Binder, autoparams
from sdk.inbox.events.auth_events import PreCreateMessageEvent
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

EventSubscriptions = list[tuple[Type[BaseEvent], Union[Callable, Iterable[Callable]]]]


class DeploymentComponent(PhoenixBaseComponent):
    config_class = DeploymentConfig
    config: DeploymentConfig
    tag_name = "deployment"
    tasks = ["extensions.deployment"]
    _ignored_error_codes = (
        DeploymentErrorCodes.DUPLICATE_ROLE_NAME,
        DeploymentErrorCodes.MODULE_WITH_PRIMITIVE_DOES_NOT_EXIST,
        DeploymentErrorCodes.DUPLICATE_LABEL_NAME,
        DeploymentErrorCodes.MAX_DEPLOYMENT_LABELS_CREATED,
    )

    def __init__(self):
        deployment_router.url_prefix = self.url_prefix
        self.routers = [deployment_router, deployment_public_router]

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_extensions",
            "route": f"/apispec_extensions.json",
            "rule_filter": lambda rule: True
            if rule.rule.startswith("/api/extensions")
            or rule.rule.startswith("/api/public")
            else False,
            "model_filter": lambda tag: True,  # all in
        }

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_deployment_repository(binder, config)
        bind_consent_repository(binder, config)
        bind_modules_manager(binder, config)
        bind_econsent_repository(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.routers

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        subscriptions: EventSubscriptions = []

        if self.config.offBoarding:
            subscriptions.append((TokenExtractionEvent, check_off_boarding))

        if self.config.onBoarding:
            subscriptions.append((TokenExtractionEvent, check_onboarding_is_required))

        if self.config.userProfileValidation:
            pre_user_update_events = (
                validate_user_surgery_date_on_user_update,
                validate_user_surgery_details_on_user_update,
                validate_profile_fields_on_user_update,
                validate_extra_custom_fields_on_user_update,
            )
            subscriptions.append((PreUserProfileUpdateEvent, pre_user_update_events))

        subscriptions.append((MFARequiredEvent, deployment_mfa_required))
        subscriptions.append((PreCreateMessageEvent, custom_message_check))

        subscriptions.append((PreDeploymentUpdateEvent, pre_deployment_update))
        subscriptions.append((PostDeploymentUpdateEvent, post_deployment_update_event))

        for event, callback in subscriptions:
            event_bus.subscribe(event, callback)

        super().post_setup()

    def setup_auth(self):
        blueprint = self.blueprint[0]

        @blueprint.before_request
        def _setup_auth():
            self.default_auth()
