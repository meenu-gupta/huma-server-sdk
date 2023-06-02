from datetime import datetime

from flasgger import swag_from
from flask import jsonify, request, g

from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.models.user_fields_converter import UserFieldsConverter
from extensions.authorization.router.policies import (
    get_update_profile_policy,
    get_default_profile_policy,
    get_assign_roles_policy,
    get_retrieve_personal_documents_policy,
    get_retrieve_profile_policy,
    get_retrieve_profiles_policy,
    get_assign_proxy_policy,
    deny_user_with_star_resource,
    get_own_resource_policy,
)
from extensions.authorization.router.user_profile_request import (
    AddRolesToUsersRequestObject,
    AssignLabelsToUserRequestObject,
    AssignLabelsToUsersRequestObject,
    RetrieveProfilesRequestObject,
    UpdateUserProfileRequestObject,
    CreateTagRequestObject,
    RetrieveUserProfileRequestObject,
    DeleteTagRequestObject,
    AssignManagerRequestObject,
    AssignManagersToUsersRequestObject,
    RetrieveAssignedProfilesRequestObject,
    UpdateUserCarePlanGroupRequestObject,
    RetrieveUserCarePlanGroupLogRequestObject,
    RetrieveFullConfigurationRequestObject,
    AddRolesRequestObject,
    CreatePersonalDocumentRequestObject,
    RetrievePersonalDocumentsRequestObject,
    RetrieveDeploymentConfigRequestObject,
    RetrieveStaffRequestObject,
    OffBoardUserRequestObject,
    OffBoardUsersRequestObject,
    LinkProxyRequestObject,
    UnlinkProxyRequestObject,
    CreateHelperAgreementLogRequestObject,
    RemoveRolesRequestObject,
    UpdateUserRoleRequestObject,
    RetrieveProxyInvitationsRequestObject,
    ReactivateUserRequestObject,
    ReactivateUsersRequestObject,
    RetrieveUserResourcesRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.add_role_use_case import AddRolesUseCase
from extensions.authorization.use_cases.add_roles_to_users_use_case import (
    AddRolesToUsersUseCase,
)
from extensions.authorization.use_cases.assign_labels_to_user_use_case import (
    AssignLabelsToUserUseCase,
)
from extensions.authorization.use_cases.assign_labels_to_users_use_case import (
    AssignLabelsToUsersUseCase,
)
from extensions.authorization.use_cases.assign_manager_use_case import (
    AssignManagerUseCase,
)
from extensions.authorization.use_cases.assign_managers_to_users_use_case import (
    AssignManagersToUsersUseCase,
)
from extensions.authorization.use_cases.create_helper_agreement_log_use_case import (
    CreateHelperAgreementLogUseCase,
)
from extensions.authorization.use_cases.create_personal_document_use_case import (
    CreatePersonalDocumentUseCase,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.authorization.use_cases.offboard_users_use_case import (
    OffBoardUsersUseCase,
)
from extensions.authorization.use_cases.proxy_use_cases import (
    LinkProxyUserUseCase,
    UnlinkProxyUserUseCase,
)
from extensions.authorization.use_cases.reactivate_user_use_case import (
    ReactivateUserUseCase,
)
from extensions.authorization.use_cases.reactivate_users_use_case import (
    ReactivateUsersUseCase,
)
from extensions.authorization.use_cases.remove_role_use_case import RemoveRolesUseCase
from extensions.authorization.use_cases.retrieve_assigned_profiles_use_case import (
    RetrieveAssignedProfilesUseCase,
)
from extensions.authorization.use_cases.retrieve_deployment_config_use_case import (
    RetrieveDeploymentConfigUseCase,
)
from extensions.authorization.use_cases.retrieve_full_configuration_use_case import (
    RetrieveFullConfigurationUseCase,
)
from extensions.authorization.use_cases.retrieve_personal_documents_use_case import (
    RetrievePersonalDocumentsUseCase,
)
from extensions.authorization.use_cases.retrieve_profile_use_case import (
    RetrieveProfileUseCase,
)
from extensions.authorization.use_cases.retrieve_profiles_use_case import (
    RetrieveProfilesUseCase,
    RetrieveProfilesV1UseCase,
)
from extensions.authorization.use_cases.retrieve_proxy_invitations import (
    RetrieveProxyInvitationsUseCase,
)
from extensions.authorization.use_cases.retrieve_staff_use_case import (
    RetrieveStaffUseCase,
)
from extensions.authorization.use_cases.retrieve_user_resources_use_case import (
    RetrieveUserResourcesUseCase,
)
from extensions.authorization.use_cases.sign_consent_use_case import SignConsentUseCase
from extensions.authorization.use_cases.sign_econsent_use_case import (
    SignEConsentUseCase,
)
from extensions.authorization.use_cases.update_care_plan_group_use_case import (
    UpdateUserCarePlanGroupUseCase,
)
from extensions.authorization.use_cases.update_user_profile_use_case import (
    UpdateUserProfileUseCase,
)
from extensions.authorization.use_cases.withdraw_econsent_use_case import (
    WithdrawEConsentUseCase,
)
from extensions.common.policies import get_off_board_policy, deny_not_self
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.router.deployment_requests import (
    AddUserNotesRequestObject,
    SignConsentRequestObject,
    SignEConsentRequestObject,
    RetrieveUserNotesRequestObject,
    WithdrawEConsentRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.use_case.add_user_notes_use_case import AddUserNotesUseCase
from extensions.deployment.use_case.retrieve_user_notes_use_case import (
    RetrieveUserNotesUseCase,
)
from sdk.auth.use_case.auth_request_objects import DeleteUserRequestObject
from sdk.auth.use_case.auth_use_cases import DeleteUserCase
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
    get_request_json_list_or_raise_exception,
    validate_request_body_type_is_object,
)
from sdk.common.utils.json_utils import replace_key_values
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "user_profile_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=get_default_profile_policy,
)

api_v1 = IAMBlueprint(
    "user_profile_route_v1",
    __name__,
    url_prefix="/api/extensions/v1/user",
    policy=get_default_profile_policy,
)


@api.route("/<user_id>", methods=["GET"])
@api.require_policy(get_retrieve_profile_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_user_profile.yml")
def retrieve_user_profile(user_id):
    authz_path_user: AuthorizedUser = g.authz_path_user
    if authz_path_user.is_manager() or authz_path_user.is_super_admin():
        return jsonify(authz_path_user.user.to_dict(include_none=False)), 200

    authz_user: AuthorizedUser = g.authz_user
    has_id_permission = authz_user.has_identifier_data_permission(user_id=user_id)
    is_proxy_participant = authz_path_user.is_proxy_for_user(g.authz_user.id)
    is_identified = has_id_permission or is_proxy_participant
    body = {
        RetrieveUserProfileRequestObject.USER_ID: user_id,
        RetrieveUserProfileRequestObject.CAN_VIEW_IDENTIFIER_DATA: is_identified,
        RetrieveUserProfileRequestObject.IS_MANAGER: authz_user.is_manager(),
        RetrieveUserProfileRequestObject.DEPLOYMENT_ID: authz_user.deployment_id(),
        RetrieveUserProfileRequestObject.CALLER_LANGUAGE: authz_user.get_language(),
    }
    body = remove_none_values(body)
    request_object = RetrieveUserProfileRequestObject.from_dict(body)
    response = RetrieveProfileUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.route("/profiles", methods=["POST"])
@api.require_policy(get_retrieve_profiles_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_user_profiles.yml")
def retrieve_user_profiles():
    body = validate_request_body_type_is_object(request)
    authz_user: AuthorizedUser = g.authz_user
    is_identified = authz_user.has_identifier_data_permission()

    enabled_module_ids = []
    if authz_user.deployment_id():
        enabled_module_ids = [mc.id for mc in authz_user.deployment.moduleConfigs]

    body.update(
        {
            RetrieveProfilesRequestObject.DEPLOYMENT_ID: authz_user.deployment_id(),
            RetrieveProfilesRequestObject.CAN_VIEW_IDENTIFIER_DATA: is_identified,
            RetrieveProfilesRequestObject.ENABLED_MODULE_IDS: enabled_module_ids,
            RetrieveProfilesRequestObject.SUBMITTER: authz_user,
        }
    )
    request_object = RetrieveProfilesRequestObject.from_dict(body)
    response = RetrieveProfilesUseCase().execute(request_object)
    translated_response = replace_key_values(
        response.value, authz_user.localization, string_list_translator=True
    )
    return jsonify(translated_response), 200


@api_v1.route("/profiles", methods=["POST"])
@api_v1.require_policy(get_retrieve_profiles_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_user_profiles_v1.yml")
def retrieve_user_profiles_v1():
    body = validate_request_body_type_is_object(request)
    authz_user: AuthorizedUser = g.authz_user
    is_identified = authz_user.has_identifier_data_permission()

    enabled_module_ids = []
    if authz_user.deployment_id():
        enabled_module_ids = [mc.id for mc in authz_user.deployment.moduleConfigs]

    body.update(
        {
            RetrieveProfilesRequestObject.DEPLOYMENT_ID: authz_user.deployment_id(),
            RetrieveProfilesRequestObject.CAN_VIEW_IDENTIFIER_DATA: is_identified,
            RetrieveProfilesRequestObject.ENABLED_MODULE_IDS: enabled_module_ids,
            RetrieveProfilesRequestObject.SUBMITTER: authz_user,
        }
    )
    request_object = RetrieveProfilesRequestObject.from_dict(remove_none_values(body))
    response = RetrieveProfilesV1UseCase().execute(request_object)
    response.value.users = replace_key_values(
        response.value.users, authz_user.localization, string_list_translator=True
    )
    return jsonify(response.value), 200


@api.route("/staff", methods=["POST"])
@api.require_policy(PolicyType.VIEW_STAFF_LIST, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_staff_list.yml")
def retrieve_staff_list():
    body = get_request_json_dict_or_raise_exception(request)
    body.update({RetrieveStaffRequestObject.SUBMITTER: g.authz_user})
    request_object = RetrieveStaffRequestObject.from_dict(body)
    response = RetrieveStaffUseCase().execute(request_object)
    language = g.authz_user.get_language()
    staff_list = [
        UserFieldsConverter(user, language=language).to_dict()
        for user in response.value
    ]
    return jsonify(staff_list), 200


@api.route("/add-role", methods=["POST"])
@api.require_policy(get_assign_roles_policy, override=True)
@audit(AuthorizationAction.AddRolesToUsers)
@swag_from(f"{SWAGGER_DIR}/update_users_roles.yml")
def add_roles_to_users():
    body = get_request_json_dict_or_raise_exception(request)
    request_object = AddRolesToUsersRequestObject.from_dict(
        {
            **body,
            AddRolesToUsersRequestObject.SUBMITTER: g.authz_user,
        }
    )
    response_object = AddRolesToUsersUseCase().execute(request_object)
    return jsonify(response_object.value), 200


@api.post("/assign")
@api.require_policy(PolicyType.ASSIGN_PATIENT_TO_STAFF, override=True)
@audit(AuthorizationAction.AssignManagersToUsers)
@swag_from(f"{SWAGGER_DIR}/assign_managers_to_users.yml")
def assign_managers_to_users():
    body = get_request_json_dict_or_raise_exception(request)
    request_object = AssignManagersToUsersRequestObject.from_dict(
        {
            **body,
            AssignManagersToUsersRequestObject.SUBMITTER_ID: g.user.id,
        }
    )

    response_object = AssignManagersToUsersUseCase().execute(request_object)
    return jsonify(response_object.value), 201


@api.post("/offboard")
@api.require_policy(get_off_board_policy, override=True)
@audit(AuthorizationAction.OffBoardUsers)
@swag_from(f"{SWAGGER_DIR}/offboard_users.yml")
def offboard_users():
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            OffBoardUsersRequestObject.DEPLOYMENT: g.authz_user.deployment,
            OffBoardUsersRequestObject.SUBMITTER_ID: g.user.id,
            OffBoardUsersRequestObject.LANGUAGE: g.authz_user.get_language(),
        }
    )
    request_object = OffBoardUsersRequestObject.from_dict(body)
    response = OffBoardUsersUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.post("/reactivate")
@api.require_policy(get_off_board_policy, override=True)
@audit(AuthorizationAction.ReactivateUsers)
@swag_from(f"{SWAGGER_DIR}/reactivate_users.yml")
def reactivate_users():
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            ReactivateUsersRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
            ReactivateUsersRequestObject.SUBMITTER_ID: g.user.id,
        }
    )
    request_object = ReactivateUsersRequestObject.from_dict(body)
    response = ReactivateUsersUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.route("/<user_id>", methods=["POST"])
@api.require_policy(get_update_profile_policy, override=True)
@audit(AuthorizationAction.UpdateUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/user_profile_update.yml")
def update_user_profile(user_id):
    req_body = validate_request_body_type_is_object(request)
    body = remove_none_values(req_body)
    body.update(
        {
            UpdateUserProfileRequestObject.ID: user_id,
            UpdateUserProfileRequestObject.PREVIOUS_STATE: g.path_user,
        }
    )
    request_object = UpdateUserProfileRequestObject.from_dict(body)
    use_case = UpdateUserProfileUseCase(deployment_id=g.authz_user.deployment_id())
    response = use_case.execute(request_object)
    return jsonify({"id": response.value}), 200


@api.route("/<user_id>/assign-roles", methods=["POST"])
@api.require_policy(get_assign_roles_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/assign_user_roles.yml")
def assign_user_roles(user_id: str):
    """@deprecated"""
    body = get_request_json_dict_or_raise_exception(request)
    body.update({UpdateUserRoleRequestObject.SUBMITTER: g.authz_user})
    roles: list[RoleAssignment] = UpdateUserRoleRequestObject.from_dict(body).roles
    updated_id = AuthorizationService().update_user_roles(user_id, roles)
    return jsonify({"id": updated_id}), 200


@api.route("/<user_id>/add-role", methods=["POST"])
@api.require_policy(get_assign_roles_policy, override=True)
@audit(AuthorizationAction.AddRoles, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/update_role.yml")
def add_roles(user_id: str):
    body = get_request_json_list_or_raise_exception(request)
    AddRolesRequestObject.check_permission(body, g.authz_user)
    data = {
        AddRolesRequestObject.ROLES: body,
        AddRolesRequestObject.SUBMITTER: g.authz_user,
        AddRolesRequestObject.USER_ID: user_id,
    }
    request_object = AddRolesRequestObject.from_dict(data)
    response = AddRolesUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@api.route("/<user_id>/remove-role", methods=["POST"])
@api.require_policy(get_assign_roles_policy, override=True)
@audit(AuthorizationAction.RemoveRoles, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/update_role.yml")
def remove_roles(user_id: str):
    body = get_request_json_list_or_raise_exception(request)
    data = {
        RemoveRolesRequestObject.ROLES: body,
        RemoveRolesRequestObject.SUBMITTER: g.authz_user,
        RemoveRolesRequestObject.USER_ID: user_id,
    }
    request_object = RemoveRolesRequestObject.from_dict(data)
    response = RemoveRolesUseCase().execute(request_object)
    return jsonify({"id": response.value}), 204


@api.route("/<user_id>/configuration", methods=["GET"])
@api.require_policy(deny_user_with_star_resource)
@swag_from(f"{SWAGGER_DIR}/retrieve_configuration.yml")
def retrieve_deployment_config(user_id: str):
    authz_user: AuthorizedUser = g.authz_user
    request_data = {RetrieveDeploymentConfigRequestObject.USER: authz_user}
    request_object = RetrieveDeploymentConfigRequestObject.from_dict(request_data)
    use_case = RetrieveDeploymentConfigUseCase()
    response = use_case.execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/<user_id>/fullconfiguration", methods=["GET"])
@api.require_policy(deny_user_with_star_resource)
@swag_from(f"{SWAGGER_DIR}/retrieve_full_configuration.yml")
def retrieve_full_configuration_for_user(user_id: str):
    request_object = RetrieveFullConfigurationRequestObject.from_dict(
        {RetrieveFullConfigurationRequestObject.USER: g.authz_user}
    )
    response = RetrieveFullConfigurationUseCase().execute(request_object)
    return jsonify(response.value.to_dict()), 200


@api.route("/<user_id>/consent/<consent_id>/sign", methods=["POST"])
@api.require_policy(PolicyType.EDIT_OWN_PROFILE)
@audit(AuthorizationAction.SignConsent, target_key="consent_id")
@swag_from(f"{SWAGGER_DIR}/sign_consent.yml")
def sign_consent(user_id, consent_id):
    body = validate_request_body_type_is_object(request)
    authz_user: AuthorizedUser = g.authz_user
    request_object = SignConsentRequestObject.from_dict(
        {
            **body,
            SignConsentRequestObject.USER_ID: user_id,
            SignConsentRequestObject.CONSENT_ID: consent_id,
            SignConsentRequestObject.DEPLOYMENT_ID: authz_user.deployment_id(),
        }
    )
    result = SignConsentUseCase().execute(request_object)
    return jsonify({"id": result.value}), 201


@api.route("/<user_id>/labels", methods=["POST"])
@api.require_policy(PolicyType.ASSIGN_PATIENT_LABELS, override=True)
@audit(AuthorizationAction.AssignLabelsToUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/assign_user_labels.yml")
def assign_user_labels(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_obj: AssignLabelsToUserRequestObject = AssignLabelsToUserRequestObject.from_dict(
        {
            **body,
            AssignLabelsToUserRequestObject.ASSIGNED_BY: g.user.id,
            AssignLabelsToUserRequestObject.USER_ID: user_id,
            AssignLabelsToUserRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
        }
    )
    use_case = AssignLabelsToUserUseCase()
    response = use_case.execute(req_obj)
    return jsonify(response.value), 200


@api.route("/labels", methods=["POST"])
@api.require_policy(PolicyType.ASSIGN_PATIENT_LABELS, override=True)
@audit(AuthorizationAction.AssignLabelsToUsers)
@swag_from(f"{SWAGGER_DIR}/assign_users_labels.yml")
def assign_labels_to_users():
    body = get_request_json_dict_or_raise_exception(request)
    req_obj: AssignLabelsToUsersRequestObject = AssignLabelsToUsersRequestObject.from_dict(
        {
            **body,
            AssignLabelsToUsersRequestObject.ASSIGNED_BY: g.user.id,
            AssignLabelsToUsersRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
        }
    )
    use_case = AssignLabelsToUsersUseCase()
    response = use_case.execute(req_obj)
    return jsonify(response.value), 200


@api.route("/<user_id>/tags", methods=["POST"])
@api.require_policy(PolicyType.CHANGE_PATIENT_STATUS, override=True)
@audit(AuthorizationAction.CreateTag, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/user_set_tags.yml")
def create_tag(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_obj = CreateTagRequestObject.from_dict(
        {
            CreateTagRequestObject.TAGS: body,
            CreateTagRequestObject.TAGS_AUTHOR_ID: g.user.id,
            CreateTagRequestObject.USER_ID: user_id,
        }
    )
    service = AuthorizationService()
    user_id = service.create_tag(req_obj.userId, req_obj.tags, req_obj.tagsAuthorId)
    return jsonify({"id": user_id}), 201


@api.route("/<user_id>/tags", methods=["DELETE"])
@api.require_policy(PolicyType.CHANGE_PATIENT_STATUS, override=True)
@audit(AuthorizationAction.DeleteTag, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/user_delete_tags.yml")
def delete_tag(user_id: str):
    request_object: DeleteTagRequestObject = DeleteTagRequestObject.from_dict(
        {
            DeleteTagRequestObject.USER_ID: user_id,
            DeleteTagRequestObject.TAGS_AUTHOR_ID: g.user.id,
        }
    )

    service = AuthorizationService()
    service.delete_tag(request_object.userId, request_object.tagsAuthorId)
    return "", 204


@api.route("/<user_id>/assign", methods=["POST"])
@api.require_policy(PolicyType.ASSIGN_PATIENT_TO_STAFF, override=True)
@audit(AuthorizationAction.AssignManager, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/assign_managers.yml")
def assign_manager(user_id: str):
    body = validate_request_body_type_is_object(request)
    request_object = AssignManagerRequestObject.from_dict(
        {
            **body,
            AssignManagerRequestObject.USER_ID: user_id,
            AssignManagerRequestObject.SUBMITTER_ID: g.user.id,
        }
    )

    response_object = AssignManagerUseCase().execute(request_object)
    return jsonify(response_object.value), 201


@api.post("/<user_id>/assign-proxy")
@api.require_policy(get_assign_proxy_policy)
@audit(AuthorizationAction.LinkProxyUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/link_proxy_user.yml")
def link_proxy_user(user_id: str):
    request_json = get_request_json_dict_or_raise_exception(request)
    request_object = LinkProxyRequestObject.from_dict(
        {**request_json, LinkProxyRequestObject.AUTHZ_USER: g.authz_path_user}
    )

    response = LinkProxyUserUseCase().execute(request_object)
    return jsonify(response.value.to_dict()), 201


@api.post("/<user_id>/unassign-proxy")
@api.require_policy(PolicyType.EDIT_OWN_PROFILE)
@audit(AuthorizationAction.UnLinkProxyUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/unlink_proxy_user.yml")
def unlink_proxy_user(user_id: str):
    request_json = validate_request_body_type_is_object(request)
    request_json.update({UnlinkProxyRequestObject.USER_ID: user_id})
    request_object = UnlinkProxyRequestObject.from_dict(request_json)
    user_id = UnlinkProxyUserUseCase().execute(request_object)
    return jsonify({"id": user_id}), 204


@api.route("/profiles/assigned", methods=["GET"])
@api.require_policy(PolicyType.VIEW_PATIENT_PROFILE, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_assigned_users.yml")
def retrieve_profiles_with_assigned_manager():
    request_object = RetrieveAssignedProfilesRequestObject.from_dict(
        {RetrieveAssignedProfilesRequestObject.MANAGER_ID: g.user.id}
    )
    response = RetrieveAssignedProfilesUseCase().execute(request_object)
    language = g.authz_user.get_language()
    profiles = [
        UserFieldsConverter(profile, language=language).to_dict()
        for profile in response.value
    ]
    return jsonify(profiles), 200


@api.route("/<user_id>/profiles/assigned", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_assigned_users_with_user_id.yml")
def retrieve_profiles_with_assigned_manager_with_user_id(user_id=None):
    request_object = RetrieveAssignedProfilesRequestObject.from_dict(
        {RetrieveAssignedProfilesRequestObject.MANAGER_ID: user_id}
    )
    response = RetrieveAssignedProfilesUseCase().execute(request_object)
    language = g.authz_user.get_language()
    profiles = [
        UserFieldsConverter(profile, language=language).to_dict()
        for profile in response.value
    ]
    return jsonify(profiles), 200


@api.route("/<user_id>/deployment/<deployment_id>/care-plan-group", methods=["POST"])
@api.require_policy(PolicyType.MOVE_PATIENT_TO_OTHER_GROUP, override=True)
@audit(AuthorizationAction.UpdateUserCarePlanGroup, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/update_user_care_plan.yml")
def update_user_care_plan_group(user_id: str, deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            UpdateUserCarePlanGroupRequestObject.USER_ID: user_id,
            UpdateUserCarePlanGroupRequestObject.SUBMITTER_ID: g.user.id,
            UpdateUserCarePlanGroupRequestObject.SUBMITTER_NAME: g.user.get_full_name(),
            UpdateUserCarePlanGroupRequestObject.DEPLOYMENT_ID: deployment_id,
        }
    )
    request_object = UpdateUserCarePlanGroupRequestObject.from_dict(body)
    response = UpdateUserCarePlanGroupUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@api.route("/<user_id>/deployment/<deployment_id>/care-plan-groups", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_care_plan_group.yml")
def retrieve_care_plan_group(user_id: str, deployment_id: str):
    deployment = DeploymentService().retrieve_deployment(deployment_id)
    care_plan_groups = deployment.retrieve_care_plan_groups()
    for key in care_plan_groups:
        module_configs = [
            item.to_dict(include_none=False)
            for item in care_plan_groups[key][Deployment.MODULE_CONFIGS]
        ]
        care_plan_groups[key][Deployment.MODULE_CONFIGS] = module_configs
    return jsonify({"groups": care_plan_groups}), 200


@api.route("/<user_id>/deployment/<deployment_id>/care-plan-group-log", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_user_care_plan_group_log.yml")
def retrieve_user_care_plan_group_log(user_id: str, deployment_id: str):
    req_obj = RetrieveUserCarePlanGroupLogRequestObject.from_dict(
        {
            RetrieveUserCarePlanGroupLogRequestObject.USER_ID: user_id,
            RetrieveUserCarePlanGroupLogRequestObject.DEPLOYMENT_ID: deployment_id,
        }
    )
    user_care_plan_group_logs = DeploymentService().retrieve_user_care_plan_group_log(
        req_obj.deploymentId, req_obj.userId
    )
    return jsonify([m.to_dict() for m in user_care_plan_group_logs]), 200


@api.route("/<user_id>/econsent/<econsent_id>/sign", methods=["POST"])
@api.require_policy(PolicyType.EDIT_OWN_PROFILE)
@audit(AuthorizationAction.SignEConsent, target_key="econsent_id")
@swag_from(f"{SWAGGER_DIR}/sign_econsent.yml")
def sign_econsent(user_id, econsent_id):
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            SignEConsentRequestObject.ECONSENT_ID: econsent_id,
            SignEConsentRequestObject.USER: g.authz_user,
            SignEConsentRequestObject.USER_ID: user_id,
            SignEConsentRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
            SignEConsentRequestObject.REQUEST_ID: g.uuid,
        }
    )
    request_object = SignEConsentRequestObject.from_dict(body)
    rsp = SignEConsentUseCase().execute(request_object)
    return jsonify({"id": rsp.value}), 201


@api.route("/<user_id>/econsent/<econsent_id>/withdraw", methods=["POST"])
@api.require_policy(PolicyType.EDIT_OWN_PROFILE)
@audit(AuthorizationAction.OffBoardUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/withdraw_econsent.yml")
def withdraw_econsent(user_id, econsent_id):
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            WithdrawEConsentRequestObject.USER_ID: user_id,
            WithdrawEConsentRequestObject.ECONSENT_ID: econsent_id,
            WithdrawEConsentRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
        }
    )
    request_object = WithdrawEConsentRequestObject.from_dict(body)
    response = WithdrawEConsentUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


# if manager, returns all users' econsent pdfs and if user, return only his econsent pdf
@api.route("/<user_id>/econsent/<econsent_id>/pdf", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_econsent_pdf.yml")
def retrieve_econsent_pdf(user_id, econsent_id):
    service = AuthorizationService()
    user: User = service.retrieve_user_profile(user_id=user_id)
    auth_user_for_econsent = AuthorizedUser(user)

    pdfs = DeploymentService().retrieve_econsent_logs(
        econsent_id, auth_user_for_econsent, g.authz_user.is_manager()
    )
    return jsonify(pdfs), 200


# retrieve careplangroup notes and questionnaires' notes whose type is OBSERVATION_NOTES
@api.route("/<user_id>/deployment/<deployment_id>/notes", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_user_notes.yml")
def retrieve_user_notes(user_id, deployment_id):
    body = validate_request_body_type_is_object(request)
    request_object: RetrieveUserNotesRequestObject = (
        RetrieveUserNotesRequestObject.from_dict(
            {
                **body,
                RetrieveUserNotesRequestObject.USER_ID: user_id,
                RetrieveUserNotesRequestObject.DEPLOYMENT_ID: deployment_id,
            }
        )
    )

    use_case = RetrieveUserNotesUseCase()
    response_obj = use_case.execute(request_object)
    result = response_obj.notes_to_array()
    translated_result = replace_key_values(
        result, g.authz_user.localization, string_list_translator=True
    )
    return jsonify(translated_result), 200


@api_v1.route("/<user_id>/deployment/<deployment_id>/notes", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_user_notes_v1.yml")
def retrieve_user_notes_v1(user_id, deployment_id):
    args = request.args or {}
    skip = int(args.get(RetrieveUserNotesRequestObject.SKIP, 0))
    limit = int(args.get(RetrieveUserNotesRequestObject.LIMIT, 100))
    request_object = RetrieveUserNotesRequestObject.from_dict(
        {
            RetrieveUserNotesRequestObject.USER_ID: user_id,
            RetrieveUserNotesRequestObject.DEPLOYMENT_ID: deployment_id,
            RetrieveUserNotesRequestObject.SKIP: skip,
            RetrieveUserNotesRequestObject.LIMIT: limit,
        }
    )

    use_case = RetrieveUserNotesUseCase()
    response_obj = use_case.execute(request_object)
    result = response_obj.notes_to_array()
    translated_result = replace_key_values(
        result, g.authz_user.localization, string_list_translator=True
    )
    return jsonify(translated_result), 200


@api_v1.route("/<user_id>/deployment/<deployment_id>/notes", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/add_user_notes_v1.yml")
def add_user_notes_v1(user_id, deployment_id):
    request_body = get_request_json_dict_or_raise_exception(request)
    request_dict = {
        **request_body,
        AddUserNotesRequestObject.USER_ID: user_id,
        AddUserNotesRequestObject.SUBMITTER_ID: g.user.id,
        AddUserNotesRequestObject.DEPLOYMENT_ID: deployment_id,
        AddUserNotesRequestObject.CREATE_DATE_TIME: datetime.utcnow(),
    }
    request_object = AddUserNotesRequestObject.from_dict(request_dict)
    response = AddUserNotesUseCase().execute(request_object)
    return jsonify(response), 201


@api.route("/<user_id>/delete-user", methods=["DELETE"])
@api.require_policy(PolicyType.REMOVE_USER, override=True)
@audit(AuthorizationAction.DeleteUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/delete_user.yml")
def delete_user(user_id):
    """Allows to delete user and all its dependencies"""

    request_object = DeleteUserRequestObject.from_dict(
        {DeleteUserRequestObject.USER_ID: user_id}
    )
    DeleteUserCase().execute(request_object)

    return "", 204


@api.route("/<user_id>/offboard", methods=["POST"])
@api.require_policy(get_off_board_policy, override=True)
@audit(AuthorizationAction.OffBoardUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/off_board_user.yml")
def off_board_user(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            OffBoardUserRequestObject.USER_ID: user_id,
            OffBoardUserRequestObject.DEPLOYMENT: g.authz_user.deployment,
            OffBoardUserRequestObject.SUBMITTER_ID: g.user.id,
            OffBoardUserRequestObject.LANGUAGE: g.authz_user.get_language(),
        }
    )
    request_object = OffBoardUserRequestObject.from_dict(body)
    response = OffBoardUserUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@api.route("/<user_id>/reactivate", methods=["POST"])
@api.require_policy(get_off_board_policy, override=True)
@audit(AuthorizationAction.ReactivateUser, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/reactivate_user.yml")
def reactivate_user(user_id: str):
    request_object: ReactivateUserRequestObject = ReactivateUserRequestObject.from_dict(
        {
            ReactivateUserRequestObject.USER_ID: user_id,
            ReactivateUserRequestObject.SUBMITTER_ID: g.user.id,
        }
    )
    response = ReactivateUserUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@api.route("/<user_id>/document", methods=["POST"])
@api.require_policy(get_update_profile_policy, override=True)
@audit(AuthorizationAction.CreatePersonalDocument, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/create_personal_document.yml")
def create_personal_document(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CreatePersonalDocumentRequestObject.USER_ID: user_id})
    request_object = CreatePersonalDocumentRequestObject.from_dict(body)
    response = CreatePersonalDocumentUseCase().execute(request_object)
    return jsonify({"id": response.value}), 201


@api.route("/<user_id>/document", methods=["GET"])
@api.require_policy(get_retrieve_personal_documents_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_personal_documents.yml")
def retrieve_personal_documents(user_id: str):
    request_object = RetrievePersonalDocumentsRequestObject(userId=user_id)
    response = RetrievePersonalDocumentsUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.route("/<user_id>/deployment/<deployment_id>/helperagreementlog", methods=["POST"])
@api.require_policy(deny_not_self, override=True)
@audit(AuthorizationAction.CreateHelperAgreementLog, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/create_helper_agreement_log.yml")
def create_helper_agreement_log(user_id: str, deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update(
        {
            CreateHelperAgreementLogRequestObject.USER_ID: user_id,
            CreateHelperAgreementLogRequestObject.DEPLOYMENT_ID: deployment_id,
        }
    )
    request_object = CreateHelperAgreementLogRequestObject.from_dict(body)
    response = CreateHelperAgreementLogUseCase().execute(request_object)

    return jsonify({"id": response.value}), 201


@api.route("/<user_id>/proxy-invitations", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_proxy_invitations.yml")
def retrieve_proxy_invitations(user_id: str):
    request_data = {RetrieveProxyInvitationsRequestObject.SUBMITTER: g.authz_path_user}
    request_object = RetrieveProxyInvitationsRequestObject.from_dict(request_data)
    response = RetrieveProxyInvitationsUseCase().execute(request_object)

    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/<user_id>/resources", methods=["GET"])
@api.require_policy(get_own_resource_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_user_resources.yml")
def retrieve_user_resources(user_id: str):
    request_object = RetrieveUserResourcesRequestObject.from_dict(
        {RetrieveUserResourcesRequestObject.USER_ID: user_id}
    )
    response = RetrieveUserResourcesUseCase().execute(request_object)

    return jsonify(response.value.to_dict(include_none=False)), 200
