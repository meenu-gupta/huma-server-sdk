from extensions.module_result.common.enums import Regularly
from extensions.module_result.models.primitives import AdditionalQoL
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class AdditionalQoLTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        payload = {
            AdditionalQoL.VIEW_FAMILY: Regularly.STRONGLY_AGREE,
            AdditionalQoL.CONTACT_PROFESSIONALS: Regularly.STRONGLY_AGREE,
            AdditionalQoL.CONTRIBUTE_ACTIVITIES: Regularly.STRONGLY_AGREE,
            AdditionalQoL.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "30cad609-cd6a-418d-a1de-6eacfa3a2d9d",
                        QuestionnaireAnswer.QUESTION: "I am able to see my friends and family more in person",
                        QuestionnaireAnswer.ANSWER_TEXT: "AGREE",
                    }
                ]
            },
        }

        COMMON_FIELDS.update(payload)

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = AdditionalQoL.create_from_dict(COMMON_FIELDS, name="AdditionalQoL")
        self.assertIsNotNone(primitive)

    def test_failed_missing_required_fields(self):
        required_fields_keys = [
            AdditionalQoL.VIEW_FAMILY,
            AdditionalQoL.CONTACT_PROFESSIONALS,
            AdditionalQoL.CONTRIBUTE_ACTIVITIES,
            AdditionalQoL.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(AdditionalQoL)

        self._assert_convertible_validation_err(AdditionalQoL)

    def test_failed_invalid_view_family_value(self):
        self.set_primitive_values()
        COMMON_FIELDS[AdditionalQoL.VIEW_FAMILY] = 11
        self._assert_convertible_validation_err(AdditionalQoL)
