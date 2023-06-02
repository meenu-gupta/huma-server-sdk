from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from bson import ObjectId
from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.autocomplete.component import AutocompleteComponent
from extensions.common.s3object import S3Object
from extensions.common.sort import SortField
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.exceptions import DeploymentErrorCodes
from extensions.deployment.models.deployment import (
    Deployment,
    IntegrationConfig,
    ModuleConfig,
    PAMIntegrationConfig,
)

from extensions.module_result.common.questionnaire_utils import build_question_map
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.config.pam_integration_client_config import (
    PAMIntegrationClientConfig,
)
from extensions.module_result.exceptions import ModuleResultErrorCodes
from extensions.module_result.models.module_config import RagThreshold
from extensions.module_result.models.primitives import (
    BMI,
    IKDC,
    NORFOLK,
    AZFurtherPregnancyKeyActionTrigger,
    AZGroupKeyActionTrigger,
    BodyMeasurement,
    ECGHealthKit,
    ECGReading,
    Lysholm,
    PeakFlow,
    Primitive,
    Questionnaire,
    QuestionnaireAnswer,
    Server,
    Weight,
)
from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.models.primitives.primitive_oacs import OACS
from extensions.module_result.models.primitives.primitive_oars import OARS
from extensions.module_result.models.primitives.primitive_oxford_hip import (
    HipAffected,
    OxfordHipScore,
    HipData,
)
from extensions.module_result.models.primitives.primitive_oxford_knee import (
    LegAffected,
    LegData,
    OxfordKneeScore,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswerMediaFile,
    QuestionnaireAnswerMediaType,
)
from extensions.module_result.models.primitives.primitive_step import Step
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode
from extensions.module_result.modules import (
    BVIModule,
    FJSKneeScoreModule,
    GeneralAnxietyDisorderModule,
    IKDCModule,
    KCCQQuestionnaireModule,
    KOOSQuestionnaireModule,
    LysholmTegnerModule,
    NorfolkQuestionnaireModule,
    SF36QuestionnaireModule,
    HighFrequencyHeartRateModule,
    MedicationTrackerModule,
    QuestionnaireModule,
)
from extensions.module_result.modules.eq5d_5l import EQ5D5LModule
from extensions.module_result.modules.oacs import OACSModule
from extensions.module_result.modules.oars import OARSModule
from extensions.module_result.pam.pam_integration_client import PAMIntegrationClient
from extensions.module_result.questionnaires.pam_questionnaire_calculator import (
    get_pam_config,
)
from extensions.module_result.router.custom_module_config_requests import (
    CreateOrUpdateCustomModuleConfigRequestObject,
)
from extensions.module_result.router.module_result_requests import (
    AggregateModuleResultsRequestObjects,
    RetrieveModuleResultsRequestObject,
)
from extensions.module_result.router.module_result_response import (
    Flags,
    UnseenModuleResult,
    UnseenModulesResponse,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_bmi_data,
    sample_body_measurement,
    sample_breathlessness,
    sample_daily_check_in,
    sample_diabetes_distress_score_data,
    sample_eq5d_questionnaire_result_deprecated,
    sample_questionnaire_with_other_option,
    sample_ecg,
    sample_eq5d_questionnaire_result_with_multiple_arabic_answers,
    sample_fjs_hip_score_data,
    sample_fjs_knee_score_data,
    sample_further_information,
    sample_gad_7,
    sample_group_information,
    sample_heart_rate,
    sample_high_frequency_heart_rate_multiple_values,
    sample_high_frequency_heart_rate_multiple_values_second,
    sample_high_frequency_heart_rate_ppg_type,
    sample_high_frequency_heart_rate_single_value,
    sample_ikdc,
    sample_kccq_all_zero_weight_anwsers,
    sample_kccq_data,
    sample_kccq_data_missing_answers,
    sample_koos_and_womac_data,
    sample_koos_and_womac_data_with_not_enough_answers,
    sample_lysholm_and_tegner,
    sample_medication_result,
    sample_norfolk_questionnaire_missing_answers,
    sample_norfolk_questionnaire_module_data,
    sample_oacs,
    sample_oars,
    sample_oxford_both_knee_score,
    sample_oxford_hip_score,
    sample_oxford_only_one_knee_score,
    sample_pam_questionnaire_result,
    sample_peak_flow_data,
    sample_questionnaire,
    sample_questionnaire_with_reverse_and_max_score,
    sample_respiratory_rate,
    sample_sensor_capture,
    sample_sf36_data,
    sample_steps,
    sample_steps_deprecated,
    sample_surgery_details,
    sample_surgery_details_answers,
    sample_weight,
    sample_symptom,
    sample_blood_glucose,
    sample_bg_thresholds,
    sample_oxford_only_one_hip_score,
    sample_questionnaire_with_autocomplete_option,
    sample_questionnaire_with_media,
    sample_questionnaire_with_recall_text,
)
from extensions.tests.shared.test_helpers import simple_deployment
from extensions.tests.test_case import ExtensionTestCase
from requests import Response
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils import inject
from sdk.common.utils.validators import utc_str_field_to_val
from sdk.phoenix.config.server_config import Client
from sdk.storage.component import StorageComponent
from sdk.tests.utils.UnitTests.flask_request_utils_tests import (
    SAMPLE_STRINGFIED_PAYLOAD,
)
from sdk.versioning.component import VersionComponent
from sdk.versioning.models.version import Version
from sdk.versioning.user_agent_parser import UserAgent

VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER_ID = "5e8f0c74b50aa9656c34789c"

VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
ECG_SAMPLE_FILE = "ecg_sample"
COLOR = RagThreshold.COLOR
DEPLOYMENT_COLLECTION = "deployment"

NAME = "name"
PRIMITIVE = "primitive"
EXPECTED_RESULT_VALUE = "expectedResultValue"
VALUE = "value"


def now_str():
    return utc_str_field_to_val(datetime.utcnow())


class BaseModuleResultTest(ExtensionTestCase):
    components = [
        AuthComponent(),
        StorageComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        CalendarComponent(),
        AutocompleteComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    config_file_path = Path(__file__).with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/medication_dump.json"),
        Path(__file__).parent.joinpath("fixtures/autocomplete_dump.json"),
        Path(__file__).parent.joinpath("fixtures/unseenrecentresult.json"),
    ]

    USER_ID_WITHOUT_GENDER = "5e8f0c74b50aa9656c341111"
    USER_ID_WITHOUT_DOB = "5e8f0c74b50aa9656c342222"
    USER_ID_WITHOUT_HEIGHT = "5e8f0c74b50aa9656c34789d"

    def setUp(self):
        super().setUp()

        agent = "Huma-QA/1.4.0 (bundleId: com.huma.humaapp.dev; build: 1; software: Android 29 (10); hardware: samsung SM-G970F)"
        self.headers = self.get_headers_for_token(VALID_MANAGER_ID)
        self.headers["x-hu-user-agent"] = agent
        self.base_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"


