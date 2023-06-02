import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

from extensions.autocomplete.models.modules.az_vaccine_batch_number_autocomplete import (
    AZVaccineBatchNumberModule,
)
from extensions.autocomplete.models.modules.medications_autocomplete import (
    MedicationsAutocompleteModule,
)
from extensions.autocomplete.models.modules.symptoms_autocomplete import (
    SymptomsAutocompleteModule,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


def get_file_cache() -> dict:
    path = Path(__file__).parent.parent.joinpath("IntegrationTests")
    with open(path.joinpath("fixtures/assets/file_list.json")) as myfile:
        files = json.load(myfile)
    file_cache = {}
    for file_object in files:
        file_path = path.joinpath(f"fixtures/assets/{file_object['filename']}")
        with open(file_path, "rb") as file:
            content = file.read()
            file_cache[f"{file_object['moduleId']}.{file_object['language']}"] = content
    return file_cache


class MockRemoteFileReader(MagicMock):
    @staticmethod
    def refresh_file():
        return MagicMock()

    @staticmethod
    def read_file(x):
        return get_file_cache()[x]


class SymptomsAutocompleteTests(TestCase):
    def setUp(self) -> None:
        self.module = SymptomsAutocompleteModule()
        self.module.cache_dict_per_language = None

    def test_success_retrieve_search_result_with_en(self):
        self.assertEqual(
            [
                "Discomfort in joints",
                "Joint ache",
                "Joint dislocation",
                "Joint infection",
                "Joint inflammation",
                "Joint injury",
                "Joint instability",
                "Joint lock",
                "Joint pain",
                "Joint stiffness",
                "Joint swelling",
                "Joint warmth",
                "Vaccination site joint discomfort",
                "Vaccination site joint erythema",
                "Vaccination site joint infection",
                "Vaccination site joint inflammation",
                "Vaccination site joint pain",
                "Vaccination site joint swelling",
            ],
            self.module.retrieve_search_result("joint"),
        )

    def test_success_retrieve_search_result_with_de(self):
        result = self.module.retrieve_search_result("öger", language="de")
        self.assertEqual(
            [
                "Entwicklungsverzögerung",
                "Medikamentenwirkung verzögert",
                "Verzögerte Feinmotorik",
                "Verzögerte Grobmotorik",
                "Wundheilung verzögert",
            ],
            result,
        )

    def test_failure_invalid_name(self):
        self.assertEqual(self.module.retrieve_search_result("nows"), [])


class MedicationAutocompleteTests(TestCase):
    def setUp(self) -> None:
        self.module = MedicationsAutocompleteModule()
        self.module.cache_dict_per_language = None

    def test_success_retrieve_search_result_with_en(self):
        result = self.module.retrieve_search_result("Anti")
        self.assertEqual(
            ["Anti-thymocyte globulin (rabbit)", "Anti-lymphocyte globulin (horse)"],
            result,
        )

    def test_success_retrieve_search_result_with_de(self):
        result = self.module.retrieve_search_result("mycin", language="de")
        self.assertEqual(
            ["Bleomycin", "Dactinomycin", "Erythromycin", "Fosfomycin", "Mitomycin"],
            result,
        )

    def test_failure_invalid_name(self):
        self.assertEqual([], self.module.retrieve_search_result("notexist"))


class AZVaccineAutocompleteTests(TestCase):
    def setUp(self) -> None:
        self.module = AZVaccineBatchNumberModule()
        self.module.cache_dict_per_language = None

    def test_success_retrieve_search_result_with_en(self):
        result = self.module.retrieve_search_result("ABV3922", exact_word=True)
        self.assertEqual(["ABV3922"], result)

    def test_failure_with_exact_word_false(self):
        with self.assertRaises(InvalidRequestException):
            self.module.retrieve_search_result("ABV3922")

    def test_failure_invalid_name(self):
        result = self.module.retrieve_search_result("notexist", exact_word=True)
        self.assertEqual([], result)
