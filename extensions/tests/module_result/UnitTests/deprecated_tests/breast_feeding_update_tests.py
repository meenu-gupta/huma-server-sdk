from extensions.module_result.common.enums import NewSymptomAction, HealthIssueAction
from extensions.module_result.models.primitives import (
    BreastFeedingUpdate,
    BreastFeedingUpdateBabyDetails,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class BreastFeedingUpdateTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        breastfeeding_payload = {
            BreastFeedingUpdate.IS_BREASTFEEDING_NOW: True,
            BreastFeedingUpdate.STOP_DATE: "2020-06-30T00:00:00Z",
            BreastFeedingUpdate.NOW_OR_WORSE_SYMPTOM: [
                NewSymptomAction.DISABILITY_INCAPACITATION,
                NewSymptomAction.CONSULT_DOCTOR,
            ],
            BreastFeedingUpdate.BREASTFEEDING_BABY_DETAILS: [
                {
                    BreastFeedingUpdateBabyDetails.HEALTH_ISSUE: ["fever"],
                    BreastFeedingUpdateBabyDetails.HEALTH_ISSUE_ACTION: [
                        HealthIssueAction.CONSULT_DOCTOR,
                        HealthIssueAction.VISIT_ER,
                    ],
                    BreastFeedingUpdateBabyDetails.HAS_RECEIVED_DIAGNOSIS: True,
                    BreastFeedingUpdateBabyDetails.DIAGNOSIS_LIST: [],
                }
            ],
            BreastFeedingUpdate.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                        QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                    }
                ]
            },
        }

        COMMON_FIELDS.update(breastfeeding_payload)

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = BreastFeedingUpdate.create_from_dict(
            COMMON_FIELDS, name="BreastFeedingUpdate"
        )
        self.assertIsNotNone(primitive)

    def test_failed_missing_required_fields_in_BreastFeedingUpdate(self):
        required_fields_keys = [
            BreastFeedingUpdate.IS_BREASTFEEDING_NOW,
            BreastFeedingUpdate.NOW_OR_WORSE_SYMPTOM,
            BreastFeedingUpdate.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(BreastFeedingUpdate)

    def test_failed_missing_required_fields_in_BreastFeedingUpdateBabyDetails(self):

        required_nested_field_keys = [
            BreastFeedingUpdateBabyDetails.HEALTH_ISSUE,
            BreastFeedingUpdateBabyDetails.HEALTH_ISSUE_ACTION,
            BreastFeedingUpdateBabyDetails.HAS_RECEIVED_DIAGNOSIS,
        ]

        for field in required_nested_field_keys:
            self.set_primitive_values()
            nested_field = COMMON_FIELDS[
                BreastFeedingUpdate.BREASTFEEDING_BABY_DETAILS
            ][0]
            del nested_field[field]
            self._assert_convertible_validation_err(BreastFeedingUpdate)

    def test_failed_invalid_breastfeeding_stop_date(self):
        self.set_primitive_values()
        COMMON_FIELDS[BreastFeedingUpdate.STOP_DATE] = "2019-12-3"
        self._assert_convertible_validation_err(BreastFeedingUpdate)
