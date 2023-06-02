from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.user import User
from extensions.module_result.router.custom_module_config_requests import (
    CreateOrUpdateCustomModuleConfigRequestObject,
    RetrieveCustomModuleConfigsRequestObject, RetrieveModuleConfigLogsRequestObject,
)
from extensions.tests.module_result.UnitTests.test_helpers import (
    sample_custom_module_schedule,
    sample_rag_thresholds,
    SAMPLE_USER_ID,
    MODULE_ID,
)
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError

MODULE_CONFIG_PATH = "extensions.module_result.models.module_config.ModuleConfig"


@patch(f"{MODULE_CONFIG_PATH}.validate", MagicMock())
class TestCreateOrUpdateCustomModuleConfigRequestObject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            binder.bind(DefaultRoles, DefaultRoles())

        inject.clear_and_configure(bind)

    def test_success_create_custom_module_config_request_object(self):
        user = AuthorizedUser(User())
        request_object = CreateOrUpdateCustomModuleConfigRequestObject.from_dict(
            {
                CreateOrUpdateCustomModuleConfigRequestObject.ID: SAMPLE_USER_ID,
                CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: SAMPLE_USER_ID,
                CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: MODULE_ID,
                CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
                CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds(),
                CreateOrUpdateCustomModuleConfigRequestObject.SCHEDULE: sample_custom_module_schedule(),
                CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
                CreateOrUpdateCustomModuleConfigRequestObject.USER: user,
            }
        )
        self.assertIsNotNone(request_object)

    def test_failure_no_reason(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrUpdateCustomModuleConfigRequestObject.from_dict(
                {
                    CreateOrUpdateCustomModuleConfigRequestObject.ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: MODULE_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds(),
                    CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
                }
            )

    def test_failure_no_module_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrUpdateCustomModuleConfigRequestObject.from_dict(
                {
                    CreateOrUpdateCustomModuleConfigRequestObject.ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
                    CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
                }
            )

    def test_failure_invalid_schedule(self):
        schedule = sample_custom_module_schedule()
        schedule.update({"timesPerDuration": 2})
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrUpdateCustomModuleConfigRequestObject.from_dict(
                {
                    CreateOrUpdateCustomModuleConfigRequestObject.ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: MODULE_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
                    CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds(),
                    CreateOrUpdateCustomModuleConfigRequestObject.SCHEDULE: schedule,
                    CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
                }
            )

    def test_failure_invalid_times_of_readings(self):
        schedule = sample_custom_module_schedule()
        schedule.update({"timesOfReadings": schedule["timesOfReadings"] * 7})
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrUpdateCustomModuleConfigRequestObject.from_dict(
                {
                    CreateOrUpdateCustomModuleConfigRequestObject.ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: SAMPLE_USER_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: MODULE_ID,
                    CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
                    CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds(),
                    CreateOrUpdateCustomModuleConfigRequestObject.SCHEDULE: schedule,
                    CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
                }
            )


class TestRetrieveCustomModuleConfigsRequestObject(TestCase):
    def test_success_create_retrieve_module_result_req_obj(self):
        request_object = RetrieveCustomModuleConfigsRequestObject.from_dict(
            {RetrieveCustomModuleConfigsRequestObject.USER_ID: SAMPLE_USER_ID}
        )
        self.assertIsNotNone(request_object)

    def test_no_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveCustomModuleConfigsRequestObject.from_dict({})


class TestRetrieveCustomModuleConfigLogsRequestObject(TestCase):
    def test_success_create_retrieve_module_config_log_req_obj(self):
        request_object = RetrieveModuleConfigLogsRequestObject.from_dict(
            {
                RetrieveModuleConfigLogsRequestObject.USER_ID: SAMPLE_USER_ID,
                RetrieveModuleConfigLogsRequestObject.MODULE_CONFIG_ID: SAMPLE_USER_ID
            }
        )
        self.assertIsNotNone(request_object)

    def test_failure_no_required_fields(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveModuleConfigLogsRequestObject.from_dict({})
