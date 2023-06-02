from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.common.enums import (
    BeforeAfter,
)
from extensions.module_result.models.primitives import (
    FeverAndPainDrugs,
    QuestionnaireAnswer,
)


class FeverAndPainDrugsTestCase(PrimitiveTestCase):
    METADATA_ANSWERS = [
        {
            QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
            QuestionnaireAnswer.QUESTION: "Did you start to take the medication before or after vaccination?",
            QuestionnaireAnswer.ANSWER_TEXT: "After",
        }
    ]

    def test_success_creation(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = BeforeAfter.AFTER
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = 2
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        primitive = FeverAndPainDrugs.create_from_dict(
            COMMON_FIELDS, name="FeverAndPainDrugs"
        )
        self.assertIsNotNone(primitive)

    def test_field_med_started_before_after_wrong_value(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = "HMMM"
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = 2
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        self._assert_convertible_validation_err(FeverAndPainDrugs)

    def test_field_days_before_vac_medication_wrong_value(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = BeforeAfter.AFTER
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = 8
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        self._assert_convertible_validation_err(FeverAndPainDrugs)

    def test_field_days_before_vac_medication_negative_value(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = BeforeAfter.AFTER
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = -1
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        self._assert_convertible_validation_err(FeverAndPainDrugs)

    def test_field_days_after_vac_medication_negative_value(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = BeforeAfter.AFTER
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = -1
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        self._assert_convertible_validation_err(FeverAndPainDrugs)

    def test_field_days_after_vac_medication_wrong_value(self):
        COMMON_FIELDS[FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS] = True
        COMMON_FIELDS[FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER] = BeforeAfter.AFTER
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION] = 4
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION] = 10
        COMMON_FIELDS[FeverAndPainDrugs.IS_UNDER_MEDICATION] = False
        COMMON_FIELDS[FeverAndPainDrugs.DAYS_COUNT_MEDICATION] = 0
        COMMON_FIELDS[FeverAndPainDrugs.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        self._assert_convertible_validation_err(FeverAndPainDrugs)
