from unittest import TestCase
from unittest.mock import patch, MagicMock

from extensions.deployment.router.deployment_requests import (
    RetrieveUserNotesRequestObject,
)
from extensions.deployment.use_case.retrieve_user_notes_use_case import (
    RetrieveUserNotesUseCase,
)
from extensions.tests.authorization.UnitTests.test_helpers import (
    get_sample_deployment_with_module_configs,
    get_user_notes_sample_request,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class MockModuleResultService(MagicMock):
    retrieve_observation_notes = MagicMock()


class MockDeploymentService(MagicMock):
    retrieve_user_notes = MagicMock()
    retrieve_user_observation_notes = MagicMock()


class MockDeploymentRepo(MagicMock):
    retrieve_deployment = MagicMock()
    retrieve_deployment.return_value = get_sample_deployment_with_module_configs()


class MockModuleResultRepo(MagicMock):
    retrieve_primitives = MagicMock()


class UserNotesTests(TestCase):
    def setUp(self) -> None:
        MockDeploymentRepo.retrieve_deployment.reset_mock()
        MockDeploymentRepo.retrieve_deployment.return_value = (
            get_sample_deployment_with_module_configs()
        )
        MockModuleResultService.retrieve_observation_notes.reset_mock()

    @patch(
        "extensions.deployment.use_case.retrieve_user_notes_use_case.DeploymentService",
        MockDeploymentService,
    )
    @patch(
        "extensions.deployment.use_case.retrieve_user_notes_use_case.ModuleResultService",
        MockModuleResultService,
    )
    def test_success_retrieve_user_notes(self):
        MockDeploymentService().retrieve_user_observation_notes.return_value = ([], 0)
        use_case = RetrieveUserNotesUseCase(
            MockDeploymentRepo(), MockModuleResultRepo()
        )
        use_case.module_result_service = MockModuleResultService()
        request_object = RetrieveUserNotesRequestObject.from_dict(
            get_user_notes_sample_request()
        )
        use_case.execute(request_object)
        MockDeploymentRepo().retrieve_deployment.assert_called_once()
        MockDeploymentService().retrieve_user_notes.assert_called_once()
        MockDeploymentService().retrieve_user_observation_notes.assert_called_once()
        MockModuleResultService().retrieve_observation_notes.assert_called_once()

    def test_failure_request_object_with_no_user_id(self):
        request_obj = get_user_notes_sample_request()
        request_obj.pop(RetrieveUserNotesRequestObject.USER_ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveUserNotesRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_no_deployment_id(self):
        request_obj = get_user_notes_sample_request()
        request_obj.pop(RetrieveUserNotesRequestObject.DEPLOYMENT_ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveUserNotesRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_invalid_deployment_id(self):
        request_obj = get_user_notes_sample_request()
        request_obj[RetrieveUserNotesRequestObject.DEPLOYMENT_ID] = "depId"
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveUserNotesRequestObject.from_dict(request_obj)

    def test_success_observation_notes_count(self):
        deployment = get_sample_deployment_with_module_configs()
        self.assertEqual(2, len(deployment.observation_notes))
