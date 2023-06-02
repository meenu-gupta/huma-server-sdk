from datetime import datetime

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.autocomplete.models.mongo_autocomplete_metadata import (
    MongoAutoCompleteMetadata,
)
from extensions.autocomplete.repository.autocomplete_repository import (
    AutoCompleteRepository,
)
from sdk.common.exceptions.exceptions import ObjectDoesNotExist


class MongoAutoCompleteRepository(AutoCompleteRepository):
    def update_autocomplete_metadata(self, metadata: AutocompleteMetadata):
        query = {
            AutocompleteMetadata.MODULE_ID: metadata.moduleId,
            AutocompleteMetadata.LANGUAGE: metadata.language,
        }
        document = MongoAutoCompleteMetadata.objects(**query).first()
        metadata.updateDateTime = datetime.utcnow()
        if document:
            document.update(**metadata.to_dict(include_none=False))
        else:
            document = MongoAutoCompleteMetadata(**metadata.to_dict(include_none=False))
            document.save()

        return document.moduleId

    def retrieve_autocomplete_metadata(
        self, module_id: str, language: str
    ) -> AutocompleteMetadata:
        docs = MongoAutoCompleteMetadata.objects(moduleId=module_id, language=language)
        document = docs.first()
        if not document:
            raise ObjectDoesNotExist

        return AutocompleteMetadata.from_dict(document.to_dict())
