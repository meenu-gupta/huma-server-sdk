import copy
from unittest import TestCase
from unittest.mock import MagicMock

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User
from extensions.common.s3object import S3Object
from extensions.deployment.models.deployment import (
    Deployment,
    Features,
    OffBoardingReasons,
    Reason,
    ProfileFields,
    Profile,
)
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    LearnArticle,
    LearnSection,
    Learn,
    LearnArticleContent,
    LearnArticleContentType,
)
from extensions.deployment.models.status import EnableStatus
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.deployment.IntegrationTests.repository_tests import (
    test_deployment,
)
from extensions.tests.deployment.UnitTests.extra_custom_fields_tests import (
    extra_custom_fields_configs,
)
from extensions.tests.deployment.UnitTests.test_helpers import (
    get_sample_questionnaire_module_config,
    sample_s3_object,
    legal_docs_s3_fields,
    LICENSED_SAMPLE_KEY,
)
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.localization.utils import Language, Localization
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.inject import Binder

module_configs = [
    ModuleConfig(
        id="module1",
        moduleId="Weight",
        status=EnableStatus.ENABLED,
        about="about field",
    ),
    ModuleConfig(id="module2", moduleId="Height", status=EnableStatus.DISABLED),
    ModuleConfig(
        id="module3",
        moduleId="Questionnaire",
        status=EnableStatus.ENABLED,
        configBody={"isForManager": True},
        about="about field2",
        moduleName="Some Questionnaire",
    ),
    ModuleConfig(
        id="module4",
        moduleId="sample",
        status=EnableStatus.ENABLED,
        configBody={},
        about="about field2",
        moduleName="Sample Licensed Questionnaire Module",
    ),
]

learn = Learn(
    sections=[
        LearnSection(
            articles=[
                LearnArticle(id="articleId", title="article_title"),
                LearnArticle(id="articleId2"),
            ],
            title="some_section_title",
        )
    ]
)
key_actions = [
    KeyActionConfig(
        id="keyActionId1", type=KeyActionConfig.Type.LEARN, learnArticleId="articleId"
    ),
    KeyActionConfig(
        id="keyActionId2", type=KeyActionConfig.Type.MODULE, moduleConfigId="module1"
    ),
    KeyActionConfig(
        id="keyActionId3", type=KeyActionConfig.Type.MODULE, moduleConfigId="module2"
    ),
    KeyActionConfig(
        id="keyActionId4", type=KeyActionConfig.Type.MODULE, moduleConfigId="module3"
    ),
]


class CommonDeploymentTestCase(TestCase):
    def setUp(self) -> None:
        self.user: User = User(id="userId", carePlanGroupId="sever_group")
        self.deployment = Deployment(
            id="deploymentId",
            moduleConfigs=module_configs,
            learn=learn,
            keyActions=key_actions,
            carePlanGroup=MagicMock(),
        )

        def configure_with_binder(binder: Binder):
            binder.bind(CustomModuleConfigRepository, MagicMock())
            binder.bind(FileStorageAdapter, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)


