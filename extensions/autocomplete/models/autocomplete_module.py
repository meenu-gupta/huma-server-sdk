import json
import logging
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Optional

from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.autocomplete.repository.autocomplete_repository import (
    AutoCompleteRepository,
)
from extensions.common.monitoring import report_exception
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import BucketFileDoesNotExist, ObjectDoesNotExist
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__file__)


class AutocompleteModule(ABC):
    fallback_language = Language.EN

    moduleId: str = None
    translations: dict = None
    fallback_json_path_per_language: dict = None
    cache_dict_per_language: dict = None
    metadata_update_cache_per_language: dict[str, datetime] = None

    _assets_path = Path(__file__).parent.joinpath("./assets")

    def __init__(self):
        if not self.translations:
            error = Exception(
                "Autocomplete module should support at least one language."
            )
            report_exception(error)
            raise error

        self.cache_dict_per_language = {lang: [] for lang in self.translations}
        self.metadata_update_cache_per_language = {
            lang: None for lang in self.translations
        }

    def retrieve_search_result(
        self,
        search_key: str,
        exact_word: bool = False,
        language: str = Language.EN,
        case_sensitive: bool = False,
    ) -> list[str]:
        data = self.get_data_for_language(language)
        if exact_word:
            return [val for val in data if val == search_key]

        if case_sensitive:
            return [val for val in data if search_key in val]

        search_key = search_key.lower()
        return [val for val in data if search_key in val.lower()]

    def get_data_for_language(self, language: str):
        language = self.replace_language_with_default_if_incorrect(language)
        if self.cache_dict_per_language:
            try:
                self._validate_cache_and_refresh_if_invalid(language)
                return self.cache_dict_per_language[language]
            except (ObjectDoesNotExist, BucketFileDoesNotExist) as error:
                report_exception(error)

        return self.read_from_local_file(language)

    def replace_language_with_default_if_incorrect(self, lang: str):
        return lang if lang in self.translations else self.fallback_language

    def read_from_local_file(self, language: str) -> list:
        if not self.fallback_json_path_per_language:
            error = Exception("No file to read from")
            report_exception(error)
            raise error

        file_path = self._get_fallback_json_path(language)
        if not file_path:
            return []

        with open(file_path, "rb") as local_file:
            return json.load(local_file)

    def _get_fallback_json_path(self, language: str) -> Optional[str]:
        file_path = self.fallback_json_path_per_language.get(language)
        if not file_path:
            return

        return str(self._assets_path.joinpath(file_path))

    def _is_cache_valid(self, metadata: AutocompleteMetadata):
        cache_update_dt = self.metadata_update_cache_per_language[metadata.language]
        if cache_update_dt is None:
            return False

        return cache_update_dt >= metadata.updateDateTime

    @autoparams("repo")
    def _retrieve_metadata(self, language: str, repo: AutoCompleteRepository):
        return repo.retrieve_autocomplete_metadata(self.moduleId, language)

    def _validate_cache_and_refresh_if_invalid(self, language: str):
        metadata = self._retrieve_metadata(language)
        if self._is_cache_valid(metadata):
            return

        file_storage = inject.instance(FileStorageAdapter)

        s3_bucket = metadata.s3Object.bucket
        s3_key = metadata.s3Object.key
        if not file_storage.file_exist(s3_bucket, s3_key):
            raise BucketFileDoesNotExist

        object_data, _, _ = file_storage.download_file(s3_bucket, s3_key)

        self.cache_dict_per_language[language] = json.loads(object_data.read())
        self.metadata_update_cache_per_language[language] = metadata.updateDateTime
