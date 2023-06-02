import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.authorization.models.user import User
from extensions.common.sort import SortField
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    LearnArticle,
    LearnSection,
    LearnArticleType,
    LearnArticleContent,
    LearnArticleContentType,
)
from extensions.deployment.router.deployment_requests import (
    RetrieveDeploymentsRequestObject,
    CreateLearnArticleRequestObject,
    DeleteDeploymentTemplateRequestObject,
)
from extensions.deployment.router.deployment_router import (
    create_deployment_labels,
    create_localization,
    create_or_update_roles,
    retrieve_deployment_labels,
    retrieve_latest_econsent,
    create_econsent,
    create_care_plan_group,
    encrypt_value,
    delete_key_action_config,
    delete_article,
    delete_learn_section,
    delete_module_config,
    delete_deployment,
    update_deployment_labels,
    update_key_action_config,
    update_article,
    update_learn_section,
    update_deployment,
    retrieve_modules,
    retrieve_latest_consent,
    retrieve_deployment_by_version_number,
    retrieve_deployment,
    retrieve_deployments,
    update_module_config,
    create_key_action_config,
    delete_onboarding_module_config,
    update_onboarding_module_config,
    create_onboarding_module_config,
    create_article,
    create_learn_section,
    create_consent,
    create_deployment,
    api,
    retrieve_localizable_fields,
    generate_master_translation,
    reorder_learn_articles,
    retrieve_deployment_key_actions,
    create_module_configs,
    create_deployment_template,
    retrieve_deployment_template,
    retrieve_deployment_templates,
    delete_deployment_template,
    update_deployment_template,
    send_message_to_patient_list,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.audit_logger import AuditLog

DEPLOYMENT_ROUTER_PATH = "extensions.deployment.router.deployment_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()

mock_g = MagicMock()
mock_g.user = User(id="testUserId", givenName="Test", familyName="User")

USER_ID_1 = "5e8f0c74b50aa9656c34789b"
USER_ID_2 = "5e8f0c74b50aa9656c34789c"
USER_ID_3 = "5ffee8a004ae8ffa8e721114"


@patch.object(AuditLog, "create_log", MagicMock())
@patch(f"{DEPLOYMENT_ROUTER_PATH}.g", mock_g)
class DeploymentRouterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        api.policy_enabled = False

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateLocalizationsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateLocalizationsRequestObject")
    def test_success_create_localization(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_localization(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.LOCALIZATIONS: payload,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentRoleUpdateObject")
    def test_success_create_or_update_roles(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            create_or_update_roles(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            service().create_or_update_roles.assert_called_with(
                deployment_id=req_obj.from_dict().deploymentId,
                roles=req_obj.from_dict().roles,
            )
            jsonify.assert_called_with({"id": service().create_or_update_roles()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    def test_success_retrieve_latest_econsent(self, service, jsonify):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_latest_econsent(deployment_id)
            service().retrieve_deployment.assert_called_with(deployment_id)
            jsonify.assert_called_with(
                service().retrieve_deployment().econsent.to_dict()
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateEConsentRequestObject")
    def test_success_create_econsent(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_econsent(deployment_id)
            req_obj.from_dict.assert_called_with(payload)
            service().create_econsent.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({EConsent.ID: service().create_econsent()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateCarePlansRequestObject")
    def test_success_create_care_plan_group(self, req_obj, service):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_care_plan_group(deployment_id)
            req_obj.from_dict.assert_called_with(payload)
            service().create_care_plan_group.assert_called_with(
                deployment_id, req_obj.from_dict()
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.EncryptValueRequestObject")
    def test_success_encrypt_value(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            encrypt_value(deployment_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.DEPLOYMENT_ID: deployment_id, **payload}
            )
            service().encrypt_value.assert_called_with(
                req_obj.from_dict().deploymentId, req_obj.from_dict().value
            )
            jsonify.assert_called_with({"encryptedValue": service().encrypt_value()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteKeyActionRequestObject")
    def test_success_delete_key_action_config(self, req_obj, service):
        deployment_id = SAMPLE_ID
        key_action_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_key_action_config(deployment_id, key_action_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.KEY_ACTION_CONFIG_ID: key_action_id,
                }
            )
            service().delete_key_action.assert_called_with(
                req_obj.from_dict().deploymentId, req_obj.from_dict().keyActionConfigId
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteLearnArticleUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteArticleRequestObject")
    def test_success_delete_article(self, req_obj, use_case):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        article_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_article(deployment_id, section_id, article_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.SECTION_ID: section_id,
                    req_obj.ARTICLE_ID: article_id,
                    req_obj.USER_ID: mock_g.user.id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteLearnSectionUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteLearnSectionRequestObject")
    def test_success_delete_learn_section(self, req_obj, use_case):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_learn_section(deployment_id, section_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.SECTION_ID: section_id,
                    req_obj.USER_ID: mock_g.user.id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteModuleConfigRequestObject")
    def test_success_delete_module_config(self, req_obj, service):
        deployment_id = SAMPLE_ID
        module_config_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_module_config(deployment_id, module_config_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.MODULE_CONFIG_ID: module_config_id,
                }
            )
            service().delete_module_config.assert_called_with(
                req_obj.from_dict().deploymentId, req_obj.from_dict().moduleConfigId
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteDeploymentRequestObject")
    def test_success_delete_deployment(self, req_obj, service):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_deployment(deployment_id)
            req_obj.from_dict.assert_called_with({req_obj.DEPLOYMENT_ID: deployment_id})
            service().delete_deployment.assert_called_with(
                req_obj.from_dict().deploymentId
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateKeyActionConfigRequestObject")
    def test_success_update_key_action_config(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        key_action_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_key_action_config(deployment_id, key_action_id)
            req_obj.from_dict.assert_called_with(
                {**payload, KeyActionConfig.ID: key_action_id}
            )
            service().update_key_action.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().update_key_action()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateArticleRequestObject")
    def test_success_update_article(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        article_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_article(deployment_id, section_id, article_id)
            req_obj.from_dict.assert_called_with(
                {**payload, LearnArticle.ID: article_id}
            )
            service().update_article.assert_called_with(
                deployment_id, section_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().update_article()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateLearnSectionRequestObject")
    def test_success_update_learn_section(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_learn_section(deployment_id, section_id)
            req_obj.from_dict.assert_called_with(
                {**payload, LearnSection.ID: section_id}
            )
            service().update_learn_section.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().update_learn_section()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateDeploymentRequestObject")
    def test_success_update_deployment(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_deployment(deployment_id)
            req_obj.from_dict.assert_called_with({**payload, req_obj.ID: deployment_id})
            service().update_deployment.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: service().update_deployment()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    def test_success_retrieve_modules(self, service, jsonify):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_modules()
            service().retrieve_modules.assert_called_once()
            jsonify.assert_called_with([])

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveLatestConsentRequestObject")
    def test_success_retrieve_latest_consent(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_latest_consent(deployment_id)
            req_obj.from_dict.assert_called_with({req_obj.DEPLOYMENT_ID: deployment_id})
            service().retrieve_deployment.assert_called_with(
                req_obj.from_dict().deploymentId
            )
            jsonify.assert_called_with(
                service().retrieve_deployment().consent.to_dict()
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentByRevisionRequestObject")
    def test_success_retrieve_deployment_by_version_number(
        self, req_obj, service, jsonify
    ):
        deployment_id = SAMPLE_ID
        version_number = "1"
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_deployment_by_version_number(deployment_id, version_number)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.VERSION_NUMBER: int(version_number),
                }
            )
            service().retrieve_deployment_by_version_number.assert_called_with(
                req_obj.from_dict().deploymentId, req_obj.from_dict().versionNumber
            )
            jsonify.assert_called_with(
                service().retrieve_deployment_by_version_number().to_dict()
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentRequestObject")
    def test_success_retrieve_deployment(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_deployment(deployment_id)
            req_obj.from_dict.assert_called_with({req_obj.DEPLOYMENT_ID: deployment_id})
            service().retrieve_deployment.assert_called_with(
                req_obj.from_dict().deploymentId
            )
            jsonify.assert_called_with(service().retrieve_deployment().to_dict())

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentsRequestObject")
    def test_success_retrieve_deployments(self, req_obj, service, jsonify):
        service().retrieve_deployments.return_value = [], 0
        payload = {
            RetrieveDeploymentsRequestObject.SKIP: 1,
            RetrieveDeploymentsRequestObject.LIMIT: 5,
            RetrieveDeploymentsRequestObject.SORT: SortField.Direction.DESC.name,
            RetrieveDeploymentsRequestObject.NAME_CONTAINS: "aa",
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_deployments()
            req_obj.from_dict.assert_called_with(payload)
            service().retrieve_deployments.assert_called_with(*req_obj.from_dict())
            response = {
                "items": [],
                "total": 0,
                RetrieveDeploymentsRequestObject.LIMIT: req_obj.from_dict().limit,
                RetrieveDeploymentsRequestObject.SKIP: req_obj.from_dict().skip,
            }
            jsonify.assert_called_with(response)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateModuleConfigRequestObject")
    def test_success_update_module_config(self, req_obj, service, jsonify):
        service().create_or_update_module_config.return_value = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_module_config(deployment_id)
            req_obj.from_dict.assert_called_with({**payload})
            service().create_or_update_module_config.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": SAMPLE_ID})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateKeyActionConfigRequestObject")
    def test_success_create_key_action_config(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_key_action_config(deployment_id)
            req_obj.from_dict.assert_called_with({**payload})
            service().create_key_action.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().create_key_action()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.g", mock_g)
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateDeploymentLabelsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateLabelsRequestObject")
    def test_success_create_deployment_labels(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_deployment_labels(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.SUBMITTER_ID: mock_g.user.id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.g", mock_g)
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateDeploymentLabelUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateLabelRequestObject")
    def test_success_update_deployment_label(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        label_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_deployment_labels(deployment_id, label_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.LABEL_ID: label_id,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.SUBMITTER_ID: mock_g.user.id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentLabelsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveLabelsRequestObject")
    def test_success_retrieve_deployment_labels(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="GET", json=payload) as _:
            retrieve_deployment_labels(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteOnboardingConfigRequestObject")
    def test_success_delete_onboarding_module_config(self, req_obj, service):
        deployment_id = SAMPLE_ID
        onboarding_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_onboarding_module_config(deployment_id, onboarding_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.ONBOARDING_ID: onboarding_id,
                }
            )
            service().delete_onboarding_module_config.assert_called_with(
                req_obj.from_dict().deploymentId,
                req_obj.from_dict().onboardingId,
            )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateOnboardingConfigRequestObject")
    def test_success_update_onboarding_module_config(self, req_obj, service, jsonify):
        service().create_or_update_onboarding_module_config.return_value = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_onboarding_module_config(deployment_id)
            req_obj.from_dict.assert_called_with({**payload})
            service().create_or_update_onboarding_module_config.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": SAMPLE_ID})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateOnboardingConfigRequestObject")
    def test_success_create_onboarding_module_config(self, req_obj, service, jsonify):
        service().create_or_update_onboarding_module_config.return_value = SAMPLE_ID
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            create_onboarding_module_config(deployment_id)
            req_obj.from_dict.assert_called_with({**payload})
            service().create_or_update_onboarding_module_config.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": SAMPLE_ID})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateLearnArticleRequestObject")
    def test_success_create_article(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        article_content_dict = {
            LearnArticleContent.ID: SAMPLE_ID,
            LearnArticleContent.TEXT_DETAILS: "aa",
            LearnArticleContent.TIME_TO_READ: "aa",
            LearnArticleContent.TYPE: LearnArticleContentType.VIDEO.name,
            LearnArticleContent.URL: "aaaaa",
            LearnArticleContent.VIDEO_URL: None,
        }
        payload = {
            CreateLearnArticleRequestObject.CONTENT: article_content_dict,
            CreateLearnArticleRequestObject.TITLE: "test title",
            CreateLearnArticleRequestObject.TYPE: LearnArticleType.VIDEO.name,
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_article(deployment_id, section_id)
            req_obj.from_dict.assert_called_with(payload)
            service().create_article.assert_called_with(
                deployment_id, section_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().create_article()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateLearnSectionRequestObject")
    def test_success_create_learn_section(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_learn_section(deployment_id)
            req_obj.from_dict.assert_called_with(payload)
            service().create_learn_section.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().create_learn_section()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateConsentRequestObject")
    def test_success_create_consent(self, req_obj, service, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_consent(deployment_id)
            req_obj.from_dict.assert_called_with(payload)
            service().create_consent.assert_called_with(
                deployment_id, req_obj.from_dict()
            )
            jsonify.assert_called_with({"id": service().create_consent()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeploymentService")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateDeploymentRequestObject")
    def test_success_create_deployment(self, req_obj, service, jsonify):
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_deployment()
            req_obj.from_dict.assert_called_with(payload)
            service().create_deployment.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": service().create_deployment()})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveLocalizableFieldsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveLocalizableFieldsRequestObject")
    def test_success_retrieve_localizable_fields(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_localizable_fields(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.GenerateMasterTranslationUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.GenerateMasterTranslationRequestObject")
    def test_success_generate_master_translation(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            generate_master_translation(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.ReorderLearnArticlesUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.ReorderLearnArticles")
    def test_success_reorder_learn_articles(
        self, mock_req_obj, mock_use_case, mock_jsonify
    ):
        deployment_id = SAMPLE_ID
        section_id = SAMPLE_ID
        payload = [
            {"id": "61b08bb3d1c450434fb36a93", "order": 1},
            {"id": "61b08bc9d1c450434fb36a98", "order": 2},
        ]
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            reorder_learn_articles(deployment_id=deployment_id, section_id=section_id)
            mock_req_obj.from_dict.assert_called_with(
                {
                    mock_req_obj.DEPLOYMENT_ID: deployment_id,
                    mock_req_obj.ITEMS: payload,
                    mock_req_obj.SECTION_ID: section_id,
                }
            )
            mock_use_case().execute.assert_called_with(mock_req_obj.from_dict())
            mock_jsonify.assert_called_with(mock_use_case().execute())

    def test_failure_reorder_learn_articles(self):
        deployment_id = SAMPLE_ID
        section_id = "section_id"
        payload = [
            {"id": "61b08bb3d1c450434fb36a93", "order": 1},
            {"id": "61b08bc9d1c450434fb36a98", "order": 2},
        ]
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            with self.assertRaises(ConvertibleClassValidationError):
                reorder_learn_articles(
                    deployment_id=deployment_id, section_id=section_id
                )

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentKeyActionsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentKeyActionsRequestObject")
    def test_success_retrieve_key_actions_for_deployment(
        self, req_obj, use_case, jsonify
    ):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_deployment_key_actions(deployment_id)
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.DEPLOYMENT_ID: deployment_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"events": use_case().execute().value})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateMultipleModuleConfigsUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateMultipleModuleConfigsRequestObject")
    def test_success_create_multiple_module_configs(self, req_obj, use_case, jsonify):
        deployment_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_module_configs(deployment_id)
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.DEPLOYMENT_ID: deployment_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"ids": use_case().execute().value})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateDeploymentTemplateUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.CreateDeploymentTemplateRequestObject")
    def test_success_create_deployment_template(self, req_obj, use_case, jsonify):
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_deployment_template()
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.SUBMITTER: mock_g.authz_user}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentTemplateUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentTemplateRequestObject")
    def test_success_retrieve_deployment_template(self, req_obj, use_case, jsonify):
        with testapp.test_request_context("/", method="GET") as _:
            template_id = "61fbd9652bde4421dd34e952"
            retrieve_deployment_template(template_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.TEMPLATE_ID: template_id,
                    req_obj.ORGANIZATION_ID: None,
                    req_obj.SUBMITTER: mock_g.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentTemplatesUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.RetrieveDeploymentTemplatesRequestObject")
    def test_retrieve_deployment_templates(self, req_obj, use_case, jsonify):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_deployment_templates()
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.ORGANIZATION_ID: None,
                    req_obj.SUBMITTER: mock_g.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"templates": []})

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteDeploymentTemplateUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.DeleteDeploymentTemplateRequestObject")
    def test_success_delete_deployment_template(self, req_obj, use_case):
        with testapp.test_request_context("/", method="GET") as _:
            template_id = "61fbd9652bde4421dd34e952"
            delete_deployment_template(template_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.TEMPLATE_ID: template_id,
                    DeleteDeploymentTemplateRequestObject.ORGANIZATION_ID: None,
                    req_obj.SUBMITTER: mock_g.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateDeploymentTemplateUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.UpdateDeploymentTemplateRequestObject")
    def test_success_update_deployment_template(self, req_obj, use_case, jsonify):
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="GET", json=payload) as _:
            template_id = "61fbd9652bde4421dd34e952"
            update_deployment_template(template_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.TEMPLATE_ID: template_id,
                    req_obj.ORGANIZATION_ID: None,
                    req_obj.SUBMITTER: mock_g.authz_user,
                    req_obj.UPDATE_DATA: payload,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch.object(AuditLog, "create_log", MagicMock())
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.g", mock_g)
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.SendMessageToDeploymentPatientListUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.SendMessageToPatientListRequestObject")
    def test_success_send_message_to_users(self, req_obj, use_case, jsonify):
        user_id = USER_ID_2
        payload = {
            "userIds": [user_id],
            "allUsers": False,
            "text": "text",
            "custom": True,
        }
        jsonify.return_value = "{}"
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_message_to_patient_list()
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.SUBMITTER_ID: mock_g.user.id,
                    req_obj.SUBMITTER_NAME: mock_g.user.get_full_name(),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch.object(AuditLog, "create_log", MagicMock())
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.g", mock_g)
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.SendMessageToDeploymentPatientListUseCase")
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.SendMessageToPatientListRequestObject")
    def test_success_send_message_to_all_users(self, req_obj, use_case, jsonify):
        payload = {
            "userIds": [],
            "allUsers": True,
            "text": "text",
            "custom": True,
        }
        jsonify.return_value = "{}"
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_message_to_patient_list()
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.SUBMITTER_ID: mock_g.user.id,
                    req_obj.SUBMITTER_NAME: mock_g.user.get_full_name(),
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch.object(AuditLog, "create_log", MagicMock())
    @patch(f"{DEPLOYMENT_ROUTER_PATH}.g")
    def test_fail_send_message_to_users(self, g_mock):
        submitter_id = USER_ID_1
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.id = submitter_id
        g_mock.user_full_name = "Test User"
        payload = {
            "userIds": [],
            "allUsers": False,
            "text": "text",
            "custom": True,
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            with self.assertRaises(ConvertibleClassValidationError):
                send_message_to_patient_list()


if __name__ == "__main__":
    unittest.main()