class DeploymentTestCase(CommonDeploymentTestCase):
    def test_success_prepare_for_role_called_with_care_plan_group(self):
        self.deployment.prepare_for_role = MagicMock()
        self.deployment.apply_care_plan_by_id(self.user.carePlanGroupId, RoleName.USER)
        self.deployment.prepare_for_role.assert_called_once()

    def test_success_prepare_for_role_called_without_care_plan_group(self):
        self.deployment.prepare_for_role = MagicMock()
        self.deployment.carePlanGroup = None
        self.deployment.apply_care_plan_by_id(self.user.carePlanGroupId, RoleName.USER)
        self.deployment.prepare_for_role.assert_called_once()

    def test_success_prepare_for_role_filters_disabled_module_configs_for_user(self):
        self.deployment.prepare_for_role(RoleName.USER, self.user.id)
        self.assertEqual(2, len(self.deployment.moduleConfigs))
        self.assertEqual(2, len(self.deployment.keyActions))

    def test_success_prepare_for_role_filters_disabled_module_configs_for_manager(self):
        self.deployment.prepare_for_role(RoleName.ADMIN, self.user.id)
        self.assertEqual(3, len(self.deployment.moduleConfigs))
        self.assertEqual(3, len(self.deployment.keyActions))

    def test_deployment_url_strip(self):
        deployment_dict = test_deployment()
        url = "   http://some_url.com    "
        url_fields = [
            Deployment.EULA_URL,
            Deployment.PRIVACY_POLICY_URL,
            Deployment.CONTACT_US_URL,
            Deployment.TERM_AND_CONDITION_URL,
        ]
        for field in url_fields:
            deployment_dict[field] = "   http://some_url.com    "
        deployment = Deployment.from_dict(deployment_dict)
        deployment_dict = Deployment.to_dict(deployment)
        for field in url_fields:
            self.assertEqual(deployment_dict[field], url.strip())

    def test_deployment_with_legal_documents_s3_objects(self):
        deployment_dict = test_deployment()
        for item in legal_docs_s3_fields():
            deployment_dict[item] = sample_s3_object()
        try:
            deployment = Deployment.from_dict(deployment_dict)
        except ConvertibleClassValidationError:
            self.fail()
        else:
            self.assertIsNotNone(deployment.privacyPolicyObject)

    def test_generate_presigned_urls_for_learn_article(self):
        learn_content_dict = {
            LearnArticleContent.TYPE: LearnArticleContentType.VIDEO.name,
            LearnArticleContent.TIME_TO_READ: "20m",
            LearnArticleContent.TEXT_DETAILS: "Here what you read",
            LearnArticleContent.CONTENT_OBJECT: {
                S3Object.BUCKET: "integrationtests",
                S3Object.KEY: "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
                S3Object.REGION: "cn",
            },
        }
        learn_content = LearnArticleContent.from_dict(learn_content_dict)

        deployment_dict = test_deployment()
        deployment = Deployment.from_dict(deployment_dict)
        deployment.learn = learn

        deployment.learn.sections[0].articles[0].content = learn_content
        self.assertIsNone(learn_content.url)
        deployment.generate_presigned_urls_for_learn_article()
        self.assertIsNotNone(deployment.learn.sections[0].articles[0].content)

    def test_populate_profile_fields_ordering(self):
        deployment_dict = test_deployment()
        profile_data = {
            Deployment.PROFILE: {Profile.FIELDS: {ProfileFields.DATE_OF_BIRTH: True}}
        }
        deployment_dict.update(profile_data)

        deployment = Deployment.from_dict(deployment_dict)
        deployment.populate_profile_fields_ordering()
        orderable_fields = ProfileFields.get_orderable_fields()
        self.assertEqual(orderable_fields, deployment.profile.fields.ordering)

    def test_orderable_fields(self):
        orderable_fields = ProfileFields.get_orderable_fields()
        for f in orderable_fields:
            self.assertNotIn(f, ProfileFields._excluded_from_ordering_fields)

    def test_deployment_no_feature_field(self):
        deployment_dict = test_deployment()
        deployment: Deployment = Deployment.from_dict(deployment_dict)

        self._assert_feature_field_exist(deployment.features)
        self.assertListEqual(
            deployment.features.offBoardingReasons.reasons,
            Reason._default_reasons_obj(),
        )
        self.assertTrue(deployment.features.offBoardingReasons.otherReason)
        self.assertFalse(deployment.features.labels)

    def test_deployment_with_offboarding_reason_other_reason_set_only(self):
        deployment_dict = test_deployment()
        features_field = {
            Features.OFF_BOARDING_REASONS: {OffBoardingReasons.OTHER_REASON: False},
        }
        deployment_dict[Deployment.FEATURES] = features_field
        deployment = Deployment.from_dict(deployment_dict)

        self._assert_feature_field_exist(deployment.features)
        self.assertListEqual(
            deployment.features.offBoardingReasons.reasons,
            Reason._default_reasons_obj(),
        )
        self.assertFalse(deployment.features.offBoardingReasons.otherReason)

    def test_deployment_with_offboarding_reason_reasons_set_only(self):
        deployment_dict = test_deployment()
        features_field = {
            Features.OFF_BOARDING_REASONS: {
                OffBoardingReasons.REASONS: Reason._default_reasons()[:3]
            },
        }
        deployment_dict[Deployment.FEATURES] = features_field
        deployment = Deployment.from_dict(deployment_dict)

        self._assert_feature_field_exist(deployment.features)
        self.assertEqual(len(deployment.features.offBoardingReasons.reasons), 3)
        self.assertTrue(deployment.features.offBoardingReasons.otherReason)

    def test_deployment_with_offboarding_reason_reasons_and_other_reason(self):
        deployment_dict = test_deployment()
        features_field = {
            Features.OFF_BOARDING_REASONS: {
                OffBoardingReasons.REASONS: Reason._default_reasons()[:3],
                OffBoardingReasons.OTHER_REASON: False,
            },
        }
        deployment_dict[Deployment.FEATURES] = features_field
        deployment = Deployment.from_dict(deployment_dict)

        self._assert_feature_field_exist(deployment.features)
        self.assertEqual(len(deployment.features.offBoardingReasons.reasons), 3)
        self.assertFalse(deployment.features.offBoardingReasons.otherReason)

    def _assert_feature_field_exist(self, features: Features):
        self.assertIsNotNone(getattr(features, Features.OFF_BOARDING_REASONS))
        self.assertIn(
            OffBoardingReasons.REASONS,
            features.offBoardingReasons.to_dict(),
        )


