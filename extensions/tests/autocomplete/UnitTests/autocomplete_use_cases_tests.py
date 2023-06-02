import unittest
from unittest.mock import MagicMock

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.autocomplete.repository.autocomplete_repository import (
    AutoCompleteRepository,
)
from extensions.autocomplete.router.autocomplete_requests import (
    UpdateAutoCompleteSearchMetadataRequestObject,
)
from extensions.autocomplete.use_cases.update_autocomplete_metadata_use_case import (
    UpdateAutoCompleteMetadataUseCase,
)
from extensions.common.s3object import S3Object
from sdk.common.utils import inject

USE_CASE_PATH = (
    "extensions.autocomplete.use_cases.update_autocomplete_metadata_use_case"
)


class MockAutoCompleteRepo:
    update_autocomplete_metadata = MagicMock()


class UpdateAutoCompleteMetadataUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_autocomplete_repository = MockAutoCompleteRepo

        def bind(binder):
            binder.bind_to_provider(
                AutoCompleteRepository, self.mock_autocomplete_repository
            )

        inject.clear_and_configure(bind)

    def test_success(self):
        request_obj = UpdateAutoCompleteSearchMetadataRequestObject.from_dict(
            {
                UpdateAutoCompleteSearchMetadataRequestObject.METADATA: [
                    {
                        AutocompleteMetadata.MODULE_ID: "",
                        AutocompleteMetadata.LANGUAGE: "",
                        AutocompleteMetadata.S3_OBJECT: {
                            S3Object.BUCKET: "bucket",
                            S3Object.KEY: "key",
                            S3Object.REGION: "eu",
                        },
                    }
                ]
            }
        )
        try:
            UpdateAutoCompleteMetadataUseCase().execute(request_obj)
        except Exception as error:
            self.fail(error)
