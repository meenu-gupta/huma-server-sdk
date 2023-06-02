from dataclasses import field
from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from sdk import convertibleclass, meta
from sdk.common.localization.utils import Language
from sdk.common.utils.convertible import required_field
from sdk.common.utils.validators import (
    incorrect_language_to_default,
    must_not_be_present,
)


@convertibleclass
class SearchAutocompleteRequestObject:
    LIST_ENDPOINT_ID = "listEndpointId"
    SEARCH = "search"
    EXACT_WORD = "exactWord"
    LANGUAGE = "language"

    listEndpointId: str = required_field()
    search: str = required_field()
    exactWord: bool = field(default=False)
    language: str = field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )


@convertibleclass
class UpdateAutoCompleteSearchMetadataRequestObject:
    METADATA = "metadata"

    metadata: list[AutocompleteMetadata] = required_field()

    @classmethod
    def validate(cls, instance):
        for m in instance.metadata:
            must_not_be_present(updateDateTime=m.updateDateTime)
