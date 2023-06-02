import datetime
import io
import unittest
import uuid
from pathlib import Path
from typing import Any, Optional, Union

from bson import ObjectId
from freezegun import freeze_time

from extensions.authorization.models.role.role import Role
from extensions.authorization.models.user import User, RoleAssignment, UserLabel
from extensions.common.sort import SortField
from extensions.dashboard.models.configuration import (
    DeploymentLevelConfiguration,
    DayAnchor,
)
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import (
    Deployment,
    Label,
    OffBoardingReasons,
    Reason,
    Security,
    ModuleConfig,
    AdditionalContactDetailsItem,
    Profile,
    ProfileFields,
    EthnicityOption,
    Features,
    AppMenuItem,
    FieldValidator,
    OnboardingModuleConfig,
    DeploymentRevision,
    ChangeType,
    DeploymentTemplate,
    TemplateCategory,
    Location,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action import DeploymentEvent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    Learn,
    LearnSection,
    OrderUpdateObject,
    LearnArticle,
)
from extensions.deployment.models.status import Status, EnableStatus
from extensions.deployment.repository.models.mongo_deployment_template_model import (
    MongoDeploymentTemplateModel,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.deployment.router.deployment_requests import (
    CloneDeploymentRequestObject,
    CreateLabelsRequestObject,
    RetrieveDeploymentsRequestObject,
    RetrieveDeploymentKeyActionsRequestObject,
    UpdateLabelRequestObject,
)
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from extensions.key_action.models.key_action_log import KeyAction
from extensions.tests.deployment.IntegrationTests.abstract_deployment_test_case_tests import (
    AbstractDeploymentTestCase,
)
from extensions.tests.deployment.IntegrationTests.test_helpers import (
    simple_module_config,
    module_config_with_config_body,
    modified_deployment,
    modified_deployment_with_gender_options,
    modified_deployment_with_ethnicity_options,
    modified_deployment_with_additional_contact_details,
)
from extensions.tests.deployment.UnitTests.test_helpers import (
    legal_docs_s3_fields,
    sample_s3_object,
)
from extensions.tests.shared.test_helpers import simple_deployment
from sdk.calendar.utils import get_dt_from_str
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import ErrorCodes, PermissionDenied
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.models.message import Message
from sdk.inbox.models.search_message import (
    MessageSearchResponseObject,
    MessageSearchRequestObject,
)

VALID_SUPER_ADMIN_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
VALID_MANAGER_ID = "5ffca6d91882ddc1cd8ab94f"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
VALID_CUSTOM_ROLE_ID = "600720843111683010a73b4e"
VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT = "6009d2409b0e1f2eab20bbb3"
HUMA_SUPPORT_USER_ID = "5ed803dd5f2f99da73675513"
ACCOUNT_MANAGER_USER_ID = "61cb194c630781b664bf8eb5"
ORGANIZATION_OWNER_USER_ID = "61cb194c630781b664bc7eb5"
ORGANIZATION_EDITOR_USER_ID = "61e6a8e2d9681a389f060848"

INVALID_DEPLOYMENT = "5e8f0c74b50aa9656c34789c"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
ORG_ID = "5fde855f12db509a2785da06"


def role_fields(
    count: int = 0, name: str = "Nurse", user_type: str = Role.UserType.MANAGER
) -> dict:
    permissions = [
        "VIEW_PATIENT_IDENTIFIER",
        "VIEW_PATIENT_DATA",
        "MANAGE_PATIENT_DATA",
        "Temporary_",
    ]
    return {
        Role.NAME: name,
        Role.PERMISSIONS: permissions[0:count],
        Role.USER_TYPE: user_type,
    }


def extra_custom_fields(count: int = 1) -> dict:
    extra_custom_fields_dict = {}
    field_config = {
        "errorMessage": "Test error message",
        "validation": "/*/",
        "onboardingCollectionText": "Please enter your Insurance Number",
        "description": "Please enter your Insurance Number description",
        "profileCollectionText": "Insurance Number",
        "required": False,
        "clinicianUpdate": True,
        "showClinicianHeader": True,
        "type": "NUMERIC",
        "order": 1,
    }
    for i in range(count):
        new_field = "mediclinicNumber" + (str(i) if i else "")
        extra_custom_fields_dict.update({new_field: field_config})

    return {"extraCustomFields": extra_custom_fields_dict}


class CreateDeploymentTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.create_url = f"{self.deployment_route}/deployment"

    def test_deployment_creation(self):
        rsp = self.flask_client.post(
            self.create_url, json=simple_deployment(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

    def test_success_create_deployment_with_legal_documents_s3_objects(self):
        deployment = simple_deployment()
        for item in legal_docs_s3_fields():
            deployment[item] = sample_s3_object()
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        collection_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        deployment_data = self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(rsp.json[Deployment.ID])}
        )
        for item in legal_docs_s3_fields():
            self.assertEqual(deployment_data[item], sample_s3_object())

    def test_deployment_creation_with_onfido_required_reports(self):
        deployment = simple_deployment()
        deployment[Deployment.ONFIDO_REQUIRED_REPORTS] = [
            OnfidoReportNameType.DOCUMENT.name
        ]
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

        deployment = self.get_deployment(rsp.json["id"])
        self.assertEqual(
            deployment[Deployment.ONFIDO_REQUIRED_REPORTS][0],
            OnfidoReportNameType.DOCUMENT.name,
        )

    def test_deployment_creation_without_name(self):
        deployment = simple_deployment()
        del deployment[Deployment.NAME]
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_id(self):
        deployment = simple_deployment()
        deployment["id"] = uuid.uuid4()
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_learn(self):
        deployment = simple_deployment()
        deployment[Deployment.LEARN] = []
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_module_config(self):
        deployment = simple_deployment()
        deployment[Deployment.MODULE_CONFIGS] = [{}]
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_consent(self):
        deployment = simple_deployment()
        deployment[Deployment.CONSENT] = [{}]
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_enrollment_counter(self):
        deployment = simple_deployment()
        deployment[Deployment.ENROLLMENT_COUNTER] = 79
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_valid_location(self):
        deployment = simple_deployment()
        deployment[Deployment.LOCATION] = {
            Location.ADDRESS: "London, United Kingdom",
            Location.COUNTRY: "United Kingdom",
            Location.COUNTRY_CODE: "GB",
            Location.CITY: "London",
            Location.LATITUDE: 51.5,
            Location.LONGITUDE: -0.083333,
        }
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_deployment_creation_with_date(self):
        deployment = simple_deployment()
        deployment[Deployment.CREATE_DATE_TIME] = "2020-04-07T17:05:51Z"
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        del deployment[Deployment.CREATE_DATE_TIME]
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

        deployment[Deployment.UPDATE_DATE_TIME] = "2020-04-07T17:05:51Z"
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_deployment_creation_with_profile_fields_validators(self):
        deployment = simple_deployment()
        validators = {"birthDate": {FieldValidator.MIN_ISO_DURATION: "P10D"}}
        deployment[Deployment.PROFILE] = {
            Profile.FIELDS: {ProfileFields.VALIDATORS: validators}
        }
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def _check_deployment_fields(
        self, update_body, initial_deployment, updated_deployment
    ):
        updated_fields = [
            *update_body.keys(),
            Deployment.UPDATE_DATE_TIME,
            Deployment.VERSION,
        ]
        initial_values = {
            k: v for k, v in initial_deployment.items() if k in updated_fields
        }
        updated_values = {
            k: v for k, v in updated_deployment.items() if k in updated_fields
        }
        for key in updated_fields:
            # Confirming that these fields were updated
            self.assertNotEqual(initial_values[key], updated_values[key])
            # Removing them to compare later and confirm that the rest left as is
            del initial_deployment[key]
            del updated_deployment[key]
        self.assertDictEqual(initial_deployment, updated_deployment)

    def test_success_deployment_update_without_extra_custom_fields(self):
        initial_deployment = self.get_deployment()
        update_body = {Deployment.NAME: "New Deployment", Deployment.STATUS: "ARCHIVED"}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=update_body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        updated_deployment = self.get_deployment()
        # just check if moduleConfigs, keyActions, consent, profile fields are correct in vision
        self.assertListEqual(
            list(updated_deployment[Deployment.EXTRA_CUSTOM_FIELDS].keys()),
            ["mediclinicNumber"],
        )
        self.assertEqual(
            updated_deployment[Deployment.KEY_ACTIONS][0][KeyActionConfig.TITLE],
            "PAM Questionnaire",
        )
        self.assertEqual(
            updated_deployment[Deployment.MODULE_CONFIGS][0][ModuleConfig.MODULE_ID],
            "BloodPressure",
        )
        self.assertEqual(
            updated_deployment[Deployment.CONSENT][Consent.INSTITUTE_NAME],
            "consent institute name",
        )
        self.assertEqual(
            update_body[Deployment.STATUS], updated_deployment[Deployment.STATUS]
        )
        self.assertEqual(
            update_body[Deployment.NAME], updated_deployment[Deployment.NAME]
        )
        self._check_deployment_fields(
            update_body, initial_deployment, updated_deployment
        )

    def test_success_deployment_update_with_extra_custom_fields(self):
        initial_deployment = self.get_deployment()
        update_body = {
            Deployment.EXTRA_CUSTOM_FIELDS: {
                "mediclinicNumber": {
                    "errorMessage": "Insurance Number is incorrect - 1",
                    "validation": "\\d{7}",
                    "onboardingCollectionText": "Please enter mediclinic number - 1",
                    "profileCollectionText": "Patient Unique ID",
                    "required": True,
                    "clinicianUpdate": True,
                    "showClinicianHeader": True,
                    "type": "TEXT",
                    "order": 2,
                }
            }
        }
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=update_body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        updated_deployment = self.get_deployment()

        self._check_deployment_fields(
            update_body, initial_deployment, updated_deployment
        )

    def test_success_deployment_with_additional_contact_details(self):
        deployment = modified_deployment_with_additional_contact_details({})
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_deployment_with_additional_contact_details_no_mandatory(self):
        update_body = {AdditionalContactDetailsItem.ALT_CONTACT_NUMBER: False}
        deployment = modified_deployment_with_additional_contact_details(update_body)
        del deployment[Deployment.PROFILE][Profile.FIELDS][
            ProfileFields.ADDITIONAL_CONTACT_DETAILS
        ][AdditionalContactDetailsItem.MANDATORY_FIELDS]
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_with_alt_contact_number_false_but_in_mandatory_List(self):
        update_body = {AdditionalContactDetailsItem.ALT_CONTACT_NUMBER: False}
        deployment = modified_deployment_with_additional_contact_details(update_body)
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_deployment_creation_with_hide_app_support_feature(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {Features.HIDE_APP_SUPPORT: True}
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        self.assertEqual(
            get_rsp.json[Deployment.FEATURES][Features.HIDE_APP_SUPPORT], True
        )

    def test_deployment_creation_with_mfa_required(self):
        deployment = simple_deployment()
        deployment[Deployment.SECURITY] = {
            Security.MFA_REQUIRED: True,
            Security.APP_LOCK_REQUIRED: False,
        }
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        self.assertEqual(get_rsp.json[Deployment.SECURITY][Security.MFA_REQUIRED], True)
        self.assertEqual(
            get_rsp.json[Deployment.SECURITY][Security.APP_LOCK_REQUIRED], False
        )

    def test_deployment_creation_with_deprecated_mfa_required(self):
        deployment = simple_deployment()
        deployment[Security.MFA_REQUIRED] = False
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        self.assertEqual(
            get_rsp.json[Deployment.SECURITY][Security.MFA_REQUIRED], False
        )
        self.assertEqual(get_rsp.json[Security.MFA_REQUIRED], False)

    def test_deployment_omited_profile_field_date_of_birth_and_biological_sex(self):
        deployment = simple_deployment()
        profile_field = {
            Profile.FIELDS: dict(),
        }
        deployment[Deployment.PROFILE] = profile_field

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_profile_field_dob_biological_sex_not_requested_but_mandated(
        self,
    ):
        deployment = simple_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.DATE_OF_BIRTH: False,
                ProfileFields.BIOLOGICAL_SEX: False,
                ProfileFields.MANDATORY_ONBOARDING_FIELDS: [
                    ProfileFields.DATE_OF_BIRTH,
                    ProfileFields.BIOLOGICAL_SEX,
                ],
            },
        }
        deployment[Deployment.PROFILE] = profile_field

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_not_requested_and_not_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_not_requested_and_not_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_omit_biological_sex_and_dob_not_requested(self):
        deployment = simple_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.DATE_OF_BIRTH: False,
            },
        }
        deployment[Deployment.PROFILE] = profile_field

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_not_requested_and_not_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )

    def test_deployment_omit_dob_and_biological_sex_not_requested(self):
        deployment = simple_deployment()
        profile_field = {
            Profile.FIELDS: {
                ProfileFields.BIOLOGICAL_SEX: False,
            },
        }
        deployment[Deployment.PROFILE] = profile_field

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_not_requested_and_not_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )

    def test_deployment_omit_profile(self):
        deployment = simple_deployment()

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )

    def test_deployment_omit_profile_fields(self):
        deployment = simple_deployment()
        profile_field = {Profile.FIELDS: None}
        deployment[Deployment.PROFILE] = profile_field

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.BIOLOGICAL_SEX
        )
        rsp_data = get_rsp.json
        self._assert_profile_field_requested_and_mandated(
            rsp_data, ProfileFields.DATE_OF_BIRTH
        )

    def test_deployment_omit_features_field(self):
        deployment = simple_deployment()

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertTrue(
            rsp_data[Deployment.FEATURES][Features.OFF_BOARDING_REASONS][
                OffBoardingReasons.OTHER_REASON
            ]
        )
        deployment_reasons = rsp_data[Deployment.FEATURES][
            Features.OFF_BOARDING_REASONS
        ][OffBoardingReasons.REASONS]
        self._assert_off_boarding_field_reasons_exist(
            deployment_reasons, Reason._default_reasons()
        )
        self.assertFalse(rsp_data[Deployment.FEATURES][Features.LABELS])

    def test_deployment_omit_onboarding_reasons_field(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {Features.HIDE_APP_SUPPORT: True}

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertTrue(
            rsp_data[Deployment.FEATURES][Features.OFF_BOARDING_REASONS][
                OffBoardingReasons.OTHER_REASON
            ]
        )
        deployment_reasons = rsp_data[Deployment.FEATURES][
            Features.OFF_BOARDING_REASONS
        ][OffBoardingReasons.REASONS]
        self._assert_off_boarding_field_reasons_exist(
            deployment_reasons, Reason._default_reasons()
        )

    def test_deployment_omit_feature_labels_field(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {Features.HIDE_APP_SUPPORT: True}

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertFalse(rsp_data[Deployment.FEATURES][Features.LABELS])

    def test_deployment_feature_labels_not_enabled_field(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {Features.LABELS: False}

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertFalse(rsp_data[Deployment.FEATURES][Features.LABELS])

    def test_deployment_feature_labels_enabled_field(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {Features.LABELS: True}

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertTrue(rsp_data[Deployment.FEATURES][Features.LABELS])

    def test_deployment_onboarding_reasons_omit_other_reasons_field(self):
        sample_reason = [{Reason.DISPLAY_NAME: "some_display_name", Reason.ORDER: 1}]
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {
            Features.OFF_BOARDING_REASONS: {OffBoardingReasons.REASONS: sample_reason}
        }

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        deployment_reasons = rsp_data[Deployment.FEATURES][
            Features.OFF_BOARDING_REASONS
        ][OffBoardingReasons.REASONS]
        self.assertTrue(
            rsp_data[Deployment.FEATURES][Features.OFF_BOARDING_REASONS][
                OffBoardingReasons.OTHER_REASON
            ]
        )
        self.assertListEqual(deployment_reasons, sample_reason)

    def test_deployment_onboarding_reasons_omit_reasons_field(self):
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {
            Features.OFF_BOARDING_REASONS: {OffBoardingReasons.OTHER_REASON: False}
        }

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        self.assertFalse(
            rsp_data[Deployment.FEATURES][Features.OFF_BOARDING_REASONS][
                OffBoardingReasons.OTHER_REASON
            ]
        )
        deployment_reasons = rsp_data[Deployment.FEATURES][
            Features.OFF_BOARDING_REASONS
        ][OffBoardingReasons.REASONS]
        self._assert_off_boarding_field_reasons_exist(
            deployment_reasons, Reason._default_reasons()
        )

    def test_deployment_onboarding_reasons(self):
        sample_reason = [{Reason.DISPLAY_NAME: "some_display_name", Reason.ORDER: 1}]
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {
            Features.OFF_BOARDING_REASONS: {
                OffBoardingReasons.REASONS: sample_reason,
                OffBoardingReasons.OTHER_REASON: False,
            }
        }

        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        get_rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{rsp.json[Deployment.ID]}",
            headers=self.headers,
        )
        rsp_data = get_rsp.json
        deployment_reasons = rsp_data[Deployment.FEATURES][
            Features.OFF_BOARDING_REASONS
        ][OffBoardingReasons.REASONS]
        self.assertFalse(
            rsp_data[Deployment.FEATURES][Features.OFF_BOARDING_REASONS][
                OffBoardingReasons.OTHER_REASON
            ]
        )
        self.assertListEqual(deployment_reasons, sample_reason)

    def test_failure_deployment_onboarding_reasons_duplicates_order(self):
        sample_reason = [
            {Reason.DISPLAY_NAME: "some_display_name", Reason.ORDER: 1},
            {Reason.DISPLAY_NAME: "some_display_name2", Reason.ORDER: 1},
        ]
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {
            Features.OFF_BOARDING_REASONS: {
                OffBoardingReasons.REASONS: sample_reason,
                OffBoardingReasons.OTHER_REASON: False,
            }
        }
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(rsp.json["code"], 100050)

    def test_failure_deployment_onboarding_reasons_duplicates_display_name(self):
        sample_reason = [
            {Reason.DISPLAY_NAME: "some_display_name", Reason.ORDER: 1},
            {Reason.DISPLAY_NAME: "some_display_name", Reason.ORDER: 3},
        ]
        deployment = simple_deployment()
        deployment[Deployment.FEATURES] = {
            Features.OFF_BOARDING_REASONS: {
                OffBoardingReasons.REASONS: sample_reason,
                OffBoardingReasons.OTHER_REASON: False,
            }
        }
        rsp = self.flask_client.post(
            self.create_url, json=deployment, headers=self.headers
        )
        self.assertEqual(rsp.status_code, 403)
        self.assertEqual(rsp.json["code"], 100050)

    def _assert_profile_field_requested_and_mandated(
        self, deployment_dict: dict[str, Any], field: str
    ):
        self.assertTrue(deployment_dict[Deployment.PROFILE][Profile.FIELDS][field])
        self.assertIn(
            field,
            deployment_dict[Deployment.PROFILE][Profile.FIELDS][
                ProfileFields.MANDATORY_ONBOARDING_FIELDS
            ],
        )

    def _assert_profile_field_not_requested_and_not_mandated(
        self, deployment_dict: dict[str, Any], field: str
    ):
        self.assertFalse(deployment_dict[Deployment.PROFILE][Profile.FIELDS][field])
        self.assertNotIn(
            field,
            deployment_dict[Deployment.PROFILE][Profile.FIELDS][
                ProfileFields.MANDATORY_ONBOARDING_FIELDS
            ],
        )

    def _assert_off_boarding_field_reasons_exist(
        self,
        reasons: list[dict[str, Union[str, int]]],
        expected_reason: list[dict[str, Union[str, int]]],
    ):
        self.assertEqual(len(reasons), len(expected_reason))
        self.assertIn(Reason.DISPLAY_NAME, reasons[0])
        self.assertIn(Reason.ORDER, reasons[0])


class UpdateDeploymentTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.base_url = f"{self.deployment_route}/deployment/{DEPLOYMENT_ID}"

    def test_deployment_update(self):
        deployment = modified_deployment()
        rsp = self.update_deployment(deployment)
        self.assertEqual(200, rsp.status_code)
        self.assertNameChanged(deployment[Deployment.NAME])

    def test_deployment_update_with_dashboard_configuration(self):
        deployment = modified_deployment()
        dashboard_configuration = {
            DeploymentLevelConfiguration.TARGET_CONSENTED_MONTHLY: 1000,
            DeploymentLevelConfiguration.TARGET_CONSENTED: 1000,
            DeploymentLevelConfiguration.DAY_0_ANCHOR: DayAnchor.REGISTRATION_DATE.value,
            DeploymentLevelConfiguration.TARGET_COMPLETED: 100,
        }
        deployment[Deployment.DASHBOARD_CONFIGURATION] = dashboard_configuration
        rsp = self.update_deployment(deployment)
        self.assertEqual(200, rsp.status_code)

    def test_deployment_update_with_legal_documents_s3_objects(self):
        deployment = modified_deployment()
        for item in legal_docs_s3_fields():
            deployment[item] = sample_s3_object()
        rsp = self.update_deployment(deployment)
        self.assertEqual(200, rsp.status_code)

        collection_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        deployment_data = self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(deployment[Deployment.ID])}
        )
        for item in legal_docs_s3_fields():
            self.assertEqual(deployment_data[item], sample_s3_object())

    def test_deployment_update_not_existing(self):
        deployment = modified_deployment()
        deployment["id"] = "5d386cc6ff885918d96edb1c"
        rsp = self.update_deployment(deployment, deployment["id"])
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_deployment_update_version_is_same(self):
        body = {"name": "New Dep"}
        old_deployment = self.mongo_database.deployment.find_one(
            {"_id": ObjectId(DEPLOYMENT_ID)}
        )
        rsp = self.update_deployment(body)
        self.assertEqual(200, rsp.status_code)
        new_deployment = self.mongo_database.deployment.find_one(
            {"_id": ObjectId(DEPLOYMENT_ID)}
        )
        self.assertVersionIncreased(old_deployment, new_deployment)

    def test_success_deployment_update_with_gender_options(self):
        deployment = modified_deployment_with_gender_options()
        rsp = self.update_deployment(deployment)
        self.assertEqual(200, rsp.status_code)

        expected_fields = deployment[Deployment.PROFILE][Profile.FIELDS]
        self.assertProfileFieldsUpdated(expected_fields, ProfileFields.GENDER_OPTIONS)

    def test_success_deployment_update_with_ethnicity_options(self):
        deployment = modified_deployment_with_ethnicity_options()
        rsp = self.update_deployment(deployment)
        self.assertEqual(200, rsp.status_code)

        expected_fields = deployment[Deployment.PROFILE][Profile.FIELDS]
        self.assertProfileFieldsUpdated(
            expected_fields,
            field_name=ProfileFields.ETHNICITY_OPTIONS,
        )

    def test_failure_deployment_update_with_ethnicity_option(self):
        deployment = modified_deployment_with_ethnicity_options()
        deployment[Deployment.PROFILE][Profile.FIELDS][ProfileFields.ETHNICITY_OPTIONS][
            0
        ][EthnicityOption.VALUE] = "Mixed"
        rsp = self.update_deployment(deployment)
        self.assertEqual(400, rsp.status_code)

    def test_failure_deployment_update_with_invalid_gender_option(self):
        deployment = modified_deployment_with_gender_options()
        deployment[Deployment.PROFILE]["fields"]["genderOptions"][0]["value"] = "Man"
        rsp = self.update_deployment(deployment)
        self.assertEqual(400, rsp.status_code)

    def test_success_update_deployment_with_profile_fields_validators(self):
        validators = {User.DATE_OF_BIRTH: {FieldValidator.MIN_ISO_DURATION: "P10D"}}
        request_data = {
            Deployment.PROFILE: {Profile.FIELDS: {ProfileFields.VALIDATORS: validators}}
        }
        rsp = self.update_deployment(request_data)
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment(DEPLOYMENT_ID)
        self.assertIn(Deployment.PROFILE, deployment)
        self.assertIn(Profile.FIELDS, deployment[Deployment.PROFILE])
        self.assertIn(
            member=ProfileFields.VALIDATORS,
            container=deployment[Deployment.PROFILE][Profile.FIELDS],
        )

    def test_failure_update_deployment_with_profile_fields_validators(self):
        validators = {"birthDate": {FieldValidator.MIN_ISO_DURATION: "P10D"}}
        request_data = {
            Deployment.PROFILE: {Profile.FIELDS: {ProfileFields.VALIDATORS: validators}}
        }
        rsp = self.update_deployment(request_data)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def update_deployment(self, json: dict, deployment_id: str = None):
        url = self.base_url
        if deployment_id:
            url = self.base_url.replace(DEPLOYMENT_ID, deployment_id)
        return self.flask_client.put(url, json=json, headers=self.headers)

    def assertNameChanged(self, expected_name: str):
        updated_deployment = self.get_deployment()
        self.assertEqual(expected_name, updated_deployment[Deployment.NAME])

    def assertProfileFieldsUpdated(self, expected_fields: dict, field_name: str):
        updated_deployment = self.get_deployment()
        fields = updated_deployment[Deployment.PROFILE][Profile.FIELDS]
        self.assertListEqual(expected_fields[field_name], fields[field_name])

    def assertVersionIncreased(self, old_deployment, new_deployment):
        self.assertGreater(
            new_deployment[Deployment.VERSION],
            old_deployment[Deployment.VERSION],
        )


class RetrieveDeploymentTestCase(AbstractDeploymentTestCase):
    def test_retrieve_deployment(self):
        rsp = self.retrieve_deployment(DEPLOYMENT_ID)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(DEPLOYMENT_ID, rsp.json[Deployment.ID])
        self.assertEqual("deployment description", rsp.json[Deployment.DESCRIPTION])

    def test_failure_retrieve_deployment__not_exist(self):
        rsp = self.retrieve_deployment(INVALID_DEPLOYMENT)
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_failure_retrieve_deployment_different_deployment_ids(self):
        headers = {**self.headers, "x-deployment-id": INVALID_DEPLOYMENT}
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{DEPLOYMENT_ID}",
            headers=headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual("Access of different resources", rsp.json["message"])

    def retrieve_deployment(self, id_: str):
        return self.flask_client.get(
            f"{self.deployment_route}/deployment/{id_}", headers=self.headers
        )


class SearchDeploymentsTestCase(AbstractDeploymentTestCase):
    def test_search_deployments(self):
        search = "plan\\"
        data = self.get_search_deployments_request_body(search=search)
        rsp = self.search(json=data)
        self.assertEqual(200, rsp.status_code)
        self.assertNotEqual(0, len(rsp.json["items"]))

    def test_search_deployments__by_search_criteria(self):
        part_of_deployment_id = "b2c"
        data = self.get_search_deployments_request_body(search=part_of_deployment_id)
        rsp = self.search(json=data)

        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json["items"]))

        first_deployment_id = rsp.json["items"][0]["id"]
        self.assertIn(part_of_deployment_id, first_deployment_id)

    def test_search_deployments__by_status_draft(self):
        data = self.get_search_deployments_request_body(status=[Status.DRAFT.name])
        rsp = self.search(json=data)
        self.assertAllDeploymentsAreDraft(rsp.json["items"])

    def test_search_deployments__by_status_deployed(self):
        data = self.get_search_deployments_request_body(status=[Status.DEPLOYED.name])
        rsp = self.search(json=data)
        self.assertAllDeploymentsAreDeployed(rsp.json["items"])

    @staticmethod
    def default_deployment_names() -> list[str]:
        return ["Unnamed care plan", "Test care plan\\"]

    def test_sorting_deployments_by_name__descending(self):
        data = self.get_search_deployments_request_body(
            status=[Status.DEPLOYED.name], sort_direction=SortField.Direction.DESC.value
        )
        rsp = self.search(json=data)
        res_deployment_names = [i["name"] for i in rsp.json["items"]]
        self.assertEqual(self.default_deployment_names(), res_deployment_names)

    def test_sorting_deployments_by_name__ascending(self):
        data = self.get_search_deployments_request_body(
            status=[Status.DEPLOYED.name], sort_direction=SortField.Direction.ASC.value
        )
        rsp = self.search(json=data)
        res_deployment_names = [i["name"] for i in rsp.json["items"]]
        self.assertEqual(self.default_deployment_names()[::-1], res_deployment_names)

    def test_sorting_deployments_all_acceptable_fields(self):
        allowed_fields = Deployment.VALID_SORT_FIELDS
        for field in allowed_fields:
            data = self.get_search_deployments_request_body(sort_field_name=field)
            rsp = self.search(json=data)
            self.assertEqual(rsp.status_code, 200)

    def test_sorting_deployments_by_name__ascending_with_skip(self):
        data = self.get_search_deployments_request_body(
            status=[Status.DEPLOYED.name],
            sort_direction=SortField.Direction.ASC.value,
            skip=1,
        )
        rsp = self.search(json=data)
        res_deployment_names = [i["name"] for i in rsp.json["items"]]
        self.assertEqual(len(res_deployment_names), 1)
        self.assertEqual(res_deployment_names[0], self.default_deployment_names()[0])

    def test_sorting_deployments_by_name__descending_with_skip(self):
        data = self.get_search_deployments_request_body(
            status=[Status.DEPLOYED.name],
            sort_direction=SortField.Direction.DESC.value,
            skip=1,
        )
        rsp = self.search(json=data)
        res_deployment_names = [i["name"] for i in rsp.json["items"]]
        self.assertEqual(len(res_deployment_names), 1)
        self.assertEqual(res_deployment_names[0], self.default_deployment_names()[-1])

    def test_search_deployments__by_status_draft_and_deployed(self):
        data = self.get_search_deployments_request_body(
            status=[Status.DRAFT.name, Status.DEPLOYED.name]
        )
        rsp = self.search(json=data)
        self.assertAllDeploymentsAreEitherDraftOrDeployed(rsp.json["items"])

    def test_failure_search_deployments_negative_limit(self):
        data = self.get_search_deployments_request_body(limit=-1)
        rsp = self.search(json=data)
        self.assertEqual(403, rsp.status_code)

    def test_failure_search_deployments_negative_skip(self):
        data = self.get_search_deployments_request_body(skip=-1)
        rsp = self.search(json=data)
        self.assertEqual(403, rsp.status_code)

    def test_search_deployments_empty_List(self):
        data = self.get_search_deployments_request_body(skip=10)
        rsp = self.search(json=data)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json["items"]))

    def search(self, json):
        url = f"{self.deployment_route}/deployment/search"
        return self.flask_client.post(url, json=json, headers=self.headers)

    @staticmethod
    def get_search_deployments_request_body(
        skip: int = 0,
        limit: int = 10,
        name_contains: str = "",
        search: str = "",
        status: list[str] = None,
        sort_direction: str = SortField.Direction.ASC.value,
        sort_field_name: str = Deployment.NAME,
    ):
        payload = {
            RetrieveDeploymentsRequestObject.SKIP: skip,
            RetrieveDeploymentsRequestObject.LIMIT: limit,
            RetrieveDeploymentsRequestObject.NAME_CONTAINS: name_contains,
            RetrieveDeploymentsRequestObject.SEARCH_CRITERIA: search,
            RetrieveDeploymentsRequestObject.STATUS: status,
            RetrieveDeploymentsRequestObject.SORT: [
                {SortField.FIELD: sort_field_name, SortField.DIRECTION: sort_direction}
            ],
        }
        return remove_none_values(payload)

    def assertAllDeploymentsAreDraft(self, items: list[dict]):
        self.assertGreater(len(items), 0)
        all_deps_are_draft = all(
            d[Deployment.STATUS] == Status.DRAFT.name for d in items
        )
        msg = "Not all deployments are draft"
        self.assertTrue(all_deps_are_draft, msg)

    def assertAllDeploymentsAreDeployed(self, items: list[dict]):
        all_deps_are_deployed = all(
            d[Deployment.STATUS] == Status.DEPLOYED.name for d in items
        )
        msg = "Not all deployments are deployed"
        self.assertTrue(all_deps_are_deployed, msg)

    def assertAllDeploymentsAreEitherDraftOrDeployed(self, items: list[dict]):
        status = [Status.DEPLOYED.name, Status.DRAFT.name]
        all_deps_are_deployed = all(d[Deployment.STATUS] in status for d in items)
        msg = "Not all deployments are draft or deployed"
        self.assertTrue(all_deps_are_deployed, msg)


