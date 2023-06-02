from extensions.autocomplete.models.autocomplete_module import AutocompleteModule
from sdk.common.localization.utils import Language


class SymptomsAutocompleteModule(AutocompleteModule):
    moduleId = "Symptoms"
    translations = {
        Language.EN,
        Language.DE,
        Language.FR,
        Language.ES,
        Language.SV,
        Language.CA,
    }
    fallback_json_path_per_language = {
        Language.EN: "symptoms-en.json",
        Language.DE: "symptoms-de.json",
        Language.FR: "symptoms-fr.json",
        Language.ES: "symptoms-es.json",
        Language.SV: "symptoms-sv.json",
        Language.CA: "symptoms-ca.json",
    }
