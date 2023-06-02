from unittest import TestCase

from extensions.module_result.common.questionnaire_utils import manual_translation

sample_raw_data = [
    {
        "answers": [
            {
                "answerText": "Very mild problem",
                "question": "In the past 4 weeks, has pain kept you awake or woken you at night?",
                "questionId": "hu_norfolk_diffiactivities_q40",
            }
        ]
    }
]
question_map = {
    "hu_norfolk_diffiactivities_q40": {
        "logic": {"isEnabled": False},
        "description": "",
        "id": "hu_norfolk_diffiactivities_q40",
        "required": True,
        "format": "TEXTCHOICE",
        "order": 1,
        "text": "hu_norfolk_dressing",
        "options": [
            {
                "label": "hu_norfolk_commonOp_notaProblem",
                "value": "0",
                "weight": 0,
            },
            {
                "label": "hu_norfolk_commonOp_veryMild",
                "value": "1",
                "weight": 1,
            },
        ],
        "selectionCriteria": "SINGLE",
    }
}

localization = {
    "hu_norfolk_commonOp_notaProblem": "Not a problem",
    "hu_norfolk_commonOp_veryMild_diff_label_1": "Very mild problem",
    "hu_norfolk_commonOp_veryMild_diff_label_2": "Very mild problem",
    "hu_norfolk_commonOp_veryMild": "Very mild problem",
}


class QuestionnaireUtilsTestCase(TestCase):
    def test_success_manual_translation_missing_answer_text(self):
        raw_data = [
            {
                "deploymentId": "61701c88bb156fe41f26147e",
                "deviceName": "Android",
                "hipCircumference": 209.19223022460938,
                "totalBodyFat": 26.0,
                "type": "BodyMeasurement",
                "userId": "617923c7d18c164cfd2d4ac8",
                "version": 1,
                "visceralFat": 6.5,
                "waistCircumference": 179.0,
            },
            {
                "answers": [
                    {
                        "compositeAnswer": {
                            "weight": 56,
                            "height": 200,
                            "activityLevel": 2,
                        },
                        "question": "'What is your age, sex at birth, weight, height and activity level?'",
                        "questionId": "'body_measurement_health_info'",
                        "questionText": "'What is your age, sex at birth, weight, height and activity level?'",
                    },
                ]
            },
        ]
        result = manual_translation(raw_data, {}, {})
        self.assertIsNotNone(result)

    def test_correct_label_is_assigned_to_correct_localized_answer(self):
        """Test if the label for the translated answer is a valid option in the config of the question"""
        result = manual_translation(sample_raw_data, question_map, localization)
        correct_config_option = "hu_norfolk_commonOp_veryMild"
        self.assertEqual(correct_config_option, result[0]["answers"][0]["answerText"])
