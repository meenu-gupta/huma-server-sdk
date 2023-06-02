import unittest
from dataclasses import fields
from unittest.mock import MagicMock, patch

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.deployment.models.deployment import (
    Features,
    OffBoardingReasons,
    Reason,
    TemplateCategory,
    Deployment,
    Profile,
    ProfileFields,
    DeploymentTemplate,
)
from extensions.deployment.models.learn import OrderUpdateObject
from extensions.deployment.models.status import Status
from extensions.deployment.router.deployment_requests import (
    CreateDeploymentRequestObject,
    ReorderLearnArticles,
    ReorderRequestObject,
    RetrieveDeploymentKeyActionsRequestObject,
    CreateMultipleModuleConfigsRequestObject,
    CreateDeploymentTemplateRequestObject,
    RetrieveDeploymentTemplateRequestObject,
    RetrieveDeploymentTemplatesRequestObject,
    DeleteDeploymentTemplateRequestObject,
    UpdateDeploymentTemplateRequestObject,
)
from extensions.tests.deployment.IntegrationTests.repository_tests import (
    test_deployment,
)
from extensions.tests.deployment.UnitTests.test_helpers import get_sample_module_config
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_VALID_OBJ_ID_1 = "60a20766c85cd55b38c99e12"
SAMPLE_VALID_OBJ_ID_2 = "60a20766c85cd55b38c99e13"

MODULE_CONFIG_PATH = "extensions.module_result.models.module_config.ModuleConfig"


class ReorderRequestTestCase(unittest.TestCase):
    def test_success_reorder_learn_articles(self):
        try:
            ReorderLearnArticles.from_dict(
                {
                    ReorderRequestObject.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID_1,
                    ReorderLearnArticles.SECTION_ID: SAMPLE_VALID_OBJ_ID_2,
                    ReorderRequestObject.ITEMS: [
                        {
                            OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID_1,
                            OrderUpdateObject.ORDER: 1,
                        },
                        {
                            OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID_2,
                            OrderUpdateObject.ORDER: 2,
                        },
                    ],
                }
            )
        except ConvertibleClassValidationError as e:
            self.fail(e)

    def test_failure_reorder_learn_articles_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ReorderLearnArticles.from_dict(
                {
                    ReorderRequestObject.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID_1,
                    ReorderLearnArticles.SECTION_ID: SAMPLE_VALID_OBJ_ID_2,
                }
            )

    def test_failure_reorder_learn_articles_invalid_object_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ReorderLearnArticles.from_dict(
                {
                    ReorderRequestObject.DEPLOYMENT_ID: "invalid_deployment_id",
                    ReorderLearnArticles.SECTION_ID: SAMPLE_VALID_OBJ_ID_2,
                    ReorderRequestObject.ITEMS: [
                        {
                            OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID_1,
                            OrderUpdateObject.ORDER: 1,
                        },
                    ],
                }
            )


