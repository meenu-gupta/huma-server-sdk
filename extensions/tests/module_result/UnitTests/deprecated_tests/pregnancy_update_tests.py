from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.module_result.models.primitives import (
    PregnancyUpdate,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)
from sdk.common.utils.validators import utc_date_to_str


class PregnancyUpdateTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        menstrual_date = "2021-01-02T00:00:00Z"
        due_date = utc_date_to_str(datetime.utcnow() + relativedelta(days=10))
        COMMON_FIELDS[PregnancyUpdate.HAS_MENSTRUAL_PERIOD] = True
        COMMON_FIELDS[PregnancyUpdate.EXPECTED_DUE_DATE] = due_date
        COMMON_FIELDS[PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1] = menstrual_date
        COMMON_FIELDS[PregnancyUpdate.BECAME_PREGNANT] = False
        COMMON_FIELDS[PregnancyUpdate.PAST_BABY_COUNT] = 3
        COMMON_FIELDS[PregnancyUpdate.BABY_COUNT] = 2
        COMMON_FIELDS[PregnancyUpdate.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "a285d625-54d1-421f-ba5e-d9748690c461",
                    QuestionnaireAnswer.QUESTION: "Have you had your menstrual period in the last year?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "de8a8e98-81a7-42be-a33f-0b8f0393ada1",
                    QuestionnaireAnswer.QUESTION: "What was the first day of your last menstrual period date? ",
                    QuestionnaireAnswer.ANSWER_TEXT: "2021-01-01T00:00:00Z",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "0f473b35-1dc9-40de-af16-17eaa4f4ff7f",
                    QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                },
            ]
        }

    def test_success_pregnancy_update_creation(self):
        self._assign_primitive_values()
        primitive = PregnancyUpdate.create_from_dict(
            COMMON_FIELDS, name="PregnancyUpdate"
        )
        self.assertIsNotNone(primitive)

    def test_failure_pregnancy_creation_wrong_menstrual_period_date_format(self):
        self._assign_primitive_values()
        COMMON_FIELDS[
            PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1
        ] = "WRONG_DATE_FORMAT"
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_failure_negative_baby_count_update(self):
        self._assign_primitive_values()
        COMMON_FIELDS[PregnancyUpdate.PAST_BABY_COUNT] = -1
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_failure_last_menstrual_period_before_2020(self):
        self._assign_primitive_values()
        COMMON_FIELDS[PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1] = "2019-12-11"
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_failure_baby_count_too_many_babies(self):
        self._assign_primitive_values()
        COMMON_FIELDS[PregnancyUpdate.BABY_COUNT] = 42
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_failure_baby_count_negative(self):
        self._assign_primitive_values()
        COMMON_FIELDS[PregnancyUpdate.BABY_COUNT] = -1
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_failure_last_menstrual_period_date_day1_no_dates_in_the_future(self):
        self._assign_primitive_values()
        tomorrow_date = str(date.today() + timedelta(days=1))
        COMMON_FIELDS[PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1] = tomorrow_date
        self._assert_convertible_validation_err(PregnancyUpdate)

    def test_success_last_mestrual_period_date_day1_fix_bug(self):
        self._assign_primitive_values()
        tomorrow_date = str(date.today() + timedelta(days=1))
        COMMON_FIELDS[PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1] = tomorrow_date
        with freeze_time(tomorrow_date):
            primitive = PregnancyUpdate.create_from_dict(
                COMMON_FIELDS, name="PregnancyUpdate"
            )
        self.assertIsNotNone(primitive)