class DeleteDeploymentTestCase(AbstractDeploymentTestCase):
    def test_delete_deployment(self):
        deployment_id = "5d386cc6ff885918d96edb2a"
        rsp = self.flask_client.delete(
            f"{self.deployment_route}/deployment/{deployment_id}", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_delete_deployment_not_exist(self):
        deployment_id = "5d386cc6ff885918d96edb5f"
        rsp = self.flask_client.delete(
            f"{self.deployment_route}/deployment/{deployment_id}", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])


class RetrieveDeploymentWithVersionTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()

        self.retrieve_url = f"{self.deployment_route}/deployment/version"
        self.create_url = f"{self.deployment_route}/deployment"

    def test_retrieve_deployment_with_version_number(self):
        rsp = self.flask_client.post(
            self.create_url, json=simple_deployment(), headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

        deployment_id = rsp.json["id"]
        version_number = 0
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{deployment_id}/version/{version_number}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["version"], version_number)

    def test_retrieve_deployment_with_version_number_from_deployment_revision(self):
        deployment_id = "5d386cc6ff885918d96edb1a"
        version_number = 8
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{deployment_id}/version/{version_number}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["version"], version_number)

    def test_retrieve_deployment_with_version_number_no_exist(self):
        deployment_id = "5d386cc6ff885918d96edb5f"
        version_number = 1
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{deployment_id}/version/{version_number}",
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300018, rsp.json["code"])


class DeploymentExtraCustomFieldsTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super(DeploymentExtraCustomFieldsTestCase, self).setUp()
        self.remove_onboarding()

    def test_create_fields(self):
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=extra_custom_fields(),
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        deployment_dict = self.get_deployment()
        self.assertIn("extraCustomFields", deployment_dict)
        self.assertIn("mediclinicNumber", deployment_dict["extraCustomFields"])

    def test_failure_create_by_user(self):
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=extra_custom_fields(),
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_with_missing_fields(self):
        body = extra_custom_fields()
        del body["extraCustomFields"]["mediclinicNumber"]["errorMessage"]

        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_six_fields(self):
        body = extra_custom_fields(count=6)
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_success_remove_all_custom_fields(self):
        body = extra_custom_fields()
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        deployment = self.get_deployment(deployment_id=self.deployment_id)
        self.assertEqual(
            len(deployment[Deployment.EXTRA_CUSTOM_FIELDS]),
            len(body[Deployment.EXTRA_CUSTOM_FIELDS]),
        )

        body = {Deployment.EXTRA_CUSTOM_FIELDS: {}}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment(deployment_id=self.deployment_id)
        self.assertDictEqual(deployment[Deployment.EXTRA_CUSTOM_FIELDS], {})


class DeploymentRolesTestCase(AbstractDeploymentTestCase):
    existing_role_id = "5e8eeae1b707216625ca4203"

    def setUp(self):
        super(DeploymentRolesTestCase, self).setUp()
        self.remove_onboarding()

    def test_success_create_or_update_roles(self):
        success_test_cases = (
            (VALID_SUPER_ADMIN_ID, "Custom Role", ["MANAGE_PATIENT_DATA"]),
            (
                VALID_MANAGER_ID,
                "name1",
                ["MANAGE_PATIENT_DATA", "VIEW_PATIENT_IDENTIFIER", "VIEW_PATIENT_DATA"],
            ),
        )
        existing_role = {
            Role.ID: self.existing_role_id,
            Role.NAME: "Custom Role",
            Role.PERMISSIONS: [
                "MANAGE_PATIENT_DATA",
                "VIEW_PATIENT_IDENTIFIER",
                "VIEW_PATIENT_DATA",
                "CONTACT_PATIENT",
            ],
        }
        for test_case, name, permissions in success_test_cases:
            existing_role.update({Role.NAME: name, Role.PERMISSIONS: permissions})
            new_role_name = "Head" + name
            rsp = self.flask_client.put(
                f"{self.deployment_route}/deployment/{self.deployment_id}/role",
                json={Deployment.ROLES: [existing_role, role_fields(2, new_role_name)]},
                headers=self.get_headers_for_token(test_case),
            )
            self.assertEqual(200, rsp.status_code)
            deployment_dict = self.get_deployment()
            roles = deployment_dict.get(Deployment.ROLES)
            self.assertIsNotNone(roles)
            self.assertEqual(2, len(roles))
            self.assertEqual(name, roles[0][Role.NAME])
            self.assertEqual(new_role_name, roles[1][Role.NAME])

    def test_failure_create_two_identical_roles(self):
        roles = [role_fields(2), role_fields(2)]

        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json={Deployment.ROLES: roles},
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_create_role_with_invalid_user_type(self):
        roles = [role_fields(2, "Nurse", "Contributor")]

        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json={Deployment.ROLES: roles},
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_roles(self):
        failure_test_cases = (
            (VALID_CONTRIBUTOR_ID, "name1"),
            (VALID_CUSTOM_ROLE_ID, "name2"),
            (VALID_USER_ID, "name3"),
        )
        existing_role = {
            Role.ID: self.existing_role_id,
            Role.NAME: "Custom Role",
            Role.PERMISSIONS: [
                "MANAGE_PATIENT_DATA",
                "VIEW_PATIENT_IDENTIFIER",
                "VIEW_PATIENT_DATA",
                "CONTACT_PATIENT",
            ],
        }
        for test_case, name in failure_test_cases:
            existing_role.update({Role.NAME: name})
            rsp = self.flask_client.put(
                f"{self.deployment_route}/deployment/{self.deployment_id}/role",
                json={Deployment.ROLES: [role_fields(2)]},
                headers=self.get_headers_for_token(test_case),
            )
            self.assertEqual(403, rsp.status_code)
            deployment_dict = self.get_deployment()
            roles = deployment_dict.get(Deployment.ROLES)
            self.assertIsNotNone(roles)
            self.assertNotEqual(1, len(roles))
            for role in roles:
                self.assertNotEqual(name, role[Role.NAME])

    def test_failure_update_roles_without_permission(self):
        role_dict = role_fields()
        role_dict[Role.ID] = self.existing_role_id
        json_body = {Deployment.ROLES: [role_dict]}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json=json_body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_roles_with_unknown_permission(self):
        role_dict = role_fields(4)
        role_dict[Role.ID] = self.existing_role_id
        json_body = {Deployment.ROLES: [role_dict]}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json=json_body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_roles_invalid_deployment(self):
        role_dict = role_fields(2)
        role_dict[Role.ID] = self.existing_role_id
        json_body = {Deployment.ROLES: [role_dict]}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{INVALID_DEPLOYMENT}/role",
            json=json_body,
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)

    def test_success_create_first_role(self):
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json={Deployment.ROLES: []},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json={Deployment.ROLES: [role_fields(2)]},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_delete_user_role_deleted(self):
        key = f"{User.ROLES}.{RoleAssignment.ROLE_ID}"
        user = self.mongo_database["user"].find_one({key: self.existing_role_id})
        self.assertIsNotNone(user)
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}/role",
            json={Deployment.ROLES: []},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        user = self.mongo_database["user"].find_one({key: self.existing_role_id})
        self.assertIsNone(user)