class RetrieveDeploymentKeyActionsRequestObjectTestCase(unittest.TestCase):
    @staticmethod
    def _sample_obj():
        sample_dt = "2019-10-13T00:00:26.255616Z"
        return {
            RetrieveDeploymentKeyActionsRequestObject.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID_1,
            RetrieveDeploymentKeyActionsRequestObject.START_DATE: sample_dt,
            RetrieveDeploymentKeyActionsRequestObject.END_DATE: sample_dt,
        }

    def test_success_create_retrieve_deployment_key_action_obj(self):
        data = self._sample_obj()
        try:
            RetrieveDeploymentKeyActionsRequestObject.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_retrieve_deployment_key_action_obj__missing_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(RetrieveDeploymentKeyActionsRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                RetrieveDeploymentKeyActionsRequestObject.from_dict(data)


@patch(f"{MODULE_CONFIG_PATH}.validate", MagicMock())
class CreateMultipleModuleConfigsRequestObjectTestCase(unittest.TestCase):
    @staticmethod
    def _sample_dict_obj():
        return {
            CreateMultipleModuleConfigsRequestObject.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID_1,
            CreateMultipleModuleConfigsRequestObject.MODULE_CONFIGS: [
                get_sample_module_config()
            ],
        }

    def test_create_multiple_configs_request_object(self):
        try:
            CreateMultipleModuleConfigsRequestObject.from_dict(self._sample_dict_obj())
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_multiple_configs_request_object__no_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(CreateMultipleModuleConfigsRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_dict_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                RetrieveDeploymentKeyActionsRequestObject.from_dict(data)


class CreateDeployentRequestObjectTestCase(unittest.TestCase):
    def test_deployment_with_no_profile(self):
        deployment_dict = test_deployment()
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_with_with_no_profile_field(self):
        deployment_dict = test_deployment()
        deployment_dict[Deployment.PROFILE] = {Profile.FIELDS: None}
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_omited_profile_field_date_of_birth(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {ProfileFields.DATE_OF_BIRTH: None},
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_omited_profile_field_biological_sex(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {ProfileFields.BIOLOGICAL_SEX: None},
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_profile_field_date_of_birth_not_requested_but_mandated(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.DATE_OF_BIRTH: False,
                ProfileFields.MANDATORY_ONBOARDING_FIELDS: [
                    ProfileFields.DATE_OF_BIRTH
                ],
            },
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_not_requested_and_not_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_profile_field_biological_sex_not_requested_but_mandated(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.BIOLOGICAL_SEX: False,
                ProfileFields.MANDATORY_ONBOARDING_FIELDS: [
                    ProfileFields.BIOLOGICAL_SEX
                ],
            },
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_not_requested_and_not_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )

    def test_deployment_profile_field_biological_sex_date_of_birth_requested_and_mandated(
        self,
    ):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.BIOLOGICAL_SEX: True,
                ProfileFields.DATE_OF_BIRTH: True,
                ProfileFields.MANDATORY_ONBOARDING_FIELDS: [
                    ProfileFields.BIOLOGICAL_SEX,
                    ProfileFields.DATE_OF_BIRTH,
                ],
            },
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_profile_field_biological_sex_date_of_birth_not_requested_and_not_mandated(
        self,
    ):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.BIOLOGICAL_SEX: False,
                ProfileFields.DATE_OF_BIRTH: False,
            }
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self.assertFalse(
            getattr(deployment.profile.fields, ProfileFields.BIOLOGICAL_SEX)
        )
        self.assertFalse(
            getattr(deployment.profile.fields, ProfileFields.DATE_OF_BIRTH)
        )
        self.assertEqual(
            len(deployment.profile.fields.mandatoryOnboardingFields),
            0,
        )

    def test_deployment_profile_field_biological_sex_requested_not_mandated(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.BIOLOGICAL_SEX: True,
            },
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)

        self._assert_profile_field_requested_and_mandated(
            deployment, ProfileFields.DATE_OF_BIRTH
        )
        self.assertTrue(
            getattr(deployment.profile.fields, ProfileFields.BIOLOGICAL_SEX)
        )
        self.assertNotIn(
            ProfileFields.BIOLOGICAL_SEX,
            deployment.profile.fields.mandatoryOnboardingFields,
        )

    def test_deployment_profile_field_date_of_birth_requested_not_mandated(self):
        deployment_dict = test_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.DATE_OF_BIRTH: True,
            },
        }
        deployment_dict[Deployment.PROFILE] = profile_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)
        self.assertTrue(getattr(deployment.profile.fields, ProfileFields.DATE_OF_BIRTH))
        self.assertNotIn(
            ProfileFields.DATE_OF_BIRTH,
            deployment.profile.fields.mandatoryOnboardingFields,
        )

    def test_deployment_no_feature_field(self):
        deployment_dict = test_deployment()
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)
        self._assert_feature_field_exist(deployment.features)
        self.assertListEqual(
            deployment.features.offBoardingReasons.reasons,
            Reason._default_reasons_obj(),
        )
        self.assertTrue(deployment.features.offBoardingReasons.otherReason)

    def test_deployment_with_offboarding_reason_other_reason_set_only(self):
        deployment_dict = test_deployment()
        features_field = {
            Features.OFF_BOARDING_REASONS: {OffBoardingReasons.OTHER_REASON: False},
        }
        deployment_dict[Deployment.FEATURES] = features_field
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)
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
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)
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
        deployment = CreateDeploymentRequestObject.from_dict(deployment_dict)
        self._assert_feature_field_exist(deployment.features)
        self.assertEqual(len(deployment.features.offBoardingReasons.reasons), 3)
        self.assertFalse(deployment.features.offBoardingReasons.otherReason)

    def _assert_profile_field_requested_and_mandated(
        self, deployment: CreateDeploymentRequestObject, field: str
    ):
        self.assertTrue(getattr(deployment.profile.fields, field))
        self.assertIn(field, deployment.profile.fields.mandatoryOnboardingFields)

    def _assert_profile_field_not_requested_and_not_mandated(
        self, deployment: CreateDeploymentRequestObject, field: str
    ):
        self.assertFalse(getattr(deployment.profile.fields, field))
        self.assertNotIn(field, deployment.profile.fields.mandatoryOnboardingFields)

    def _assert_feature_field_exist(self, features: Features):
        self.assertIsNotNone(getattr(features, Features.OFF_BOARDING_REASONS))
        self.assertIn(
            OffBoardingReasons.REASONS,
            features.offBoardingReasons.to_dict(),
        )


