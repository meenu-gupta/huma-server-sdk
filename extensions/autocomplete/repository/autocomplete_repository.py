import abc
from abc import ABC

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata


class AutoCompleteRepository(ABC):
    @abc.abstractmethod
    def update_autocomplete_metadata(self, metadata: AutocompleteMetadata) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_autocomplete_metadata(
        self, module_id: str, language: str
    ) -> AutocompleteMetadata:
        raise NotImplementedError