class ModuleResultTest(BaseModuleResultTest):
    def upload_ecg_file(self):
        path = Path(__file__).parent.joinpath(f"fixtures/{ECG_SAMPLE_FILE}")
        with open(path, "rb") as ecg_file:
            file_data = ecg_file.read()
        data = {
            "filename": ECG_SAMPLE_FILE,
            "mime": "application/octet-stream",
            "file": (BytesIO(file_data), "file"),
        }
        self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.get_headers_for_token(VALID_USER_ID),
            content_type="multipart/form-data",
        )

    def test_retrieve_unseen_module_results(self):
        user_id = "5e8f0c74b50aa9656c34789d"
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}/flagged-modules",
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        flags_resp = UnseenModulesResponse.FLAGS
        flags_result = UnseenModuleResult.FLAGS
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json[flags_resp]))
        self.assertEqual(4, rsp.json[flags_resp][0][flags_result][Flags.RED])
        # test sort order
        result: list = deepcopy(rsp.json[flags_resp])

        result.sort(
            key=lambda x: (
                x[flags_result][Flags.RED],
                x[flags_result][Flags.AMBER],
                x[flags_result][Flags.GRAY],
            ),
            reverse=True,
        )
        self.assertListEqual(result, rsp.json[UnseenModulesResponse.FLAGS])
        self.assertEqual(
            "Thu, 18 Nov 2021 04:39:42 GMT",
            rsp.json[UnseenModulesResponse.LAST_MANAGER_NOTE],
        )

    def test_retrieve_empty_unseen_module_results(self):
        user_id = "5e8f0c74f51aa9656c34789e"
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}/flagged-modules",
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        flags_resp = UnseenModulesResponse.FLAGS
        self.assertEqual(200, rsp.status_code)
        self.assertEmpty(rsp.json[flags_resp])
        self.assertNotIn(UnseenModulesResponse.LAST_MANAGER_NOTE, rsp.json)

    def test_other_option_in_multiple_choice_questionnaire(self):
        other_options = ["other option 1", "other option 2", "other option 3"]
        sample_questionnaire = sample_questionnaire_with_other_option()
        sample_questionnaire[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.OTHER_TEXT
        ] = " , ".join(other_options)
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_questionnaire],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue("error" not in rsp.json)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        response_data = rsp.json

        self.assertTrue("Questionnaire" in response_data)
        self.assertTrue(Questionnaire.ANSWERS in response_data["Questionnaire"][0])
        self.assertEqual(
            1, len(response_data["Questionnaire"][0][Questionnaire.ANSWERS])
        )
        self.assertTrue(
            QuestionnaireAnswer.OTHER_SELECTED_CHOICES
            in response_data["Questionnaire"][0][Questionnaire.ANSWERS][0]
        )
        other_selected_choices = response_data["Questionnaire"][0][
            Questionnaire.ANSWERS
        ][0][QuestionnaireAnswer.OTHER_SELECTED_CHOICES]
        self.assertEqual(len(other_options), len(other_selected_choices))
        self.assertEqual(sorted(other_options), sorted(other_selected_choices))

    def test_autocomplete_questionnaire(self):
        selected_options = ["other option 1", "other option 2", "other option 3"]
        sample_autocomplete_questionnaire = (
            sample_questionnaire_with_autocomplete_option()
        )
        sample_autocomplete_questionnaire[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.ANSWERS_LIST
        ] = selected_options
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_autocomplete_questionnaire],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue("error" not in rsp.json)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        response_data = rsp.json

        self.assertTrue("Questionnaire" in response_data)
        self.assertTrue(Questionnaire.ANSWERS in response_data["Questionnaire"][0])
        response_answers = response_data["Questionnaire"][0][Questionnaire.ANSWERS]
        self.assertEqual(1, len(response_answers))
        self.assertTrue(QuestionnaireAnswer.ANSWERS_LIST in response_answers[0])
        response_answer_list = response_answers[0][QuestionnaireAnswer.ANSWERS_LIST]
        self.assertListEqual(selected_options, response_answer_list)

    def test_media_questionnaire(self):
        sample_autocomplete_questionnaire = sample_questionnaire_with_media()
        files = sample_autocomplete_questionnaire[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.FILES_LIST
        ]
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_autocomplete_questionnaire],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue("error" not in rsp.json)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        response_data = rsp.json

        self.assertTrue("Questionnaire" in response_data)
        self.assertTrue(Questionnaire.ANSWERS in response_data["Questionnaire"][0])
        response_answers = response_data["Questionnaire"][0][Questionnaire.ANSWERS]
        self.assertEqual(1, len(response_answers))
        self.assertTrue(QuestionnaireAnswer.FILES_LIST in response_answers[0])
        response_file_list = response_answers[0][QuestionnaireAnswer.FILES_LIST]
        self.assertListEqual(files, response_file_list)

    def test_media_questionnaire_validation_errors(self):
        # TODO: unblock test when validation is back
        return
        # Test Max Answers
        files = [
            {
                QuestionnaireAnswerMediaFile.MEDIA_TYPE: QuestionnaireAnswerMediaType.FILE.value,
                QuestionnaireAnswerMediaFile.FILE: "613bb279d393b8b116d65d12",
            }
        ]
        sample_autocomplete_questionnaire = sample_questionnaire_with_media()
        sample_autocomplete_questionnaire[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.FILES_LIST
        ] = (files * 3)
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_autocomplete_questionnaire],
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

        # Test File Type Check
        files = [
            {
                QuestionnaireAnswerMediaFile.MEDIA_TYPE: QuestionnaireAnswerMediaType.VIDEO.value,
                QuestionnaireAnswerMediaFile.FILE: "613bb279d393b8b116d65d12",
            }
        ]
        sample_autocomplete_questionnaire[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.FILES_LIST
        ] = files
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_autocomplete_questionnaire],
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_questionnaire_with_recall_text(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_questionnaire_with_recall_text()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertIn(
            QuestionnaireAnswer.RECALLED_TEXT,
            rsp.json[QuestionnaireModule.moduleId][0][Questionnaire.ANSWERS][1],
        )

    def test_retrieve_questionnaire_for_manager(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_questionnaire()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        self.assertIn("Questionnaire", json)
        self.assertEqual(1, len(json["Questionnaire"]))

    def test_retrieve_no_module_with_primitive(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/aaa/search", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(
            rsp.json["code"], DeploymentErrorCodes.MODULE_WITH_PRIMITIVE_DOES_NOT_EXIST
        )

    def test_retrieve_questionnaire_for_user(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_questionnaire()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        self.headers = self.get_headers_for_token(VALID_USER_ID)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        self.assertIn("Questionnaire", json)
        self.assertEqual(0, len(json["Questionnaire"]))

    def save_doctor_questionnaire(self):
        doctor_questionnaire = {**sample_questionnaire(), "isForManager": True}
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[doctor_questionnaire],
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        self.assertEqual(201, rsp.status_code)

    def test_retrieve_questionnaire_for_manager_by_user(self):
        self.save_doctor_questionnaire()
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search",
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)

        for item in rsp.json["Questionnaire"]:
            self.assertFalse(item.get("isForManager", False))

    def test_retrieve_questionnaire_for_manager_by_manager(self):
        self.save_doctor_questionnaire()

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search",
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        self.assertEqual(200, rsp.status_code)

        for item in rsp.json["Questionnaire"]:
            self.assertTrue(item.get("isForManager", False))

    @staticmethod
    def _get_weight_module_body(function: str = AggregateFunc.AVG.name) -> dict:
        return {
            AggregateModuleResultsRequestObjects.MODE: AggregateMode.NONE.name,
            AggregateModuleResultsRequestObjects.PRIMITIVE_NAME: Weight.__name__,
            AggregateModuleResultsRequestObjects.FUNCTION: function,
            AggregateModuleResultsRequestObjects.FROM_DATE: utc_str_field_to_val(
                datetime.utcnow() - timedelta(hours=1)
            ),
            AggregateModuleResultsRequestObjects.TO_DATE: utc_str_field_to_val(
                datetime.utcnow() + timedelta(hours=1)
            ),
        }

    def test_aggregate_avg_weight(self):
        body = self._get_weight_module_body()

        rsp = self.aggregate_weight_for_user(body)
        result = rsp.json[0]
        self.assertIn("value", result)
        self.assertEqual(result["value"], 125.0)

    def test_failure_aggregate_negative_skip(self):
        body = self._get_weight_module_body()
        body[AggregateModuleResultsRequestObjects.SKIP] = -1

        rsp = self.flask_client.post(
            f"{self.base_route}/aggregate", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_aggregate_not_valid_timezone(self):
        body = self._get_weight_module_body()
        body[AggregateModuleResultsRequestObjects.TIMEZONE] = "aaa"

        rsp = self.flask_client.post(
            f"{self.base_route}/aggregate", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_aggregate_negative_limit(self):
        body = self._get_weight_module_body()
        body[AggregateModuleResultsRequestObjects.LIMIT] = -1

        rsp = self.flask_client.post(
            f"{self.base_route}/aggregate", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_aggregate_max_weight(self):
        body = self._get_weight_module_body(AggregateFunc.MAX.name)

        rsp = self.aggregate_weight_for_user(body)
        result = rsp.json[0]
        self.assertIn("value", result)
        self.assertEqual(result["value"], 150.0)

    def test_aggregate_min_weight(self):
        body = self._get_weight_module_body(AggregateFunc.MIN.name)

        rsp = self.aggregate_weight_for_user(body)
        result = rsp.json[0]
        self.assertIn("value", result)
        self.assertEqual(result["value"], 100.0)

    def aggregate_weight_for_user(self, body):
        rsp = self.flask_client.post(
            f"{self.base_route}/Weight",
            json=[sample_weight(), sample_weight(150)],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        self.headers = self.get_headers_for_token(VALID_USER_ID)

        rsp = self.flask_client.post(
            f"{self.base_route}/aggregate", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        return rsp

    @patch("extensions.module_result.pam.pam_integration_client.requests")
    @patch.object(PAMIntegrationClient, "generate_identifier")
    @patch(
        "extensions.module_result.questionnaires.pam_questionnaire_calculator.get_pam_config"
    )
    def test_create_pam_questionnaire_result(
        self, mock_get_pam, mock_client, mock_requests
    ):
        third_party_identifier = "27VInKyucB9A7aVvrPE9c4d24pli6grg"

        mock_requests.post.side_effect = self.side_effect
        mock_client.return_value = third_party_identifier
        mock_get_pam.return_value = PAMIntegrationClientConfig(
            submitSurveyURI="",
            enrollUserURI="",
            clientExtID="",
            clientPassKey="test",
            subgroupExtID="test",
            timeout=12200,
        )

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_pam_questionnaire_result()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue(mock_get_pam.called)
        self.assertEqual(mock_get_pam.call_args.args[0].id, VALID_DEPLOYMENT_ID)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        self.assertIn("Questionnaire", json)
        self.assertEqual(1, len(json["Questionnaire"]))

        self.assertEqual(34.2, json["Questionnaire"][0]["value"])
        self.assertCountEqual(
            [
                {"label": "PAMSCORE", "valueFloat": 34.2, "valueType": "VALUE_FLOAT"},
                {
                    "label": "PAMRESULTLEVEL",
                    "valueFloat": 1.0,
                    "valueType": "VALUE_FLOAT",
                },
            ],
            json["Questionnaire"][0]["appResult"]["values"],
        )

        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        user = rsp.json
        self.assertIn(third_party_identifier, user["pamThirdPartyIdentifier"])

    @patch("extensions.module_result.pam.pam_integration_client.requests")
    @patch.object(PAMIntegrationClient, "generate_identifier")
    @patch(
        "extensions.module_result.questionnaires.pam_questionnaire_calculator.get_pam_config"
    )
    def test_http_error_on_pam_request(self, mock_get_pam, mock_client, mock_requests):
        third_party_identifier = "27VInKyucB9A7aVvrPE9c4d24pli6grg"

        mock_requests.post.side_effect = self.side_effect_400
        mock_client.return_value = third_party_identifier
        mock_get_pam.return_value = PAMIntegrationClientConfig(
            submitSurveyURI="",
            enrollUserURI="",
            clientExtID="65654",
            clientPassKey="test",
            subgroupExtID="test",
            timeout=12200,
        )

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_pam_questionnaire_result()],
            headers=self.headers,
        )

        self.assertIn("errors", rsp.json)

    def side_effect_400(self, *args, **kwargs):
        response = Response()
        response.status_code = 400
        return response

    def test_get_pam_config_from_config(self):
        dep = Deployment.from_dict({"id": VALID_DEPLOYMENT_ID, **simple_deployment()})
        self.assertEqual(
            get_pam_config(dep, self.config.server).clientExtID, "338682114"
        )

    def test_get_pam_config_from_deployment(self):
        dep = Deployment.from_dict({"id": VALID_DEPLOYMENT_ID, **simple_deployment()})
        dep.integration = IntegrationConfig(
            pamConfig=PAMIntegrationConfig.from_dict(
                {
                    "submitSurveyURI": "https://servicesUAT.insigniahealth.com/services/XML/v1.0/ihapi.svc/submitusersurvey",
                    "enrollUserURI": "https://servicesUAT.insigniahealth.com/services/XML/v1.0/ihapi.svc/enrolluser",
                    "clientExtID": "338682113",
                    "clientPassKeyEncrypted": "gAAAAABfvHA9BmPRETKAaifxZNIlULq6dmzTauy5r01dk7nImRe0ZofNXO0f3QU3QQPliLVmGrrQvS8NAVmV-Rl5AZsjlp5-Dw==",
                    "subgroupExtID": "751841373",
                }
            )
        )
        self.assertEqual(
            get_pam_config(dep, self.config.server).clientExtID, "338682113"
        )

    def test_create_sensor_capture_for_breathing(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/Breathing",
            json=[sample_sensor_capture()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_retrieve_sensor_capture_with_sanity_check_true(self):
        # Create sensor capture data with sanityCheck as True
        rsp = self.flask_client.post(
            f"{self.base_route}/Breathing",
            json=[sample_sensor_capture()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        # Create sensor capture data with sanityCheck as False
        sensor_capture_sanity_check_false = sample_sensor_capture()
        sensor_capture_sanity_check_false["sanityCheck"] = False

        rsp = self.flask_client.post(
            f"{self.base_route}/Breathing",
            json=[sensor_capture_sanity_check_false],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/Breathing/search",
            json={"filters": {"sanityCheck": True}},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        self.assertIn("SensorCapture", json)
        self.assertEqual(1, len(json["SensorCapture"]))
        self.assertEqual(True, json["SensorCapture"][0]["sanityCheck"])

    def side_effect(self, *args, **kwargs):
        response = Response()
        response.status_code = 200

        if (
            kwargs["url"]
            == "https://servicesUAT.insigniahealth.com/services/XML/v1.0/ihapi.svc/submitusersurvey"
        ):
            response.status_code = 201
            response._content = b'<UserSurveyResponseData xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><StatusCode>Success_SurveySubmit</StatusCode><StatusMessage>Submit User Survey success.</StatusMessage><SurveyEnteredDateTime>2019-01-01T00:00:00</SurveyEnteredDateTime><SurveyName>PAM13_S</SurveyName><SurveyResult><ResponseData><Type id="PAMLevel" value="1"/><Type id="PAMScore" value="34.20"/></ResponseData></SurveyResult><ThirdPartyIdentifier>HumaUser42</ThirdPartyIdentifier></UserSurveyResponseData>'
        elif (
            kwargs["url"]
            == "https://servicesUAT.insigniahealth.com/services/XML/v1.0/ihapi.svc/enrolluser"
        ):
            response._content = b'<RegisterResponseData xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><StatusCode>Success_Register</StatusCode><StatusMessage>User successfully registered.</StatusMessage><ExternalUserID>200727-E0JH2GV1</ExternalUserID><NationalPatientIdentifier i:nil="true"/><ThirdPartyIdentifier>27VInKyucB9A7aVvrPE9c4d24pli6grg</ThirdPartyIdentifier></RegisterResponseData>'

        return response

    def test_bmi_weight_creates_bmi_result(self):
        data = sample_bmi_data()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{BMI.__name__}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{BMI.__name__}/search", json={}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json))
        bmi_primitives = [BMI.__name__, Weight.__name__]
        for primitive_name in bmi_primitives:
            self.assertIn(primitive_name, rsp.json)
            self.assertEqual(1, len(rsp.json[primitive_name]))

    def test_exception_if_no_height_for_bmi(self):
        data = sample_bmi_data()
        # this user have no height in profile
        headers = self.get_headers_for_token(self.USER_ID_WITHOUT_HEIGHT)
        url = f"/api/extensions/v1beta/user/{self.USER_ID_WITHOUT_HEIGHT}/module-result"
        rsp = self.flask_client.post(
            f"{url}/{BMI.__name__}", json=[data], headers=headers
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])
        self.assertEqual(
            'Field "height" is not set in user profile', rsp.json["message"]
        )

    def test_save_diabetes_distress_score_questionnaire(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/DiabetesDistressScore",
            json=[sample_diabetes_distress_score_data()],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

    @patch("extensions.module_result.modules.ecg_module.pdf_utils.pdfkit")
    def test_success_save_and_retrieve_ecg_data(self, mock_pdfkit):
        self.upload_ecg_file()
        mock_pdfkit.from_string.return_value = b""
        data = sample_ecg()
        rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        ecg_data = json["ECGHealthKit"][0]

        self.assertIn(ECGHealthKit.ECG_READING, ecg_data)
        self.assertIn(ECGHealthKit.GENERATED_PDF, ecg_data)
        self.assertEqual(
            ecg_data[ECGHealthKit.ECG_READING][ECGReading.AVERAGE_HEART_RATE], 1850
        )
        self.assertIn(ECGReading.DATA_POINTS, ecg_data[ECGHealthKit.ECG_READING])
        self.assertEqual(
            list, type(ecg_data[ECGHealthKit.ECG_READING][ECGReading.DATA_POINTS])
        )

        self.assertEqual(
            ecg_data[ECGHealthKit.GENERATED_PDF][S3Object.BUCKET], "integrationtests"
        )

    def test_success_create_module_result_uses_user_rag(self):
        bg_module = "BloodGlucose"
        bg_module_config_id = "5e94b2007773091c9a592888"
        search_payload = {
            "direction": "DESC",
            "moduleConfigId": bg_module_config_id,
            "limit": 1,
        }

        self.create_module_result(
            module_name=bg_module, data=[sample_blood_glucose(value=8.0)]
        )
        result = self.get_latest_module_result(
            module_name=bg_module, data=search_payload
        )
        self.assertEqual(
            {"red": 0, "amber": 0, "gray": 1}, result[bg_module][0]["flags"]
        )
        self.validate_profile_thresholds(
            VALID_USER_ID, bg_module_config_id, bg_module, "green"
        )

        payload = {
            CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: bg_module,
            CreateOrUpdateCustomModuleConfigRequestObject.MODULE_NAME: bg_module,
            CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
            CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_bg_thresholds(),
        }
        rsp = self.flask_client.put(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/moduleConfig/{bg_module_config_id}",
            json=payload,
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        self.assertEqual(200, rsp.status_code)

        # New data submitted will take into account user personalised RAG thresholds
        self.create_module_result(
            module_name=bg_module, data=[sample_blood_glucose(value=8.0)]
        )
        result = self.get_latest_module_result(
            module_name=bg_module, data=search_payload
        )
        self.assertEqual(
            {"red": 0, "amber": 1, "gray": 0}, result[bg_module][0]["flags"]
        )
        self.validate_profile_thresholds(
            VALID_USER_ID, bg_module_config_id, bg_module, "amber", True
        )

    def test_create_module_result_defaults_to_deployment_thresholds(self):
        bg_module = "BloodGlucose"
        bg_module_config_id = "5e94b2007773091c9a592888"
        search_payload = {
            "direction": "DESC",
            "moduleConfigId": bg_module_config_id,
            "limit": 1,
        }

        self.create_module_result(
            module_name=bg_module, data=[sample_blood_glucose(value=8.0)]
        )
        result = self.get_latest_module_result(
            module_name=bg_module, data=search_payload
        )
        self.assertEqual(
            {"red": 0, "amber": 0, "gray": 1}, result[bg_module][0]["flags"]
        )

    def create_module_result(self, module_name: str, data: list):
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_name}",
            json=data,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

    def get_latest_module_result(self, module_name: str, data: dict):
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_name}/search",
            json=data,
            headers=self.get_headers_for_token(VALID_MANAGER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def validate_profile_thresholds(
        self,
        user_id: str,
        config_id: str,
        module: str,
        color: str,
        custom: bool = False,
    ):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{user_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        recent_result = rsp.json[User.RECENT_MODULE_RESULTS][config_id][0][module]
        threshold = recent_result["ragThreshold"]
        if module in threshold:
            self.assertEqual(threshold[module]["value"]["color"], color)
            if custom:
                self.assertEqual(threshold[module]["value"]["isCustom"], True)
            else:
                self.assertEqual(threshold[module]["value"]["isCustom"], False)
        else:
            self.fail()

    def test_success_save_and_retrieve_data_with_translation(self):
        arabic_value = "Arabic A serious problem"

        headers_with_english_language = {
            **self.get_headers_for_token(VALID_USER_ID),
            "x-hu-locale": "en",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/DiabetesDistressScore",
            json=[sample_diabetes_distress_score_data()],
            headers=headers_with_english_language,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue("error" not in rsp.json)

        headers_with_arabic_language = {
            **self.get_headers_for_token(VALID_USER_ID),
            "x-hu-locale": "ar",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/DiabetesDistressScore/search",
            headers=headers_with_arabic_language,
        )
        self.assertEqual(200, rsp.status_code)
        response_data = rsp.json

        self.assertTrue("DiabetesDistressScore" in response_data)
        self.assertTrue("Questionnaire" in response_data)

        questionnaire_data = response_data["Questionnaire"][0]["answers"][0][
            QuestionnaireAnswer.ANSWER_TEXT
        ]
        self.assertEqual(questionnaire_data, arabic_value)

    @patch("extensions.module_result.modules.ecg_module.pdf_utils.pdfkit")
    def test_create_ecg_raise_exception_500(self, mock_pdfkit):
        self.upload_ecg_file()
        mock_pdfkit.from_string.return_value.raiseError.side_effect = Exception()
        data = sample_ecg()
        rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(500, rsp.status_code)

    @patch("extensions.module_result.modules.ecg_module.pdf_utils.pdfkit")
    def test_excluded_fields(self, mock_pdfkit):
        self.upload_ecg_file()
        mock_pdfkit.from_string.return_value = b""
        data = sample_ecg()
        rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

        search_rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit/search", headers=self.headers
        )
        self.assertEqual(200, search_rsp.status_code)
        ecg_data = search_rsp.json["ECGHealthKit"][0]
        self.assertIn(ECGReading.DATA_POINTS, ecg_data[ECGHealthKit.ECG_READING])

        data = {
            RetrieveModuleResultsRequestObject.EXCLUDED_FIELDS: [
                f"{ECGHealthKit.ECG_READING}.{ECGReading.DATA_POINTS}"
            ]
        }
        search_rsp = self.flask_client.post(
            f"{self.base_route}/ECGHealthKit/search", headers=self.headers, json=data
        )
        self.assertEqual(200, search_rsp.status_code)
        ecg_data = search_rsp.json["ECGHealthKit"][0]
        self.assertNotIn(ECGReading.dataPoints, ecg_data[ECGHealthKit.ECG_READING])

    def test_create_eq5d_questionnaire_result_deprecated(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire",
            json=[sample_eq5d_questionnaire_result_deprecated()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/Questionnaire/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        questionnaire_primitives = json.get("Questionnaire")
        self.assertIsNotNone(questionnaire_primitives)
        self.assertEqual(1, len(questionnaire_primitives))
        self.assertEqual(0.105, questionnaire_primitives[0][Questionnaire.VALUE])
        answers = questionnaire_primitives[0].get(Questionnaire.ANSWERS)
        expected_text = "I have no problems in walking about"
        self.assertEqual(expected_text, answers[0][QuestionnaireAnswer.ANSWER_TEXT])

    def test_create_eq5d_questionnaire_result_multiple_with_translation(self):
        # TODO: Remove `return` when we have all the translations in place
        return

        headers_with_arabic_language = {
            **self.headers,
            "x-hu-locale": "ar",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{EQ5D5LModule.moduleId}",
            json=[sample_eq5d_questionnaire_result_with_multiple_arabic_answers()],
            headers=headers_with_arabic_language,
        )
        self.assertEqual(201, rsp.status_code)

        headers_with_english_language = {
            **self.headers,
            "x-hu-locale": "en",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{EQ5D5LModule.moduleId}/search",
            headers=headers_with_english_language,
        )
        self.assertEqual(200, rsp.status_code)

        json = rsp.json
        self.assertIn("Questionnaire", json)
        self.assertEqual(1, len(json["Questionnaire"]))
        self.assertEqual(
            "Eye problems,Kidney problems,Circulatory problems",
            json["Questionnaire"][0]["answers"][0][QuestionnaireAnswer.ANSWER_TEXT],
        )

    def test_create_peak_flow_and_check_percent_value_result(self):
        data = sample_peak_flow_data()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{PeakFlow.__name__}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{PeakFlow.__name__}/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        json = rsp.json
        self.assertIn(PeakFlow.__name__, json)
        self.assertEqual(1, len(json[PeakFlow.__name__]))
        item = json[PeakFlow.__name__][0]
        self.assertIn(PeakFlow.VALUE, item)
        self.assertIn(PeakFlow.VALUE_PERCENT, item)

    def test_exception_if_no_gender_for_peak_flow(self):
        data = sample_peak_flow_data()
        # this user have no gender in profile
        headers = self.get_headers_for_token(self.USER_ID_WITHOUT_GENDER)
        url = f"/api/extensions/v1beta/user/{self.USER_ID_WITHOUT_GENDER}/module-result"
        rsp = self.flask_client.post(
            f"{url}/{PeakFlow.__name__}", json=[data], headers=headers
        )
        self.assertIn("errors", rsp.json)
        self.assertEqual(
            f'Error creating primitive {PeakFlow.__name__}: Field "{User.GENDER}" is not set in user profile',
            rsp.json["errors"][0],
        )

    def test_exception_if_no_dateOfBirth_for_peak_flow(self):
        data = sample_peak_flow_data()
        # this user have no dateOfBirth in profile
        headers = self.get_headers_for_token(self.USER_ID_WITHOUT_DOB)
        url = f"/api/extensions/v1beta/user/{self.USER_ID_WITHOUT_DOB}/module-result"
        rsp = self.flask_client.post(
            f"{url}/{PeakFlow.__name__}", json=[data], headers=headers
        )
        self.assertIn("errors", rsp.json)
        self.assertEqual(
            f"Error creating primitive {PeakFlow.__name__}: User attribute [{User.DATE_OF_BIRTH}] is missing",
            rsp.json["errors"][0],
        )

    def test_exception_if_no_height_for_peak_flow(self):
        data = sample_peak_flow_data()
        # this user have no height in profile
        headers = self.get_headers_for_token(self.USER_ID_WITHOUT_HEIGHT)
        url = f"/api/extensions/v1beta/user/{self.USER_ID_WITHOUT_HEIGHT}/module-result"
        rsp = self.flask_client.post(
            f"{url}/{PeakFlow.__name__}", json=[data], headers=headers
        )
        self.assertIn("errors", rsp.json)
        self.assertEqual(
            f'Error creating primitive {PeakFlow.__name__}: Field "{User.HEIGHT}" is not set in user profile',
            rsp.json["errors"][0],
        )

    def test_success_create_module_result(self):
        module_id = FJSKneeScoreModule.moduleId
        data = sample_fjs_knee_score_data()
        url = f"{self.base_route}/{module_id}"

        rsp = self.flask_client.post(url, json=[data], headers=self.headers)
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_module_result(self):
        # TODO: unblock test when validation is back
        return

        module_id = FJSKneeScoreModule.moduleId
        data = sample_fjs_knee_score_data()
        data[Questionnaire.ANSWERS].extend(data[Questionnaire.ANSWERS][:2])
        url = f"{self.base_route}/{module_id}"

        rsp = self.flask_client.post(url, json=[data], headers=self.headers)
        self.assertEqual(400, rsp.status_code)

    def test_retrieve_module_results_by_module_config_id(self):
        weight_config_id_1 = "5e94b2007773091c9a592660"
        weight_config_id_2 = "5e94b2007773091c9a592550"
        module_id = Weight.__name__
        url = f"{self.base_route}/{module_id}/search"

        # test first weight module config
        options = {
            RetrieveModuleResultsRequestObject.LIMIT: 2,
            RetrieveModuleResultsRequestObject.MODULE_ID: module_id,
        }
        rsp = self.flask_client.post(url, json=options, headers=self.headers)
        self.assertEqual(2, len(rsp.json[Weight.__name__]))
        primitive = rsp.json[Weight.__name__][0]
        self.assertEqual(weight_config_id_1, primitive.get(Weight.MODULE_CONFIG_ID))

        # test second weight module config
        options.update(
            {RetrieveModuleResultsRequestObject.MODULE_CONFIG_ID: weight_config_id_2}
        )
        rsp = self.flask_client.post(url, json=options, headers=self.headers)
        self.assertEqual(1, len(rsp.json[Weight.__name__]))
        primitive = rsp.json[Weight.__name__][0]
        self.assertEqual(weight_config_id_2, primitive.get(Weight.MODULE_CONFIG_ID))

    def test_retrieve_module_results_with_pagination(self):
        weight_id_1st = "5f7dd1f0e03d4a97e8007a91"
        weight_id_2nd = "5f7dd1f0e03d4a97e8007a51"
        weight_id_3rd = "5f7dd1f0e03d4a97e8007a84"
        module_id = Weight.__name__
        url = f"{self.base_route}/{module_id}/search"

        # 1. Skip only
        body = {"skip": 1}
        rsp = self.flask_client.post(url, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json[module_id]))
        self.assertEqual(weight_id_2nd, rsp.json[module_id][0][Primitive.ID])
        self.assertEqual(weight_id_3rd, rsp.json[module_id][1][Primitive.ID])

        # 2. Limit only
        body = {"limit": 2}
        rsp = self.flask_client.post(url, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json[module_id]))
        self.assertEqual(weight_id_1st, rsp.json[module_id][0][Primitive.ID])
        self.assertEqual(weight_id_2nd, rsp.json[module_id][1][Primitive.ID])

        # 2. Skip + Limit
        body = {"limit": 1, "skip": 1}
        rsp = self.flask_client.post(url, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json[module_id]))
        self.assertEqual(weight_id_2nd, rsp.json[module_id][0][Primitive.ID])


class CommonModuleResultsTestClass(BaseModuleResultTest):
    def post_results(self, module_id, result):
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[result],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code, rsp.json.get("message"))
        errors = rsp.json.get("errors") or []
        self.assertEqual(0, len(errors), f"Error: {module_id}")
        return rsp

    def retrieve_module_config(self, module_id: str):
        deployment_dict = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {
                Deployment.MODULE_CONFIGS: {
                    "$elemMatch": {ModuleConfig.MODULE_ID: module_id}
                }
            }
        )

        if not deployment_dict:
            return

        module_configs = deployment_dict.get(Deployment.MODULE_CONFIGS)
        module_config = next(
            filter(
                lambda config: config.get(ModuleConfig.MODULE_ID) == module_id,
                module_configs,
            ),
            None,
        )
        return module_config

    def retrieve_result(self, module_id, primitive):
        expected_client_value = {
            UserAgent.PRODUCT: "Huma-QA",
            UserAgent.VERSION: "1.4.0",
            UserAgent.BUNDLE_ID: "com.huma.humaapp.dev",
            UserAgent.BUILD: "1",
            UserAgent.SOFTWARE_NAME: "Android",
            UserAgent.SOFTWARE_VERSION: "29 (10)",
            UserAgent.HARDWARE: "samsung SM-G970F",
            UserAgent.CLIENT_TYPE: Client.ClientType.USER_ANDROID.value,
        }
        version = inject.instance(Version)
        expected_server_value = {
            Server.HOST_URL: getattr(self.config.server, "hostUrl", None),
            Server.SERVER: str(version.server),
            Server.API: version.api,
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        value = rsp.json[primitive][0]
        self.assertIsNotNone(value[Primitive.CLIENT])
        self.assertIsNotNone(value[Primitive.SERVER])

        self.assertDictEqual(expected_client_value, value[Primitive.CLIENT])
        self.assertDictEqual(expected_server_value, value[Primitive.SERVER])
        return value


class ModuleResultBasicsTest(CommonModuleResultsTestClass):

    module_maps = {
        "SurgeryDetails": {
            NAME: "SurgeryDetails",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_surgery_details(),
            EXPECTED_RESULT_VALUE: {
                Questionnaire.ANSWERS: sample_surgery_details_answers()
            },
        },
        "ComplexHeartRate": {
            NAME: "HeartRate",
            PRIMITIVE: "HeartRate",
            VALUE: sample_heart_rate(include_extra_fields=True),
            EXPECTED_RESULT_VALUE: {
                "value": 100,
                "variabilityAVNN": 99,
                "goodIBI": 9,
            },
        },
        "AZGroupKeyActionTrigger": {
            NAME: "AZGroupKeyActionTrigger",
            PRIMITIVE: "AZGroupKeyActionTrigger",
            VALUE: sample_group_information(),
            EXPECTED_RESULT_VALUE: {
                AZGroupKeyActionTrigger.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: "Which of the following group is most applicable to you?",
                            QuestionnaireAnswer.ANSWER_TEXT: "I am pregnant",
                        }
                    ]
                },
            },
        },
        "AZFurtherPregnancyKeyActionTrigger": {
            NAME: "AZFurtherPregnancyKeyActionTrigger",
            PRIMITIVE: "AZFurtherPregnancyKeyActionTrigger",
            VALUE: sample_further_information(),
            EXPECTED_RESULT_VALUE: {
                AZFurtherPregnancyKeyActionTrigger.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: "Which of the following group is most applicable to you?",
                            QuestionnaireAnswer.ANSWER_TEXT: "I am pregnant",
                        }
                    ]
                },
            },
        },
        "SimpleHeartRate": {
            NAME: "HeartRate",
            PRIMITIVE: "HeartRate",
            VALUE: sample_heart_rate(),
            EXPECTED_RESULT_VALUE: {VALUE: 100},
        },
        "RespiratoryRate": {
            NAME: "RespiratoryRate",
            PRIMITIVE: "RespiratoryRate",
            VALUE: sample_respiratory_rate(),
            EXPECTED_RESULT_VALUE: {VALUE: 26},
        },
        "MedicationTracker": {
            NAME: "MedicationTracker",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_medication_result(),
            EXPECTED_RESULT_VALUE: {VALUE: 29.0},
        },
        "Weight": {
            NAME: "Weight",
            PRIMITIVE: "Weight",
            VALUE: sample_weight(),
            EXPECTED_RESULT_VALUE: {VALUE: 100.0},
        },
        "PeakFlow": {
            NAME: "PeakFlow",
            PRIMITIVE: "PeakFlow",
            VALUE: sample_peak_flow_data(),
            EXPECTED_RESULT_VALUE: {VALUE: 400},
        },
        "Breathlessness": {
            NAME: "Breathlessness",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_breathlessness(),
            EXPECTED_RESULT_VALUE: {VALUE: 2},
        },
        "DailyCheckIn": {
            NAME: "DailyCheckIn",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_daily_check_in(),
            EXPECTED_RESULT_VALUE: {VALUE: 1},
        },
        "FJSHip": {
            NAME: "FJSHip",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_fjs_hip_score_data(),
            EXPECTED_RESULT_VALUE: {VALUE: 100},
        },
        "FJSKnee": {
            NAME: "FJSKnee",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_fjs_knee_score_data(),
            EXPECTED_RESULT_VALUE: {VALUE: 45.833333333333336},
        },
        "NORFOLK": {
            NAME: "NORFOLK",
            PRIMITIVE: "NORFOLK",
            VALUE: sample_norfolk_questionnaire_module_data(),
            EXPECTED_RESULT_VALUE: {
                NORFOLK.TOTAL_QOL_SCORE: 46.0,
                NORFOLK.PHYSICAL_FUNCTION_LARGER_FIBER: 26.0,
                NORFOLK.ACTIVITIES_OF_DAILY_LIVING: 8.0,
                NORFOLK.SYMPTOMS: 7.0,
                NORFOLK.SMALL_FIBER: 2.0,
                NORFOLK.AUTOMIC: 3.0,
            },
        },
        "Questionnaire": {
            NAME: "Questionnaire",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_questionnaire_with_reverse_and_max_score(),
            EXPECTED_RESULT_VALUE: {VALUE: 43},
        },
        "GeneralAnxietyDisorder": {
            NAME: "GeneralAnxietyDisorder",
            PRIMITIVE: "Questionnaire",
            VALUE: sample_gad_7(),
            EXPECTED_RESULT_VALUE: {
                Questionnaire.ANSWERS: [
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                        QuestionnaireAnswer.QUESTION_ID: "d571d295-9da6-4583-98dc-db92126a4f34",
                        QuestionnaireAnswer.QUESTION: "Feeling nervous, anxious or on edge?",
                        QuestionnaireAnswer.ANSWER_SCORE: 0,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                        QuestionnaireAnswer.QUESTION_ID: "12ed5202-e636-4929-8d31-6ecdec107cee",
                        QuestionnaireAnswer.QUESTION: "Not being able to stop or control worrying?",
                        QuestionnaireAnswer.ANSWER_SCORE: 3,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                        QuestionnaireAnswer.QUESTION_ID: "181c7bf0-e765-45e9-894b-805ff65c529a",
                        QuestionnaireAnswer.QUESTION: "Worrying too much about different things?",
                        QuestionnaireAnswer.ANSWER_SCORE: 0,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                        QuestionnaireAnswer.QUESTION_ID: "359501cb-60cf-4307-b3e5-2aaa8d1949ef",
                        QuestionnaireAnswer.QUESTION: "Trouble relaxing?",
                        QuestionnaireAnswer.ANSWER_SCORE: 0,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Nearly every day",
                        QuestionnaireAnswer.QUESTION_ID: "1739c17d-6bca-440d-a21a-565209700bfd",
                        QuestionnaireAnswer.QUESTION: "Being so restless that it is hard to sit still?",
                        QuestionnaireAnswer.ANSWER_SCORE: 3,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                        QuestionnaireAnswer.QUESTION_ID: "707fbe5e-96bc-4b60-acd9-aeeaa9a1270d",
                        QuestionnaireAnswer.QUESTION: "Becoming easily annoyed or irritable?",
                        QuestionnaireAnswer.ANSWER_SCORE: 0,
                    },
                    {
                        QuestionnaireAnswer.ANSWER_TEXT: "Not at all",
                        QuestionnaireAnswer.QUESTION_ID: "f1065a9d-2bb9-4f68-b143-9685a1bd80b1",
                        QuestionnaireAnswer.QUESTION: "Feeling afraid as if something awful might happen?",
                        QuestionnaireAnswer.ANSWER_SCORE: 0,
                    },
                ],
                Questionnaire.VALUE: 6,
            },
        },
        "BodyMeasurement": {
            NAME: "BodyMeasurement",
            PRIMITIVE: "BodyMeasurement",
            VALUE: sample_body_measurement(),
            EXPECTED_RESULT_VALUE: {
                BodyMeasurement.VISCERAL_FAT: 10,
                BodyMeasurement.TOTAL_BODY_FAT: 50,
                BodyMeasurement.WAIST_CIRCUMFERENCE: 50,
                BodyMeasurement.WAIST_CIRCUMFERENCE_UNIT: HumaMeasureUnit.WAIST_CIRCUMFERENCE.value,
                BodyMeasurement.HIP_CIRCUMFERENCE: 50,
                BodyMeasurement.HIP_CIRCUMFERENCE_UNIT: HumaMeasureUnit.HIP_CIRCUMFERENCE.value,
                BodyMeasurement.WAIST_TO_HIP_RATIO: 1,
            },
        },
    }

    def test_upload_download_module_results(self):
        self.mongo_database["weight"].delete_many({})
        for i, module in enumerate(self.module_maps.values()):
            module_id = module[NAME]
            self.post_results(module_id, module[VALUE])

            result = self.retrieve_result(module_id, module[PRIMITIVE])
            expected = dict(result, **module[EXPECTED_RESULT_VALUE])
            self.assertDictEqual(expected, result, f"Error: {module_id}")

    def test_post_high_frequency_heart_rate_multiple_values(self):
        data = sample_high_frequency_heart_rate_multiple_values()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp_data = rsp.json["HighFrequencyHeartRate"][0]
        self.assertIn("multipleValues", rsp_data)
        self.assertEqual(len(rsp_data["multipleValues"]), 2)
        self.assertIn("rawDataObject", rsp_data)
        self.assertIn("dataType", rsp_data)
        self.assertEqual(rsp_data["dataType"], "MULTIPLE_VALUE")

    def _check_rag_threshold(self, module):
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/user/profiles", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        body = rsp.json
        user = next(filter(lambda x: x["id"], body), None)

        for value in user["ragThresholds"].values():
            if module in value:
                return value[module]
            else:
                self.fail()

    def test_success_post_oxford_only_right_knee(self):
        data = sample_oxford_only_one_knee_score(LegAffected.RIGHT.value)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_score = 12 * 3
        self.assertEqual(rsp[OxfordKneeScore.RIGHT_KNEE_SCORE], expected_score)
        self.assertNotIn(OxfordKneeScore.LEFT_KNEE_SCORE, rsp)

        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.SCORE], expected_score
        )
        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.LEG_AFFECTED],
            LegAffected.RIGHT.value,
        )

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordKneeScore.RIGHT_KNEE_SCORE][COLOR], "#CBEBF0")

    def test_success_symptoms(self):
        data = sample_symptom()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_symptoms_severity_out_of_range(self):
        # Test if severity is out of range for current deployment
        data = sample_symptom(severity=5)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(rsp.json["code"], 100050)

    def test_success_post_oxford_knee_zero_as_total_value_should_have_threshold(self):
        data = sample_oxford_only_one_knee_score(LegAffected.RIGHT.value, 5)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_score = 0
        self.assertEqual(rsp[OxfordKneeScore.RIGHT_KNEE_SCORE], expected_score)
        self.assertNotIn(OxfordKneeScore.LEFT_KNEE_SCORE, rsp)

        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.SCORE], expected_score
        )
        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.LEG_AFFECTED],
            LegAffected.RIGHT.value,
        )

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordKneeScore.RIGHT_KNEE_SCORE][COLOR], "#FBCCD7")

    def test_error_message_post_oxford_only_right_hip(self):
        data = sample_oxford_only_one_hip_score(HipAffected.RIGHT.value)
        # Add inconsistency in hipsData and hipAffected
        data["hipAffected"] = HipAffected.BOTH.value
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, rsp.json["code"])

        data = sample_oxford_only_one_hip_score(HipAffected.RIGHT.value)
        # Set hipsData to empty
        data["hipsData"] = []
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, rsp.json["code"])

        data = sample_oxford_only_one_hip_score(HipAffected.RIGHT.value)
        # Pop hipsData
        data.pop("hipsData")
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, rsp.json["code"])

    def test_success_post_oxford_only_right_hip(self):
        data = sample_oxford_only_one_hip_score(HipAffected.RIGHT.value)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_score = 12 * 3
        self.assertEqual(rsp[OxfordHipScore.RIGHT_HIP_SCORE], expected_score)
        self.assertNotIn(OxfordHipScore.LEFT_HIP_SCORE, rsp)

        self.assertEqual(
            rsp[OxfordHipScore.HIPS_DATA][0][HipData.SCORE], expected_score
        )
        self.assertEqual(
            rsp[OxfordHipScore.HIPS_DATA][0][HipData.HIP_AFFECTED],
            HipAffected.RIGHT.value,
        )

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordHipScore.RIGHT_HIP_SCORE][COLOR], "#CBEBF0")

    def test_success_post_oxford_hip_zero_as_total_value_should_have_threshold(self):
        data = sample_oxford_only_one_hip_score(HipAffected.RIGHT.value, 5)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_score = 0
        self.assertEqual(rsp[OxfordHipScore.RIGHT_HIP_SCORE], expected_score)
        self.assertNotIn(OxfordHipScore.LEFT_HIP_SCORE, rsp)

        self.assertEqual(
            rsp[OxfordHipScore.HIPS_DATA][0][HipData.SCORE], expected_score
        )
        self.assertEqual(
            rsp[OxfordHipScore.HIPS_DATA][0][HipData.HIP_AFFECTED],
            HipAffected.RIGHT.value,
        )

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordHipScore.RIGHT_HIP_SCORE][COLOR], "#FBCCD7")

    def test_success_submit_medication_tracker_no_answer_text(self):
        data = sample_medication_result()
        data[Questionnaire.ANSWERS][0].pop(QuestionnaireAnswer.ANSWER_TEXT)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data[Questionnaire.QUESTIONNAIRE_NAME]}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_post_oxford_only_left_knee(self):
        data = sample_oxford_only_one_knee_score(LegAffected.LEFT.value)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_score = 12 * 3
        self.assertEqual(rsp[OxfordKneeScore.LEFT_KNEE_SCORE], expected_score)
        self.assertNotIn(OxfordKneeScore.RIGHT_KNEE_SCORE, rsp)

        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.SCORE], expected_score
        )
        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.LEG_AFFECTED],
            LegAffected.LEFT.value,
        )

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordKneeScore.LEFT_KNEE_SCORE][COLOR], "#CBEBF0")

    def test_rag_threshold_for_oxford_both_knees(self):
        data = sample_oxford_both_knee_score()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        threshold = self._check_rag_threshold(data["type"])
        self.assertEqual(threshold[OxfordKneeScore.LEFT_KNEE_SCORE][COLOR], "#FFDA9F")
        self.assertEqual(threshold[OxfordKneeScore.RIGHT_KNEE_SCORE][COLOR], "#CBEBF0")

    def test_rag_threshold_for_lysholm(self):
        data = sample_lysholm_and_tegner()
        module_id = LysholmTegnerModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        threshold = self._check_rag_threshold("Lysholm")
        self.assertEqual(threshold[Lysholm.LYSHOLM][COLOR], "#FBCCD7")

    def test_rag_threshold_for_ikdc(self):
        data = sample_ikdc()
        module_id = IKDCModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        threshold = self._check_rag_threshold("IKDC")
        self.assertEqual(threshold[IKDC.VALUE][COLOR], "#FFDA9F")

    def test_rag_threshold_for_oacs(self):
        data = sample_oacs()
        module_id = OACSModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        threshold = self._check_rag_threshold(module_id)
        self.assertEqual(threshold[OACS.OACS_SCORE][COLOR], "#FFDA9F")

    def test_rag_threshold_for_oars(self):
        data = sample_oars()
        module_id = OARSModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        threshold = self._check_rag_threshold(module_id)
        self.assertEqual(threshold[OARS.OARS_SCORE][COLOR], "#FFDA9F")

    def test_success_post_oxford_both_knees(self):
        data = sample_oxford_both_knee_score()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]][0]

        expected_right_score = 12 * 3
        expected_left_score = 12 * 2

        self.assertEqual(rsp[OxfordKneeScore.RIGHT_KNEE_SCORE], expected_right_score)
        self.assertEqual(rsp[OxfordKneeScore.LEFT_KNEE_SCORE], expected_left_score)

        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.SCORE], expected_right_score
        )
        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][0][LegData.LEG_AFFECTED],
            LegAffected.RIGHT.value,
        )

        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][1][LegData.SCORE], expected_left_score
        )
        self.assertEqual(
            rsp[OxfordKneeScore.LEGS_DATA][1][LegData.LEG_AFFECTED],
            LegAffected.LEFT.value,
        )

    def test_failure_oxford_both_knees_only_one_is_present_not_got_created(self):
        data = sample_oxford_only_one_knee_score(LegAffected.BOTH.value)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json[data["type"]]
        self.assertEqual(len(rsp), 0)

    def test_success_submit_koos(self):
        data = sample_koos_and_womac_data()
        module_id = KOOSQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json

        primitives = [p.__name__ for p in KOOSQuestionnaireModule.primitives]
        for primitive in primitives:
            self.assertIn(primitive, rsp)

    def test_success_retrieve_koos_with_user(self):
        data = sample_koos_and_womac_data()
        module_id = KOOSQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        questionnaire_data = rsp.json[Questionnaire.__name__][0]
        questionnaire_answers = questionnaire_data[Questionnaire.ANSWERS]

        self.assertIn(Questionnaire.SKIPPED, questionnaire_data)
        self.assertEqual(1, len(questionnaire_data[Questionnaire.SKIPPED]))
        for answer in questionnaire_answers:
            self.assertIn(QuestionnaireAnswer.SELECTION_CRITERIA, answer)
            self.assertIn(QuestionnaireAnswer.FORMAT, answer)

    def test_success_question_got_localized_for_exact_module(self):
        data = sample_koos_and_womac_data()
        module_id = KOOSQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        # firstly, verifying if it has been properly translated
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = rsp.json
        translated_question = rsp[Questionnaire.__name__][0][Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.QUESTION
        ]
        question_id = data[Questionnaire.ANSWERS][0][QuestionnaireAnswer.QUESTION_ID]
        self.assertEqual(f"{question_id}: Some tricky, question", translated_question)

        # now getting data from db to make sure it has proper module placeholder,
        # as we have same keys for multiple modules
        data_from_db = self.mongo_database[Questionnaire.__name__.lower()].find_one(
            {Primitive.MODULE_ID: module_id}
        )
        placeholder = data_from_db[Questionnaire.ANSWERS][0][
            QuestionnaireAnswer.QUESTION
        ]
        self.assertEqual(placeholder, "hu_koos_1")

    def test_success_localized_answer_text_is_a_valid_question_option(self):
        data = sample_norfolk_questionnaire_module_data()
        module_id = NorfolkQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        # verify translation
        rsp = rsp.json
        submitted_answer = rsp[Questionnaire.__name__][0][Questionnaire.ANSWERS][25]
        translated_answers_text = submitted_answer[QuestionnaireAnswer.ANSWER_TEXT]
        self.assertEqual("Severe problem", translated_answers_text)

        # now get data from db to make sure it has proper module placeholder,
        # as we have same values for multiple keys
        data_from_db = self.mongo_database[Questionnaire.__name__.lower()].find_one(
            {Primitive.MODULE_ID: module_id}
        )
        placeholder = data_from_db[Questionnaire.ANSWERS][25][
            QuestionnaireAnswer.ANSWER_TEXT
        ]
        self.assertEqual(placeholder, "hu_norfolk_commonOp_Severe")

        # test if the the placeholder of the translation is a valid option
        # in the module config of the question
        module_config = self.retrieve_module_config(
            module_id=NorfolkQuestionnaireModule.moduleId
        )
        question_map = build_question_map(module_config["configBody"])
        question_id = submitted_answer[QuestionnaireAnswer.QUESTION_ID]
        options = question_map[question_id].get("options", [])
        labels = [option["label"] for option in options]
        self.assertIn(placeholder, labels)

    def test_failure_submit_koos_not_enough_answers(self):
        data = sample_koos_and_womac_data_with_not_enough_answers()
        module_id = KOOSQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(rsp.json["code"], 120014)

    def test_post_high_frequency_heart_rate_ppg_type(self):
        data = sample_high_frequency_heart_rate_ppg_type()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp_data = rsp.json["HighFrequencyHeartRate"][0]
        self.assertIn("dataType", rsp_data)
        self.assertEqual(rsp_data["dataType"], "PPG_VALUE")
        self.assertEqual(rsp_data["value"], 90)

    def submit_fjs(self, limit: int):
        data = sample_fjs_knee_score_data()
        data = {**data, Questionnaire.ANSWERS: data[Questionnaire.ANSWERS][:limit]}
        module_id = FJSKneeScoreModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        return rsp

    def test_failure_submit_fjs_module_not_enough_answers(self):
        # we should have min 8 answered questions
        rsp = self.submit_fjs(7)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(rsp.json["code"], 120014)

    def test_success_submit_fjs_module_min_limit_of_questions(self):
        rsp = self.submit_fjs(8)
        self.assertEqual(201, rsp.status_code)

    def test_high_frequency_heart_rate_type(self):
        data = sample_high_frequency_heart_rate_ppg_type()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp_data = rsp.json["HighFrequencyHeartRate"][0]
        self.assertEqual(rsp_data["heartRateType"], "HIGH_FREQ")

    def test_success_create_and_retrieve_oxford_hip_score(self):
        data = sample_oxford_hip_score()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        module_result_id = rsp.json[data["type"]][0]["id"]
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/primitive/{data['type']}/{module_result_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["value"], 5)

    def _send_several_results(self, dates):
        data = sample_high_frequency_heart_rate_ppg_type()
        start_times = [f"{d}T00:00:00Z" for d in dates]
        end_times = [f"{d}T02:00:00Z" for d in dates]

        for period in zip(start_times, end_times):
            data[Primitive.START_DATE_TIME] = period[0]
            data[Primitive.END_DATE_TIME] = period[1]

            rsp = self.flask_client.post(
                f"{self.base_route}/{data['type']}",
                json=[data],
                headers=self.headers,
            )
            self.assertEqual(201, rsp.status_code)

    def test_success_retrieve_unseen_results_only(self):
        module_id = HighFrequencyHeartRateModule.moduleId
        dates = [
            "2019-06-30",
            "2019-07-30",
            "2019-08-30",
        ]
        self._send_several_results(dates)

        self.mongo_database[Primitive.UNSEEN_PRIMITIVES_COLLECTION].remove()

        dates = [
            "2019-06-15",
            "2019-07-15",
            "2019-08-15",
        ]
        self._send_several_results(dates)

        body = {
            RetrieveModuleResultsRequestObject.DIRECTION: SortField.Direction.DESC.value,
            RetrieveModuleResultsRequestObject.LIMIT: 6,
            RetrieveModuleResultsRequestObject.MODULE_ID: module_id,
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers, json=body
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json[module_id]))
        primitives_with_flags = [p for p in rsp.json[module_id] if Primitive.FLAGS in p]
        self.assertEqual(3, len(primitives_with_flags))

        body[RetrieveModuleResultsRequestObject.UNSEEN_ONLY] = True
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers, json=body
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json[module_id]))

    def test_success_retrieve_heart_freq_rate_module_result(self):
        data = sample_high_frequency_heart_rate_ppg_type()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        module_result_id = rsp.json[data["type"]][0]["id"]
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/primitive/{data['type']}/{module_result_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json[ModuleConfig.MODULE_ID], data["type"])

    def test_post_high_frequency_heart_rate_single_value(self):
        data = sample_high_frequency_heart_rate_single_value()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp_data = rsp.json["HighFrequencyHeartRate"][0]
        self.assertIn("dataType", rsp_data)
        self.assertEqual(rsp_data["dataType"], "SINGLE_VALUE")
        self.assertEqual(rsp_data["value"], 90)

    def test_high_frequency_heart_rate_search(self):
        data = sample_high_frequency_heart_rate_multiple_values()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        # adding another one with other date ranges
        data = sample_high_frequency_heart_rate_multiple_values_second()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        search_payload = {
            "fromDateTime": "2019-06-30T00:00:00Z",
            "toDateTime": "2019-08-30T02:00:00Z",
        }

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search",
            headers=self.headers,
            json=search_payload,
        )
        self.assertEqual(200, rsp.status_code)

        rsp_data = rsp.json["HighFrequencyHeartRate"]
        self.assertEqual(len(rsp_data), 2)

    def test_success_submit_kccq_questionnaire(self):
        data = sample_kccq_data()
        module_id = KCCQQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        primitives = [p.__name__ for p in KCCQQuestionnaireModule.primitives]
        for primitive in primitives:
            self.assertIn(primitive, rsp.json)

    def test_failure_submit_kccq_zero_weight_answers(self):
        data = sample_kccq_all_zero_weight_anwsers()
        module_id = KCCQQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(
            rsp.json["code"], ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED
        )

    def test_failure_submit_kccq_questionnaire_insufficient_answers(self):
        data = sample_kccq_data_missing_answers()
        module_id = KCCQQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(
            rsp.json["code"], ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED
        )

    def test_success_submit_sf36_questionnaire(self):
        data = sample_sf36_data()
        module_id = SF36QuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        primitives = [p.__name__ for p in SF36QuestionnaireModule.primitives]
        for primitive in primitives:
            self.assertIn(primitive, rsp.json)

    def test_success_submit_questionnaire_ignore_fields_module_id_field(self):
        data = sample_sf36_data()
        module_id = SF36QuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        data_from_db = self.mongo_database[module_id.lower()].find_one(
            {Primitive.ID_: ObjectId(rsp.json["ids"][1])}
        )
        self.assertEqual(data_from_db[Primitive.MODULE_ID], module_id)

    def test_submit_with_numeric_validation(self):
        # TODO: unblock test when validation is back
        return
        module_id = NorfolkQuestionnaireModule.moduleId
        data = sample_norfolk_questionnaire_module_data()

        def set_answer_text(answer_text: str):
            data[Questionnaire.ANSWERS][-1] = {
                QuestionnaireAnswer.ANSWER_TEXT: answer_text,
                QuestionnaireAnswer.QUESTION_ID: "hu_norfolk_generic_q10",
                QuestionnaireAnswer.QUESTION: "something",
            }

        def submit_data_with_error(err_message: str):
            rsp = self.flask_client.post(
                f"{self.base_route}/{module_id}",
                json=[data],
                headers=self.headers,
            )
            self.assertEqual(400, rsp.status_code)
            self.assertEqual(err_message, rsp.json["message"])

        # trying to submit 'numeric-like' answer
        set_answer_text("1.45.76")
        submit_data_with_error("hu_norfolk_generic_q10 should be numeric")

        # trying to submit text answer
        set_answer_text("AAAAA")
        submit_data_with_error("hu_norfolk_generic_q10 should be numeric")

        # trying to submit data out of range
        set_answer_text("99999")
        submit_data_with_error("hu_norfolk_generic_q10 should not be greater 100")

        # trying to submit under lower limit
        set_answer_text("20")
        submit_data_with_error("hu_norfolk_generic_q10 should not be lower 50")

        # trying to submit negative number
        set_answer_text("-20")
        submit_data_with_error("hu_norfolk_generic_q10 should not be lower 50")

        # trying to submit right answer
        set_answer_text("55")
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_submit_norfolk_questionnaire(self):
        data = sample_norfolk_questionnaire_module_data()
        module_id = NorfolkQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        primitives = [p.__name__ for p in NorfolkQuestionnaireModule.primitives]
        for primitive in primitives:
            self.assertIn(primitive, rsp.json)

        questionnaire_answers = rsp.json[Questionnaire.__name__][0][
            Questionnaire.ANSWERS
        ]
        for answer in questionnaire_answers:
            self.assertNotIn("Feet,Legs,None", answer[QuestionnaireAnswer.ANSWER_TEXT])

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            "/api/extensions/v1beta/user/profiles", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        user = next(filter(lambda x: x["id"], rsp.json), None)
        for item in user["ragThresholds"].values():
            norfolk_thesholds = item[NORFOLK.__name__]
            self.assertNotIn("fieldNameThatDoesNotExist", norfolk_thesholds)

            for attr in NORFOLK.__annotations__.keys():
                self.assertIn(attr, norfolk_thesholds)
                self.assertIn(RagThreshold.COLOR, norfolk_thesholds[attr])
                self.assertIn(RagThreshold.DIRECTION, norfolk_thesholds[attr])

    def test_failure_submit_norfolk_questionnaire_insufficient_answers(self):
        data = sample_norfolk_questionnaire_missing_answers()
        module_id = NorfolkQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(
            rsp.json["code"], ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED
        )

    def test_success_submit_sf36_questionnaire_and_search_as_user(self):
        data = sample_sf36_data()
        module_id = SF36QuestionnaireModule.moduleId
        headers = self.get_headers_for_token(VALID_USER_ID)

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=headers,
        )

        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_search_sf36_no_data(self):
        module_id = SF36QuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_submit_step(self):
        module_id = Step.__name__
        data = sample_steps()
        rsp = self.post_results(module_id, data)
        self.assertEqual(201, rsp.status_code)

    def test_sucess_submit_step_and_search_as_user(self):
        module_id = Step.__name__
        data = sample_steps()
        rsp = self.post_results(module_id, data)
        self.assertEqual(201, rsp.status_code)
        expected_multiple_values = {
            "id": "5b5279d1e303d394db6ea0f8",
            "h": {"0": 100},
            "d": "2019-06-30T00:00:00.000000Z",
        }

        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

        rsp_steps = rsp.json[Step.__name__][0]
        self.assertDictEqual(expected_multiple_values, rsp_steps["multipleValues"][0])

    def test_sucess_submit_deprecated_step_and_search_as_user(self):
        module_id = Step.__name__
        data = sample_steps_deprecated()
        rsp = self.post_results(module_id, data)
        self.assertEqual(201, rsp.status_code)
        expected_multiple_values = {
            "id": "5b5279d1e303d394db6ea0f8",
            "h": {"0": 250},
            "d": "2019-06-30T00:00:00.000000Z",
        }

        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

        rsp_steps = rsp.json[Step.__name__][0]
        self.assertDictEqual(expected_multiple_values, rsp_steps["multipleValues"][0])

    def test_failure_submit_with_module_config_id_for_different_module(self):
        bvi_module_id = BVIModule.moduleId
        weight_config_id = "5e94b2007773091c9a592660"
        rsp = self.flask_client.post(
            f"{self.base_route}/{bvi_module_id}",
            json=[sample_body_measurement()],
            query_string={"moduleConfigId": weight_config_id},
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)