class CloneDeploymentTestCase(AbstractDeploymentTestCase):
    base_url = "/api/extensions/v1beta/deployment/%s"

    @classmethod
    def setUpClass(cls) -> None:
        super(CloneDeploymentTestCase, cls).setUpClass()
        CloneDeploymentTestCase.upload_files()

    @staticmethod
    def upload_files():
        bucket = "integrationtests"
        keys = (
            f"deployment/{DEPLOYMENT_ID}/section/5e946c69e8002eac4a107f56/article/5e8c58176207e5f78023e655/assets/sample.png",
            f"deployment/{DEPLOYMENT_ID}/section/5e946c69e8002eac4a107f56/article/5e8c58176207e5f78023e655/assets/sample.mp4",
            f"deployment/{DEPLOYMENT_ID}/econsent/assets/sample.png",
            f"deployment/{DEPLOYMENT_ID}/econsent/assets/sample.mp4",
            f"deployment/{DEPLOYMENT_ID}/sample.png",
        )
        storage = inject.instance(FileStorageAdapter)
        for key in keys:
            file_path = Path(__file__).parent.joinpath("fixtures/sample.png")
            with open(file_path, "rb") as file:
                content = file.read()
                storage.upload_file(bucket, key, io.BytesIO(content), len(content))

    def retrieve_deployment(self, deployment_id: str = None):
        url = self.base_url % (deployment_id or self.deployment_id)
        return self.flask_client.get(url, headers=self.headers)

    def test_success_clone_deployment(self):
        rsp = self.retrieve_deployment()
        ref_dep = rsp.json

        new_name = "Cloned Deployment"
        data = {
            CloneDeploymentRequestObject.REFERENCE_ID: self.deployment_id,
            CloneDeploymentRequestObject.NAME: new_name,
        }
        rsp = self.flask_client.post(
            self.base_url % "clone", json=data, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.retrieve_deployment(rsp.json[Deployment.ID])
        cloned_dep = rsp.json

        self.assertEqual(Deployment.FIRST_VERSION, cloned_dep[Deployment.VERSION])
        self.assertEqual(new_name, cloned_dep[Deployment.NAME])

        consent = cloned_dep[Deployment.CONSENT]
        self.assertEqual(Consent.FIRST_VERSION, consent[Consent.REVISION])

        econsent = cloned_dep[Deployment.ECONSENT]
        self.assertEqual(EConsent.FIRST_VERSION, econsent[EConsent.REVISION])

        module_configs = cloned_dep[Deployment.MODULE_CONFIGS]
        ref_module_config_ids = {
            mc[ModuleConfig.ID] for mc in ref_dep[Deployment.MODULE_CONFIGS]
        }
        ref_article_ids = set()
        for section in ref_dep[Deployment.LEARN][Learn.SECTIONS]:
            for article in section[LearnSection.ARTICLES]:
                ref_article_ids.add(article[Deployment.ID])

        for mc in module_configs:
            # check if id was replaced
            self.assertNotIn(mc[ModuleConfig.ID], ref_module_config_ids)

            # check if learnArticleIds were replaced
            for article_id in mc.get(ModuleConfig.LEARN_ARTICLE_IDS) or []:
                self.assertNotIn(article_id, ref_article_ids)

        key_actions = cloned_dep[Deployment.KEY_ACTIONS]
        for ka in key_actions:
            # check if moduleConfigId was replaced
            config_id = ka.get(KeyAction.moduleConfigId)
            self.assertNotIn(config_id, ref_module_config_ids)

            # check if articleId was replaced
            article_id = ka.get(KeyAction.LEARN_ARTICLE_ID)
            self.assertNotIn(article_id, ref_article_ids)


class ReorderEndpointsTestCase(AbstractDeploymentTestCase):
    def _reorder_and_get_deployment_data(self, url_item: str, body: list[dict]):
        deployment_id = "5d386cc6ff885918d96edb2c"
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{deployment_id}/{url_item}/reorder",
            headers=self.headers,
            json=body,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual([i[OrderUpdateObject.ID] for i in body], rsp.json)

        return self.flask_client.get(
            f"{self.deployment_route}/deployment/{deployment_id}",
            headers=self.headers,
        )

    def test_success_reorder_sections(self):
        body = [
            {
                OrderUpdateObject.ID: "5e946c69e8002eac4a107f56",
                OrderUpdateObject.ORDER: 1,
            }
        ]

        get_rsp = self._reorder_and_get_deployment_data("learn-section", body)
        learn_sections = get_rsp.json[Deployment.LEARN][Learn.SECTIONS]
        self.assertEqual(1, learn_sections[0][LearnSection.ORDER])

    def test_success_reorder_module_configs(self):
        body = [
            {
                OrderUpdateObject.ID: "5e94b2007773091c9a592650",
                OrderUpdateObject.ORDER: 1,
            }
        ]
        get_rsp = self._reorder_and_get_deployment_data("module-config", body)
        module_configs = get_rsp.json[Deployment.MODULE_CONFIGS]
        self.assertEqual(1, module_configs[0][ModuleConfig.ORDER])

    def test_success_reorder_onboarding_module_configs(self):
        body = [
            {
                OrderUpdateObject.ID: "604c89573a295dad259abb03",
                OrderUpdateObject.ORDER: 1,
            },
            {
                OrderUpdateObject.ID: "604c895da1adf357ed1fe15f",
                OrderUpdateObject.ORDER: 2,
            },
        ]

        get_rsp = self._reorder_and_get_deployment_data(
            "onboarding-module-config", body
        )
        module_configs = get_rsp.json[Deployment.ONBOARDING_CONFIGS]
        self.assertEqual(1, module_configs[0][OnboardingModuleConfig.ORDER])
        self.assertEqual(2, module_configs[1][OnboardingModuleConfig.ORDER])

    def test_success_reorder_articles(self):
        section_id = "5e946c69e8002eac4a107f56"
        body = [
            {
                OrderUpdateObject.ID: "5e8c58176207e5f78023e655",
                OrderUpdateObject.ORDER: 1,
            }
        ]

        get_rsp = self._reorder_and_get_deployment_data(
            f"learn-section/{section_id}/article", body
        )
        learn_articles = get_rsp.json[Deployment.LEARN][Learn.SECTIONS][0][
            LearnSection.ARTICLES
        ]
        self.assertEqual(1, learn_articles[0][LearnArticle.ORDER])


class RetrieveLocalizableFieldsTestCase(AbstractDeploymentTestCase):
    def test_success_retrieve_localizable_keys(self):
        expected_res = [
            "deployment.moduleConfigs.notificationData.body",
            "deployment.consent.review.title",
            "deployment.econsent.signature.nameDetails",
            "deployment.econsent.overviewText",
            "deployment.econsent.signature.signatureDetails",
            "deployment.profile.fields.ethnicityOptions.displayName",
            "deployment.learn.sections.title",
            "deployment.features.messaging.messages",
            "deployment.consent.signature.signatureDetails",
            "deployment.consent.review.details",
            "deployment.econsent.sections.details",
            "deployment.moduleConfigs.about",
            "deployment.econsent.sections.title",
            "deployment.econsent.contactText",
            "deployment.moduleConfigs.notificationData.title",
            "deployment.learn.sections.articles.title",
            "deployment.consent.signature.signatureTitle",
            "deployment.econsent.additionalConsentQuestions.text",
            "deployment.econsent.review.title",
            "deployment.consent.additionalConsentQuestions.text",
            "deployment.consent.sections.details",
            "deployment.consent.signature.nameTitle",
            "deployment.econsent.review.details",
            "deployment.profile.fields.genderOptions.displayName",
            "deployment.econsent.sections.reviewDetails",
            "deployment.econsent.signature.signatureTitle",
            "deployment.keyActions.title",
            "deployment.econsent.title",
            "deployment.keyActions.description",
            "deployment.econsent.signature.nameTitle",
            "deployment.consent.signature.nameDetails",
            "deployment.consent.sections.reviewDetails",
            "deployment.extraCustomFields.mediclinicNumber.errorMessage",
            "deployment.extraCustomFields.mediclinicNumber.onboardingCollectionText",
            "deployment.extraCustomFields.mediclinicNumber.profileCollectionText",
            "deployment.moduleConfigs.configBody.name",
            "deployment.moduleConfigs.configBody.trademarkText",
            "deployment.moduleConfigs.configBody.submissionPage.text",
            "deployment.moduleConfigs.configBody.submissionPage.buttonText",
            "deployment.moduleConfigs.configBody.pages.name",
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
            "deployment.moduleConfigs.configBody.pages.complexSymptoms.scale.value",
            "deployment.moduleConfigs.configBody.pages.complexSymptoms.name",
            "deployment.symptom.ragThresholds.fieldName",
        ]

        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/localizable-fields",
            headers=self.headers,
        )
        for item in expected_res:
            self.assertIn(item, rsp.json)

    def test_failure_retrieve_localizable_keys_deployment_does_not_exist(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/61a4780f4d2e7e719180d10d/localizable-fields",
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(DeploymentErrorCodes.INVALID_DEPLOYMENT_ID, rsp.json["code"])

    def test_success_generate_master_translation(self):
        collection_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        initial_deployment_data = self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(self.deployment_id)}
        )

        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/{self.deployment_id}/generate-master-translation",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        expected_res = {
            "hu_azscreeningquestionnaire_about": "string",
            "hu_bloodpressure_about": "string",
            "hu_bloodpressure_notificationData_body": "someBody",
            "hu_bloodpressure_notificationData_title": "someTitle",
            "hu_consent_additionalConsentQuestions_0_text": "Would you like your data to be used in future studies?",
            "hu_consent_review_details": "please review the form below, and tap agree if you are ready to continue. if you have any questions or queries, please contact us at support@medopad.com",
            "hu_consent_review_title": "review",
            "hu_consent_sections_0_details": "",
            "hu_consent_sections_0_reviewDetails": "",
            "hu_consent_sections_1_details": "string",
            "hu_consent_sections_1_reviewDetails": "string",
            "hu_consent_signature_nameDetails": "type your full name in text fields below",
            "hu_consent_signature_nameTitle": "medopad consent",
            "hu_consent_signature_signatureDetails": "please sign using your finger in the box below",
            "hu_consent_signature_signatureTitle": "signature",
            "hu_econsent_additionalConsentQuestions_0_text": "Would you like your data to be used in future studies?",
            "hu_econsent_additionalConsentQuestions_1_text": "Do you allow the research investigators to retrieve your data from the vaccine registry?",
            "hu_econsent_contactText": "Please contact your study team at contact@studyteam.com if you have any questions.",
            "hu_econsent_overviewText": "To participate in the trial study, please read  the consent form through in detail. \n\nIf you have any questions, please contact your study team at studyteam@reallylongemail.com or +44 1234 567 890 providing your consent to participate.",
            "hu_econsent_review_details": "please review the form below, and tap agree if you are ready to continue. if you have any questions or queries, please contact us at support@medopad.com",
            "hu_econsent_review_title": "review",
            "hu_econsent_sections_0_details": "INTRODUCTION",
            "hu_econsent_sections_0_reviewDetails": "You have been asked to participate in a clinical research study initiated, managed, and financed by ABC LAbs, who is the Sponsor of this study. Before your decide, it is important for you to understand why the research is being done and what it will involve. This informed consent form will provide you with essential information about this study and your rights as a study participant so that you can make an informed decision about your participation. Y \nYour decision to participate in this study is entirely voluntary. You will not lose any benefits to which you would otherwise be entitled if you refuse to participant. In addition, you may withdraw from the study at any time without penality or loss of benefits to which you are otherwise entitled. You will be informed in a timely manner, if any relevant new information about this drug or this study becomes available that may alter your willingness to continue to participate. If you agree, your General Practitioner will be told that you are taking part in this study.",
            "hu_econsent_sections_0_title": "Introduction",
            "hu_econsent_sections_1_reviewDetails": "You are being asked to participate in this clinical research study because you have high blood pressure and are already taking prescribed commercial Cligoliob for an approved dose and indication in your countr.\nYou are eligible to participate in this study because following discussions with your own doctor you have decided to continue taking Cigoliob.\nInformation regarding the use of Cigoliob may be obtained from the patient information leaflet which accompanies your supply of Cigoliob and from your own treating physician.\nThe purpose of this study is to assess the levels of Cigoliob in blood across the course of the study in study participants with high blood pressure.\nThis study is expected to enroll approximately 100 women who have high blood pressure while takingcommercial Cigoliob across approximately 13 centers throughout Canada, USA, Swizerland and selected countries in the European Union (possible including but not necessarily limited to France, Germany, Spain or Italy).",
            "hu_econsent_sections_1_title": "PURPOSE",
            "hu_econsent_sections_2_reviewDetails": "I have read and understood this consent document. By signing this:\u2028\n• I confirm that I have had time to read carefully and understand the study participant informed consent provided for this study.\n• I confirm that I have had the opportunity to discuss the study and ask questions, and I am satisfied with the answers and explanations that I have been provided.\n• I give permission for my medical records to be reviewed by the Sponsor or designee and/or representatives of any Drug Reculatory Authorities such as the U.S. FDA and Insitutional Review Boards.\n• I understand that my participation is voluntary and that I am free to withdraw at any time without giving any reason and without my medical care or legal rights being affected.. I agree that the Sponsor can continue to use the information about my health collected during the study to preserve the integrity of the study, even if I withdraw from the study.",
            "hu_econsent_sections_2_title": "REVIEW_TO_SIGN",
            "hu_econsent_sections_3_reviewDetails": "During the course of this trial, you’ll be asked to complete a series of task such as:\n• Entering your blood pressure in the morning every day in the Huma app\n•Recording your medication intake in the Huma app\n• Attending telemedicine video conferences with your study care team in the Huma app\n• Attending face-to-face appointments with your study care team every 3 months\nThere are some acitivites that you would not be able to do during the course of the trial. They are:\n• Donating blood\n• Traveling via plane or helicopter",
            "hu_econsent_sections_3_title": "DURING_THE_TRIAL",
            "hu_econsent_signature_nameDetails": "Type your full name in text fields below",
            "hu_econsent_signature_nameTitle": "Medopad Consent",
            "hu_econsent_signature_signatureDetails": "Please sign using your finger in the box below",
            "hu_econsent_signature_signatureTitle": "Signature",
            "hu_econsent_title": "Informed consent form",
            "hu_extraCustomFields_mediclinicNumber_description": "Please enter mediclinic number description",
            "hu_extraCustomFields_mediclinicNumber_errorMessage": "Insurance Number is incorrect",
            "hu_extraCustomFields_mediclinicNumber_onboardingCollectionText": "Please enter mediclinic number",
            "hu_extraCustomFields_mediclinicNumber_profileCollectionText": "Patient Unique ID",
            "hu_features_messaging_messages_0": "Great job! Keep up the good work.",
            "hu_features_messaging_messages_1": "second message",
            "hu_keyActions_0_description": "You have a new activity for the DeTAP study. Please complete as soon as you are able to.",
            "hu_keyActions_0_title": "PAM Questionnaire",
            "hu_keyActions_1_description": "You have a new activity for the DeTAP study. Please complete as soon as you are able to.",
            "hu_keyActions_1_title": "Article KA",
            "hu_learn_sections_0_articles_0_title": "article_ss three",
            "hu_learn_sections_0_title": "Test section",
            "hu_profile_fields_ethnicityOptions_0_displayName": "alien",
            "hu_profile_fields_genderOptions_0_displayName": "male",
            "hu_profile_fields_genderOptions_1_displayName": "female",
            "hu_profile_fields_genderOptions_2_displayName": "other",
            "hu_questionnaire_about": "test",
            "hu_questionnaire_complexSymptoms_0_name": "Chills",
            "hu_questionnaire_complexSymptoms_0_scale_0_value": "never",
            "hu_questionnaire_complexSymptoms_0_scale_1_value": "seldom",
            "hu_questionnaire_name": "Awesome Name in ConfigBody",
            "hu_symptom_about": "string",
            "hu_symptom_complexSymptoms_0_name": "Symptom rag field name",
            "hu_symptom_complexSymptoms_0_scale_0_value": "mild",
            "hu_symptom_complexSymptoms_0_scale_1_value": "severe",
        }
        self.maxDiff = None
        self.assertEqual(expected_res, rsp.json)

        # make sure that initial deployment has been updated
        db_res = self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(self.deployment_id)}
        )
        self.assertNotEqual(initial_deployment_data, db_res)
        self.assertEqual(expected_res, db_res[Deployment.LOCALIZATIONS][Language.EN])
        self._validate_object_ids_and_datetime(db_res)

        # verify that deployment revision has been added
        revision_collection = MongoDeploymentRepository.DEPLOYMENT_REVISION_COLLECTION
        revision_db_res = self.mongo_database[revision_collection].find_one(
            {
                DeploymentRevision.DEPLOYMENT_ID: ObjectId(self.deployment_id),
                DeploymentRevision.CHANGE_TYPE: ChangeType.MULTI_LANGUAGE_CONVERSION.value,
            }
        )
        self._validate_object_ids_and_datetime(revision_db_res)
        self.assertIsNotNone(revision_db_res)
        self.assertEqual(
            initial_deployment_data, revision_db_res[DeploymentRevision.SNAP]
        )
        self.assertEqual(
            ChangeType.MULTI_LANGUAGE_CONVERSION.value,
            revision_db_res[DeploymentRevision.CHANGE_TYPE],
        )

    def _validate_object_ids_and_datetime(self, d: Union[dict, list]):
        if isinstance(d, dict):
            for key, value in d.items():
                if key == "id":
                    self.assertTrue(type(value) == ObjectId)
                elif key == "updateDateTime" or key == "createDateTime":
                    self.assertTrue(type(value) == datetime.datetime)
                self._validate_object_ids_and_datetime(value)
        elif isinstance(d, list):
            for item in d:
                self._validate_object_ids_and_datetime(item)

    def test_failure_generate_master_translation_non_existing_deployment(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/61a4780f4d2e7e719180d10d/generate-master-translation",
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(DeploymentErrorCodes.INVALID_DEPLOYMENT_ID, rsp.json["code"])


class RetrieveDeploymentKeyActionsTestCase(AbstractDeploymentTestCase):
    url = f"/api/extensions/v1beta/deployment/{DEPLOYMENT_ID}/key-actions"
    request_object = RetrieveDeploymentKeyActionsRequestObject

    def retrieve_and_test_deployment_key_actions_today_with_user_type(
        self, user_id: str
    ):
        start_dt = "2021-12-13T00:00:26.255616Z"
        trigger_dt = "2021-12-24T08:00:00.000000Z"
        end_dt = "2021-12-25T00:00:26.255616Z"

        payload = self.payload(start_dt, end_dt)
        with freeze_time(get_dt_from_str(trigger_dt)):
            headers = self.get_headers_for_token(user_id)
            rsp = self.flask_client.post(self.url, json=payload, headers=headers)
            self.assertEqual(200, rsp.status_code)

        events = rsp.json["events"]
        self.assertEqual(2, len(events))

        required_keys_in_output = DeploymentEvent.__annotations__.keys()

        date_key = DeploymentEvent.START_DATE_TIME
        for event in events:
            self.assertTrue(set(required_keys_in_output).issubset(event.keys()))
            self.assertStrDateLess(start_dt, event[date_key])
            self.assertStrDateLess(event[date_key], end_dt)

        self.assertEqual(
            "5e8c58176207e5f78023e655", events[-1][DeploymentEvent.LEARN_ARTICLE_ID]
        )

    def test_success_retrieve_deployment_key_actions_today_by_huma_support(self):
        self.retrieve_and_test_deployment_key_actions_today_with_user_type(
            HUMA_SUPPORT_USER_ID
        )

    def test_success_retrieve_deployment_key_actions_today_by_super_admin(self):
        self.retrieve_and_test_deployment_key_actions_today_with_user_type(
            VALID_SUPER_ADMIN_ID
        )

    def test_success_retrieve_deployment_key_actions_custom_trigger(self):
        start_dt = "2021-12-13T00:00:26.255616Z"
        trigger_dt = "2021-12-23T08:00:00.000000Z"
        end_dt = "2021-12-25T00:00:26.255616Z"

        payload = self.payload(start_dt, end_dt)
        payload.update({self.request_object.TRIGGER_TIME: trigger_dt})
        headers = self.get_headers_for_token(HUMA_SUPPORT_USER_ID)
        rsp = self.flask_client.post(self.url, json=payload, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json["events"]))

    def payload(self, start_dt: str, end_dt: str):
        return {
            self.request_object.DEPLOYMENT_ID: DEPLOYMENT_ID,
            self.request_object.START_DATE: start_dt,
            self.request_object.END_DATE: end_dt,
        }

    def assertStrDateLess(self, a, b, msg=None):
        a, b = get_dt_from_str(a), get_dt_from_str(b)
        self.assertLess(a, b, msg)


