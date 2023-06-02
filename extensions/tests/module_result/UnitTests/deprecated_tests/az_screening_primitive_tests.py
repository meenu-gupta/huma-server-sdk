import copy
import unittest

from extensions.module_result.models.primitives import AZScreeningQuestionnaire
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.shared.test_helpers import generate_random_stringified_object_id
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AZScreeningPrimitiveCase(unittest.TestCase):
    def sample_az_screening(self):
        return {
            AZScreeningQuestionnaire.USER_ID: generate_random_stringified_object_id(),
            AZScreeningQuestionnaire.DEPLOYMENT_ID: generate_random_stringified_object_id(),
            AZScreeningQuestionnaire.DEVICE_NAME: "IOS",
            AZScreeningQuestionnaire.MODULE_ID: AZScreeningQuestionnaire.__name__,
            AZScreeningQuestionnaire.HAS_RECEIVED_COVID_VAC_IN_PAST_4_WEEKS: True,
            AZScreeningQuestionnaire.IS_18_Y_OLD_DURING_VAC: True,
            AZScreeningQuestionnaire.IS_AZ_VAC_FIRST_DOSE: True,
            AZScreeningQuestionnaire.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION: "Are you 18 years old?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                    },
                ]
            },
        }

    def test_success_az_screening_primitive_creation(self):
        primitive = AZScreeningQuestionnaire.from_dict(self.sample_az_screening())
        self.assertIsNotNone(primitive)

    def test_failure_missing_required_fields(self):
        sample_screening = self.sample_az_screening()
        required_fields = [
            AZScreeningQuestionnaire.HAS_RECEIVED_COVID_VAC_IN_PAST_4_WEEKS,
            AZScreeningQuestionnaire.IS_18_Y_OLD_DURING_VAC,
            AZScreeningQuestionnaire.IS_AZ_VAC_FIRST_DOSE,
            AZScreeningQuestionnaire.METADATA,
        ]
        for field in required_fields:
            az_data = copy.deepcopy(sample_screening)
            az_data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                AZScreeningQuestionnaire.from_dict(az_data)


if __name__ == "__main__":
    unittest.main()
