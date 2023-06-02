from extensions.module_result.models.primitives import (
    AZFurtherPregnancyKeyActionTrigger,
    CurrentGroupCategory,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class AZFurtherPregnancyKeyActionTriggerTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        COMMON_FIELDS[
            AZFurtherPregnancyKeyActionTrigger.CURRENT_GROUP_CATEGORY
        ] = CurrentGroupCategory.PREGNANT
        COMMON_FIELDS[AZFurtherPregnancyKeyActionTrigger.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Which of the following groups is most applicable to you?",
                    QuestionnaireAnswer.ANSWER_TEXT: "I’m pregnant",
                }
            ]
        }

    def test_success_creation(self):
        self._assign_primitive_values()
        primitive = AZFurtherPregnancyKeyActionTrigger.create_from_dict(
            COMMON_FIELDS, name="AZFurtherPregnancyKeyActionTrigger"
        )
        self.assertIsNotNone(primitive)

    def test_failure_without_required_fields(self):
        required_fields = {
            AZFurtherPregnancyKeyActionTrigger.CURRENT_GROUP_CATEGORY,
            AZFurtherPregnancyKeyActionTrigger.METADATA,
        }

        for field in required_fields:
            self._assign_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(AZFurtherPregnancyKeyActionTrigger)