class CreateMultipleModuleConfigsTestCase(AbstractDeploymentTestCase):
    url = f"/api/extensions/v1beta/deployment/{DEPLOYMENT_ID}/module-configs"

    def retrieve_deployment_from_db(self, deployment_id: str = DEPLOYMENT_ID):
        collection_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        return self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(deployment_id)}
        )

    def test_success_add_multiple_module_configs__creation(self):
        deployment_before_update = self.retrieve_deployment_from_db()

        headers = self.get_headers_for_token(HUMA_SUPPORT_USER_ID)
        payload = {
            Deployment.MODULE_CONFIGS: [
                simple_module_config(),
                module_config_with_config_body(),
            ]
        }
        rsp = self.flask_client.post(self.url, json=payload, headers=headers)
        self.assertEqual(200, rsp.status_code)

        deployment_after_update = self.retrieve_deployment_from_db()
        self.assertEqual(
            len(deployment_after_update[Deployment.MODULE_CONFIGS]),
            len(deployment_before_update[Deployment.MODULE_CONFIGS]) + 2,
        )

        for config in deployment_after_update[Deployment.MODULE_CONFIGS]:
            self.assertTrue(isinstance(config[ModuleConfig.ID], ObjectId))

    def test_failure_add_multiple_module_configs__permission_denied(self):
        headers = self.get_headers_for_token(VALID_USER_ID)
        payload = {
            Deployment.MODULE_CONFIGS: [
                simple_module_config(),
                module_config_with_config_body(),
            ]
        }
        rsp = self.flask_client.post(self.url, json=payload, headers=headers)
        self.assertEqual(403, rsp.status_code)


