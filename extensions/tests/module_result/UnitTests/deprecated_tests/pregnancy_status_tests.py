from extensions.module_result.common.enums import YesNoDont
from extensions.module_result.models.primitives import (
    MedicalFacility,
    PregnancyStatus,
    PreNatalScreening,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class PregnancyStatusTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        COMMON_FIELDS[PregnancyStatus.MENSTRUAL_PERIOD] = True
        COMMON_FIELDS[PregnancyStatus.LAST_MENSTRUAL_PERIOD_DATE] = "2020-01-02"
        COMMON_FIELDS[PregnancyStatus.PREGNANCY_STATUS] = YesNoDont.DONT_KNOW
        COMMON_FIELDS[PregnancyStatus.IS_EXPECTED_DUE_DATE_AVAILABLE] = True
        COMMON_FIELDS[PregnancyStatus.EXPECTED_DUE_DATE] = "2019-06-30"
        COMMON_FIELDS[PregnancyStatus.PREGNANCY_MORE_THAN_1] = YesNoDont.YES
        COMMON_FIELDS[PregnancyStatus.PREGNANCY_TIMES] = 2
        COMMON_FIELDS[PregnancyStatus.BABY_COUNT] = 2
        COMMON_FIELDS[PregnancyStatus.HAS_MEDICAL_FERTILITY_PROCEDURE] = True
        COMMON_FIELDS[PregnancyStatus.MEDICAL_FERTILITY_PROCEDURE_ANSWER] = [
            MedicalFacility.DONOR_EGGS
        ]
        COMMON_FIELDS[PregnancyStatus.HAS_OTHER_PRENATAL_SCREENING] = True
        COMMON_FIELDS[PregnancyStatus.OTHER_MEDICAL_FERTILITY_PROCEDURE_ANSWER] = "Test"
        COMMON_FIELDS[PregnancyStatus.PREGNANT_BEFORE] = YesNoDont.YES
        COMMON_FIELDS[PregnancyStatus.PAST_PREGNANCY_LIVE_BIRTH] = 1
        COMMON_FIELDS[PregnancyStatus.PAST_PREGNANCY_STILL_BORN] = 1
        COMMON_FIELDS[PregnancyStatus.PAST_PREGNANCY_MISCARRIAGE] = 1
        COMMON_FIELDS[PregnancyStatus.PAST_PREGNANCY_ECTOPIC] = 1
        COMMON_FIELDS[PregnancyStatus.PAST_PREGNANCY_ELECTIVE_TERMINATION] = 1
        COMMON_FIELDS[PregnancyStatus.HAS_MEDICAL_PROFESSIONAL_VISIT] = True
        COMMON_FIELDS[PregnancyStatus.HIGH_RISK_CONDITION] = YesNoDont.NO
        COMMON_FIELDS[PregnancyStatus.HIGH_RISK_CONDITION_ANSWERS] = ["Test"]
        COMMON_FIELDS[PregnancyStatus.FAMILY_HISTORY_DEFECTS] = YesNoDont.YES
        COMMON_FIELDS[PregnancyStatus.FAMILY_HISTORY_DEFECTS_ANSWERS] = ["Test"]
        COMMON_FIELDS[PregnancyStatus.HAS_PRENATAL_SCREENING] = True
        COMMON_FIELDS[PregnancyStatus.PRE_NATAL_SCREENING_ANSWER] = [
            PreNatalScreening.AMNIOCENTESIS
        ]
        COMMON_FIELDS[PregnancyStatus.HAS_OTHER_PRENATAL_SCREENING] = True
        COMMON_FIELDS[PregnancyStatus.OTHER_PRENATAL_SCREENING] = "Test"
        COMMON_FIELDS[PregnancyStatus.HAS_OTHER_SCREENING_PROBLEM] = True
        COMMON_FIELDS[PregnancyStatus.OTHER_SCREENING_PROBLEM] = "Test"
        COMMON_FIELDS[PregnancyStatus.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                }
            ]
        }

    def test_success_creation(self):
        self._assign_primitive_values()
        primitive = PregnancyStatus.create_from_dict(
            COMMON_FIELDS, name="PregnancyStatus"
        )
        self.assertIsNotNone(primitive)

    def test_failure_creation_without_required_fields(self):
        required_fields = {PregnancyStatus.MENSTRUAL_PERIOD, PregnancyStatus.METADATA}
        for field in required_fields:
            self._assign_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(PregnancyStatus)

    def test_failure_invalid_menstrual_period_date(self):
        self._assign_primitive_values()
        invalid_dates = ["2019-12-3", "2019-12-31", "2100-12-31"]
        for date_ in invalid_dates:
            COMMON_FIELDS[PregnancyStatus.LAST_MENSTRUAL_PERIOD_DATE] = date_
            self._assert_convertible_validation_err(PregnancyStatus)

    def test_failure_invalid_value_int_fields(self):
        self._assign_primitive_values()
        int_fields = {
            PregnancyStatus.BABY_COUNT,
            PregnancyStatus.PREGNANCY_TIMES,
            PregnancyStatus.PAST_PREGNANCY_LIVE_BIRTH,
            PregnancyStatus.PAST_PREGNANCY_STILL_BORN,
            PregnancyStatus.PAST_PREGNANCY_MISCARRIAGE,
            PregnancyStatus.PAST_PREGNANCY_ECTOPIC,
            PregnancyStatus.PAST_PREGNANCY_ELECTIVE_TERMINATION,
        }
        for field in int_fields:
            self._assign_primitive_values()
            COMMON_FIELDS[field] = -1
            self._assert_convertible_validation_err(PregnancyStatus)

    def test_failure_invalid_value_string_fields(self):
        self._assign_primitive_values()
        string_fields = {
            PregnancyStatus.OTHER_MEDICAL_FERTILITY_PROCEDURE_ANSWER,
            PregnancyStatus.OTHER_PRENATAL_SCREENING,
            PregnancyStatus.OTHER_SCREENING_PROBLEM,
        }
        for field in string_fields:
            self._assign_primitive_values()
            COMMON_FIELDS[field] = ""
            self._assert_convertible_validation_err(PregnancyStatus)

    def test_failure_invalid_value_string_list_fields(self):
        self._assign_primitive_values()
        string_fields = {
            PregnancyStatus.HIGH_RISK_CONDITION_ANSWERS,
            PregnancyStatus.FAMILY_HISTORY_DEFECTS_ANSWERS,
        }
        for field in string_fields:
            self._assign_primitive_values()
            COMMON_FIELDS[field] = [""]
            self._assert_convertible_validation_err(PregnancyStatus)
