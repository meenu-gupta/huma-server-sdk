from extensions.module_result.common.enums import (
    MedicalDiagnosis,
    CovidSymptoms,
    CovidTestType,
    CovidTestOverall,
    YesNoDont,
    HealthIssueAction,
)
from extensions.module_result.models.primitives import (
    CancerTypeItem,
    MedicalHistory,
    CovidSymptomsItem,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class MedicalHistoryTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        medical_history_payload = {
            MedicalHistory.CANCER_TYPE: [
                {
                    CancerTypeItem.NAME: "Colorectal",
                    CancerTypeItem.IS_TAKING_MEDICATION: True,
                    CancerTypeItem.METASTATIC: YesNoDont.DONT_KNOW,
                }
            ],
            MedicalHistory.MEDICAL_DIAGNOSIS: [MedicalDiagnosis.DIABETES],
            MedicalHistory.TAKING_IMMUNO_SUPPRESSANTS: YesNoDont.YES,
            MedicalHistory.IMMUNO_SUPPRESSANTS_MEDICATION_LIST: ["Test"],
            MedicalHistory.IS_COVID_INFECTED_IN_PAST: True,
            MedicalHistory.IS_COVID_TOLD_BY_DOCTOR: False,
            MedicalHistory.TAKEN_COVID_TEST: YesNoDont.YES,
            MedicalHistory.COVID_TEST_RESULT: CovidTestOverall.ONE_POSITIVE,
            MedicalHistory.COVID_TEST_DATE: "2021-03-10",
            MedicalHistory.COVID_TEST_METHOD: CovidTestType.NOSE_THROAT_SWAB,
            MedicalHistory.COVID_SYMPTOMS: [
                {
                    CovidSymptomsItem.NAME: CovidSymptoms.FEVER,
                    CovidSymptomsItem.INTENSITY: 5,
                    CovidSymptomsItem.PERSIST_POST_INFECTION: YesNoDont.NO,
                }
            ],
            MedicalHistory.COVID_SYMPTOMS_ACTION: [
                HealthIssueAction.CONSULT_DOCTOR,
                HealthIssueAction.HOSPITALIZED,
            ],
            MedicalHistory.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                        QuestionnaireAnswer.QUESTION: "Please specify which type of cancer?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Colorectal Cancer",
                    }
                ]
            },
            MedicalHistory.IS_DIAGNOSED_WITH_CANCER: True,
        }

        COMMON_FIELDS.update(medical_history_payload)

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = MedicalHistory.create_from_dict(
            COMMON_FIELDS, name="MedicalHistory"
        )
        self.assertIsNotNone(primitive)

    def test_failed_missing_required_fields(self):
        required_fields_keys = [
            MedicalHistory.MEDICAL_DIAGNOSIS,
            MedicalHistory.TAKING_IMMUNO_SUPPRESSANTS,
            MedicalHistory.IS_COVID_INFECTED_IN_PAST,
            MedicalHistory.IS_COVID_TOLD_BY_DOCTOR,
            MedicalHistory.TAKEN_COVID_TEST,
            MedicalHistory.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(MedicalHistory)

        self._assert_convertible_validation_err(MedicalHistory)

    def test_failed_intensity_value_out_of_range(self):
        self.set_primitive_values()
        COMMON_FIELDS[MedicalHistory.COVID_SYMPTOMS] = [
            {
                CovidSymptomsItem.NAME: CovidSymptoms.FEVER,
                CovidSymptomsItem.INTENSITY: 13,
                CovidSymptomsItem.PERSIST_POST_INFECTION: YesNoDont.NO,
            }
        ]

        self._assert_convertible_validation_err(MedicalHistory)

    def test_failed_wrong_cancer_type_name_format(self):
        self.set_primitive_values()
        COMMON_FIELDS[MedicalHistory.CANCER_TYPE] = [
            {
                CancerTypeItem.NAME: ["Colorectal"],
                CancerTypeItem.IS_TAKING_MEDICATION: True,
                CancerTypeItem.METASTATIC: YesNoDont.DONT_KNOW,
            }
        ]

        self._assert_convertible_validation_err(MedicalHistory)

    def test_failure_creation_with_missing_isDiagnosedWithCancer_field(self):
        self.set_primitive_values()
        COMMON_FIELDS.pop(MedicalHistory.IS_DIAGNOSED_WITH_CANCER, None)
        with self.assertRaises(ConvertibleClassValidationError):
            MedicalHistory.create_from_dict(COMMON_FIELDS, name="MedicalHistory")

    def test_success_creation_with_hadCovidSymptoms_field(self):
        self.set_primitive_values()
        COMMON_FIELDS[MedicalHistory.HAD_COVID_SYMPTOMS] = True
        primitive = MedicalHistory.create_from_dict(
            COMMON_FIELDS, name="MedicalHistory"
        )
        self.assertIsNotNone(primitive)
