import unittest
from unittest.mock import patch

from freezegun import freeze_time

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.autocomplete.repository.mongo_autocomplete_repository import (
    MongoAutoCompleteRepository,
)
from extensions.tests.autocomplete.UnitTests.test_helpers import (
    sample_autocomplete_metadata,
)
from sdk.common.localization.utils import Language

REPO_PATH = "extensions.autocomplete.repository.mongo_autocomplete_repository"


class MongoAutocompleteRepoTestCase(unittest.TestCase):
    @patch(f"{REPO_PATH}.MongoAutoCompleteMetadata")
    @patch(f"{REPO_PATH}.AutocompleteMetadata")
    def test_success_retrieve_autocomplete_metadata(self, metadata, mongo):
        language = Language.EN
        module_id = "module_id"
        repo = MongoAutoCompleteRepository()
        repo.retrieve_autocomplete_metadata(module_id=module_id, language=language)
        mongo.objects.assert_called_with(moduleId=module_id, language=language)
        metadata.from_dict.assert_called_with(mongo.objects().first().to_dict())

    @freeze_time("2012-01-01")
    @patch(f"{REPO_PATH}.MongoAutoCompleteMetadata")
    def test_success_update_autocomplete_metadata__update_existing(self, mongo):
        language = Language.EN
        module_id = "module_id"
        metadata_dict = sample_autocomplete_metadata()
        metadata_obj = AutocompleteMetadata.from_dict(metadata_dict)
        repo = MongoAutoCompleteRepository()
        repo.update_autocomplete_metadata(metadata=metadata_obj)
        mongo.objects.assert_called_with(moduleId=module_id, language=language)
        mongo.objects().first().update.assert_called_with(
            **metadata_dict, updateDateTime="2012-01-01T00:00:00.000000Z"
        )

    @freeze_time("2012-01-01")
    @patch(f"{REPO_PATH}.MongoAutoCompleteMetadata")
    def test_success_update_autocomplete_metadata__create_new(self, mongo):
        language = Language.EN
        module_id = "module_id"
        metadata_dict = sample_autocomplete_metadata()
        metadata_obj = AutocompleteMetadata.from_dict(metadata_dict)
        mongo.objects().first.return_value = None

        repo = MongoAutoCompleteRepository()
        repo.update_autocomplete_metadata(metadata=metadata_obj)
        mongo.objects.assert_called_with(moduleId=module_id, language=language)
        mongo.objects().first.update.assert_not_called()
        mongo().save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
