from unittest import TestCase

from sdk.auth.validators import (
    validate_project_id,
    validate_client_id,
    validate_project_and_client_id,
)
from sdk.common.exceptions.exceptions import (
    InvalidClientIdException,
    InvalidProjectIdException,
    ErrorCodes,
)
from sdk.phoenix.config.server_config import Project, Client

SAMPLE_PROJECT_ID = "p1"
SAMPLE_CLIENT_ID = "c1"
SAMPLE_PROJECT = Project.from_dict(
    {
        Project.ID: SAMPLE_PROJECT_ID,
        Project.MASTER_KEY: "88888888",
        Project.CLIENTS: [
            {
                Client.CLIENT_ID: SAMPLE_CLIENT_ID,
                Client.CLIENT_TYPE: Client.ClientType.USER_ANDROID.value,
            }
        ],
    }
)


class ValidatorsTestCase(TestCase):
    def test_success_validate_project_id(self):
        try:
            validate_project_id(SAMPLE_PROJECT_ID, SAMPLE_PROJECT)
        except InvalidProjectIdException:
            self.fail()

    def test_failure_validate_project_id(self):
        with self.assertRaises(InvalidProjectIdException) as context:
            validate_project_id("invalid project id", SAMPLE_PROJECT)
        self.assertEqual(context.exception.code, ErrorCodes.INVALID_PROJECT_ID)
        self.assertEqual("Invalid project id", str(context.exception))

    def test_success_validate_client_id(self):
        try:
            validate_client_id(SAMPLE_CLIENT_ID, SAMPLE_PROJECT)
        except InvalidClientIdException:
            self.fail()

    def test_failure_validate_client_id(self):
        with self.assertRaises(InvalidClientIdException) as context:
            validate_client_id("invalid client id", SAMPLE_PROJECT)
        self.assertEqual(context.exception.code, ErrorCodes.INVALID_CLIENT_ID)
        self.assertEqual("Invalid client id", str(context.exception))

    def test_success_validate_client_and_project_id(self):
        try:
            validate_project_and_client_id(
                SAMPLE_CLIENT_ID, SAMPLE_PROJECT_ID, SAMPLE_PROJECT
            )
        except (InvalidClientIdException, InvalidProjectIdException):
            self.fail()

    def test_failure_validate_client_and_project_id_with_invalid_client_id(self):
        with self.assertRaises(InvalidClientIdException) as context:
            validate_project_and_client_id(
                "invalid client id", SAMPLE_PROJECT_ID, SAMPLE_PROJECT
            )
        self.assertEqual(context.exception.code, ErrorCodes.INVALID_CLIENT_ID)
        self.assertEqual("Invalid client id", str(context.exception))

    def test_failure_validate_client_and_project_id_with_invalid_project_id(self):
        with self.assertRaises(InvalidProjectIdException) as context:
            validate_project_and_client_id(
                SAMPLE_CLIENT_ID, "invalid project id", SAMPLE_PROJECT
            )
        self.assertEqual(context.exception.code, ErrorCodes.INVALID_PROJECT_ID)
        self.assertEqual("Invalid project id", str(context.exception))
