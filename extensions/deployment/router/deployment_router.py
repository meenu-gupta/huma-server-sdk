from flasgger import swag_from
from flask import request, jsonify, g

from extensions.authorization.middleware import AuthorizationMiddleware
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import DeploymentAction
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import LearnSection, LearnArticle
from extensions.deployment.router.deployment_requests import (
    AddFilesToLibraryRequestObject,
    CreateDeploymentRequestObject,
    CreateConsentRequestObject,
    CreateLabelsRequestObject,
    CreateLearnSectionRequestObject,
    CreateLearnArticleRequestObject,
    DeleteLabelRequestObject,
    RetrieveFilesInLibraryRequestObject,
    RetrieveLabelsRequestObject,
    UpdateDeploymentRequestObject,
    UpdateLabelRequestObject,
    UpdateLearnSectionRequestObject,
    UpdateArticleRequestObject,
    RetrieveDeploymentsRequestObject,
    RetrieveDeploymentByRevisionRequestObject,
    DeleteModuleConfigRequestObject,
    CreateModuleConfigRequestObject,
    UpdateModuleConfigRequestObject,
    CreateKeyActionConfigRequestObject,
    DeleteKeyActionRequestObject,
    UpdateKeyActionConfigRequestObject,
    RetrieveDeploymentRequestObject,
    RetrieveLatestConsentRequestObject,
    DeleteDeploymentRequestObject,
    DeleteLearnSectionRequestObject,
    DeleteArticleRequestObject,
    EncryptValueRequestObject,
    CreateCarePlansRequestObject,
    CreateEConsentRequestObject,
    DeploymentRoleUpdateObject,
    CreateOnboardingConfigRequestObject,
    UpdateOnboardingConfigRequestObject,
    DeleteOnboardingConfigRequestObject,
    UpdateLocalizationsRequestObject,
    CloneDeploymentRequestObject,
    ReorderRequestObject,
    ReorderLearnArticles,
    RetrieveLocalizableFieldsRequestObject,
    GenerateMasterTranslationRequestObject,
    RetrieveDeploymentKeyActionsRequestObject,
    CreateMultipleModuleConfigsRequestObject,
    CreateDeploymentTemplateRequestObject,
    RetrieveDeploymentTemplateRequestObject,
    RetrieveDeploymentTemplatesRequestObject,
    UpdateDeploymentTemplateRequestObject,
    DeleteDeploymentTemplateRequestObject,
)
from extensions.deployment.router.inbox_request import (
    SendMessageToPatientListRequestObject,
)
from extensions.deployment.router.policies import (
    match_deployment_or_wildcard,
    wildcard_resource,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.use_case.clone_deployment_use_case import (
    CloneDeploymentUseCase,
)
from extensions.deployment.use_case.create_deployment_labels import (
    CreateDeploymentLabelsUseCase,
)
from extensions.deployment.use_case.create_deployment_template_use_case import (
    CreateDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.delete_deployment_label import (
    DeleteDeploymentLabelUseCase,
)
from extensions.deployment.use_case.delete_deployment_template_use_case import (
    DeleteDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.delete_learn_article_use_case import (
    DeleteLearnArticleUseCase,
)
from extensions.deployment.use_case.delete_learn_section_use_case import (
    DeleteLearnSectionUseCase,
)
from extensions.deployment.use_case.file_library_use_case import (
    AddFilesToLibraryUseCase,
    RetrieveFilesInLibraryUseCase,
)
from extensions.deployment.use_case.generate_master_translation_use_case import (
    GenerateMasterTranslationUseCase,
)
from extensions.deployment.use_case.inbox_use_case import (
    SendMessageToDeploymentPatientListUseCase,
)
from extensions.deployment.use_case.reorder_use_case import (
    ReorderOnboardingModuleConfigsUseCase,
    ReorderModuleConfigsUseCase,
    ReorderLearnArticlesUseCase,
    ReorderLearnSectionsUseCase,
)
from extensions.deployment.use_case.add_multiple_module_configs_use_case import (
    CreateMultipleModuleConfigsUseCase,
)
from extensions.deployment.use_case.retrieve_deployment_key_actions_use_case import (
    RetrieveDeploymentKeyActionsUseCase,
)
from extensions.deployment.use_case.retrieve_deployment_labels import (
    RetrieveDeploymentLabelsUseCase,
)
from extensions.deployment.use_case.retrieve_deployment_template_use_case import (
    RetrieveDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.retrieve_deployment_templates_use_case import (
    RetrieveDeploymentTemplatesUseCase,
)
from extensions.deployment.use_case.retrieve_localizable_fields_use_case import (
    RetrieveLocalizableFieldsUseCase,
)
from extensions.deployment.use_case.update_deployment_label import (
    UpdateDeploymentLabelUseCase,
)
from extensions.deployment.use_case.update_deployment_template_use_case import (
    UpdateDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.update_localizations_use_case import (
    UpdateLocalizationsUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
    get_request_json_list_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.models.message import Message

from sdk.inbox.router.log_actions import InboxAction
from sdk.inbox.utils import translate_message_text_to_placeholder
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint("deployment_route", __name__, policy=match_deployment_or_wildcard)

LEARN_URL = "/<deployment_id>/learn-section/<section_id>"
SEARCH_FIELD = "search"
REQUEST_ASC_ORDER = "asc"
REQUEST_DESC_ORDER = "desc"
SKIP = "skip"
LIMIT = "limit"
SORT_FIELD = "field"
SORT_ORDER = "direction"
SORTING = "sortBy"


@api.route("", methods=["POST"])
@api.require_policy(PolicyType.CREATE_DEPLOYMENT)
@audit(DeploymentAction.CreateDeployment)
@swag_from(f"{SWAGGER_DIR}/create_deployment.yml")
def create_deployment():
    body = get_request_json_dict_or_raise_exception(request)
    deployment = CreateDeploymentRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_deployment(deployment)

    return jsonify({"id": inserted_id}), 201


@api.route("/<deployment_id>/consent", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateConsent, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_consent.yml")
def create_consent(deployment_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: CreateConsentRequestObject = CreateConsentRequestObject.from_dict(
        body
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_consent(deployment_id, request_object)

    return jsonify({Consent.ID: inserted_id}), 201


@api.route("/<deployment_id>/learn-section", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateLearnSection, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_learn_section.yml")
def create_learn_section(deployment_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: CreateLearnSectionRequestObject = (
        CreateLearnSectionRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    new_article_id = service.create_learn_section(deployment_id, request_object)

    return jsonify({LearnSection.ID: new_article_id}), 201


@api.route("/<deployment_id>/learn-section/reorder", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateLearnSection, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/reorder_learn_sections.yml")
def reorder_learn_sections(deployment_id):
    body = get_request_json_list_or_raise_exception(request)
    req_obj: ReorderRequestObject = ReorderRequestObject.from_dict(
        {
            ReorderRequestObject.DEPLOYMENT_ID: deployment_id,
            ReorderRequestObject.ITEMS: body,
        }
    )
    res = ReorderLearnSectionsUseCase().execute(req_obj)
    return jsonify(res), 200


@api.route(f"{LEARN_URL}/article/reorder", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateArticle, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/reorder_learn_articles.yml")
def reorder_learn_articles(deployment_id, section_id):
    body = get_request_json_list_or_raise_exception(request)
    req_obj: ReorderLearnArticles = ReorderLearnArticles.from_dict(
        {
            ReorderLearnArticles.DEPLOYMENT_ID: deployment_id,
            ReorderLearnArticles.ITEMS: body,
            ReorderLearnArticles.SECTION_ID: section_id,
        }
    )
    res = ReorderLearnArticlesUseCase().execute(req_obj)
    return jsonify(res), 200


@api.route("/<deployment_id>/module-config/reorder", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/reorder_module_configs.yml")
def reorder_module_configs(deployment_id):
    body = get_request_json_list_or_raise_exception(request)
    req_obj: ReorderRequestObject = ReorderRequestObject.from_dict(
        {
            ReorderRequestObject.DEPLOYMENT_ID: deployment_id,
            ReorderRequestObject.ITEMS: body,
        }
    )
    res = ReorderModuleConfigsUseCase().execute(req_obj)
    return jsonify(res), 200


@api.route("/<deployment_id>/onboarding-module-config/reorder", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/reorder_onboarding_module_configs.yml")
def reorder_onboarding_module_configs(deployment_id):
    body = get_request_json_list_or_raise_exception(request)
    req_obj: ReorderRequestObject = ReorderRequestObject.from_dict(
        {
            ReorderRequestObject.DEPLOYMENT_ID: deployment_id,
            ReorderRequestObject.ITEMS: body,
        }
    )
    res = ReorderOnboardingModuleConfigsUseCase().execute(req_obj)
    return jsonify(res), 200


@api.route(f"{LEARN_URL}/article", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateArticle, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_learn_article.yml")
def create_article(deployment_id, section_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: CreateLearnArticleRequestObject = (
        CreateLearnArticleRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    new_article_id = service.create_article(deployment_id, section_id, request_object)

    return jsonify({"id": new_article_id}), 201


@api.route("/<deployment_id>/module-config", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_module_config.yml")
def create_module_config(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: CreateModuleConfigRequestObject = (
        CreateModuleConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_module_config(deployment_id, req_object)

    return jsonify({"id": inserted_id}), 201


@api.route("/<deployment_id>/onboarding-module-config", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateOnboardingModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_onboarding_module_config.yml")
def create_onboarding_module_config(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: CreateOnboardingConfigRequestObject = (
        CreateOnboardingConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_or_update_onboarding_module_config(
        deployment_id, req_object
    )

    return jsonify({"id": inserted_id}), 201


@api.route("/<deployment_id>/onboarding-module-config", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateOnboardingModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_onboarding_module_config.yml")
def update_onboarding_module_config(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: UpdateOnboardingConfigRequestObject = (
        UpdateOnboardingConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_or_update_onboarding_module_config(
        deployment_id, req_object
    )

    return jsonify({"id": inserted_id}), 200


@api.route(
    "/<deployment_id>/onboarding-module-config/<onboarding_id>", methods=["DELETE"]
)
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteOnboardingModuleConfig, target_key="onboarding_id")
@swag_from(f"{SWAGGER_DIR}/delete_onboarding_module_config.yml")
def delete_onboarding_module_config(deployment_id: str, onboarding_id: str):
    request_object: DeleteOnboardingConfigRequestObject = (
        DeleteOnboardingConfigRequestObject.from_dict(
            {
                DeleteOnboardingConfigRequestObject.DEPLOYMENT_ID: deployment_id,
                DeleteOnboardingConfigRequestObject.ONBOARDING_ID: onboarding_id,
            }
        )
    )
    service = DeploymentService(submitter_id=g.user.id)
    service.delete_onboarding_module_config(
        request_object.deploymentId, request_object.onboardingId
    )
    return "", 204


@api.route("/<deployment_id>/key-action", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateKeyActionConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_key_action_config.yml")
def create_key_action_config(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: CreateKeyActionConfigRequestObject = (
        CreateKeyActionConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_key_action(deployment_id, req_object)

    return jsonify({"id": inserted_id}), 201


@api.route("/<deployment_id>/labels", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment_labels.yml")
def retrieve_deployment_labels(deployment_id: str):
    request_object = RetrieveLabelsRequestObject.from_dict(
        {RetrieveLabelsRequestObject.DEPLOYMENT_ID: deployment_id}
    )
    use_case = RetrieveDeploymentLabelsUseCase()
    response = use_case.execute(request_object)
    return jsonify(response.value), 200


@api.route("/<deployment_id>/labels", methods=["POST"])
@api.require_policy(PolicyType.CREATE_PATIENT_LABELS, override=True)
@audit(DeploymentAction.CreateLabel, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_deployment_labels.yml")
def create_deployment_labels(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: CreateLabelsRequestObject = CreateLabelsRequestObject.from_dict(
        {
            **body,
            CreateLabelsRequestObject.DEPLOYMENT_ID: deployment_id,
            CreateLabelsRequestObject.SUBMITTER_ID: g.user.id,
        }
    )
    use_case = CreateDeploymentLabelsUseCase()
    response = use_case.execute(request_object)
    return jsonify(response.value), 201


@api.route("/<deployment_id>/labels/<label_id>", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_PATIENT_LABELS, override=True)
@audit(DeploymentAction.UpdateLabel, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_deployment_label.yml")  # come back here
def update_deployment_labels(deployment_id: str, label_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: UpdateLabelRequestObject = UpdateLabelRequestObject.from_dict(
        {
            **body,
            UpdateLabelRequestObject.LABEL_ID: label_id,
            UpdateLabelRequestObject.DEPLOYMENT_ID: deployment_id,
            UpdateLabelRequestObject.SUBMITTER_ID: g.user.id,
        }
    )
    use_case = UpdateDeploymentLabelUseCase()
    response = use_case.execute(request_object)
    return jsonify(response.value), 200


@api.route("/<deployment_id>/labels/<label_id>", methods=["DELETE"])
@api.require_policy(PolicyType.DELETE_PATIENT_LABELS, override=True)
@audit(DeploymentAction.DeleteLabel, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/delete_deployment_label.yml")
def delete_deployment_label(deployment_id: str, label_id):

    body = {
        DeleteLabelRequestObject.LABEL_ID: label_id,
        DeleteLabelRequestObject.DEPLOYMENT_ID: deployment_id,
    }
    request_object: DeleteLabelRequestObject = DeleteLabelRequestObject.from_dict(body)
    use_case = DeleteDeploymentLabelUseCase()
    use_case.execute(request_object)
    return "", 204


@api.route("/<deployment_id>/module-config", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_module_config.yml")
def update_module_config(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: UpdateModuleConfigRequestObject = (
        UpdateModuleConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_or_update_module_config(deployment_id, req_object)

    return jsonify({"id": inserted_id}), 200


@api.route("/search", methods=["POST"])
@api.require_policy([PolicyType.VIEW_DEPLOYMENT, wildcard_resource])
@swag_from(f"{SWAGGER_DIR}/retrieve_deployments.yml")
def retrieve_deployments():
    body = get_request_json_dict_or_raise_exception(request)
    req_obj: RetrieveDeploymentsRequestObject = (
        RetrieveDeploymentsRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    deployments_list, total = service.retrieve_deployments(*req_obj)
    items = [d.to_dict(include_none=False) for d in deployments_list]
    response = {
        "items": items,
        "total": total,
        "limit": req_obj.limit,
        "skip": req_obj.skip,
    }
    return jsonify(remove_none_values(response)), 200


@api.route("/<deployment_id>", methods=["GET"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment.yml")
def retrieve_deployment(deployment_id: str):
    body = {RetrieveDeploymentRequestObject.DEPLOYMENT_ID: deployment_id}
    request_object = RetrieveDeploymentRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    deployment = service.retrieve_deployment(request_object.deploymentId)
    return jsonify(deployment.to_dict(include_none=False)), 200


@api.route("/<deployment_id>/version/<version_number>", methods=["GET"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment_by_version_number.yml")
def retrieve_deployment_by_version_number(deployment_id: str, version_number: str):
    body = {
        RetrieveDeploymentByRevisionRequestObject.DEPLOYMENT_ID: deployment_id,
        RetrieveDeploymentByRevisionRequestObject.VERSION_NUMBER: int(version_number),
    }
    request_object = RetrieveDeploymentByRevisionRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    deployment = service.retrieve_deployment_by_version_number(
        request_object.deploymentId, request_object.versionNumber
    )
    return jsonify(deployment.to_dict(include_none=False)), 200


@api.route("/<deployment_id>/consent", methods=["GET"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/retrieve_consent.yml")
def retrieve_latest_consent(deployment_id: str):
    body = {RetrieveLatestConsentRequestObject.DEPLOYMENT_ID: deployment_id}
    request_object = RetrieveLatestConsentRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    consent = service.retrieve_deployment(request_object.deploymentId).consent
    if consent:
        response = consent.to_dict(include_none=False, ignored_fields=(Consent.ID,))
    else:
        response = {}
    return jsonify(response), 200


@api.route("/modules", methods=["GET"])
@api.require_policy(PolicyType.VIEW_OWN_DEPLOYMENT, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_modules.yml")
def retrieve_modules():
    service = DeploymentService(submitter_id=g.user.id)
    modules = [m.to_dict() for m in service.retrieve_modules()]
    return jsonify(modules), 200


@api.route("/<deployment_id>", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateDeployment, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_deployment.yml")
def update_deployment(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({UpdateDeploymentRequestObject.ID: deployment_id})
    request_object = UpdateDeploymentRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    deployment_id = service.update_deployment(request_object)
    return jsonify({UpdateDeploymentRequestObject.ID: deployment_id}), 200


@api.route(LEARN_URL, methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateLearnSection, target_key="section_id")
@swag_from(f"{SWAGGER_DIR}/update_learn_section.yml")
def update_learn_section(deployment_id, section_id):
    request_json = get_request_json_dict_or_raise_exception(request)
    request_json[LearnSection.ID] = section_id

    request_object = UpdateLearnSectionRequestObject.from_dict(request_json)
    service = DeploymentService(submitter_id=g.user.id)
    updated_section_id = service.update_learn_section(deployment_id, request_object)
    return jsonify({"id": updated_section_id}), 200


@api.route(f"{LEARN_URL}/article/<article_id>", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateArticle, target_key="article_id")
@swag_from(f"{SWAGGER_DIR}/update_learn_article.yml")
def update_article(deployment_id, section_id, article_id):
    request_json = get_request_json_dict_or_raise_exception(request)
    request_json[LearnArticle.ID] = article_id

    request_object = UpdateArticleRequestObject.from_dict(request_json)
    service = DeploymentService(submitter_id=g.user.id)
    upd_article_id = service.update_article(deployment_id, section_id, request_object)
    return jsonify({"id": upd_article_id}), 200


@api.route("/<deployment_id>/key-action/<key_action_id>", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.UpdateKeyActionConfig, target_key="key_action_id")
@swag_from(f"{SWAGGER_DIR}/update_key_action_config.yml")
def update_key_action_config(deployment_id: str, key_action_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({KeyActionConfig.ID: key_action_id})

    request_object: UpdateKeyActionConfigRequestObject = (
        UpdateKeyActionConfigRequestObject.from_dict(body)
    )
    service = DeploymentService(submitter_id=g.user.id)
    updated_id = service.update_key_action(deployment_id, request_object)
    return jsonify({"id": updated_id}), 200


@api.route("/<deployment_id>", methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteDeployment, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/delete_deployment.yml")
def delete_deployment(deployment_id):
    request_object = DeleteDeploymentRequestObject.from_dict(
        {DeleteDeploymentRequestObject.DEPLOYMENT_ID: deployment_id}
    )

    service = DeploymentService(submitter_id=g.user.id)
    service.delete_deployment(request_object.deploymentId)
    return "", 204


@api.route("/<deployment_id>/module-config/<module_config_id>", methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteModuleConfig, target_key="module_config_id")
@swag_from(f"{SWAGGER_DIR}/delete_module_config.yml")
def delete_module_config(deployment_id: str, module_config_id: str):
    request_object: DeleteModuleConfigRequestObject = (
        DeleteModuleConfigRequestObject.from_dict(
            {
                DeleteModuleConfigRequestObject.DEPLOYMENT_ID: deployment_id,
                DeleteModuleConfigRequestObject.MODULE_CONFIG_ID: module_config_id,
            }
        )
    )
    service = DeploymentService(submitter_id=g.user.id)
    service.delete_module_config(
        request_object.deploymentId, request_object.moduleConfigId
    )
    return "", 204


@api.route(LEARN_URL, methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteLearnSection, target_key="section_id")
@swag_from(f"{SWAGGER_DIR}/delete_learn_section.yml")
def delete_learn_section(deployment_id, section_id):
    request_object: DeleteLearnSectionRequestObject = (
        DeleteLearnSectionRequestObject.from_dict(
            {
                DeleteLearnSectionRequestObject.DEPLOYMENT_ID: deployment_id,
                DeleteLearnSectionRequestObject.SECTION_ID: section_id,
                DeleteLearnSectionRequestObject.USER_ID: g.user.id,
            }
        )
    )

    DeleteLearnSectionUseCase().execute(request_object)
    return "", 204


@api.route(f"{LEARN_URL}/article/<article_id>", methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteArticle, target_key="article_id")
@swag_from(f"{SWAGGER_DIR}/delete_learn_article.yml")
def delete_article(deployment_id, section_id, article_id):
    request_object: DeleteArticleRequestObject = DeleteArticleRequestObject.from_dict(
        {
            DeleteArticleRequestObject.DEPLOYMENT_ID: deployment_id,
            DeleteArticleRequestObject.SECTION_ID: section_id,
            DeleteArticleRequestObject.ARTICLE_ID: article_id,
            DeleteArticleRequestObject.USER_ID: g.user.id,
        }
    )

    DeleteLearnArticleUseCase().execute(request_object)
    return "", 204


@api.route("/<deployment_id>/key-action/<key_action_id>", methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.DeleteKeyActionConfig, target_key="key_action_id")
@swag_from(f"{SWAGGER_DIR}/delete_key_action_config.yml")
def delete_key_action_config(deployment_id: str, key_action_id: str):
    req_object: DeleteKeyActionRequestObject = DeleteKeyActionRequestObject.from_dict(
        {
            DeleteKeyActionRequestObject.DEPLOYMENT_ID: deployment_id,
            DeleteKeyActionRequestObject.KEY_ACTION_CONFIG_ID: key_action_id,
        }
    )
    service = DeploymentService(submitter_id=g.user.id)
    service.delete_key_action(req_object.deploymentId, req_object.keyActionConfigId)
    return "", 204


@api.route("/<deployment_id>/encrypt", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/encrypt_value.yml")
def encrypt_value(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object: EncryptValueRequestObject = EncryptValueRequestObject.from_dict(
        {EncryptValueRequestObject.DEPLOYMENT_ID: deployment_id, **body}
    )
    service = DeploymentService(submitter_id=g.user.id)
    encrypted_value = service.encrypt_value(req_object.deploymentId, req_object.value)
    return jsonify({"encryptedValue": encrypted_value}), 200


@api.route("/<deployment_id>/care-plan-group", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateCarePlanGroup, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_care_plan_group.yml")
def create_care_plan_group(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_object = CreateCarePlansRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    service.create_care_plan_group(deployment_id, req_object)
    return "Successfully Created", 201


@api.route("/<deployment_id>/econsent", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateEConsent, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/create_econsent.yml")
def create_econsent(deployment_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object = CreateEConsentRequestObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    inserted_id = service.create_econsent(deployment_id, request_object)

    return jsonify({EConsent.ID: inserted_id}), 201


@api.route("/<deployment_id>/econsent", methods=["GET"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/retrieve_econsent.yml")
def retrieve_latest_econsent(deployment_id: str):
    service = DeploymentService(submitter_id=g.user.id)
    econsent = service.retrieve_deployment(deployment_id).econsent
    if econsent:
        response = econsent.to_dict(include_none=False, ignored_fields=(EConsent.ID,))
    else:
        response = {}
    return jsonify(response), 200


@api.route("/<deployment_id>/role", methods=["PUT"])
@api.require_policy(PolicyType.EDIT_CUSTOM_ROLES)
@audit(DeploymentAction.CreateOrUpdateRoles, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_role.yml")
def create_or_update_roles(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({DeploymentRoleUpdateObject.DEPLOYMENT_ID: deployment_id})
    req_object: DeploymentRoleUpdateObject = DeploymentRoleUpdateObject.from_dict(body)
    service = DeploymentService(submitter_id=g.user.id)
    updated_id = service.create_or_update_roles(
        deployment_id=req_object.deploymentId,
        roles=req_object.roles,
    )
    return jsonify({"id": updated_id}), 200


@api.route("/<deployment_id>/update-localizations", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateLocalization, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/update_localizations.yml")
def create_localization(deployment_id):
    body = get_request_json_dict_or_raise_exception(request)

    request_object = UpdateLocalizationsRequestObject.from_dict(
        {
            UpdateLocalizationsRequestObject.DEPLOYMENT_ID: deployment_id,
            UpdateLocalizationsRequestObject.LOCALIZATIONS: body,
        }
    )

    rsp = UpdateLocalizationsUseCase().execute(request_object)

    return jsonify({"id": rsp.value}), 201


@api.route("clone", methods=["POST"])
@api.require_policy(PolicyType.CREATE_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/clone_deployment.yml")
def clone_deployment():
    body = get_request_json_dict_or_raise_exception(request)
    request_obj = CloneDeploymentRequestObject.from_dict(body)
    response = CloneDeploymentUseCase().execute(request_obj)
    return jsonify({"id": response.value}), 201


@api.route("/<deployment_id>/localizable-fields", methods=["GET"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT)
@swag_from(f"{SWAGGER_DIR}/retrieve_localizable_fields.yml")
def retrieve_localizable_fields(deployment_id):
    body = {RetrieveLocalizableFieldsRequestObject.DEPLOYMENT_ID: deployment_id}
    request_object = RetrieveLocalizableFieldsRequestObject.from_dict(body)
    rsp = RetrieveLocalizableFieldsUseCase().execute(request_object)
    return jsonify(rsp.value), 200


@api.route("/<deployment_id>/generate-master-translation", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.GenerateMasterTranslation, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/generate_master_translation.yml")
def generate_master_translation(deployment_id):
    body = {GenerateMasterTranslationRequestObject.DEPLOYMENT_ID: deployment_id}
    request_object = GenerateMasterTranslationRequestObject.from_dict(body)
    rsp = GenerateMasterTranslationUseCase().execute(request_object)
    return jsonify(rsp.value), 200


@api.route("/<deployment_id>/key-actions", methods=["POST"])
@api.require_policy(PolicyType.VIEW_DEPLOYMENT_KEY_ACTIONS)
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment_key_actions.yml")
def retrieve_deployment_key_actions(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_obj = RetrieveDeploymentKeyActionsRequestObject.from_dict(
        {**body, RetrieveDeploymentKeyActionsRequestObject.DEPLOYMENT_ID: deployment_id}
    )
    response = RetrieveDeploymentKeyActionsUseCase().execute(req_obj)
    return jsonify({"events": response.value}), 200


@api.route("/<deployment_id>/module-configs", methods=["POST"])
@api.require_policy(PolicyType.EDIT_DEPLOYMENT)
@audit(DeploymentAction.CreateModuleConfig, target_key="deployment_id")
@swag_from(f"{SWAGGER_DIR}/add_multiple_module_configs.yml")
def create_module_configs(deployment_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_obj = CreateMultipleModuleConfigsRequestObject.from_dict(
        {
            **body,
            CreateMultipleModuleConfigsRequestObject.DEPLOYMENT_ID: deployment_id,
        }
    )
    response = CreateMultipleModuleConfigsUseCase().execute(req_obj)
    return jsonify({"ids": response.value}), 200


@api.route("/template", methods=["POST"])
@api.require_policy(PolicyType.CREATE_DEPLOYMENT_TEMPLATE, override=True)
@audit(DeploymentAction.CreateDeploymentTemplate)
@swag_from(f"{SWAGGER_DIR}/create_deployment_template.yml")
def create_deployment_template():
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CreateDeploymentTemplateRequestObject.SUBMITTER: g.authz_user})
    req_obj = CreateDeploymentTemplateRequestObject.from_dict(body)
    response = CreateDeploymentTemplateUseCase().execute(req_obj)
    return jsonify({"id": response.value}), 201


@api.route("/templates", methods=["GET"])
@api.require_policy(PolicyType.RETRIEVE_DEPLOYMENT_TEMPLATE, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment_templates.yml")
def retrieve_deployment_templates():
    req_obj = RetrieveDeploymentTemplatesRequestObject.from_dict(
        {
            RetrieveDeploymentTemplatesRequestObject.SUBMITTER: g.authz_user,
            RetrieveDeploymentTemplatesRequestObject.ORGANIZATION_ID: request.headers.get(
                AuthorizationMiddleware.ORGANIZATION_HEADER_KEY
            ),
        }
    )
    response = RetrieveDeploymentTemplatesUseCase().execute(req_obj)
    templates = [d.to_dict(include_none=False) for d in response.value]
    return jsonify({"templates": templates}), 200


@api.route("/template/<template_id>", methods=["GET"])
@api.require_policy(PolicyType.RETRIEVE_DEPLOYMENT_TEMPLATE, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_deployment_template.yml")
def retrieve_deployment_template(template_id: str):
    req_obj = RetrieveDeploymentTemplateRequestObject.from_dict(
        {
            RetrieveDeploymentTemplateRequestObject.TEMPLATE_ID: template_id,
            RetrieveDeploymentTemplateRequestObject.ORGANIZATION_ID: request.headers.get(
                AuthorizationMiddleware.ORGANIZATION_HEADER_KEY
            ),
            RetrieveDeploymentTemplateRequestObject.SUBMITTER: g.authz_user,
        }
    )
    response = RetrieveDeploymentTemplateUseCase().execute(req_obj)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/template/<template_id>", methods=["DELETE"])
@api.require_policy(PolicyType.DELETE_DEPLOYMENT_TEMPLATE, override=True)
@audit(DeploymentAction.DeleteDeploymentTemplate)
@swag_from(f"{SWAGGER_DIR}/delete_deployment_template.yml")
def delete_deployment_template(template_id: str):
    req_obj = DeleteDeploymentTemplateRequestObject.from_dict(
        {
            DeleteDeploymentTemplateRequestObject.TEMPLATE_ID: template_id,
            RetrieveDeploymentTemplateRequestObject.ORGANIZATION_ID: request.headers.get(
                AuthorizationMiddleware.ORGANIZATION_HEADER_KEY
            ),
            DeleteDeploymentTemplateRequestObject.SUBMITTER: g.authz_user,
        }
    )
    DeleteDeploymentTemplateUseCase().execute(req_obj)
    return "", 204


@api.route("/template/<template_id>", methods=["PUT"])
@api.require_policy(PolicyType.UPDATE_DEPLOYMENT_TEMPLATE, override=True)
@audit(DeploymentAction.UpdateDeploymentTemplate)
@swag_from(f"{SWAGGER_DIR}/update_deployment_template.yml")
def update_deployment_template(template_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    req_obj = UpdateDeploymentTemplateRequestObject.from_dict(
        {
            UpdateDeploymentTemplateRequestObject.TEMPLATE_ID: template_id,
            UpdateDeploymentTemplateRequestObject.ORGANIZATION_ID: request.headers.get(
                AuthorizationMiddleware.ORGANIZATION_HEADER_KEY
            ),
            UpdateDeploymentTemplateRequestObject.SUBMITTER: g.authz_user,
            UpdateDeploymentTemplateRequestObject.UPDATE_DATA: body,
        }
    )
    updated_id = UpdateDeploymentTemplateUseCase().execute(req_obj).value
    return jsonify({"id": updated_id}), 200


@api.route("/user/message/send", methods=["POST"])
@api.require_policy(PolicyType.SEND_PATIENT_MESSAGE, override=True)
@audit(InboxAction.SendMessageToUserList)
@swag_from(f"{SWAGGER_DIR}/send_message_to_users_swag.yml")
def send_message_to_patient_list():
    body = get_request_json_dict_or_raise_exception(request)

    if not body.get(Message.CUSTOM) and hasattr(g, "authz_user"):
        body[Message.TEXT] = translate_message_text_to_placeholder(
            body[Message.TEXT], g.authz_user.localization
        )

    request_object = SendMessageToPatientListRequestObject.from_dict(
        {
            **body,
            SendMessageToPatientListRequestObject.SUBMITTER_ID: g.user.id,
            SendMessageToPatientListRequestObject.SUBMITTER_NAME: g.user.get_full_name(),
        }
    )

    response_object = SendMessageToDeploymentPatientListUseCase().execute(
        request_object
    )
    return jsonify(response_object.value), 201


@api.post("/file-library")
@api.require_policy([], override=True)
@swag_from(f"{SWAGGER_DIR}/add_files_to_library.yml")
def add_files_to_library():
    body = get_request_json_dict_or_raise_exception(request)

    req_obj: AddFilesToLibraryRequestObject = AddFilesToLibraryRequestObject.from_dict(
        {**body, AddFilesToLibraryRequestObject.USER_ID: g.user.id}
    )
    req_obj.check_permission()
    AddFilesToLibraryUseCase().execute(req_obj)
    return "", 200


@api.get("/file-library/<library_id>")
@api.require_policy([], override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_files_in_library.yml")
def retrieve_file_libraries(library_id):
    args = request.args or {}
    offset = int(args.get(RetrieveFilesInLibraryRequestObject.OFFSET, 0))
    limit = int(args.get(RetrieveFilesInLibraryRequestObject.LIMIT, 100))
    data = {
        RetrieveFilesInLibraryRequestObject.LIBRARY_ID: library_id,
        RetrieveFilesInLibraryRequestObject.OFFSET: offset,
        RetrieveFilesInLibraryRequestObject.LIMIT: limit,
        RetrieveFilesInLibraryRequestObject.USER_ID: g.user.id,
    }
    deployment_id = args.get("deployment_id")
    if deployment_id:
        data[RetrieveFilesInLibraryRequestObject.DEPLOYMENT_ID] = deployment_id
    req_obj: RetrieveFilesInLibraryRequestObject = (
        RetrieveFilesInLibraryRequestObject.from_dict(data)
    )
    req_obj.check_permission()

    response = RetrieveFilesInLibraryUseCase().execute(req_obj)
    return jsonify(remove_none_values(response)), 200
