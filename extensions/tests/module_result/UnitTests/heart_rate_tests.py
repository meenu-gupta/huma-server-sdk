from extensions.module_result.models.primitives.primitive import MeasureUnit
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import (
    HeartRate,
    QuestionnaireAnswer,
)


class HeartRateTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS[HeartRate.VALUE] = 80
        primitive = HeartRate.create_from_dict(COMMON_FIELDS, name=HeartRate.__name__)
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, MeasureUnit.BEATS_PER_MINUTE.value)

    def test_success_creation_zero_as_value(self):
        COMMON_FIELDS[HeartRate.VALUE] = 0
        primitive = HeartRate.create_from_dict(COMMON_FIELDS, name=HeartRate.__name__)
        self.assertIsNotNone(primitive)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS[HeartRate.VALUE] = 251
        self._assert_convertible_validation_err(HeartRate)

    def test_success_creation_with_metadata(self):
        answer_data = {
            QuestionnaireAnswer.ANSWER_TEXT: "Yes|No",
            QuestionnaireAnswer.VALUE: True,
            QuestionnaireAnswer.FORMAT: "BOOLEAN",
            QuestionnaireAnswer.QUESTION_ID: "extra_question",
            QuestionnaireAnswer.QUESTION: "question",
        }
        answer_object = QuestionnaireAnswer.from_dict(answer_data)
        metadata = {QuestionnaireMetadata.ANSWERS: [answer_data]}
        data = COMMON_FIELDS.copy()
        data[HeartRate.VALUE] = 80
        data[HeartRate.METADATA] = metadata
        primitive = HeartRate.create_from_dict(data, name=HeartRate.__name__)
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.metadata.answers, [answer_object])