class DeploymentMultiLanguageStateTestCase(TestCase):
    def setUp(self):
        def bind(binder):
            binder.bind(ModulesManager, ModulesManager())
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(bind)

    def test_convert_multi_language_deployment_to_multi_language_state_with_learn_and_module(
        self,
    ):
        deployment = Deployment(
            id="deploymentId",
            moduleConfigs=copy.deepcopy(module_configs[0]),
            learn=learn,
        )
        res = deployment.generate_deployment_multi_language_state()

        expected_en_localization = {
            "hu_learn_sections_0_articles_0_title": "article_title",
            "hu_learn_sections_0_title": "some_section_title",
            "hu_weight_about": "about field",
        }
        self.assertEqual(expected_en_localization, res.localizations[Language.EN])

        # verifying learn
        res_learn = res.learn.sections[0]
        self.assertEqual(res_learn.title, "hu_learn_sections_0_title")
        learn_article = res_learn.articles[0]
        self.assertEqual(learn_article.title, "hu_learn_sections_0_articles_0_title")

    def test_convert_to_multi_language_with_extra_custom_fields(self):
        deployment = Deployment.from_dict(
            {
                "id": "5f15aaea6530a4c3c6db4506",
                "extraCustomFields": extra_custom_fields_configs(),
            }
        )
        res = deployment.generate_deployment_multi_language_state()
        expected_en_localization = {
            "hu_extraCustomFields_mediclinicNumber_errorMessage": "Insurance Number is incorrect",
            "hu_extraCustomFields_mediclinicNumber_onboardingCollectionText": "Please enter mediclinic number",
            "hu_extraCustomFields_mediclinicNumber_profileCollectionText": "Patient Unique ID",
            "hu_extraCustomFields_mediclinicNumber_description": "Please enter mediclinic number description",
        }

        self.assertEqual(res.localizations[Language.EN], expected_en_localization)
        # verify that translation placeholders are set in deployment
        deployment_extra_fields = res.extraCustomFields["mediclinicNumber"]
        self.assertEqual(
            "hu_extraCustomFields_mediclinicNumber_errorMessage",
            deployment_extra_fields.errorMessage,
        )
        self.assertEqual(
            "hu_extraCustomFields_mediclinicNumber_onboardingCollectionText",
            deployment_extra_fields.onboardingCollectionText,
        )
        self.assertEqual(
            "hu_extraCustomFields_mediclinicNumber_profileCollectionText",
            deployment_extra_fields.profileCollectionText,
        )
        self.assertEqual(
            "hu_extraCustomFields_mediclinicNumber_description",
            deployment_extra_fields.description,
        )

    def test_convert_to_multi_language_with_questionnaire_pages_and_items(self):
        questionnaire = ModuleConfig(**get_sample_questionnaire_module_config())
        questionnaire.moduleName = "test"
        questionnaire.configBody["submissionPage"] = {
            "description": "Scroll up to change any of your answers. Changing answers may add new questions.",
            "id": "64fa6352-58e8-4959-94af-f3865d2caf71",
            "text": "You’ve completed the questionnaire",
            "buttonText": "Submit",
            "order": 4,
            "type": "SUBMISSION",
        }
        deployment = Deployment(id="deploymentId", moduleConfigs=[questionnaire])
        res = deployment.generate_deployment_multi_language_state()
        expected_en_localization = {
            "hu_test_pages_0_items_0_autocomplete_placeholder": "Search conditions",
            "hu_test_pages_0_items_0_placeholder": "Enter Condition",
            "hu_test_pages_0_items_0_text": "What condition do you have?",
            "hu_test_pages_1_items_0_description": "In the last 7 days how has your activity changed compared to the week before?",
            "hu_test_pages_1_items_0_text": "Overall physical activity",
            "hu_test_pages_1_items_0_options_0_label": "Decreased",
            "hu_test_submissionPage_description": "Scroll up to change any of your answers. Changing answers may add new questions.",
            "hu_test_submissionPage_text": "You’ve completed the questionnaire",
            "hu_test_submissionPage_buttonText": "Submit",
        }

        self.assertEqual(expected_en_localization, res.localizations[Language.EN])
        # verify that data in deployment has been changed to placeholders
        module_data = res.moduleConfigs[0]
        self.assertEqual(
            "hu_test",
            module_data.localizationPrefix,
        )

        expected_config_body = {
            "isForManager": False,
            "pages": [
                {
                    "type": "QUESTION",
                    "items": [
                        {
                            "format": "AUTOCOMPLETE_TEXT",
                            "autocomplete": {
                                "placeholder": "hu_test_pages_0_items_0_autocomplete_placeholder",
                                "listEndpointId": "AZVaccineBatchNumber",
                                "allowFreeText": True,
                            },
                            "order": 1,
                            "required": True,
                            "placeholder": "hu_test_pages_0_items_0_placeholder",
                            "text": "hu_test_pages_0_items_0_text",
                        }
                    ],
                    "order": 1,
                },
                {
                    "type": "QUESTION",
                    "items": [
                        {
                            "logic": {"isEnabled": False},
                            "description": "hu_test_pages_1_items_0_description",
                            "required": True,
                            "format": "TEXTCHOICE",
                            "order": 1,
                            "text": "hu_test_pages_1_items_0_text",
                            "options": [
                                {
                                    "label": "hu_test_pages_1_items_0_options_0_label",
                                    "value": "0",
                                    "weight": 0,
                                }
                            ],
                        }
                    ],
                    "order": 2,
                },
            ],
            "submissionPage": {
                "description": "hu_test_submissionPage_description",
                "id": "64fa6352-58e8-4959-94af-f3865d2caf71",
                "text": "hu_test_submissionPage_text",
                "buttonText": "hu_test_submissionPage_buttonText",
                "order": 4,
                "type": "SUBMISSION",
            },
        }
        self.assertEqual(expected_config_body, module_data.configBody)

    def test_failure_convert_to_multi_language_generated_placeholder_name_is_too_big(
        self,
    ):
        questionnaire = ModuleConfig(**get_sample_questionnaire_module_config())
        questionnaire.moduleName = "test" * 100
        questionnaire.configBody["submissionPage"] = {
            "description": "Scroll up to change any of your answers. Changing answers may add new questions.",
            "id": "64fa6352-58e8-4959-94af-f3865d2caf71",
            "text": "You’ve completed the questionnaire",
            "buttonText": "Submit",
            "order": 4,
            "type": "SUBMISSION",
        }
        deployment = Deployment(id="deploymentId", moduleConfigs=[questionnaire])
        with self.assertRaises(ConvertibleClassValidationError):
            deployment.generate_deployment_multi_language_state()

    def test_convert_to_multi_language_with_key_actions(self):
        key_action = KeyActionConfig(
            **{
                KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "P6M",
                KeyActionConfig.DURATION_ISO: "P6M",
                KeyActionConfig.TYPE: KeyActionConfig.Type.LEARN.value,
                KeyActionConfig.TRIGGER: KeyActionConfig.Trigger.SIGN_UP.value,
                KeyActionConfig.TITLE: "some name",
            }
        )
        deployment = Deployment(id="deploymentId", keyActions=[key_action])
        res = deployment.generate_deployment_multi_language_state()
        self.assertEqual(
            "hu_keyActions_0_title",
            res.keyActions[0].title,
        )

    def test_licensed_questionnaire_localization(self):
        deployment = Deployment(
            id="deploymentId", moduleConfigs=copy.deepcopy(module_configs[3])
        )

        deployment_localization = deployment.get_localization(Language.EN)
        expected_translation = "translation text for LicenseModule on en from file"
        translation = deployment_localization.get(LICENSED_SAMPLE_KEY)
        self.assertEqual(expected_translation, translation)
