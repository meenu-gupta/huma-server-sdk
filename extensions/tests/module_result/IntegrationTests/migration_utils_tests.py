from pathlib import Path

from bson import ObjectId

from extensions.module_result.migration_utils import migrate_eq5_to_new_structure
from extensions.module_result.models.primitives import (
    Questionnaire,
    EQ5D5L,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
)
from extensions.module_result.modules import EQ5D5LModule
from extensions.tests.test_case import ExtensionTestCase


class MigrationUtilsTest(ExtensionTestCase):
    components = []
    config_file_path = Path(__file__).with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
    ]
    eq_5d_5l_module_collection = EQ5D5L.__name__.lower()

    def test_migrate_eq5_to_new_structure(self):
        data = self._sample_eq5_data_in_db()
        self.mongo_database[Questionnaire.__name__.lower()].insert(data)

        eq5_data_before_migration = self._retrieve_all_eq_data_from_db()
        self.assertEqual(0, len([d for d in eq5_data_before_migration]))

        migrate_eq5_to_new_structure(self.mongo_database)
        eq5_data_after_converting = [d for d in self._retrieve_all_eq_data_from_db()]

        self.assertEqual(1, len(eq5_data_after_converting))
        eq5_dict = eq5_data_after_converting[0]
        eq5_primitive = EQ5D5L.from_dict(eq5_dict)
        self.assertIsNotNone(eq5_primitive)
        for item in [
            EQ5D5L.MOBILITY,
            EQ5D5L.SELF_CARE,
            EQ5D5L.USUAL_ACTIVITIES,
            EQ5D5L.PAIN,
            EQ5D5L.ANXIETY,
            EQ5D5L.EQ_VAS,
        ]:
            self.assertEqual(3, eq5_dict[item])
        eq5_primitive.healthState = 33333
        eq5_primitive.indexValue = 0.516

        res = self.mongo_database["deployment"].find(
            {"moduleConfigs.moduleId": EQ5D5LModule.moduleId}
        )
        self.assertNotEqual(0, len([r for r in res]))

        res = self.mongo_database["questionnaire"].find(
            {"moduleId": EQ5D5LModule.moduleId}
        )
        self.assertNotEqual(0, len([r for r in res]))

        res = self.mongo_database["questionnaire"].find_one(
            {"questionnaireName": "EQ-5D-5L"}
        )
        question_ids = [
            "hu_eq5d5l_mobility",
            "hu_eq5d5l_selfcare",
            "hu_eq5d5l_usualactivity",
            "hu_eq5d5l_paindiscomfort",
            "hu_eq5d5l_anxiety",
            "hu_eq5d5l_scale",
        ]
        for answer in res[Questionnaire.ANSWERS]:
            self.assertIn(answer[QuestionnaireAnswer.QUESTION_ID], question_ids)

        expected_module_config = "5f15af1967af6dcbc05e2790"
        recent_results_data = self.mongo_database["user"].find(
            {
                f"recentModuleResults.{expected_module_config}.Questionnaire.moduleId": "Questionnaire"
            }
        )
        self.assertEqual(0, recent_results_data.count())
        recent_results_data = self.mongo_database["user"].find(
            {
                f"recentModuleResults.{expected_module_config}.Questionnaire.moduleId": EQ5D5LModule.moduleId
            }
        )
        self.assertEqual(1, recent_results_data.count())

        query = {"moduleId": "Questionnaire", "questionnaireName": "EQ-5D-5L"}
        unseen_recent_results = self.mongo_database["unseenrecentresult"].find(query)
        self.assertEqual(0, unseen_recent_results.count())

        query = {"moduleId": EQ5D5LModule.moduleId, "questionnaireName": "EQ-5D-5L"}
        unseen_recent_results = self.mongo_database["unseenrecentresult"].find(query)
        self.assertEqual(1, unseen_recent_results.count())

    def _retrieve_all_eq_data_from_db(self):
        return self.mongo_database[self.eq_5d_5l_module_collection].find({})

    @staticmethod
    def _sample_eq5_data_in_db():
        return {
            Questionnaire.ID_: ObjectId("5f64f54e61c37dd829c8cf15"),
            Questionnaire.RAG_THRESHOLD: {Questionnaire.__name__: {}},
            Questionnaire.USER_ID: ObjectId("5e8f0c74b50aa9656c34789d"),
            Questionnaire.MODULE_ID: "Questionnaire",
            Questionnaire.MODULE_CONFIG_ID: ObjectId("5f15af1967af6dcbc05e2790"),
            Questionnaire.DEPLOYMENT_ID: ObjectId("5d386cc6ff885918d96edb2c"),
            Questionnaire.VERSION: 0,
            Questionnaire.DEVICE_NAME: "iOS",
            Questionnaire.IS_AGGREGATED: False,
            Questionnaire.SUBMITTER_ID: ObjectId("5e8f0c74b50aa9656c34789d"),
            Questionnaire.ANSWERS: [
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I have moderate problems in walking about",
                    QuestionnaireAnswer.ANSWER_SCORE: 3,
                    QuestionnaireAnswer.QUESTION_ID: "b037104f-8c1d-42a7-bb94-851206b8f057",
                    QuestionnaireAnswer.QUESTION: "<b>Your mobility TODAY</b>",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I have moderate problems washing or dressing myself",
                    QuestionnaireAnswer.ANSWER_SCORE: 3,
                    QuestionnaireAnswer.QUESTION_ID: "ace68441-6a3a-4ccd-9a26-8c37dc3273d9",
                    QuestionnaireAnswer.QUESTION: "<b>Your self-care TODAY</b>",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I have moderate problems doing my usual activities",
                    QuestionnaireAnswer.ANSWER_SCORE: 3,
                    QuestionnaireAnswer.QUESTION_ID: "dc5632b4-2ce7-4b72-b187-e4f8f777a94a",
                    QuestionnaireAnswer.QUESTION: "<b>Your usual activities TODAY</b>",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I have moderate pain or discomfort",
                    QuestionnaireAnswer.ANSWER_SCORE: 3,
                    QuestionnaireAnswer.QUESTION_ID: "647a6dc7-2289-4988-8451-c791c72b924f",
                    QuestionnaireAnswer.QUESTION: "<b>Your pain / discomfort TODAY</b>",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I'm moderately anxious or pressed",
                    QuestionnaireAnswer.ANSWER_SCORE: 3,
                    QuestionnaireAnswer.QUESTION_ID: "0cc66b89-108e-44d2-966a-e3a7be63bd63",
                    QuestionnaireAnswer.QUESTION: "<b>Your anxiety / depression TODAY</b>",
                },
                {
                    QuestionnaireAnswer.QUESTION_ID: "hu_eq5d5l_scale",
                    QuestionnaireAnswer.QUESTION: "Please tap or drag the scale to indicate how your health is TODAY",
                    QuestionnaireAnswer.FORMAT: QuestionAnswerFormat.SCALE.value,
                    QuestionnaireAnswer.VALUE: 3,
                },
            ],
            Questionnaire.QUESTIONNAIRE_ID: "8b517b38-acfd-4c1d-9158-3c91f2a64a58",
            Questionnaire.QUESTIONNAIRE_NAME: "EQ-5D-5L",
            Questionnaire.VALUE: 0.516,
        }