class TestMeasureUnits(BaseModuleResultTest):
    def test_success_bmi_and_weight_measure_units(self):
        data = sample_bmi_data()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{BMI.__name__}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{BMI.__name__}/search", json={}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        weight_rsp_data = rsp.json.get(Weight.__name__)[0]
        self.assertEqual(weight_rsp_data["valueUnit"], "kg")

    def test_success_peak_flow_units(self):
        data = sample_peak_flow_data()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{PeakFlow.__name__}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{PeakFlow.__name__}/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            rsp.json.get(PeakFlow.__name__)[0]["valueUnit"],
            "L/s",
        )

    def test_success_heart_rate(self):
        data = sample_heart_rate()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json.get(data["type"])[0]["valueUnit"], "bpm")

    def test_success_heart_rate_with_variability(self):
        data = sample_heart_rate(include_extra_fields=True)
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            rsp.json.get(data["type"])[0]["variabilitySDNN"], data["variabilitySDNN"]
        )
        self.assertEqual(
            rsp.json.get(data["type"])[0]["classification"], data["classification"]
        )

    def test_failure_payload_passed_as_dictionary(self):
        # https://sentry.io/organizations/huma-therapeutics-ltd-qc/issues/2636556755/?project=5738131
        data = sample_respiratory_rate()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}", json=data, headers=headers
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def test_success_respiratory_rate(self):
        data = sample_respiratory_rate()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}", json=[data], headers=headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json.get(data["type"])[0]["valueUnit"], "rpm")

    def test_success_check_submitter_id(self):
        headers = self.get_headers_for_token(VALID_MANAGER_ID)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Questionnaire",
            json=[sample_questionnaire()],
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)
        result_id = rsp.json["ids"][0]
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/primitive/Questionnaire/{result_id}",
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_USER_ID, rsp.json[Primitive.USER_ID])
        self.assertEqual(VALID_MANAGER_ID, rsp.json[Primitive.SUBMITTER_ID])

    def test_failure_stringified_json_body(self):
        headers = self.get_headers_for_token(VALID_MANAGER_ID)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Questionnaire",
            json=SAMPLE_STRINGFIED_PAYLOAD,
            headers=headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def test_success_retrieve_KCCQ_with_user(self):
        data = sample_kccq_data()
        module_id = KCCQQuestionnaireModule.moduleId
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}/search",
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_submit_empty_answers_gad7_module(self):
        module_id = GeneralAnxietyDisorderModule.moduleId
        data = sample_gad_7()
        data.update({Questionnaire.ANSWERS: []})
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_submit_invalid_value_medication_tracker_module(self):
        module_id = MedicationTrackerModule.moduleId
        data = sample_medication_result()
        data[Questionnaire.ANSWERS][0][QuestionnaireAnswer.ANSWER_TEXT] = -1
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(400, rsp.status_code)

        data = sample_medication_result()
        data[Questionnaire.ANSWERS][0][QuestionnaireAnswer.ANSWER_TEXT] = 101
        rsp = self.flask_client.post(
            f"{self.base_route}/{module_id}",
            json=[data],
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(400, rsp.status_code)
