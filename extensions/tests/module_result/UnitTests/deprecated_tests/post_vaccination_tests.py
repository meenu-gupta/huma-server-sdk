from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.common.enums import (
    BrandOfVaccine,
    PlaceOfVaccination,
)
from extensions.module_result.models.primitives import (
    PostVaccination,
)


class PostVaccinationTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        COMMON_FIELDS[PostVaccination.SECOND_COVID_VACCINATION_DOSE] = "2019-06-30"
        COMMON_FIELDS[PostVaccination.IS_SECOND_DOSE_AZ] = False
        COMMON_FIELDS[PostVaccination.SECOND_DOSE_BRAND] = BrandOfVaccine.SINOVAC
        COMMON_FIELDS[PostVaccination.BATCH_NUMBER_VACCINE] = "ABV3922"
        COMMON_FIELDS[PostVaccination.IS_SAME_PLACE_VACCINE_2_AS_1] = True
        COMMON_FIELDS[PostVaccination.VACCINATION_PLACE] = PlaceOfVaccination.AIRPORT
        COMMON_FIELDS[PostVaccination.VACCINATION_PLACE_OTHER] = "HOME"
        COMMON_FIELDS[PostVaccination.VACCINATION_PLACE_LOCATION] = "LA"
        COMMON_FIELDS[PostVaccination.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                    QuestionnaireAnswer.QUESTION: "Please provide the date of your second COVID-19 vaccination dose.",
                    QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
                }
            ]
        }

    def test_success_creation(self):
        self._assign_primitive_values()
        primitive = PostVaccination.create_from_dict(
            COMMON_FIELDS, name="PostVaccination"
        )
        self.assertIsNotNone(primitive)

    def test_failure_creation_without_required_fields(self):
        required_fields = {
            PostVaccination.SECOND_COVID_VACCINATION_DOSE,
            PostVaccination.IS_SECOND_DOSE_AZ,
            PostVaccination.IS_SAME_PLACE_VACCINE_2_AS_1,
            PostVaccination.METADATA,
        }

        for field in required_fields:
            self._assign_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(PostVaccination)
