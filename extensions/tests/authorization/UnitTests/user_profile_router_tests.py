import unittest
from unittest.mock import ANY, MagicMock, Mock, patch

from flask import Flask, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    OffBoardUserRequestObject,
    OffBoardUsersRequestObject,
    ReactivateUsersRequestObject,
)
from extensions.authorization.router.user_profile_router import (
    assign_labels_to_users,
    create_helper_agreement_log,
    reactivate_users,
    retrieve_personal_documents,
    create_personal_document,
    off_board_user,
    offboard_users,
    delete_user,
    retrieve_user_notes,
    retrieve_econsent_pdf,
    sign_econsent,
    retrieve_user_care_plan_group_log,
    retrieve_care_plan_group,
    update_user_care_plan_group,
    retrieve_profiles_with_assigned_manager_with_user_id,
    retrieve_profiles_with_assigned_manager,
    unlink_proxy_user,
    link_proxy_user,
    assign_manager,
    assign_managers_to_users,
    delete_tag,
    create_tag,
    sign_consent,
    retrieve_full_configuration_for_user,
    retrieve_deployment_config,
    remove_roles,
    add_roles,
    update_user_profile,
    retrieve_staff_list,
    retrieve_user_profiles,
    retrieve_user_profiles_v1,
    retrieve_user_profile,
    api,
    api_v1,
    reactivate_user,
)
from extensions.common.s3object import S3Object
from extensions.deployment.models.consent.consent_log import ConsentLog
from sdk.common.localization.utils import Language
from sdk.common.utils.json_utils import replace_values
from sdk.phoenix.audit_logger import AuditLog

