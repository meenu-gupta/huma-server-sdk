from datetime import date, timedelta

from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    GroupCategory,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class AZGroupKeyActionTriggerTestCase(PrimitiveTestCase):
    @staticmethod
    def _assign_primitive_values():
        COMMON_FIELDS[AZGroupKeyActionTrigger.FIRST_VACCINE_DATE] = "2019-06-30"
        COMMON_FIELDS[
            AZGroupKeyActionTrigger.GROUP_CATEGORY
        ] = GroupCategory.MALE_OR_FEMALE_OVER_50
        COMMON_FIELDS[AZGroupKeyActionTrigger.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Please provide the date of your flu vaccine.",
                    QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
                }
            ]
        }

    def test_success_creation(self):
        self._assign_primitive_values()
        primitive = AZGroupKeyActionTrigger.create_from_dict(
            COMMON_FIELDS, name="AZGroupKeyActionTrigger"
        )
        self.assertIsNotNone(primitive)

    def test_failure_invalid_dates(self):
        self._assign_primitive_values()
        COMMON_FIELDS[AZGroupKeyActionTrigger.FIRST_VACCINE_DATE] = str(
            date.today() + timedelta(days=1)
        )
        self._assert_convertible_validation_err(AZGroupKeyActionTrigger)

    def test_failure_without_required_fields(self):
        required_fields = {
            AZGroupKeyActionTrigger.FIRST_VACCINE_DATE,
            AZGroupKeyActionTrigger.GROUP_CATEGORY,
            AZGroupKeyActionTrigger.METADATA,
        }

        for field in required_fields:
            self._assign_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(AZGroupKeyActionTrigger)
