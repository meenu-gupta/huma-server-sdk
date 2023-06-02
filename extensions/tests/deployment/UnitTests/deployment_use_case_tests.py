import unittest
from unittest.mock import MagicMock

from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.use_case.create_deployment_template_use_case import (
    CreateDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.delete_deployment_template_use_case import (
    DeleteDeploymentTemplateUseCase,
)
from extensions.deployment.use_case.generate_master_translation_use_case import (
    GenerateMasterTranslationUseCase,
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
from extensions.deployment.use_case.update_deployment_template_use_case import (
    UpdateDeploymentTemplateUseCase,
)
from sdk.common.utils import inject


class RetrieveLocalizableFieldsUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, self._deployment_repo)

        inject.clear_and_configure(bind)

    def test_success_retrieve_localizable_keys_process_request(self):
        req_obj = MagicMock()
        RetrieveLocalizableFieldsUseCase().process_request(request_object=req_obj)
        self._deployment_repo().retrieve_deployment.assert_called_with(
            deployment_id=req_obj.deploymentId
        )
        self._deployment_repo().retrieve_deployment().get_localized_path.assert_called_with(
            path="deployment"
        )

    def test_generate_extra_custom_fields_paths(self):
        extra_custom_fields = {"first_field": {"key": "item"}}
        expected_res = [
            "deployment.extraCustomFields.first_field.errorMessage",
            "deployment.extraCustomFields.first_field.onboardingCollectionText",
            "deployment.extraCustomFields.first_field.profileCollectionText",
        ]
        res = RetrieveLocalizableFieldsUseCase._generate_extra_custom_fields_paths(
            extra_custom_fields
        )
        for item in expected_res:
            self.assertIn(item, res)

    def test_generate_modules_config_body_paths(self):
        expected_res = [
            "deployment.moduleConfigs.configBody.name",
            "deployment.moduleConfigs.configBody.trademarkText",
            "deployment.moduleConfigs.configBody.submissionPage.text",
            "deployment.moduleConfigs.configBody.submissionPage.buttonText",
            "deployment.moduleConfigs.configBody.pages.text",
            "deployment.moduleConfigs.configBody.pages.description",
            "deployment.moduleConfigs.configBody.pages.items.text",
            "deployment.moduleConfigs.configBody.pages.items.shortText",
            "deployment.moduleConfigs.configBody.pages.items.placeholder",
            "deployment.moduleConfigs.configBody.pages.items.lowerBoundLabel",
            "deployment.moduleConfigs.configBody.pages.items.upperBoundLabel",
            "deployment.moduleConfigs.configBody.pages.items.options.label",
            "deployment.moduleConfigs.configBody.pages.items.autocomplete.placeholder",
            "deployment.moduleConfigs.configBody.pages.items.autocomplete.options.value",
            "deployment.moduleConfigs.configBody.pages.items.autocomplete.validation.errorMessage",
            "deployment.moduleConfigs.configBody.pages.items.fields.placeholder",
            "deployment.moduleConfigs.configBody.pages.items.fields.validation.errorMessage",
        ]
        res = RetrieveLocalizableFieldsUseCase._generate_modules_config_body_paths()
        for item in expected_res:
            self.assertIn(item, res)


class GenerateMasterTranslationUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, self._deployment_repo)
            binder.bind_to_provider(ConsentRepository, MagicMock())
            binder.bind_to_provider(EConsentRepository, MagicMock())

        inject.clear_and_configure(bind)

    def test_success_process_request(self):
        self._deployment_repo.retrieve_deployment.return_value = MagicMock()
        req_obj = MagicMock()
        GenerateMasterTranslationUseCase().process_request(request_object=req_obj)
        self._deployment_repo().retrieve_deployment.assert_called_with(
            deployment_id=req_obj.deploymentId
        )
        self._deployment_repo().retrieve_deployment().generate_deployment_multi_language_state.assert_called_once()
        self._deployment_repo().update_full_deployment.assert_called_once_with(
            deployment=self._deployment_repo()
            .retrieve_deployment()
            .generate_deployment_multi_language_state()
        )


class DeploymentTemplateBaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, self._deployment_repo)

        inject.clear_and_configure(bind)


class CreateDeploymentTemplateUseCaseTestCase(DeploymentTemplateBaseTestCase):
    def test_success_process_request(self):
        req_obj = MagicMock()
        CreateDeploymentTemplateUseCase().execute(req_obj)
        self._deployment_repo().create_deployment_template.assert_called_with(req_obj)


class RetrieveDeploymentTemplatesUseCaseTestCase(DeploymentTemplateBaseTestCase):
    def test_success_process_request(self):
        req_obj = MagicMock()
        RetrieveDeploymentTemplatesUseCase().execute(req_obj)
        self._deployment_repo().retrieve_deployment_templates.assert_called_with(
            req_obj.organizationId
        )


class RetrieveDeploymentTemplateUseCaseTestCase(DeploymentTemplateBaseTestCase):
    def test_success_process_request(self):
        req_obj = MagicMock()
        RetrieveDeploymentTemplateUseCase().execute(req_obj)
        self._deployment_repo().retrieve_deployment_template.assert_called_with(
            req_obj.templateId
        )


class DeleteDeploymentTemplateUseCaseTestCase(DeploymentTemplateBaseTestCase):
    def test_success_process_request(self):
        req_obj = MagicMock()
        DeleteDeploymentTemplateUseCase().execute(req_obj)
        self._deployment_repo().delete_deployment_template.assert_called_with(
            req_obj.templateId
        )


class UpdateDeploymentTemplateUseCaseTestCase(DeploymentTemplateBaseTestCase):
    def test_success_process_request(self):
        req_obj = MagicMock()
        UpdateDeploymentTemplateUseCase().execute(req_obj)
        self._deployment_repo().update_deployment_template.assert_called_with(
            req_obj.templateId, req_obj.updateData
        )


if __name__ == "__main__":
    unittest.main()
