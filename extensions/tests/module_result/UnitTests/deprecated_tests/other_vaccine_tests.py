import copy

from extensions.module_result.common.enums import VaccineCategory
from extensions.module_result.models.primitives import OtherVaccine, VaccineListItem
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import COMMON_FIELDS
from extensions.tests.module_result.UnitTests.primitives_tests import PrimitiveTestCase
from sdk.common.utils.convertible import ConvertibleClassValidationError


class OtherVaccineTestCase(PrimitiveTestCase):
    def setUp(self):
        self.common_fields = copy.deepcopy(COMMON_FIELDS)

    def set_primitive_values(self):
        other_vaccine_payload = {
            OtherVaccine.HAS_FLU_VACCINE: True,
            OtherVaccine.FLU_VACCINE_DATE: "2021-03-30",
            OtherVaccine.HAS_OTHER_VACCINE: True,
            OtherVaccine.VACCINE_CATEGORY: [
                VaccineCategory.HPV,
                VaccineCategory.MENINGITIS,
            ],
            OtherVaccine.VACCINE_LIST: [
                {
                    VaccineListItem.NAME: "Sinopharm",
                    VaccineListItem.VACCINATED_DATE: "2021-03-30",
                }
            ],
            OtherVaccine.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                        QuestionnaireAnswer.QUESTION: "Have you received the seasonal flu vaccine since the last time we asked?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                    },
                ]
            },
        }
        self.common_fields.update(other_vaccine_payload)

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = OtherVaccine.create_from_dict(
            self.common_fields, name="OtherVaccine"
        )
        self.assertIsNotNone(primitive)

    def test_failure_invalid_date(self):
        self.common_fields[OtherVaccine.HAS_FLU_VACCINE] = True
        self.common_fields[OtherVaccine.FLU_VACCINE_DATE] = "2020-03-30"
        self.common_fields[OtherVaccine.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                    QuestionnaireAnswer.QUESTION: "Have you received the seasonal flu vaccine since the last time we asked?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
            ]
        }

        self._assert_convertible_validation_err(OtherVaccine)

    def test_failure_creation_with_missing_hasFluVaccine_field(self):
        self.set_primitive_values()
        self.common_fields.pop(OtherVaccine.HAS_FLU_VACCINE, None)
        with self.assertRaises(ConvertibleClassValidationError):
            OtherVaccine.create_from_dict(self.common_fields, name="OtherVaccine")

    def test_failure_creation_with_missing_hasOtherVaccine_field(self):
        self.set_primitive_values()
        self.common_fields.pop(OtherVaccine.HAS_OTHER_VACCINE, None)
        with self.assertRaises(ConvertibleClassValidationError):
            OtherVaccine.create_from_dict(self.common_fields, name="OtherVaccine")
