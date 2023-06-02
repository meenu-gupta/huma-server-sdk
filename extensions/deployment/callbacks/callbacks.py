from datetime import datetime, date
from typing import Optional

from flask import request, g

from extensions.authorization.boarding.manager import BoardingManager
from extensions.authorization.events.get_custom_role_event import (
    GetDeploymentCustomRoleEvent,
    GetOrganizationCustomRoleEvent,
)
from extensions.authorization.events.pre_user_update_event import (
    PreUserProfileUpdateEvent,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import Role
from extensions.authorization.models.user import User
from extensions.authorization.services.authorization import AuthorizationService
from extensions.common.validators import validate_user_profile_field
from extensions.dashboard.models.configuration import DayAnchor
from extensions.deployment.common import is_user_proxy_or_user_type
from extensions.deployment.events import (
    PreDeploymentUpdateEvent,
    PostDeploymentUpdateEvent,
    TargetConsentedUpdateEvent,
)
from extensions.deployment.exceptions import DeploymentDoesNotExist
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.validators import (
    validate_surgery_date,
    build_date_time_validator,
)
from extensions.exceptions import OrganizationDoesNotExist
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.auth.events.mfa_required_event import MFARequiredEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.inbox.events.auth_events import PreCreateMessageEvent

DISABLED_FEATURE_TEXT = "Feature not available"
DISABLED_CUSTOM_MESSAGING = "Custom messages not available"
INVALID_PREDEFINED_MSG_TEXT = "Invalid predefined message"


def validate_extra_custom_fields_on_user_update(event: PreUserProfileUpdateEvent):
    if not event.user.extraCustomFields:
        return

    user = event.previous_state or _get_user(event.user.id)
    auth_user = AuthorizedUser(user)
    if not auth_user.is_user():
        return

    deployment = auth_user.deployment
    if not deployment.extraCustomFields:
        return
    validate_extra_custom_fields(event.user, deployment.extraCustomFields)


def validate_profile_fields_on_user_update(event: PreUserProfileUpdateEvent):
    user = event.previous_state or _get_user(event.user.id)
    auth_user = AuthorizedUser(user)
    if not auth_user.is_user():
        return

    deployment = auth_user.deployment
    profile_fields_config = deployment.profile and deployment.profile.fields
    if not profile_fields_config:
        return

    if field_validators := profile_fields_config.validators:
        validate_user_fields_with_profile_validators(event.user, field_validators)

    un_editable_fields = profile_fields_config.unEditableFields or []
    if profile_fields_config.extraIds:
        un_editable_fields.extend(profile_fields_config.extraIds.unEditableIds or [])

    if un_editable_fields:
        validate_user_fields_with_un_editable_fields(
            event.user, event.previous_state, un_editable_fields
        )


def validate_user_fields_with_profile_validators(user: User, validators: dict):
    for field_name, validator in validators.items():
        if field_value := getattr(user, field_name):
            if not isinstance(field_value, (date, datetime)):
                return

            validate = build_date_time_validator(validator)
            validate(field_name, field_value)


def validate_user_fields_with_un_editable_fields(
    new_user_state: User, old_user_state: User, un_editable_fields: list[str]
):
    for un_editable_field in un_editable_fields:
        un_editable_field_new_value = getattr(new_user_state, un_editable_field, None)
        un_editable_field_old_value = getattr(old_user_state, un_editable_field, None)
        if (
            un_editable_field_new_value
            and un_editable_field_old_value
            and (un_editable_field_old_value != un_editable_field_new_value)
        ):
            raise ConvertibleClassValidationError(
                f"[{un_editable_field}] field should not be present"
            )


def validate_extra_custom_fields(user: User, extra_custom_fields: dict):
    for key, value in user.extraCustomFields.items():
        field_config = extra_custom_fields.get(key, None)
        validate_user_profile_field(key, value, field_config)


def check_onboarding_is_required(_):
    authz_user: AuthorizedUser = g.authz_user

    if not is_user_proxy_or_user_type(authz_user):
        return

    onboarding_manager = BoardingManager(authz_user, request.path, request.url_rule)
    onboarding_manager.check_on_boarding_and_raise_error()


def validate_user_surgery_details_on_user_update(event: PreUserProfileUpdateEvent):
    user = event.user
    if user.surgeryDetails is None:
        return
    user_surgery_details_dict = user.surgeryDetails.to_dict(include_none=False)

    authz_user = AuthorizedUser(_get_user(user.id))
    if surgery_details_config := authz_user.deployment.surgeryDetails:
        errors = surgery_details_config.validate_input(user_surgery_details_dict)
    else:
        errors = {User.SURGERY_DETAILS: "No surgery details configured in deployment"}

    if errors:
        combine_errors_and_raise(errors)


def validate_user_surgery_date_on_user_update(event: PreUserProfileUpdateEvent):
    user = event.user
    if not user.surgeryDateTime:
        return

    surgery_date_rule = None

    deployment = g.authz_path_user.deployment
    if deployment.features:
        surgery_date_rule = deployment.features.surgeryDateRule
    validate_surgery_date(user.surgeryDateTime, surgery_date_rule)


def combine_errors_and_raise(errors: dict):
    message_list = []
    for key, value in errors.items():
        msg = f"Field [{key}] has error [({value})]."
        message_list.append(msg)
    raise InvalidRequestException("\n".join(message_list))


def boarding_manager_check_off_boarding(authz_user: AuthorizedUser):
    if not (authz_user.is_user() or authz_user.is_proxy()):
        return

    manager = BoardingManager(authz_user, request.path, request.url_rule)
    manager.check_off_boarding_and_raise_error()


def check_off_boarding(_):
    boarding_manager_check_off_boarding(g.authz_user)


def deployment_custom_role_callback(
    event: GetDeploymentCustomRoleEvent,
) -> Optional[Role]:
    try:
        repo = inject.instance(DeploymentRepository)
        deployment = repo.retrieve_deployment(deployment_id=event.resource_id)
    except DeploymentDoesNotExist:
        return None
    return deployment.find_role_by_id(event.role_id)


def organization_custom_role_callback(
    event: GetOrganizationCustomRoleEvent,
) -> Optional[Role]:
    try:
        repo = inject.instance(OrganizationRepository)
        org = repo.retrieve_organization(organization_id=event.resource_id)
    except OrganizationDoesNotExist:
        return None
    return org.find_role_by_id(event.role_id)


def _get_user(user_id: str):
    return AuthorizationService().retrieve_simple_user_profile(user_id)


def custom_message_check(event: PreCreateMessageEvent):
    receiver = AuthorizedUser(_get_user(event.receiver_id))
    if not receiver.deployment_id():
        raise InvalidRequestException
    features = receiver.deployment.features
    if not features or not features.messaging or not features.messaging.enabled:
        raise InvalidRequestException(DISABLED_FEATURE_TEXT)
    if not features.messaging.allowCustomMessage and event.custom:
        raise InvalidRequestException(DISABLED_CUSTOM_MESSAGING)
    predefined_messages = features.messaging.messages or []
    if not event.custom and event.text not in predefined_messages:
        raise InvalidRequestException(INVALID_PREDEFINED_MSG_TEXT)


def deployment_mfa_required(event: MFARequiredEvent) -> bool:
    authz_user = AuthorizedUser(_get_user(event.user_id))
    security = authz_user.deployment.security
    return bool(security and security.mfaRequired)


def _validate_dashboard_configuration_on_deployment_update(
    updated_deployment: Deployment, deployment_before_update: Deployment
):
    if not updated_deployment.dashboardConfiguration:
        return

    if (
        updated_deployment.dashboardConfiguration.day0Anchor == DayAnchor.CONSENT_DATE
        and not deployment_before_update.econsent
    ):
        raise InvalidRequestException(
            f"E-consent should be enabled in deployment in order to set {DayAnchor.CONSENT_DATE.value}"
        )


def _update_target_consented_on_deployment_update(updated_deployment: Deployment):
    if (
        updated_deployment.dashboardConfiguration
        and not updated_deployment.dashboardConfiguration.targetConsented
    ):
        return

    event = TargetConsentedUpdateEvent(updated_deployment.id)
    event_bus = inject.instance(EventBusAdapter)
    event_bus.emit(event)


def pre_deployment_update(event: PreDeploymentUpdateEvent):
    _validate_dashboard_configuration_on_deployment_update(
        event.deployment, event.previous_state
    )


def post_deployment_update_event(event: PostDeploymentUpdateEvent):
    _update_target_consented_on_deployment_update(event.deployment)
