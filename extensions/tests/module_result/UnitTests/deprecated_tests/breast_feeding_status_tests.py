from extensions.module_result.common.enums import YesNoDont
from extensions.module_result.models.primitives import (
    BreastFeedingStatus,
    BreastFeedingBabyStatusDetailsItem,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class BreastFeedingStatusTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        breastfeeding_payload = {
            BreastFeedingStatus.IS_BREASTFEEDING_CURRENTLY: True,
            BreastFeedingStatus.NUMBER_OF_WEEKS_AT_CHILD_BIRTH: 6,
            BreastFeedingStatus.HAD_COMPLICATIONS_AT_BIRTH: True,
            BreastFeedingStatus.COMPLICATION_LIST: ["Miscarriage", "Preeclampsia"],
            BreastFeedingStatus.HAS_RISK_CONDITIONS: True,
            BreastFeedingStatus.HIGH_RISK_CONDITIONS: [],
            BreastFeedingStatus.FAMILY_HISTORY_OF_DEFECTS: YesNoDont.NO,
            BreastFeedingStatus.NUM_BREASTFEEDING_BABIES: 1,
            BreastFeedingStatus.FAMILY_HISTORY_OF_DEFECTS_LIST: [],
            BreastFeedingStatus.BREASTFEEDING_BABY_DETAILS: [
                {
                    BreastFeedingBabyStatusDetailsItem.AGE_IN_MONTHS: 6,
                    BreastFeedingBabyStatusDetailsItem.HAS_ONLY_BREAST_MILK: False,
                    BreastFeedingBabyStatusDetailsItem.WEIGHT_AT_BIRTH: 5.5,
                    BreastFeedingBabyStatusDetailsItem.IS_BREAST_FEEDING_CURRENTLY: True,
                    BreastFeedingBabyStatusDetailsItem.HAS_BIRTH_DEFECT: False,
                    BreastFeedingBabyStatusDetailsItem.BABY_BIRTH_DEFECT_LIST: [],
                    BreastFeedingBabyStatusDetailsItem.HAS_CHRONIC_CONDITION: True,
                    BreastFeedingBabyStatusDetailsItem.CHRONIC_CONDITION_LIST: [],
                    BreastFeedingBabyStatusDetailsItem.HAS_MEDICATIONS: False,
                    BreastFeedingBabyStatusDetailsItem.IS_MEDICATION_BY_DOCTOR: True,
                    BreastFeedingBabyStatusDetailsItem.CONDITION_LIST: [],
                }
            ],
            BreastFeedingStatus.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                        QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                        QuestionnaireAnswer.ANSWER_TEXT: "No",
                    },
                ]
            },
        }

        COMMON_FIELDS.update(breastfeeding_payload)

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = BreastFeedingStatus.create_from_dict(
            COMMON_FIELDS, name="BreastFeedingStatus"
        )
        self.assertIsNotNone(primitive)

    def test_failed_missing_required_fields(self):
        required_fields_keys = [
            BreastFeedingStatus.IS_BREASTFEEDING_CURRENTLY,
            BreastFeedingStatus.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(BreastFeedingStatus)
        self._assert_convertible_validation_err(BreastFeedingStatus)

    def test_failed_missing_nested_required_fields(self):

        required_nested_field_keys = [
            BreastFeedingBabyStatusDetailsItem.WEIGHT_AT_BIRTH,
            BreastFeedingBabyStatusDetailsItem.AGE_IN_MONTHS,
            BreastFeedingBabyStatusDetailsItem.HAS_CHRONIC_CONDITION,
            BreastFeedingBabyStatusDetailsItem.HAS_MEDICATIONS,
        ]

        for field in required_nested_field_keys:
            self.set_primitive_values()
            nested_field = COMMON_FIELDS[
                BreastFeedingStatus.BREASTFEEDING_BABY_DETAILS
            ][0]
            del nested_field[field]
            self._assert_convertible_validation_err(BreastFeedingStatus)

    def test_failure_baby_weight_out_of_range(self):
        self.set_primitive_values()

        COMMON_FIELDS[BreastFeedingStatus.BREASTFEEDING_BABY_DETAILS] = [
            {
                BreastFeedingBabyStatusDetailsItem.WEIGHT_AT_BIRTH: 13,
                BreastFeedingBabyStatusDetailsItem.AGE_IN_MONTHS: 6,
                BreastFeedingBabyStatusDetailsItem.HAS_ONLY_BREAST_MILK: False,
                BreastFeedingBabyStatusDetailsItem.IS_BREAST_FEEDING_CURRENTLY: True,
            }
        ]

        self._assert_convertible_validation_err(BreastFeedingStatus)

    def test_failure_baby_age_out_of_range(self):
        self.set_primitive_values()

        COMMON_FIELDS[BreastFeedingStatus.BREASTFEEDING_BABY_DETAILS] = [
            {
                BreastFeedingBabyStatusDetailsItem.WEIGHT_AT_BIRTH: 4,
                BreastFeedingBabyStatusDetailsItem.AGE_IN_MONTHS: 0,
                BreastFeedingBabyStatusDetailsItem.HAS_ONLY_BREAST_MILK: False,
                BreastFeedingBabyStatusDetailsItem.IS_BREAST_FEEDING_CURRENTLY: True,
            }
        ]

        self._assert_convertible_validation_err(BreastFeedingStatus)
