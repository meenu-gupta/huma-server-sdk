from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from bson import ObjectId

from extensions.appointment.component import AppointmentComponent
from extensions.appointment.models.appointment import Appointment
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.appointment.IntegrationTests.appointment_router_tests import (
    stringify_date,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.inbox.component import InboxComponent

EVENT_MODEL_PATH = (
    "extensions.appointment.use_case.create_appointment_use_case.AppointmentEvent"
)
VALID_USER_ID = "5e84b0dab8dfa268b1180536"
APPOINTMENT_ID = "5eee34de4acf740d885767b8"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789c"


class AppointmentBadgesTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        AppointmentComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        InboxComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/appointments_dump.json")]
    user_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}"
    manager_route = f"/api/extensions/v1beta/user/{VALID_MANAGER_ID}/appointment"

    def get_headers_for(self, role: str = "Admin", user_id: str = None):
        if not user_id:
            user_id = VALID_MANAGER_ID if role == "Admin" else VALID_USER_ID
        return self.get_headers_for_token(user_id)

    @patch(f"{EVENT_MODEL_PATH}.execute", MagicMock())
    def test_badges_with_past_appointments(self):
        headers = self.get_headers_for("User")
        rsp = self.flask_client.get(self.user_route, headers=headers)
        user = rsp.json
        self.assertIn("badges", user)
        self.assertEqual(0, user["badges"]["appointments"])

    @patch(f"{EVENT_MODEL_PATH}.execute", MagicMock())
    def test_badges_with_future_appointments(self):
        self.flask_client.post(
            self.manager_route,
            json={
                Appointment.USER_ID: VALID_USER_ID,
                Appointment.START_DATE_TIME: stringify_date(
                    datetime.utcnow() + timedelta(hours=4)
                ),
            },
            headers=self.get_headers_for("Admin"),
        )

        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(self.user_route, headers=headers)
        user = rsp.json
        self.assertIn("badges", user)
        self.assertEqual(1, user["badges"]["appointments"])

    @patch(f"{EVENT_MODEL_PATH}.execute", MagicMock())
    def test_no_badges_when_no_appointments(self):
        self.delete_appointments_for_user()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(self.user_route, headers=headers)
        user = rsp.json
        self.assertIn("badges", user)
        self.assertEqual(0, user["badges"]["appointments"])

    @patch(f"{EVENT_MODEL_PATH}.execute", MagicMock())
    def test_no_badges_when_appointment_accepted(self):
        self.accept_appointment()
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(self.user_route, headers=headers)
        user = rsp.json
        self.assertIn("badges", user)
        self.assertEqual(0, user["badges"]["appointments"])

    def accept_appointment(self):
        self.mongo_database.appointment.update_one(
            {"_id": ObjectId(APPOINTMENT_ID)}, {"$set": {"status": "SCHEDULED"}}
        )

    def delete_appointments_for_user(self):
        self.mongo_database.appointment.delete_many({"userId": ObjectId(VALID_USER_ID)})
