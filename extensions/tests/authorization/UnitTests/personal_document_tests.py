import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.router.user_profile_request import (
    RetrievePersonalDocumentsRequestObject,
    CreatePersonalDocumentRequestObject,
)
from extensions.authorization.use_cases.retrieve_personal_documents_use_case import (
    RetrievePersonalDocumentsUseCase,
)

from extensions.authorization.use_cases.create_personal_document_use_case import (
    CreatePersonalDocumentUseCase,
)
from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.tests.auth.test_helpers import USER_ID


def get_create_personal_document_request_object_sample() -> dict:
    return {
        CreatePersonalDocumentRequestObject.USER_ID: USER_ID,
        CreatePersonalDocumentRequestObject.FILE_TYPE: "PHOTO",
        CreatePersonalDocumentRequestObject.FILE_OBJECT: {
            S3Object.BUCKET: "bucket",
            S3Object.KEY: "key",
        },
        CreatePersonalDocumentRequestObject.NAME: "test",
    }


class CreatePersonalDocumentUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mocked_auth_repo = MagicMock()

    def get_create_personal_document_use_case(self):
        return CreatePersonalDocumentUseCase(self.mocked_auth_repo)

    def test_success_validator_create_personal_document(self):
        use_case = self.get_create_personal_document_use_case()
        request_data = get_create_personal_document_request_object_sample()
        use_case.execute(CreatePersonalDocumentRequestObject.from_dict(request_data))

    def test_failure_validator_create_personal_document_wrong_filetype(self):
        use_case = self.get_create_personal_document_use_case()
        request_data = get_create_personal_document_request_object_sample()
        request_data[CreatePersonalDocumentRequestObject.FILE_TYPE] = "WRONG_VALUE"
        with self.assertRaises(ConvertibleClassValidationError):
            use_case.execute(
                CreatePersonalDocumentRequestObject.from_dict(request_data)
            )

    def test_failure_validator_create_personal_document_missing_file_object(self):
        use_case = self.get_create_personal_document_use_case()
        request_data = get_create_personal_document_request_object_sample()
        del request_data[CreatePersonalDocumentRequestObject.FILE_OBJECT]
        with self.assertRaises(ConvertibleClassValidationError):
            use_case.execute(
                CreatePersonalDocumentRequestObject.from_dict(request_data)
            )

    def test_failure_validator_create_personal_document_name_too_long(self):
        use_case = self.get_create_personal_document_use_case()
        request_data = get_create_personal_document_request_object_sample()
        request_data[CreatePersonalDocumentRequestObject.NAME] = "A" * 256
        with self.assertRaises(ConvertibleClassValidationError):
            use_case.execute(
                CreatePersonalDocumentRequestObject.from_dict(request_data)
            )


class RetrievePersonalDocumentsUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mocked_auth_repo = MagicMock()

    def get_retrieve_personal_documents_use_case(self):
        return RetrievePersonalDocumentsUseCase(self.mocked_auth_repo)

    def test_failure_validator_retrieve_personal_documents_missing_user_id(self):
        use_case = self.get_retrieve_personal_documents_use_case()
        request_data = {}
        with self.assertRaises(ConvertibleClassValidationError):
            use_case.execute(
                RetrievePersonalDocumentsRequestObject.from_dict(request_data)
            )
