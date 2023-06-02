from unittest import TestCase

from extensions.deployment.router.deployment_requests import (
    CreateModuleConfigRequestObject,
)
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.deployment.UnitTests.test_helpers import (
    get_sample_questionnaire_module_config,
)
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError


class CreateQuestionnaireModuleConfigRequestObjectTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manager = ModulesManager()
        manager.add_module(QuestionnaireModule())

        def bind(binder):
            binder.bind(ModulesManager, manager)

        inject.clear_and_configure(bind)

    def test_success_create_questionnaire_module_config_with_invalid_autocomplete_item(
        self,
    ):
        request_dict = get_sample_questionnaire_module_config()
        CreateModuleConfigRequestObject.from_dict(request_dict)

    def test_failure_create_questionnaire_module_config_with_invalid_format(self):
        request_dict = get_sample_questionnaire_module_config()
        request_dict["configBody"]["pages"][1]["items"][0]["format"] = "Invalid Format"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateModuleConfigRequestObject.from_dict(request_dict)

    def test_failure_create_questionnaire_module_config_with_missing_required_field(
        self,
    ):
        request_dict = get_sample_questionnaire_module_config()
        request_dict["configBody"]["pages"][1]["items"][0].pop("format", None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateModuleConfigRequestObject.from_dict(request_dict)
