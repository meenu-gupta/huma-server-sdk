from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import (
    BackgroundInformation,
    QuestionnaireAnswer,
)
from extensions.module_result.common.enums import (
    BabyGender,
    Employment,
    GenderIdentity,
    SmokingStatus,
    SmokingStopped,
)


class BackgroundInformationTestCase(PrimitiveTestCase):
    def set_primitive_values(self):
        COMMON_FIELDS[BackgroundInformation.AGE] = 19
        COMMON_FIELDS[BackgroundInformation.HEIGHT] = 120
        COMMON_FIELDS[BackgroundInformation.WEIGHT] = 250
        COMMON_FIELDS[BackgroundInformation.SEX_AT_BIRTH] = BabyGender.MALE
        COMMON_FIELDS[BackgroundInformation.GENDER_IDENTITY] = GenderIdentity.MALE
        COMMON_FIELDS[BackgroundInformation.RESIDENCY_COUNTRY] = "Germany"
        COMMON_FIELDS[BackgroundInformation.BIRTH_COUNTRY] = "Germany"
        COMMON_FIELDS[BackgroundInformation.EMPLOYMENT] = Employment.EMPLOYED
        COMMON_FIELDS[BackgroundInformation.SMOKING_STATUS] = SmokingStatus.FORMER
        COMMON_FIELDS[
            BackgroundInformation.SMOKING_STOPPED
        ] = SmokingStopped.ONE_TO_FIVE
        COMMON_FIELDS[BackgroundInformation.METADATA] = {
            QuestionnaireMetadata.ANSWERS: [
                {
                    QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                    QuestionnaireAnswer.QUESTION: "How old are you?",
                    QuestionnaireAnswer.ANSWER_TEXT: "19",
                },
            ]
        }

    def test_success_creation(self):
        self.set_primitive_values()
        primitive = BackgroundInformation.create_from_dict(
            COMMON_FIELDS, name="BackgroundInformation"
        )
        self.assertIsNotNone(primitive)

    def test_failed_missing_required_fields(self):
        required_fields_keys = [
            BackgroundInformation.AGE,
            BackgroundInformation.SEX_AT_BIRTH,
            BackgroundInformation.WEIGHT,
            BackgroundInformation.HEIGHT,
            BackgroundInformation.GENDER_IDENTITY,
            BackgroundInformation.RESIDENCY_COUNTRY,
            BackgroundInformation.BIRTH_COUNTRY,
            BackgroundInformation.EMPLOYMENT,
            BackgroundInformation.SMOKING_STATUS,
            BackgroundInformation.METADATA,
        ]

        for field in required_fields_keys:
            self.set_primitive_values()
            del COMMON_FIELDS[field]
            self._assert_convertible_validation_err(BackgroundInformation)

    def test_failed_age_out_of_range(self):
        self.set_primitive_values()
        COMMON_FIELDS[BackgroundInformation.AGE] = 150
        self._assert_convertible_validation_err(BackgroundInformation)

    def test_failed_weight_out_of_range(self):
        self.set_primitive_values()
        COMMON_FIELDS[BackgroundInformation.HEIGHT] = 300
        self._assert_convertible_validation_err(BackgroundInformation)

    def test_failed_height_out_of_range(self):
        self.set_primitive_values()
        COMMON_FIELDS[BackgroundInformation.WEIGHT] = 1000
        self._assert_convertible_validation_err(BackgroundInformation)
