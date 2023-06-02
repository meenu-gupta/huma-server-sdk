from extensions.module_result.models.primitives import InfantFollowUp, ChildrenItem
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class InfantFollowUpTestCase(PrimitiveTestCase):
    METADATA_ANSWERS = [
        {
            QuestionnaireAnswer.QUESTION_ID: "fbeeb07a-64c4-409d-aac7-c929674022a1",
            QuestionnaireAnswer.QUESTION: "Are you aware or has a medical doctor informed you of any developmental issues with your first child from this pregnancy?",
            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
        }
    ]

    def test_success_creation(self):
        COMMON_FIELDS[InfantFollowUp.CHILDREN] = [
            {
                ChildrenItem.ISSUES: ["ADHD", "Cerebral Palsy"],
                ChildrenItem.HAS_CHILD_DEVELOP_ISSUES: False,
            }
        ]
        COMMON_FIELDS[InfantFollowUp.IS_COV_PREG_LIVE_BIRTH] = False
        COMMON_FIELDS[InfantFollowUp.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }

        primitive = InfantFollowUp.create_from_dict(
            COMMON_FIELDS, name="InfantFollowUp"
        )
        self.assertIsNotNone(primitive)

    def test_field_children_value_not_required(self):
        COMMON_FIELDS[InfantFollowUp.METADATA] = {
            QuestionnaireMetadata.ANSWERS: self.METADATA_ANSWERS
        }
        COMMON_FIELDS[InfantFollowUp.IS_COV_PREG_LIVE_BIRTH] = False
        primitive = InfantFollowUp.create_from_dict(
            COMMON_FIELDS, name="InfantFollowUp"
        )
        self.assertIsNotNone(primitive)
