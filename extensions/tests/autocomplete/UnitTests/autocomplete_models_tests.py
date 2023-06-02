import unittest

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.tests.autocomplete.UnitTests.test_helpers import (
    sample_autocomplete_metadata,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AutoCompleteMetadataTestCase(unittest.TestCase):
    def test_success_metadata_model_create(self):
        data = sample_autocomplete_metadata()
        try:
            AutocompleteMetadata.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_metadata_model_create__no_required_fields(self):
        required_fields = sample_autocomplete_metadata().keys()
        for field in required_fields:
            data = sample_autocomplete_metadata()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                AutocompleteMetadata.from_dict(data)


if __name__ == "__main__":
    unittest.main()
