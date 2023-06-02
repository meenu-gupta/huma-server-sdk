from extensions.module_result.common.enums import (
    CovidTestResult,
    CovidTestType,
    SymptomIntensity,
    YesNoDont,
    NewSymptomAction,
    HealthIssueAction,
)
from extensions.module_result.models.primitives import (
    HealthStatus,
    HealthProblemsOrDisabilityItem,
    CovidTestListItem,
    SymptomsListItem,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class HealthStatusTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        health_status_payload = {
            HealthStatus.NEW_OR_WORSE_SYMPTOMS: NewSymptomAction.CONSULT_DOCTOR,
            HealthStatus.HEALTH_PROBLEMS_OR_DISABILITIES: [
                {
                    HealthProblemsOrDisabilityItem.SYMPTOMS_LIST: [
                        {
                            SymptomsListItem.NAME: "Headache",
                            SymptomsListItem.INTENSITY: SymptomIntensity.SEVERE,
                            SymptomsListItem.START_DATE: "2021-02-12T00:00:00Z",
                            SymptomsListItem.IS_RESOLVED: False,
                            SymptomsListItem.END_DATE: "2021-03-20T00:00:00Z",
                        }
                    ],
                    HealthProblemsOrDisabilityItem.HEALTH_ISSUE_ACTION: [
                        HealthIssueAction.CONSULT_DOCTOR,
                        HealthIssueAction.HOSPITALIZED,
                    ],
                    HealthProblemsOrDisabilityItem.REPORTED_BEFORE: YesNoDont.NO,
                    HealthProblemsOrDisabilityItem.IS_MEDICATIONS_PRESCRIBED: True,
                    HealthProblemsOrDisabilityItem.RECEIVE_DIAGNOSIS: YesNoDont.YES,
                    HealthProblemsOrDisabilityItem.LOST_DAYS_AT_WORK_OR_EDUCATION: 2,
                    HealthProblemsOrDisabilityItem.IS_HEALTH_ISSUE_DUE_TO_COVID: True,
                    HealthProblemsOrDisabilityItem.TOOK_COVID_TEST: YesNoDont.YES,
                    HealthProblemsOrDisabilityItem.NUM_COVID_TESTS_TAKEN: 2,
                    HealthProblemsOrDisabilityItem.OTHER_NEW_OR_WORSE_SYMPTOMS: True,
                    HealthProblemsOrDisabilityItem.REMOTE_CONSULTATION: 0,
                    HealthProblemsOrDisabilityItem.IN_PERSON_CONSULTATION: 0,
                    HealthProblemsOrDisabilityItem.COVID_TEST_LIST: [
                        {
                            CovidTestListItem.METHOD: CovidTestType.NOSE_THROAT_SWAB,
                            CovidTestListItem.DATE: "2021-01-30T00:00:00Z",
                            CovidTestListItem.RESULT: CovidTestResult.PENDING,
                        }
                    ],
                }
            ],
            HealthStatus.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                        QuestionnaireAnswer.QUESTION: " How intense was your headache?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Severe",
                    }
                ]
            },
        }
        COMMON_FIELDS.update(health_status_payload)

    def test_success_create_health_status(self):
        self.set_primitive_values()
        primitive = HealthStatus.create_from_dict(COMMON_FIELDS, name="HealthStatus")
        self.assertIsNotNone(primitive)

    def test_failure_missing_required_fields_in_HealthStatus(self):
        required_fields_keys = [
            HealthStatus.NEW_OR_WORSE_SYMPTOMS,
            HealthStatus.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(HealthStatus)

    def test_failure_missing_required_fields_in_HealthProblemsOrDisabilityItem(self):

        required_nested_field_keys = [
            HealthProblemsOrDisabilityItem.REPORTED_BEFORE,
            HealthProblemsOrDisabilityItem.IS_MEDICATIONS_PRESCRIBED,
            HealthProblemsOrDisabilityItem.HEALTH_ISSUE_ACTION,
            HealthProblemsOrDisabilityItem.IS_MEDICATIONS_PRESCRIBED,
            HealthProblemsOrDisabilityItem.RECEIVE_DIAGNOSIS,
            HealthProblemsOrDisabilityItem.LOST_DAYS_AT_WORK_OR_EDUCATION,
            HealthProblemsOrDisabilityItem.IS_HEALTH_ISSUE_DUE_TO_COVID,
        ]

        for field in required_nested_field_keys:
            self.set_primitive_values()
            health_problem_fields = COMMON_FIELDS[
                HealthStatus.HEALTH_PROBLEMS_OR_DISABILITIES
            ][0]
            del health_problem_fields[field]
            self._assert_convertible_validation_err(HealthStatus)

    def test_failure_missing_required_fields_in_SymptomsListItem(self):

        required_nested_field_keys = [
            SymptomsListItem.NAME,
            SymptomsListItem.INTENSITY,
            SymptomsListItem.IS_RESOLVED,
        ]

        for field in required_nested_field_keys:
            self.set_primitive_values()
            health_problem_fields = COMMON_FIELDS[
                HealthStatus.HEALTH_PROBLEMS_OR_DISABILITIES
            ][0]
            symptom_list_fields = health_problem_fields[
                HealthProblemsOrDisabilityItem.SYMPTOMS_LIST
            ][0]
            del symptom_list_fields[field]
            self._assert_convertible_validation_err(HealthStatus)

    def test_failure_missing_required_fields_in_CovidTestListItem(self):

        required_nested_field_keys = [
            CovidTestListItem.METHOD,
            CovidTestListItem.RESULT,
        ]

        for field in required_nested_field_keys:
            self.set_primitive_values()
            health_problem_fields = COMMON_FIELDS[
                HealthStatus.HEALTH_PROBLEMS_OR_DISABILITIES
            ][0]
            covid_test_list_fields = health_problem_fields[
                HealthProblemsOrDisabilityItem.COVID_TEST_LIST
            ][0]
            del covid_test_list_fields[field]
            self._assert_convertible_validation_err(HealthStatus)
