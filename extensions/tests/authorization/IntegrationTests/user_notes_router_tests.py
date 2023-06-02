import itertools
from pathlib import Path

from extensions.authorization.component import AuthorizationComponent

from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.user_note import UserNote
from extensions.module_result.component import ModuleResultComponent
from extensions.deployment.router.deployment_requests import (
    RetrieveUserNotesRequestObject,
)
from extensions.module_result.models.primitives import QuestionnaireAnswer
from extensions.organization.component import OrganizationComponent

from sdk.auth.component import AuthComponent
from sdk.tests.application_test_utils.test_utils import IntegrationTestCase

CONFIG_PATH = Path(__file__).with_name("config.test.yaml")


class UserNotesRouterTestCase(IntegrationTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/care_plan_group_dump.json")]
    config_file_path = CONFIG_PATH

    @classmethod
    def setUpClass(cls) -> None:
        super(UserNotesRouterTestCase, cls).setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.user_id = "5e8f0c74b50aa9656c34789c"
        cls.admin_id = "5e8f0c74b50aa9656c34789d"
        cls.base_path = "/api/extensions/v1beta/user"

    def _send_retrieve_user_notes_api_request(
        self, user_id: str, deployment_id: str, skip: int = 0, limit: int = 50
    ):
        headers = self.get_headers_for_token(self.admin_id)
        request_object = RetrieveUserNotesRequestObject(
            userId=user_id, deploymentId=deployment_id, skip=skip, limit=limit
        )
        return self.flask_client.post(
            f"{self.base_path}/{user_id}/deployment/{deployment_id}/notes",
            json=request_object.to_dict(),
            headers=headers,
        )

    def test_failure_retrieve_notes_negative_limit(self):
        rsp = self._send_retrieve_user_notes_api_request(
            self.user_id, self.deployment_id, limit=-1
        )
        self.assertEqual(rsp.status_code, 403)

    def test_failure_retrieve_notes_negative_skip(self):
        rsp = self._send_retrieve_user_notes_api_request(
            self.user_id, self.deployment_id, skip=-1
        )
        self.assertEqual(rsp.status_code, 403)

    def test_success_retrieve_user_notes(self):
        rsp = self._send_retrieve_user_notes_api_request(
            self.user_id, self.deployment_id
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json))

        # check translation
        self.assertEqual(
            rsp.json[2][UserNote.ANSWERS][0][QuestionnaireAnswer.ANSWER_TEXT], "aaa"
        )

        question_lists = [
            [answer[QuestionnaireAnswer.QUESTION] for answer in item[UserNote.ANSWERS]]
            for item in rsp.json
            if UserNote.ANSWERS in item
        ]
        question_list = list(itertools.chain.from_iterable(question_lists))
        self.assertNotIn("hu_obs_notes", question_list)
        self.assertNotIn("hu_obs_notes_2", question_list)

        answer_lists = [
            [
                answer[QuestionnaireAnswer.ANSWER_TEXT]
                for answer in item[UserNote.ANSWERS]
            ]
            for item in rsp.json
            if UserNote.ANSWERS in item
        ]
        answer_list = list(itertools.chain.from_iterable(answer_lists))
        self.assertNotIn("hu_sample_answer", answer_list)

        # careplangroup note should not include some fields
        self.assertEqual("test1 test1", rsp.json[0][UserNote.SUBMITTER_NAME])
        self.assertEqual(
            UserNote.UserNoteType.CAREPLANGROUPLOG.value, rsp.json[0][UserNote.TYPE]
        )
        self.assertNotIn(UserNote.ANSWERS, rsp.json[0])
        self.assertNotIn(UserNote.MODULE_CONFIG_ID, rsp.json[0])
        self.assertNotIn(UserNote.QUESTIONNAIRE_ID, rsp.json[0])

        # observation note should not include some fields
        self.assertEqual(2, len(rsp.json[1][UserNote.ANSWERS]))
        self.assertEqual("test1 test1", rsp.json[1][UserNote.SUBMITTER_NAME])
        self.assertEqual(
            UserNote.UserNoteType.OBSERVATION_NOTES.value, rsp.json[1][UserNote.TYPE]
        )
        self.assertNotIn(UserNote.FROM_CARE_PLAN_GROUP_ID, rsp.json[1])
        self.assertNotIn(UserNote.TO_CARE_PLAN_GROUP_ID, rsp.json[1])
        self.assertNotIn(UserNote.NOTE, rsp.json[1])

    def test_retrieve_notes_when_no_submitter_id(self):
        note_id = "60084cec1523b147db7cd3cd"
        rsp = self._send_retrieve_user_notes_api_request(
            self.user_id, self.deployment_id
        )
        self.assertEqual(200, rsp.status_code)
        response = rsp.json
        note_ids = [x[UserNote.ID] for x in response]
        self.assertIn(note_id, note_ids)

    def test_failure_with_invalid_deployment_id(self):
        rsp = self._send_retrieve_user_notes_api_request(
            self.user_id, "5d386cc6ff885918d96edbdd"
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_with_invalid_user_id(self):
        rsp = self._send_retrieve_user_notes_api_request(
            "5e8f0c74b50aa9656c3478cc", self.deployment_id
        )
        self.assertEqual(404, rsp.status_code)