class CreateDeploymentTemplateRequestObjectTestCase(unittest.TestCase):
    def test_create_deployment_template_request_object(self):
        try:
            CreateDeploymentTemplateRequestObject.from_dict(
                self._sample_create_deployment_template_req_obj()
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_multiple_configs_request_object__no_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(CreateDeploymentTemplateRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_create_deployment_template_req_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                CreateDeploymentTemplateRequestObject.from_dict(data)

    def test_failure_description_field_max_length_validation(self):
        description = "h" * 164
        with self.assertRaises(ConvertibleClassValidationError):
            CreateDeploymentTemplateRequestObject.from_dict(
                self._sample_create_deployment_template_req_obj(description=description)
            )

    def test_failure_name_field_max_length_validation(self):
        name = "h" * 81
        with self.assertRaises(ConvertibleClassValidationError):
            CreateDeploymentTemplateRequestObject.from_dict(
                self._sample_create_deployment_template_req_obj(name=name)
            )

    @staticmethod
    def _sample_deployment() -> dict:
        return {
            Deployment.ID: "61f2849639aa7e24341eb235",
            Deployment.NAME: "Updated Deployment",
            Deployment.STATUS: Status.DRAFT.value,
            Deployment.COLOR: "0x007AFF",
        }

    def _sample_create_deployment_template_req_obj(
        self, name: str = "sample name", description: str = "sample description"
    ):
        return {
            CreateDeploymentTemplateRequestObject.NAME: name,
            CreateDeploymentTemplateRequestObject.DESCRIPTION: description,
            CreateDeploymentTemplateRequestObject.ORGANIZATION_IDS: [
                "61f2848eda48aa2a606ce0c5",
                "61f2849639aa7e24341eb235",
            ],
            CreateDeploymentTemplateRequestObject.CATEGORY: TemplateCategory.SELF_SERVICE.value,
            CreateDeploymentTemplateRequestObject.TEMPLATE: self._sample_deployment(),
            CreateDeploymentTemplateRequestObject.SUBMITTER: MagicMock(
                spec_set=AuthorizedUser
            ),
        }


class RetrieveDeploymentTemplateRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_deployment_template_req_obj(self):
        try:
            RetrieveDeploymentTemplateRequestObject.from_dict(
                self._sample_retrieve_deployment_template_req_obj()
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_retrieve_deployment_template_req_obj__no_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(RetrieveDeploymentTemplateRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_retrieve_deployment_template_req_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                RetrieveDeploymentTemplateRequestObject.from_dict(data)

    @staticmethod
    def _sample_retrieve_deployment_template_req_obj():
        return {
            RetrieveDeploymentTemplateRequestObject.ORGANIZATION_ID: "61fbe0390eacf29c751507ed",
            RetrieveDeploymentTemplateRequestObject.SUBMITTER: MagicMock(
                spec_set=AuthorizedUser
            ),
            RetrieveDeploymentTemplateRequestObject.TEMPLATE_ID: "61fbe0390eacf29c751507ed",
        }


class RetrieveDeploymentTemplatesRequestObjectTestCase(unittest.TestCase):
    def test_success_retrieve_deployment_templates_req_obj(self):
        try:
            RetrieveDeploymentTemplatesRequestObject.from_dict(
                self._sample_retrieve_deployment_templates_req_obj()
            )
        except ConvertibleClassValidationError:
            self.fail()

    @staticmethod
    def _sample_retrieve_deployment_templates_req_obj():
        return {
            RetrieveDeploymentTemplatesRequestObject.ORGANIZATION_ID: "61fbe0390eacf29c751507ed",
            RetrieveDeploymentTemplatesRequestObject.SUBMITTER: MagicMock(
                spec_set=AuthorizedUser
            ),
        }


class DeleteDeploymentTemplateRequestObjectTestCase(
    RetrieveDeploymentTemplateRequestObjectTestCase
):
    def test_success_delete_deployment_template_req_obj(self):
        try:
            DeleteDeploymentTemplateRequestObject.from_dict(
                self._sample_retrieve_deployment_template_req_obj()
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_delete_deployment_template_req_obj__no_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(DeleteDeploymentTemplateRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_retrieve_deployment_template_req_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                DeleteDeploymentTemplateRequestObject.from_dict(data)


class UpdateDeploymentTemplateRequestObjectTestCase(unittest.TestCase):
    def test_success_update_deployment_template_req_obj(self):
        try:
            UpdateDeploymentTemplateRequestObject.from_dict(
                self._sample_update_template_req_obj()
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_update_deployment_template_req_obj__no_required_fields(
        self,
    ):
        req_obj_fields = [
            field.name
            for field in fields(UpdateDeploymentTemplateRequestObject)
            if field.metadata.get("required")
        ]
        for key in req_obj_fields:
            data = self._sample_update_template_req_obj()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                UpdateDeploymentTemplateRequestObject.from_dict(data)

    @staticmethod
    def _sample_update_template_req_obj():
        sample_id = "61fbe0390eacf29c751507ed"
        return {
            UpdateDeploymentTemplateRequestObject.ORGANIZATION_ID: sample_id,
            UpdateDeploymentTemplateRequestObject.SUBMITTER: MagicMock(
                spec_set=AuthorizedUser
            ),
            UpdateDeploymentTemplateRequestObject.TEMPLATE_ID: sample_id,
            UpdateDeploymentTemplateRequestObject.UPDATE_DATA: MagicMock(
                spec_set=DeploymentTemplate
            ),
        }