USER_PROFILE_ROUTER_PATH = "extensions.authorization.router.user_profile_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch.object(AuditLog, "create_log", MagicMock())
class UserProfileRouterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        api.policy_enabled = False
        api_v1.policy_enabled = False
        g.user = User(id="testUserId")
        g.authz_user = MagicMock()

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.CreateHelperAgreementLogUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.CreateHelperAgreementLogRequestObject")
    def test_success_create_helper_agreement_log(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {
            HelperAgreementLog.STATUS: HelperAgreementLog.Status.AGREE_AND_ACCEPT.value
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_helper_agreement_log(user_id, deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    HelperAgreementLog.STATUS: HelperAgreementLog.Status.AGREE_AND_ACCEPT.value,
                    req_obj.USER_ID: user_id,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrievePersonalDocumentsUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrievePersonalDocumentsRequestObject")
    def test_success_retrieve_personal_documents(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_personal_documents(user_id)
            req_obj.assert_called_with(userId=user_id)
            use_case().execute.assert_called_with(req_obj())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.CreatePersonalDocumentUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.CreatePersonalDocumentRequestObject")
    def test_success_create_personal_document(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_personal_document(user_id)
            req_obj.from_dict.assert_called_with({**payload, req_obj.USER_ID: user_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.OffBoardUserUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.OffBoardUserRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_off_board_user(self, g_mock: Mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        payload = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: "Recovered"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            authz_user = MagicMock()
            g_mock.authz_user = authz_user
            off_board_user(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: user_id,
                    req_obj.DEPLOYMENT: authz_user.deployment,
                    req_obj.SUBMITTER_ID: g_mock.user.id,
                    req_obj.LANGUAGE: authz_user.get_language(),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.OffBoardUsersUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.OffBoardUsersRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_offboard_users(self, g_mock: Mock, req_obj, use_case, jsonify):
        user_ids = [SAMPLE_ID]
        payload = {
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: "Recovered",
            OffBoardUsersRequestObject.USER_IDS: user_ids,
        }
        authz_user = MagicMock()
        authz_user.get_language.return_value = Language.EN
        g_mock.authz_user = authz_user
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            offboard_users()
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.DEPLOYMENT: authz_user.deployment,
                    req_obj.SUBMITTER_ID: g_mock.user.id,
                    req_obj.LANGUAGE: Language.EN,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.ReactivateUsersUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.ReactivateUsersRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_reactivate_users(self, g_mock: Mock, req_obj, use_case, jsonify):
        user_ids = [SAMPLE_ID]
        payload = {
            ReactivateUsersRequestObject.USER_IDS: user_ids,
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            reactivate_users()
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.DEPLOYMENT_ID: ANY,
                    req_obj.SUBMITTER_ID: g_mock.user.id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeleteUserCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeleteUserRequestObject")
    def test_success_delete_user(self, req_obj, use_case):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_user(user_id)
            req_obj.from_dict.assert_called_with({req_obj.USER_ID: user_id})
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify", MagicMock())
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveUserNotesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveUserNotesRequestObject")
    def test_success_retrieve_user_notes(self, req_obj, use_case, g_mock):
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.localization = {"en": {}}
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_user_notes(user_id, deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: user_id,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AuthorizationService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AuthorizedUser")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeploymentService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_econsent_pdf(
        self, g_mock, deployment_service, authz_user, auth_service, jsonify
    ):
        user_id = SAMPLE_ID
        econsent_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.is_manager.return_value = MagicMock()
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_econsent_pdf(user_id, econsent_id)
            auth_service().retrieve_user_profile.assert_called_with(user_id=user_id)
            authz_user.assert_called_with(auth_service().retrieve_user_profile())
            deployment_service().retrieve_econsent_logs.assert_called_with(
                econsent_id, authz_user(), g_mock.authz_user.is_manager()
            )
            jsonify.assert_called_with(deployment_service().retrieve_econsent_logs())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.SignEConsentUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.SignEConsentRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_sign_econsent(self, g_mock, req_obj, jsonify, sign_use_case):
        user_id = SAMPLE_ID
        econsent_id = SAMPLE_ID
        uuid = "jeQPQtXTbQv1pjoZmnePjeQPQtXTbQv1pjjj"
        g_mock.uuid = uuid
        g_mock.authz_user = MagicMock(spec=AuthorizedUser)
        g_mock.authz_user.deployment_id.return_value = SAMPLE_ID
        payload = {
            ConsentLog.SIGNATURE: {
                S3Object.KEY: "somekey",
                S3Object.BUCKET: "somebucket",
            }
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            sign_econsent(user_id, econsent_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.ECONSENT_ID: econsent_id,
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                    req_obj.REQUEST_ID: g_mock.uuid,
                    req_obj.USER: g_mock.authz_user,
                    **payload,
                }
            )
            sign_use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": sign_use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeploymentService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveUserCarePlanGroupLogRequestObject")
    def test_success_retrieve_user_care_plan_group_log(self, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_user_care_plan_group_log(user_id, deployment_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.USER_ID: user_id, req_obj.DEPLOYMENT_ID: deployment_id}
            )
            service().retrieve_user_care_plan_group_log.assert_called_with(
                req_obj.from_dict().deploymentId, req_obj.from_dict().userId
            )
            jsonify.assert_called_with([])

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeploymentService")
    def test_success_retrieve_care_plan_group(self, service, jsonify):
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_care_plan_group(user_id, deployment_id)
            service().retrieve_deployment.assert_called_with(deployment_id)
            jsonify.assert_called_with(
                {"groups": service().retrieve_deployment().retrieve_care_plan_groups()}
            )

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UpdateUserCarePlanGroupUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UpdateUserCarePlanGroupRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_update_user_care_plan_group(
        self, g_mock, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        g_mock.user = MagicMock()
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            update_user_care_plan_group(user_id, deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: user_id,
                    req_obj.SUBMITTER_ID: g_mock.user.id,
                    req_obj.SUBMITTER_NAME: g_mock.user.get_full_name(),
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveAssignedProfilesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveAssignedProfilesRequestObject")
    def test_success_retrieve_profiles_with_assigned_manager_with_user_id(
        self, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            g.authz_user = MagicMock()
            retrieve_profiles_with_assigned_manager_with_user_id(user_id)
            req_obj.from_dict.assert_called_with({req_obj.MANAGER_ID: user_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with([])

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveAssignedProfilesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveAssignedProfilesRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_profiles_with_assigned_manager(
        self, g_mock, req_obj, use_case, jsonify
    ):
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_profiles_with_assigned_manager()
            req_obj.from_dict.assert_called_with({req_obj.MANAGER_ID: g_mock.user.id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with([])

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UnlinkProxyUserUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UnlinkProxyRequestObject")
    def test_success_unlink_proxy_user(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            unlink_proxy_user(user_id)
            req_obj.from_dict.assert_called_with({req_obj.USER_ID: user_id})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute()})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.LinkProxyUserUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.LinkProxyRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_link_proxy_user(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.authz_path_user = SAMPLE_ID
        sample_email = "some_email@huma.com"
        payload = {LinkProxyRequestObject.PROXY_EMAIL: sample_email}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            link_proxy_user(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.AUTHZ_USER: g_mock.authz_path_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignManagerUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignManagerRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_assign_manager(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            assign_manager(user_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.USER_ID: user_id, req_obj.SUBMITTER_ID: g_mock.user.id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignManagersToUsersUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignManagersToUsersRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_assign_managers_to_users(self, g_mock, req_obj, use_case, jsonify):
        g_mock.user.id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            assign_managers_to_users()
            payload.update({req_obj.SUBMITTER_ID: g_mock.user.id})
            req_obj.from_dict.assert_called_with(payload)
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.AuthorizationService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.DeleteTagRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_delete_tag(self, g_mock, req_obj, service):
        user_id = SAMPLE_ID
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_tag(user_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.USER_ID: user_id, req_obj.TAGS_AUTHOR_ID: g_mock.user.id}
            )
            service().delete_tag.assert_called_with(
                req_obj.from_dict().userId, req_obj.from_dict().tagsAuthorId
            )

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AuthorizationService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.CreateTagRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_create_tag(self, g_mock, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        g_mock.user.id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_tag(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.TAGS: payload,
                    req_obj.TAGS_AUTHOR_ID: g_mock.user.id,
                    req_obj.USER_ID: user_id,
                }
            )
            service().create_tag.assert_called_with(
                req_obj.from_dict().userId,
                req_obj.from_dict().tags,
                req_obj.from_dict().tagsAuthorId,
            )
            jsonify.assert_called_with({"id": service().create_tag()})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.SignConsentUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.SignConsentRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_sign_consent(self, g_mock, req_obj, jsonify, sign_use_case):
        user_id = SAMPLE_ID
        consent_id = SAMPLE_ID
        g_mock.authz_user = MagicMock(spec=AuthorizedUser)
        g_mock.authz_user.deployment_id.return_value = SAMPLE_ID
        payload = {
            ConsentLog.SIGNATURE: {
                S3Object.BUCKET: "somebucket",
                S3Object.KEY: "somekey",
            }
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            sign_consent(user_id, consent_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: user_id,
                    req_obj.CONSENT_ID: consent_id,
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                }
            )
            sign_use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": sign_use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveFullConfigurationUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveFullConfigurationRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_full_configuration_for_user(
        self, g_mock, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_full_configuration_for_user(user_id)
            req_obj.from_dict.assert_called_with({req_obj.USER: g_mock.authz_user})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveDeploymentConfigUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveDeploymentConfigRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AuthorizationService")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_deployment_config(
        self, g_mock, service, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock(spec=AuthorizedUser)
        g_mock.authz_user.user = MagicMock()
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_deployment_config(user_id)
            req_obj.from_dict.assert_called_with({req_obj.USER: g_mock.authz_user})
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RemoveRolesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RemoveRolesRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_remove_roles(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.get_role.return_value = MagicMock()
        g_mock.authz_user.get_role.id = SAMPLE_ID
        payload = [{"a": "b"}]
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            remove_roles(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.ROLES: payload,
                    req_obj.SUBMITTER: g_mock.authz_user,
                    req_obj.USER_ID: user_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AddRolesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AddRolesRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_add_roles(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.get_role.return_value = MagicMock()
        g_mock.authz_user.get_role.id = SAMPLE_ID
        payload = [{"a": "b"}]
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            add_roles(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.ROLES: payload,
                    req_obj.SUBMITTER: g_mock.authz_user,
                    req_obj.USER_ID: user_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UpdateUserProfileUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.UpdateUserProfileRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_update_user_profile(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.deployment_id.return_value = SAMPLE_ID
        payload = {}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            update_user_profile(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.ID: user_id,
                    req_obj.PREVIOUS_STATE: g_mock.path_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveStaffUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveStaffRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_staff_list(self, g_mock, req_obj, use_case, jsonify):
        g_mock.authz_user = MagicMock()
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            g.authz_user = MagicMock()
            retrieve_staff_list()
            req_obj.from_dict.assert_called_with(
                {"a": "b", req_obj.SUBMITTER: g_mock.authz_user}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with([])

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveProfilesUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveProfilesRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_user_profiles(self, g_mock, req_obj, use_case, jsonify):
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.deployment_id.return_value = SAMPLE_ID
        g_mock.authz_user.has_identifier_data_permission.return_value = True
        payload = {}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_user_profiles()
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                    req_obj.CAN_VIEW_IDENTIFIER_DATA: True,
                    req_obj.ENABLED_MODULE_IDS: [],
                    req_obj.SUBMITTER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            result_with_replaced_values = replace_values(
                g_mock.authz_user.localization.get(), g_mock.authz_user.localization
            )
            jsonify.assert_called_with(result_with_replaced_values)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveProfilesV1UseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveProfilesRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_user_profiles_v1(
        self, g_mock, req_obj, use_case, jsonify
    ):
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.deployment_id.return_value = SAMPLE_ID
        g_mock.authz_user.has_identifier_data_permission.return_value = True
        payload = {}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_user_profiles_v1()
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                    req_obj.CAN_VIEW_IDENTIFIER_DATA: True,
                    req_obj.ENABLED_MODULE_IDS: [],
                    req_obj.SUBMITTER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveProfileUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.RetrieveUserProfileRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.remove_none_values")
    def test_success_retrieve_user_profile_regular_user(
        self, remove_none_values, g_mock, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        g_mock.authz_path_user = MagicMock()
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.deployment_id.return_value = MagicMock()
        g_mock.authz_path_user.is_manager.return_value = False
        g_mock.authz_path_user.is_super_admin.return_value = False
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_user_profile(user_id)
            data = {
                req_obj.USER_ID: user_id,
                req_obj.CAN_VIEW_IDENTIFIER_DATA: g_mock.authz_user.has_identifier_data_permission(),
                req_obj.IS_MANAGER: g_mock.authz_user.is_manager(),
                req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                req_obj.CALLER_LANGUAGE: g_mock.authz_user.get_language(),
            }
            remove_none_values.assert_called_with(data)
            req_obj.from_dict.assert_called_with(remove_none_values())
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_retrieve_user_profile_admin(self, g_mock, jsonify):
        user_id = SAMPLE_ID
        g_mock.authz_path_user = MagicMock()
        g_mock.authz_path_user.is_manager.return_value = False
        g_mock.authz_path_user.is_super_admin.return_value = True
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_user_profile(user_id)
            jsonify.assert_called_with(g_mock.authz_path_user.user.to_dict())

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.ReactivateUserUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.ReactivateUserRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_reactivate_user(
        self, mock_g, mock_req_obj, mock_use_case, mock_jsonify
    ):
        user_id = SAMPLE_ID
        mock_g.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            reactivate_user(user_id)
            mock_req_obj.from_dict.assert_called_with(
                {mock_req_obj.USER_ID: user_id, mock_req_obj.SUBMITTER_ID: user_id}
            )
            mock_use_case().execute.assert_called_with(mock_req_obj.from_dict())
            mock_jsonify.assert_called_with({"id": mock_use_case().execute().value})

    @patch(f"{USER_PROFILE_ROUTER_PATH}.jsonify")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignLabelsToUsersUseCase")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.AssignLabelsToUsersRequestObject")
    @patch(f"{USER_PROFILE_ROUTER_PATH}.g")
    def test_success_assign_user_labels(
        self, mock_g, mock_req_obj, mock_use_case, mock_jsonify
    ):
        payload = {"a": "b"}
        mock_g.authz_user = MagicMock()
        mock_g.authz_user.deployment_id.return_value = MagicMock()
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            assign_labels_to_users()
            mock_req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    mock_req_obj.ASSIGNED_BY: mock_g.user.id,
                    mock_req_obj.DEPLOYMENT_ID: mock_g.authz_user.deployment_id(),
                }
            )
            mock_use_case().execute.assert_called_with(mock_req_obj.from_dict())
            mock_jsonify.assert_called_with(mock_use_case().execute().value)


if __name__ == "__main__":
    unittest.main()