class DeploymentTemplateTestCase(AbstractDeploymentTestCase):
    create_url = f"/api/extensions/v1beta/deployment/template"
    retrieve_templates = f"/api/extensions/v1beta/deployment/templates"
    retrieve_template = create_url
    collection_name = MongoDeploymentTemplateModel._meta.get("collection")

    def test_create_template_by_super_admin_and_huma_support__allowed_categories(self):
        user_ids_to_test = [VALID_SUPER_ADMIN_ID, HUMA_SUPPORT_USER_ID]
        sample_deployment = modified_deployment()
        sample_deployment[Deployment.DESCRIPTION] = "deployment description"

        for user_id in user_ids_to_test:
            headers = self.get_headers_for_token(user_id)
            for category in self._categories_for_super_admin_and_huma_support():
                payload = self._sample_template_payload(category, sample_deployment)
                rsp = self.flask_client.post(
                    self.create_url, json=payload, headers=headers
                )
                self.assertEqual(201, rsp.status_code)

                template_id = rsp.json[DeploymentTemplate.ID]
                template = self.mongo_database[self.collection_name].find_one(
                    {DeploymentTemplate.ID_: ObjectId(template_id)}
                )
                self.assertEqual(
                    EnableStatus.ENABLED.value, template[DeploymentTemplate.STATUS]
                )
                # other fields should be filtered as we do not need them in template
                expected_template = {
                    Deployment.DESCRIPTION: "deployment description",
                    Deployment.STATUS: Status.DRAFT.value,
                    Deployment.LABELS: [],
                    Deployment.FEATURES: {
                        Features.APP_MENU: [
                            AppMenuItem.CARE_PLAN.value,
                            AppMenuItem.KEY_ACTIONS.value,
                            AppMenuItem.LEARN.value,
                            AppMenuItem.PROFILE.value,
                        ],
                        Features.APPOINTMENT: False,
                        Features.CARE_PLAN_DAILY_ADHERENCE: False,
                        Features.OFF_BOARDING_REASONS: {
                            OffBoardingReasons.REASONS: Reason._default_reasons(),
                            OffBoardingReasons.OTHER_REASON: True,
                        },
                        Features.LABELS: False,
                        Features.HEALTH_DEVICE_INTEGRATION: False,
                        Features.OFF_BOARDING: False,
                        Features.PERSONAL_DOCUMENTS: False,
                        Features.PROXY: False,
                        Features.PORTAL: {},
                        Features.HIDE_APP_SUPPORT: False,
                        Features.LINK_INVITES: False,
                        Features.PERSONALIZED_CONFIG: False,
                    },
                }
                self.assertDictEqual(
                    expected_template, template[DeploymentTemplate.TEMPLATE]
                )

    def test_failure_create_template_by_super_admin_and_huma_support__not_allowed_categories(
        self,
    ):
        user_ids_to_test = [VALID_SUPER_ADMIN_ID, HUMA_SUPPORT_USER_ID]
        sample_deployment = modified_deployment()
        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value, sample_deployment
        )
        for user_id in user_ids_to_test:
            headers = self.get_headers_for_token(user_id)
            rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_success_create_template_by_account_manager(self):
        sample_deployment = modified_deployment()
        sample_deployment[Deployment.DESCRIPTION] = "deployment description"
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value, sample_deployment, [ORG_ID]
        )
        rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_template_by_account_manager__not_in_org(self):
        sample_deployment = modified_deployment()
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value,
            sample_deployment,
            ["61f25c07e0bcb1612c1426f4"],
        )
        rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_template_by_account_manager__is_verified(self):
        sample_deployment = modified_deployment()
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value, sample_deployment, [ORG_ID], True
        )
        rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_template_by_account_manager__not_allowed_category(self):
        sample_deployment = modified_deployment()
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        for category in self._categories_for_super_admin_and_huma_support():
            payload = self._sample_template_payload(
                category, sample_deployment, [ORG_ID]
            )
            rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_failure_create_template__not_allowed_roles(self):
        sample_deployment = modified_deployment()
        roles_to_test = [
            VALID_USER_ID,
            VALID_MANAGER_ID,
            VALID_CONTRIBUTOR_ID,
            VALID_CUSTOM_ROLE_ID,
            ORGANIZATION_OWNER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
        ]
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            payload = self._sample_template_payload(
                TemplateCategory.SELF_SERVICE.value, sample_deployment, []
            )
            rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_deployment_templates_by_allowed_roles(self):
        allowed_user_ids = [
            ACCOUNT_MANAGER_USER_ID,
            HUMA_SUPPORT_USER_ID,
            VALID_SUPER_ADMIN_ID,
            ORGANIZATION_EDITOR_USER_ID,
            ORGANIZATION_OWNER_USER_ID,
        ]
        self._create_sample_deployment_template([ORG_ID])
        for user_id in allowed_user_ids:
            headers = self.get_headers_for_token(user_id)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.get(self.retrieve_templates, headers=headers)
            self.assertEqual(200, rsp.status_code)
            self.assertEqual(1, len(rsp.json["templates"]))

    def test_failure_retrieve_deployment_templates__user_not_part_of_org(self):
        roles_to_test = [
            ACCOUNT_MANAGER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
            ORGANIZATION_OWNER_USER_ID,
        ]
        self._create_sample_deployment_template([ORG_ID])
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": str(ObjectId())})
            rsp = self.flask_client.get(self.retrieve_templates, headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_failure_retrieve_templates__not_allowed_roles(self):
        roles_to_test = [
            VALID_USER_ID,
            VALID_MANAGER_ID,
            VALID_CONTRIBUTOR_ID,
            VALID_CUSTOM_ROLE_ID,
        ]
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.get(self.retrieve_templates, headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_templates_filtered_by_org(self):
        roles_to_test = [
            ACCOUNT_MANAGER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
            ORGANIZATION_OWNER_USER_ID,
        ]
        self._create_sample_deployment_template([ORG_ID])
        self._create_sample_deployment_template([str(ObjectId())])
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.get(self.retrieve_templates, headers=headers)
            self.assertEqual(200, rsp.status_code)
            # second template should be filtered as user is not part of the org
            self.assertEqual(1, len(rsp.json["templates"]))

    def test_success_retrieve_template(self):
        allowed_user_ids = [
            ACCOUNT_MANAGER_USER_ID,
            HUMA_SUPPORT_USER_ID,
            VALID_SUPER_ADMIN_ID,
            ORGANIZATION_EDITOR_USER_ID,
            ORGANIZATION_OWNER_USER_ID,
        ]
        created_id = self._create_sample_deployment_template([ORG_ID])
        for user_id in allowed_user_ids:
            headers = self.get_headers_for_token(user_id)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.get(
                f"{self.create_url}/{created_id}", headers=headers
            )
            self.assertEqual(200, rsp.status_code)
            self.assertIsNotNone(rsp.json)

    def test_failure_retrieve_template__user_is_not_part_of_org(self):
        roles_to_test = [
            ACCOUNT_MANAGER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
            ORGANIZATION_OWNER_USER_ID,
        ]
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": str(ObjectId())})
            rsp = self.flask_client.get(
                f"{self.create_url}/{str(ObjectId())}", headers=headers
            )
            self.assertEqual(403, rsp.status_code)

    def test_failure_retrieve_template__not_allowed_roles(self):
        roles_to_test = [
            VALID_USER_ID,
            VALID_MANAGER_ID,
            VALID_CONTRIBUTOR_ID,
            VALID_CUSTOM_ROLE_ID,
        ]
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.get(f"{self.create_url}/{ORG_ID}", headers=headers)
            self.assertEqual(403, rsp.status_code)

    def test_success_delete_template(self):
        roles_to_test = [
            HUMA_SUPPORT_USER_ID,
            VALID_SUPER_ADMIN_ID,
        ]
        for role in roles_to_test:
            template_id = self._create_sample_deployment_template([ORG_ID])
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.delete(
                f"{self.create_url}/{template_id}", headers=headers
            )
            self.assertEqual(204, rsp.status_code)

        # testing separately as account manager as he has a bit different permissions
        template_id = self._create_sample_deployment_template(
            [ORG_ID], ACCOUNT_MANAGER_USER_ID, TemplateCategory.SELF_SERVICE.value
        )
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        headers.update({"x-org-id": ORG_ID})
        rsp = self.flask_client.delete(
            f"{self.create_url}/{template_id}", headers=headers
        )
        self.assertEqual(204, rsp.status_code)

    def test_failure_delete_template__not_allowed_roles(self):
        roles_to_test = [
            VALID_USER_ID,
            VALID_MANAGER_ID,
            VALID_CONTRIBUTOR_ID,
            VALID_CUSTOM_ROLE_ID,
            ORGANIZATION_OWNER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
        ]
        template_id = self._create_sample_deployment_template([ORG_ID])
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            rsp = self.flask_client.delete(
                f"{self.create_url}/{template_id}", headers=headers
            )
            self.assertEqual(403, rsp.status_code)

    def test_failure_delete_template__account_manager_cases(self):
        # trying to delete not self_service category
        template_id = self._create_sample_deployment_template([ORG_ID])
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        headers.update({"x-org-id": ORG_ID})
        rsp = self.flask_client.delete(
            f"{self.create_url}/{template_id}", headers=headers
        )
        self.assertEqual(403, rsp.status_code)

        # trying to delete not own org
        org_id = "61dfd4575e82e1f92a8f932d"
        template_id = self._create_sample_deployment_template([org_id])
        headers.update({"x-org-id": ORG_ID})
        rsp = self.flask_client.delete(
            f"{self.create_url}/{template_id}", headers=headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_update_deployment_template(self):
        template_id = self._create_sample_deployment_template([ORG_ID])
        sample_deployment = modified_deployment()
        payload = self._sample_template_payload(
            TemplateCategory.CARDIOVASCULAR.value, sample_deployment, [ORG_ID]
        )
        roles_to_test = [
            HUMA_SUPPORT_USER_ID,
            VALID_SUPER_ADMIN_ID,
        ]
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            payload[DeploymentTemplate.NAME] = "UPDATED NAME"
            rsp = self.flask_client.put(
                f"{self.create_url}/{template_id}", headers=headers, json=payload
            )
            self.assertEqual(200, rsp.status_code)

            updated_template = self._retrieve_template_by_id(template_id)
            self.assertEqual(payload[DeploymentTemplate.NAME], updated_template.name)

        # testing separately as account manager as he has a bit different permissions
        template_id = self._create_sample_deployment_template(
            [ORG_ID], ACCOUNT_MANAGER_USER_ID, TemplateCategory.SELF_SERVICE.value
        )
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        headers.update({"x-org-id": ORG_ID})

        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value, sample_deployment, [ORG_ID]
        )
        payload[DeploymentTemplate.NAME] = "UPDATED NAME"
        rsp = self.flask_client.put(
            f"{self.create_url}/{template_id}", headers=headers, json=payload
        )
        self.assertEqual(200, rsp.status_code)
        updated_template = self._retrieve_template_by_id(template_id)
        self.assertEqual(payload[DeploymentTemplate.NAME], updated_template.name)

    def test_failure_update_template_account_manager_cases(self):
        # trying to update template that was not initially SELF SERVICE and set it to SELF SERVICE
        template_id = self._create_sample_deployment_template([ORG_ID])
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_USER_ID)
        headers.update({"x-org-id": ORG_ID})
        sample_deployment = modified_deployment()
        payload = self._sample_template_payload(
            TemplateCategory.SELF_SERVICE.value, sample_deployment, [ORG_ID]
        )
        rsp = self.flask_client.put(
            f"{self.create_url}/{template_id}", headers=headers, json=payload
        )
        self.assertEqual(403, rsp.status_code)

        # trying to update template passing not allowed categories
        template_id = self._create_sample_deployment_template(
            [ORG_ID],
            user_id=ACCOUNT_MANAGER_USER_ID,
            category=TemplateCategory.SELF_SERVICE.value,
        )
        not_allowed_categories = self._categories_for_super_admin_and_huma_support()
        for category in not_allowed_categories:
            payload = self._sample_template_payload(
                category, sample_deployment, [ORG_ID]
            )
            rsp = self.flask_client.put(
                f"{self.create_url}/{template_id}", headers=headers, json=payload
            )
            self.assertEqual(403, rsp.status_code)

    def test_failure_update_template__not_allowed_roles(self):
        roles_to_test = [
            VALID_USER_ID,
            VALID_MANAGER_ID,
            VALID_CONTRIBUTOR_ID,
            VALID_CUSTOM_ROLE_ID,
            ORGANIZATION_OWNER_USER_ID,
            ORGANIZATION_EDITOR_USER_ID,
        ]
        template_id = self._create_sample_deployment_template([ORG_ID])
        sample_deployment = modified_deployment()
        for role in roles_to_test:
            headers = self.get_headers_for_token(role)
            headers.update({"x-org-id": ORG_ID})
            payload = self._sample_template_payload(
                TemplateCategory.SELF_SERVICE.value, sample_deployment, [ORG_ID]
            )
            rsp = self.flask_client.put(
                f"{self.create_url}/{template_id}", headers=headers, json=payload
            )
            self.assertEqual(403, rsp.status_code)

    @staticmethod
    def _retrieve_template_by_id(template_id: str) -> DeploymentTemplate:
        updated_template = MongoDeploymentTemplateModel.objects(id=template_id).first()
        return DeploymentTemplate.from_dict(updated_template.to_dict())

    @staticmethod
    def _sample_template_payload(
        category: str,
        template: dict,
        organization_ids: list = None,
        is_verified: bool = False,
    ) -> dict:
        if not organization_ids:
            organization_ids = []
        return {
            DeploymentTemplate.NAME: "sample template name",
            DeploymentTemplate.DESCRIPTION: "description",
            DeploymentTemplate.ORGANIZATION_IDS: organization_ids,
            DeploymentTemplate.CATEGORY: category,
            DeploymentTemplate.TEMPLATE: template,
            DeploymentTemplate.IS_VERIFIED: is_verified,
        }

    @staticmethod
    def _categories_for_super_admin_and_huma_support() -> list[str]:
        return [
            TemplateCategory.CARDIOVASCULAR.value,
            TemplateCategory.METABOLIC.value,
            TemplateCategory.RESPIRATORY.value,
            TemplateCategory.NEUROLOGY.value,
            TemplateCategory.MUSCULOSKELETAL.value,
            TemplateCategory.INFECTIOUS_DISEASES.value,
        ]

    def _create_sample_deployment_template(
        self,
        org_ids: list[str],
        user_id: str = VALID_SUPER_ADMIN_ID,
        category: str = TemplateCategory.CARDIOVASCULAR.value,
    ) -> str:
        sample_deployment = modified_deployment()
        sample_deployment[Deployment.DESCRIPTION] = "deployment description"
        headers = self.get_headers_for_token(user_id)
        payload = self._sample_template_payload(category, sample_deployment, org_ids)
        rsp = self.flask_client.post(self.create_url, json=payload, headers=headers)
        return rsp.json["id"]


USER_ID_1 = "5eda5db67adadfb46f7ff71d"
USER_ID_2 = "5eda5e367adadfb46f7ff71f"
USER_ID_3 = "5eda5e367adadfb46f7ff71b"
USER_ID_FROM_OTHER_DEPLOYMENT = "5ffee8a004ae8ffa8e721114"

PREDEFINED_MESSAGE = "first message"


class DeploymentInboxTestCase(AbstractDeploymentTestCase):
    @staticmethod
    def _model_send_bulk_message_request(
        text: str, user_list: list[str], custom: bool = None, send_to_all: bool = False
    ):
        body = remove_none_values({Message.TEXT: text, Message.CUSTOM: custom})
        body["userIds"] = user_list
        body["allUsers"] = send_to_all

        return body

    def _send_bulk_message(
        self,
        sender_id: str,
        receiver_ids: list[str],
        message_body: str,
        custom: bool = False,
        send_to_all: bool = False,
    ):
        body = self._model_send_bulk_message_request(
            message_body, receiver_ids, custom, send_to_all
        )
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/deployment/user/message/send",
            headers=self.get_headers_for_token(sender_id),
            json=body,
        )
        return rsp

    def _receive_messages(
        self,
        sender_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        custom: bool = False,
    ):
        body = {
            MessageSearchRequestObject.SUBMITTER_ID: sender_id,
            MessageSearchRequestObject.SKIP: skip,
            MessageSearchRequestObject.LIMIT: limit,
            MessageSearchRequestObject.CUSTOM: custom,
        }
        rsp = self.flask_client.post(
            f"/api/inbox/v1beta/user/{user_id}/message/search",
            headers=self.get_headers_for_token(sender_id),
            json=body,
        )
        return rsp

    def test_send_bulk_message(self):
        rsp = self._send_bulk_message(
            USER_ID_1, [USER_ID_2, USER_ID_3], PREDEFINED_MESSAGE
        )
        self.assertEqual(201, rsp.status_code)

    def test_send_bulk_message_to_other_deployments(self):
        rsp = self._send_bulk_message(
            USER_ID_1,
            [USER_ID_2, USER_ID_FROM_OTHER_DEPLOYMENT],
            PREDEFINED_MESSAGE,
        )
        self.assertEqual(403, rsp.status_code)

    def test_send_bulk_and_search_messages(self):

        rsp = self._send_bulk_message(
            USER_ID_1, [USER_ID_2, USER_ID_3], PREDEFINED_MESSAGE
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self._receive_messages(USER_ID_1, USER_ID_2)
        self.assertEqual(200, rsp.status_code)

        rsp = self._receive_messages(USER_ID_1, USER_ID_3)
        self.assertEqual(200, rsp.status_code)

        messages = rsp.json[MessageSearchResponseObject.MESSAGES]
        senders = set([m[Message.SUBMITTER_ID] for m in messages])
        self.assertEqual(1, len(senders))
        self.assertIn(USER_ID_1, senders)

        receivers = set([m[Message.USER_ID] for m in messages])
        self.assertEqual(1, len(receivers))
        self.assertIn(USER_ID_3, receivers)

        message_bodies = set([m[Message.TEXT] for m in messages])
        self.assertIn(PREDEFINED_MESSAGE, message_bodies)

    def test_send_bulk_message_to_all(self):
        rsp = self._send_bulk_message(
            USER_ID_1, [], PREDEFINED_MESSAGE, send_to_all=True
        )
        self.assertEqual(201, rsp.status_code)


class DeploymentLabelsTestCase(AbstractDeploymentTestCase):

    DEPLOYMENT_NO_LABEL = "5d386cc6ff885918d96edb1a"
    DEPLOYMENT_LABEL_ENABLED = "5d386cc6ff885918d96edb2c"
    DEPLOYMENT_MULTIPLE_LABEL = "612f153c1a297695e4506d53"

    SUPER_ADMIN_ID = "5e8f0c74b50aa9656c34789b"
    DEPLOYMENT_LABEL_ENABLED_ADMIN_ID = "5ffca6d91882ddc1cd8ab94f"
    DEPLOYMENT_NO_LABEL_ADMIN_ID = "5eda5db67adadfb46f7ff71d"
    DEPLOYMENT_MULTIPLE_LABEL_ADMIN_ID = "5eda5db67adadfb49f7ff71d"

    SAMPLE_LABEL_ID = "5d386cc6ff885918d96edb2c"
    WRONG_LABEL_ID = "5e8f0c74b50aa9656c34789b"

    def setUp(self):
        super().setUp()
        self.super_admin_headers = self.get_headers_for_token(self.SUPER_ADMIN_ID)
        self.label_enabled_admin_headers = self.get_headers_for_token(
            self.DEPLOYMENT_LABEL_ENABLED_ADMIN_ID
        )
        self.label_disabled_admin_headers = self.get_headers_for_token(
            self.DEPLOYMENT_NO_LABEL_ADMIN_ID
        )
        self.multiple_labels_admin_headers = self.get_headers_for_token(
            self.DEPLOYMENT_MULTIPLE_LABEL_ADMIN_ID
        )

    def test_success_retrieve_labels(self):
        get_rsp = self._retrieve_deployment_labels(self.DEPLOYMENT_MULTIPLE_LABEL)
        self.assertEqual(200, get_rsp.status_code)
        deployment_labels = get_rsp.json
        self.assertEqual(2, len(deployment_labels))
        count_dict = {label["id"]: label["count"] for label in deployment_labels}
        expected_count_dict = {
            "5e8eeae1b707216625ca4202": 0,
            "5d386cc6ff885918d96edb2c": 1,
        }
        self.assertDictEqual(expected_count_dict, count_dict)

    def test_failure_retrieve_labels_not_enabled(self):
        get_rsp = self._retrieve_deployment_labels(self.DEPLOYMENT_NO_LABEL)
        self.assertEqual(404, get_rsp.status_code)
        self.assertEqual("Label feature is not enabled", get_rsp.json["message"])

    def test_failure_create_label_invalid_permission(self):
        body = {CreateLabelsRequestObject.TEXTS: ["RECOVERED"]}
        get_rsp = self._create_deployment_label(
            self.deployment_id, self.super_admin_headers, body
        )
        self.assertEqual(403, get_rsp.status_code)

    def test_success_create_labels(self):
        body = {CreateLabelsRequestObject.TEXTS: ["RECOVERED"]}
        get_rsp = self._create_deployment_label(
            self.deployment_id, self.label_enabled_admin_headers, body
        )
        self.assertEqual(201, get_rsp.status_code)
        label_ids = get_rsp.json
        self.assertIsNotNone(label_ids)
        ret_rsp = self._retrieve_deployment_labels(
            deployment_id=self.DEPLOYMENT_LABEL_ENABLED
        )
        self.assertEqual(200, ret_rsp.status_code)
        deployment_labels = ret_rsp.json
        self.assertEqual(1, len(get_rsp.json))
        self._assert_label_ids_in_labels(label_ids=label_ids, labels=deployment_labels)

    def test_failure_create_label_not_enabled(self):
        body = {CreateLabelsRequestObject.TEXTS: ["RECOVERED"]}
        get_rsp = self._create_deployment_label(
            self.DEPLOYMENT_NO_LABEL, self.label_disabled_admin_headers, body
        )
        self.assertEqual(404, get_rsp.status_code)
        self.assertEqual("Label feature is not enabled", get_rsp.json["message"])

    def test_failure_create_label_existing_label(self):
        body = {CreateLabelsRequestObject.TEXTS: ["RECOVERED"]}
        get_rsp = self._create_deployment_label(
            self.DEPLOYMENT_MULTIPLE_LABEL, self.multiple_labels_admin_headers, body
        )
        self.assertEqual(400, get_rsp.status_code)
        self.assertEqual(
            DeploymentErrorCodes.DUPLICATE_LABEL_NAME, get_rsp.json["code"]
        )

    def test_success_update_label(self):
        body = {UpdateLabelRequestObject.TEXT: "OKAY"}
        get_rsp = self._update_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            label_id=self.SAMPLE_LABEL_ID,
            headers=self.multiple_labels_admin_headers,
            body=body,
        )
        self.assertEqual(200, get_rsp.status_code)
        get_rsp = get_rsp.json
        rsp_deployment_id = get_rsp["id"]
        self.assertEqual(rsp_deployment_id, self.DEPLOYMENT_MULTIPLE_LABEL)
        ret_rsp = self._retrieve_deployment_labels(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL
        )
        self.assertEqual(200, ret_rsp.status_code)
        deployment_labels = ret_rsp.json
        self.assertEqual(2, len(deployment_labels))
        labels = [label[Label.TEXT] for label in deployment_labels]
        self.assertIn("OKAY", labels)

    def test_failure_update_label_invalid_permission(self):
        body = {UpdateLabelRequestObject.TEXT: "OKAY"}
        get_rsp = self._update_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            label_id=self.SAMPLE_LABEL_ID,
            headers=self.super_admin_headers,
            body=body,
        )
        self.assertEqual(403, get_rsp.status_code)

    def test_failure_update_label_no_existing_label(self):
        body = {UpdateLabelRequestObject.TEXT: "OKAY"}
        get_rsp = self._update_deployment_label(
            deployment_id=self.DEPLOYMENT_LABEL_ENABLED,
            label_id=self.SAMPLE_LABEL_ID,
            headers=self.label_enabled_admin_headers,
            body=body,
        )
        self.assertEqual(404, get_rsp.status_code)
        self.assertEqual(
            f"Label with {self.SAMPLE_LABEL_ID} doesn't exist", get_rsp.json["message"]
        )

    def test_failure_update_label_invalid_label(self):
        body = {UpdateLabelRequestObject.TEXT: "OKAY"}
        get_rsp = self._update_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            label_id=self.WRONG_LABEL_ID,
            headers=self.multiple_labels_admin_headers,
            body=body,
        )
        self.assertEqual(404, get_rsp.status_code)
        self.assertEqual(
            f"Label with {self.WRONG_LABEL_ID} doesn't exist", get_rsp.json["message"]
        )

    def test_failure_update_label_not_enabled(self):
        body = {UpdateLabelRequestObject.TEXT: "OKAY"}
        get_rsp = self._update_deployment_label(
            deployment_id=self.DEPLOYMENT_NO_LABEL,
            headers=self.label_disabled_admin_headers,
            label_id=self.WRONG_LABEL_ID,
            body=body,
        )
        self.assertEqual(404, get_rsp.status_code)
        self.assertEqual("Label feature is not enabled", get_rsp.json["message"])

    def test_success_remove_label(self):
        label_id = self.SAMPLE_LABEL_ID
        users_count = self.retrieve_no_users_with_label(label_id)
        self.assertEqual(1, users_count)

        self._delete_label_and_assert_label_deleted(label_id)

    def test_failure_remove_label_label_removed_previously(self):
        label_id = self.SAMPLE_LABEL_ID

        self._delete_label_and_assert_label_deleted(label_id)

        rsp = self._remove_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            headers=self.multiple_labels_admin_headers,
            label_id=self.SAMPLE_LABEL_ID,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def retrieve_no_users_with_label(self, label_id) -> int:
        USER_COLLECTION = "user"
        query = {f"{User.LABELS}.{UserLabel.LABEL_ID}": ObjectId(label_id)}
        db = self.mongo_database
        user = db[USER_COLLECTION].find(query)
        return user.count()

    def test_failure_remove_label_invalid_permission(self):
        rsp = self._remove_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            headers=self.super_admin_headers,
            label_id=self.WRONG_LABEL_ID,
        )
        self.assertEqual(403, rsp.status_code)

    @staticmethod
    def _search_labels(label_ids, labels):
        num_of_labels = len(label_ids)
        num_of_labels_found = 0
        for label in labels:
            if label[Label.ID] in label_ids:
                num_of_labels_found += 1
                if num_of_labels == num_of_labels_found:
                    return True
        return False

    def _assert_label_ids_in_labels(self, label_ids: list[str], labels: list[dict]):
        present = self._search_labels(label_ids=label_ids, labels=labels)
        self.assertTrue(present)

    def _delete_label_and_assert_label_deleted(self, label_id):
        rsp = self._remove_deployment_label(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL,
            headers=self.multiple_labels_admin_headers,
            label_id=label_id,
        )
        self.assertEqual(204, rsp.status_code)
        ret_rsp = self._retrieve_deployment_labels(
            deployment_id=self.DEPLOYMENT_MULTIPLE_LABEL
        )
        self.assertEqual(200, ret_rsp.status_code)
        deployment_labels = ret_rsp.json
        self._assert_label_id_not_in_labels([label_id], deployment_labels)

        users_count = self.retrieve_no_users_with_label(label_id)
        self.assertEqual(0, users_count)

    def _assert_label_id_not_in_labels(self, label_ids: list[str], labels: list[dict]):
        present = self._search_labels(label_ids=label_ids, labels=labels)
        self.assertFalse(present)

    def _create_deployment_label(self, deployment_id, headers, body: dict):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/{deployment_id}/labels",
            headers=headers,
            json=body,
        )
        return rsp

    def _retrieve_deployment_labels(self, deployment_id):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{deployment_id}/labels",
            headers=self.super_admin_headers,
        )
        return rsp

    def _update_deployment_label(self, deployment_id, label_id, headers, body):
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{deployment_id}/labels/{label_id}",
            headers=headers,
            json=body,
        )
        return rsp

    def _remove_deployment_label(self, deployment_id, label_id, headers):
        rsp = self.flask_client.delete(
            f"{self.deployment_route}/deployment/{deployment_id}/labels/{label_id}",
            headers=headers,
        )
        return rsp


if __name__ == "__main__":
    unittest.main()
