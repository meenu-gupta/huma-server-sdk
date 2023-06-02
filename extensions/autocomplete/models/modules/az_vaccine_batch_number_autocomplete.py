from extensions.autocomplete.models.autocomplete_module import AutocompleteModule
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.localization.utils import Language


class AZVaccineBatchNumberModule(AutocompleteModule):
    moduleId = "AZVaccineBatchNumber"
    translations = {Language.EN}
    fallback_json_path_per_language = {Language.EN: "vaccine.json"}

    def retrieve_search_result(
        self,
        search_key: str,
        exact_word: bool = False,
        language: str = Language.EN,
        case_sensitive: bool = False,
    ) -> list[str]:
        if not exact_word:
            raise InvalidRequestException(
                "AZVaccineBatchNumber only support exactWord equal to True"
            )
        data = self.get_data_for_language(language)
        if case_sensitive:
            return [val for val in data if val == search_key]
        return [val for val in data if val.lower() == search_key.lower()]
