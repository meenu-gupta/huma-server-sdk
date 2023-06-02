import unittest

from extensions.common.s3object import S3Object
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_video_questionnaire import (
    VideoQuestionnaireStep,
    VideoQuestionnaire,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class VideoQuestionnairePrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            VideoQuestionnaireStep.S3OBJECT: {
                S3Object.BUCKET: "somebucket",
                S3Object.KEY: "somekey",
            },
            VideoQuestionnaireStep.START_DATE_TIME: 1634872593,
        }

    def test_success_create_video_questionnaire_step_primitive(self):
        data = self._sample_data()
        try:
            VideoQuestionnaireStep.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_video_questionnaire_step__no_required_fields(self):
        required_fields = [
            VideoQuestionnaireStep.START_DATE_TIME,
            VideoQuestionnaireStep.S3OBJECT,
        ]
        for field in required_fields:
            data = self._sample_data()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                VideoQuestionnaireStep.from_dict(data)

    def test_success_create_video_questionnaire_primitive(self):
        data = {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            VideoQuestionnaire.STEPS: [self._sample_data()],
        }
        try:
            VideoQuestionnaire.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_video_questionnaire_primitive__no_required_fields(self):
        data = {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
        }
        with self.assertRaises(ConvertibleClassValidationError):
            VideoQuestionnaire.from_dict(data)


if __name__ == "__main__":
    unittest.main()
