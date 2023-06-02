from pathlib import Path
from unittest.mock import patch

from extensions.appointment.component import AppointmentComponent
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.twilio_video.router.twilio_video_request import (
    InitiateVideoCallRequestObject,
)
from sdk.common.exceptions.exceptions import ObjectDoesNotExist, ErrorCodes
from extensions.tests.test_case import ExtensionTestCase
from extensions.twilio_video.component import TwilioVideoComponent
from extensions.twilio_video.models.twilio_video import VideoCall
from extensions.twilio_video.repository.mongo_video_repository import (
    MongoVideoCallRepository,
)
from sdk.auth.component import AuthComponent
from sdk.notification.component import NotificationComponent

SERVICE_PATH = "extensions.twilio_video.router.twilio_video_router.TwilioVideoService"
ADAPTER_PATH = "sdk.common.adapter.twilio.twilio_video_adapter.TwilioVideoAdapter"


def mocked_create_room(self, room_name):
    return VideoCallTestCase.MOCKED_ROOM_SID


def mock_twilio_validate(*args, **kwargs):
    return True


class VideoCallTestCase(ExtensionTestCase):
    VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789b"
    ANOTHER_DEPLOYMENT_MANAGER = "5e8f0c74b50aa9656c34789a"
    VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
    VALID_SUPER_ADMIN_ID = "602d031c68b787d552c55fb6"
    INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"
    VALID_ROOM_NAME = "5f0496ab82a630a9725336c1"
    VALID_APPOINTMENT_ID = "62b06da6c7f5ae7050c5a86d"
    INVALID_APPOINTMENT_ID = "111111111111111aaaaa5939"
    MOCKED_ROOM_SID = "RM63d1d8ce79ecd7d5a26a096b81a04396"
    MOCKED_AUTH_TOKEN = "TOKEN123"
    API_URL = "/api/extensions/v1beta"

    components = [
        AuthComponent(),
        AuthorizationComponent(),
        AppointmentComponent(),
        TwilioVideoComponent(),
        NotificationComponent(),
        DeploymentComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/data.json")]
    override_config = {"server.twilioVideo.enableAuth": "true"}

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(self.VALID_USER_ID)

    def initiate_call(
        self, manager_id=VALID_MANAGER_ID, user_id=VALID_USER_ID, **kwargs
    ):
        return self.flask_client.post(
            f"{self.API_URL}/manager/{manager_id}/video/user/{user_id}/initiate",
            headers=self.get_headers_for_token(manager_id),
            **kwargs,
        )

    @patch(
        "sdk.common.adapter.twilio.twilio_video_adapter.TwilioVideoAdapter.create_room",
        mocked_create_room,
    )
    def test_initiate_video_call__valid_with_same_deployment(self):
        resp = self.initiate_call()
        self.assertEqual(201, resp.status_code)
        self.assertEqual(self.MOCKED_ROOM_SID, resp.json["roomSid"])

    def test_initiate_video_call__invalid_with_different_deployments(self):
        resp = self.initiate_call(self.ANOTHER_DEPLOYMENT_MANAGER, self.VALID_USER_ID)
        self.assertEqual(403, resp.status_code)
        self.assertEqual(ErrorCodes.FORBIDDEN_ID, resp.json["code"])

    @patch(
        "sdk.common.adapter.twilio.twilio_video_adapter.TwilioVideoAdapter.create_room",
        mocked_create_room,
    )
    def test_initiate_video_call__invalid_with_empty_appointment(self):
        resp = self.initiate_call(
            json={InitiateVideoCallRequestObject.APPOINTMENT_ID: ""}
        )
        self.assertEqual(403, resp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, resp.json["code"])

    def test_initiate_video_call__invalid_with_wrong_appointment(self):
        resp = self.initiate_call(
            json={
                InitiateVideoCallRequestObject.APPOINTMENT_ID: self.INVALID_APPOINTMENT_ID
            }
        )
        self.assertEqual(404, resp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, resp.json["code"])

    @patch(
        "sdk.common.adapter.twilio.twilio_video_adapter.TwilioVideoAdapter.create_room",
        mocked_create_room,
    )
    def test_initiate_video_call_successfully_with_valid_appointment_id(self):
        resp = self.initiate_call(
            json={
                InitiateVideoCallRequestObject.APPOINTMENT_ID: self.VALID_APPOINTMENT_ID
            }
        )
        self.assertEqual(201, resp.status_code)
        self.assertEqual(self.MOCKED_ROOM_SID, resp.json["roomSid"])

    def test_twilio_callback_validator(self):
        resp = self.flask_client.post(f"{self.API_URL}/video/callbacks")
        self.assertEqual(403, resp.status_code)
        self.assertEqual(100004, resp.json["code"])

    @patch("twilio.request_validator.RequestValidator.validate", mock_twilio_validate)
    @patch(f"{SERVICE_PATH}.send_user_push_notification_invitation")
    @patch(f"{SERVICE_PATH}.update_video_call")
    @patch(f"{SERVICE_PATH}.complete_video_call")
    def test_twilio_callback_manager_joined(
        self, mocked_complete_video_call, mocked_update_video_call, mocked_push
    ):
        data = {
            "RoomName": self.VALID_ROOM_NAME,
            "RoomStatus": "in-progress",
            "StatusCallbackEvent": "participant-connected",
            "RoomDuration": 3,
            "ParticipantIdentity": f"manager:{self.VALID_MANAGER_ID}",
            "RoomSid": self.MOCKED_ROOM_SID,
        }
        resp = self.flask_client.post(f"{self.API_URL}/video/callbacks", data=data)
        self.assertEqual(200, resp.status_code)
        mocked_push.assert_called_once_with(
            room_name=self.VALID_ROOM_NAME,
            manager_id=self.VALID_MANAGER_ID,
            user_id=self.VALID_USER_ID,
        )
        mocked_update_video_call.assert_not_called()
        mocked_complete_video_call.assert_not_called()

    @patch("twilio.request_validator.RequestValidator.validate", mock_twilio_validate)
    @patch(f"{SERVICE_PATH}.send_user_push_notification_invitation")
    @patch(f"{SERVICE_PATH}.update_video_call")
    @patch(f"{SERVICE_PATH}.complete_video_call")
    def test_twilio_callback_user_joined(
        self, mocked_complete_video_call, mocked_update_video_call, mocked_push
    ):
        data = {
            "RoomName": self.VALID_ROOM_NAME,
            "RoomStatus": "in-progress",
            "StatusCallbackEvent": "participant-connected",
            "RoomDuration": 3,
            "ParticipantIdentity": f"user:{self.VALID_USER_ID}",
            "RoomSid": self.MOCKED_ROOM_SID,
        }
        resp = self.flask_client.post(f"{self.API_URL}/video/callbacks", data=data)
        self.assertEqual(200, resp.status_code)
        mocked_push.assert_not_called()
        mocked_update_video_call.assert_not_called()
        mocked_complete_video_call.assert_not_called()

    @patch("twilio.request_validator.RequestValidator.validate", mock_twilio_validate)
    @patch(f"{SERVICE_PATH}.send_user_push_notification_invitation")
    @patch(f"{SERVICE_PATH}.update_video_call")
    @patch(f"{SERVICE_PATH}.complete_video_call")
    def test_twilio_callback_room_closed(
        self, mocked_complete_video_call, mocked_update_video_call, mocked_push
    ):
        data = {
            "RoomName": self.VALID_ROOM_NAME,
            "RoomStatus": "completed",
            "StatusCallbackEvent": "room-ended",
            "RoomDuration": 3,
            "RoomSid": self.MOCKED_ROOM_SID,
        }
        video_call = VideoCall.from_dict(
            {
                "id": self.VALID_ROOM_NAME,
                "roomStatus": data["RoomStatus"],
                "duration": data["RoomDuration"],
            },
            ignored_fields=["roomStatus"],
        )
        resp = self.flask_client.post(f"{self.API_URL}/video/callbacks", data=data)
        self.assertEqual(200, resp.status_code)
        mocked_push.assert_not_called()
        mocked_update_video_call.assert_called_once_with(video_call)
        mocked_complete_video_call.assert_not_called()

    @patch("twilio.request_validator.RequestValidator.validate", mock_twilio_validate)
    @patch(f"{SERVICE_PATH}.retrieve_call_participants")
    @patch(f"{SERVICE_PATH}.send_user_push_notification_invitation")
    @patch(f"{SERVICE_PATH}.update_video_call")
    @patch(f"{SERVICE_PATH}.complete_video_call")
    def test_twilio_callback_no_one_left(
        self,
        mocked_complete_video_call,
        mocked_update_video_call,
        mocked_push,
        mock_call_participants,
    ):
        mock_call_participants.return_value = []
        data = {
            "RoomName": self.VALID_ROOM_NAME,
            "RoomStatus": "in-progress",
            "StatusCallbackEvent": "participant-disconnected",
            "RoomDuration": 3,
            "ParticipantIdentity": f"user:{self.VALID_USER_ID}",
            "RoomSid": self.MOCKED_ROOM_SID,
        }

        resp = self.flask_client.post(f"{self.API_URL}/video/callbacks", data=data)
        self.assertEqual(200, resp.status_code)
        mocked_push.assert_not_called()
        mocked_update_video_call.assert_not_called()
        mocked_complete_video_call.assert_called_once_with(self.MOCKED_ROOM_SID)

    @patch(f"{SERVICE_PATH}.send_user_push_notification_call_ended")
    @patch(f"{ADAPTER_PATH}.complete_room")
    def test_complete_video_call_valid_by_manager(
        self, mocked_complete_room, mocked_push
    ):
        resp = self.flask_client.post(
            f"{self.API_URL}/manager/{self.VALID_MANAGER_ID}/video/{self.VALID_ROOM_NAME}/complete",
            headers=self.get_headers_for_token(self.VALID_MANAGER_ID),
        )
        self.assertEqual(200, resp.status_code)
        mocked_complete_room.assert_called_once()
        mocked_push.assert_called_once()

    @patch(f"{ADAPTER_PATH}.complete_room")
    def test_complete_video_call_valid_by_user(self, mocked_complete_room):
        resp = self.flask_client.post(
            f"{self.API_URL}/user/{self.VALID_USER_ID}/video/{self.VALID_ROOM_NAME}/complete",
            headers=self.headers,
        )
        self.assertEqual(200, resp.status_code)
        mocked_complete_room.assert_called_once()

    def test_success_delete_user_video_call(self):
        repo = MongoVideoCallRepository()
        video_call_id = repo.create_video_call(
            manager_id=self.VALID_MANAGER_ID, user_id=self.VALID_USER_ID
        )

        video_call = repo.retrieve_video_call(video_call_id=video_call_id)
        self.assertIsNotNone(video_call)

        super_admin_headers = self.get_headers_for_token(self.VALID_SUPER_ADMIN_ID)

        del_user_path = f"{self.API_URL}/user/{self.VALID_USER_ID}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=super_admin_headers)
        self.assertEqual(rsp.status_code, 204)

        with self.assertRaises(ObjectDoesNotExist):
            repo.retrieve_video_call(video_call_id=video_call_id)


class TwilioTestAppTestCase(ExtensionTestCase):
    API_URL = "/api/extensions/v1beta"
    override_config = {"server.twilioVideo.enableAuth": "true"}
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        TwilioVideoComponent(),
    ]

    def test_get_twilio_test_app_debug_success(self):
        self.test_server.config.server.debugRouter = True
        resp = self.flask_client.get(f"{self.API_URL}/video/test")
        self.assertEqual(200, resp.status_code)

    def test_get_twilio_test_app_no_debug_fails(self):
        self.test_server.config.server.debugRouter = False
        resp = self.flask_client.get(f"{self.API_URL}/video/test")
        self.assertEqual(403, resp.status_code)
