from datetime import date, timedelta

from extensions.module_result.common.enums import VaccineLocation, VaccineCategory
from extensions.module_result.models.primitives import VaccinationDetails
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class VaccinationDetailsTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        payload = {
            VaccinationDetails.VACCINATED_PLACE: VaccineLocation.HOSPITAL,
            VaccinationDetails.VACCINATION_LOCATION: "NHS",
            VaccinationDetails.VACCINATION_CITY: "London",
            VaccinationDetails.BATCH_NUMBER: "ABV3922",
            VaccinationDetails.IS_SECOND_DOSE_VACC: "NO",
            VaccinationDetails.IS_SEASON_FLU_VAC: False,
            VaccinationDetails.IS_OTHER_SPECIFIED_VACC: True,
            VaccinationDetails.IS_ALLERGIC_REACTION_VACC: "NO",
            VaccinationDetails.OTHER_SPECIFIED_VACC: [
                VaccineCategory.SINGLES,
                VaccineCategory.HEPATITIS_A_or_B,
            ],
            VaccinationDetails.METADATA: {
                QuestionnaireMetadata.ANSWERS: [
                    {
                        QuestionnaireAnswer.QUESTION_ID: "032db29f-363c-418f-b626-2fa21adcc557",
                        QuestionnaireAnswer.QUESTION: "Where were you vaccinated?",
                        QuestionnaireAnswer.ANSWER_TEXT: "Hospital",
                    },
                    {
                        QuestionnaireAnswer.QUESTION_ID: "1d8efcfc-02c8-4153-95c3-f9bdb32499e0",
                        QuestionnaireAnswer.QUESTION: "Please specify where",
                        QuestionnaireAnswer.ANSWER_TEXT: "NHS",
                    },
                    {
                        QuestionnaireAnswer.QUESTION_ID: "3ce7cf65-f3d6-4bd0-8e67-fd9c98b636fd",
                        QuestionnaireAnswer.QUESTION: "Please specify the city/town.",
                        QuestionnaireAnswer.ANSWER_TEXT: "London",
                    },
                ]
            },
        }
        COMMON_FIELDS.update(payload)

    def test_success_creation(self):
        within_one_year = str(date.today() + timedelta(days=300))
        self.set_primitive_values()
        COMMON_FIELDS[VaccinationDetails.SECOND_VAC_SCHEDULE_DATE] = within_one_year
        primitive = VaccinationDetails.create_from_dict(
            COMMON_FIELDS, name="VaccinationDetails"
        )
        self.assertIsNotNone(primitive)

    def test_field_other_specified_vacc_wrong_value(self):
        self.set_primitive_values()
        COMMON_FIELDS[VaccinationDetails.OTHER_SPECIFIED_VACC] = "WRONGVALUE"
        self._assert_convertible_validation_err(VaccinationDetails)

    def test_failure_invalid_second_vac_schedule_date(self):
        over_one_year = str(date.today() + timedelta(days=367))
        self.set_primitive_values()
        COMMON_FIELDS[VaccinationDetails.SECOND_VAC_SCHEDULE_DATE] = over_one_year
        self._assert_convertible_validation_err(VaccinationDetails)
