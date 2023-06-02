import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.router.user_profile_request import (
    CreateHelperAgreementLogRequestObject,
)
from extensions.authorization.use_cases.create_helper_agreement_log_use_case import (
    CreateHelperAgreementLogUseCase,
)
from extensions.deployment.exceptions import (
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)

AUTH_SERVICE_PATH = "extensions.authorization.use_cases.create_helper_agreement_log_use_case.AuthorizationService"
OFF_BOARD_USE_CASE_PATH = "extensions.authorization.use_cases.create_helper_agreement_log_use_case.OffBoardUserUseCase"


def sample_request_object(status):
    req_obj_dict = {
        CreateHelperAgreementLogRequestObject.USER_ID: "60a20732edcf03b6b227dc5b",
        CreateHelperAgreementLogRequestObject.DEPLOYMENT_ID: "60a20766c85cd55b38c99e12",
        CreateHelperAgreementLogRequestObject.STATUS: status.value,
    }
    return CreateHelperAgreementLogRequestObject.from_dict(req_obj_dict)


class CreateHelperAgreementLogTestCase(unittest.TestCase):
    @patch(AUTH_SERVICE_PATH)
    def test_success_process_request(self, mock_auth_service):
        repo = MagicMock()
        use_case = CreateHelperAgreementLogUseCase(auth_repo=repo)
        req_obj = sample_request_object(HelperAgreementLog.Status.AGREE_AND_ACCEPT)
        use_case.execute(req_obj)
        repo.create_helper_agreement_log.assert_called_with(
            helper_agreement_log=req_obj
        )

    @patch(OFF_BOARD_USE_CASE_PATH)
    @patch(AUTH_SERVICE_PATH)
    def test_success_offboard_user(self, mock_auth_service, mock_use_case):
        repo = MagicMock()
        mock_use_case.execute = MagicMock()
        use_case = CreateHelperAgreementLogUseCase(auth_repo=repo)
        req_obj = sample_request_object(HelperAgreementLog.Status.DO_NOT_AGREE)
        with self.assertRaises(OffBoardingRequiredError) as context:
            use_case.execute(req_obj)

        self.assertEqual(
            context.exception.code,
            DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_HELPER_AGREEMENT,
        )


if __name__ == "__main__":
    unittest.main()
