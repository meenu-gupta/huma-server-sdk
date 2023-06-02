from extensions.module_result.common.enums import (
    BabyGender,
    BabyQuantity,
    ChildBirth,
)
from extensions.module_result.models.primitives import BabyInfo, PregnancyFollowUp
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


def sample_baby_info():
    return {
        BabyInfo.PREGNANCY_FOR_BABY: 1,
        BabyInfo.DATE_DELIVERY: "2021-01-01",
        BabyInfo.PREGNANCY_DURATION: 23,
        BabyInfo.SPECIFIED_OUTCOME: [],
        BabyInfo.BABY_GENDER: BabyGender.MALE,
        BabyInfo.METHOD_DELIVERY: ChildBirth.VAGINAL,
        BabyInfo.IS_BREAST_FEEDING_BABY: True,
        BabyInfo.IS_CURRENTLY_BREASTFEEDING_BABY: True,
        BabyInfo.BREASTFEED_LONG_TERM: 12,
        BabyInfo.IS_BABY_NO_LIQUID: True,
        BabyInfo.IS_BABY_ISSUES: 1,
        BabyInfo.SPECIFIED_ISSUES: [],
    }


class PregnancyFollowUpTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        COMMON_FIELDS[PregnancyFollowUp.PREGNANCY_MEDICATION] = True
        COMMON_FIELDS[PregnancyFollowUp.PRESCRIPTION_MEDICATIONS] = []
        COMMON_FIELDS[PregnancyFollowUp.OVER_COUNTER_PREGNANCY_MEDICATIONS] = True
        COMMON_FIELDS[PregnancyFollowUp.OVER_COUNTER_MEDICATIONS] = []
        COMMON_FIELDS[PregnancyFollowUp.BABY_COUNT] = BabyQuantity.SINGLE_BABY
        COMMON_FIELDS[PregnancyFollowUp.CURRENT_BABY_COUNT] = 1
        COMMON_FIELDS[PregnancyFollowUp.BABY_INFO] = [sample_baby_info()]
        COMMON_FIELDS[PregnancyFollowUp.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "What was the method of delivery?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Caesarean section",
                }
            ]
        }

    def test_success_creation(self):
        self._assign_primitive_values()
        primitive = PregnancyFollowUp.create_from_dict(
            COMMON_FIELDS, name="PregnancyFollowUp"
        )
        self.assertIsNotNone(primitive)

    def test_failure_without_required_fields(self):
        required_fields = {
            PregnancyFollowUp.PREGNANCY_MEDICATION,
            PregnancyFollowUp.OVER_COUNTER_PREGNANCY_MEDICATIONS,
            PregnancyFollowUp.BABY_COUNT,
            PregnancyFollowUp.BABY_INFO,
            PregnancyFollowUp.METADATA,
        }

        for field in required_fields:
            self._assign_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(PregnancyFollowUp)

    def test_failure_without_required_fields_baby_info(self):
        required_fields = {
            BabyInfo.PREGNANCY_FOR_BABY,
        }

        for field in required_fields:
            baby_info = sample_baby_info()
            del baby_info[field]
            with self.assertRaises(ConvertibleClassValidationError):
                BabyInfo.from_dict(baby_info)
