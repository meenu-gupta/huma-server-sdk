from extensions.autocomplete.models.autocomplete_module import AutocompleteModule
from sdk.common.localization.utils import Language


class MedicationsAutocompleteModule(AutocompleteModule):
    moduleId = "Medications"
    translations = {
        Language.EN,
        Language.DE,
        Language.FR,
        Language.ES,
        Language.SV,
        Language.CA,
    }
    fallback_json_path_per_language = {
        Language.EN: "medications-en.json",
        Language.DE: "medications-de.json",
        Language.FR: "medications-fr.json",
        Language.ES: "medications-es.json",
        Language.SV: "medications-sv.json",
        Language.CA: "medications-ca.json",
    }
