from pathlib import Path
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.authorization.callbacks import on_calendar_view_users_data_callback
from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.deployment.component import DeploymentComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.auth.use_case.auth_request_objects import Method
from sdk.calendar.events import CalendarViewUserDataEvent
from sdk.common.utils import inject
from sdk.tests.auth.test_helpers import (
    send_verification_token,
    phone_number_sign_in_request,
    set_auth_attributes,
    USER_EMAIL,
    USER_PHONE_NUMBER,
    CONFIRMATION_CODE,
)

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
USER_ID = "5ed803dd5f2f99da73684412"


class CallbacksTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        def mock_sms_adaptor(binder):
            binder.bind("aliCloudSmsVerificationAdapter", MagicMock())
            binder.bind("twilioSmsVerificationAdapter", MagicMock())

        inject.get_injector().rebind(mock_sms_adaptor)

    def test_success_on_calendar_view_users_data_callback(self):
        required_fields = ("createDateTime", "surgeryDateTime")
        event = CalendarViewUserDataEvent()
        result = on_calendar_view_users_data_callback(event)
        match_query = {"$elemMatch": {RoleAssignment.ROLE_ID: RoleName.USER}}
        query = {User.ROLES: match_query}
        users_in_db = self.mongo_database["user"].find(query).count()

        self.assertEqual(users_in_db, len(result.users_data))
        user_id_with_no_data = "5e8f0c74b50aa9656c34789e"
        user_id_with_one_data = "61fb852583e256e58e7ea9e3"
        for item in result.users_data:
            if item["id"] == user_id_with_no_data:
                self.assertEqual(len(item.keys()), 1)
                continue
            if item["id"] == user_id_with_one_data:
                self.assertEqual(len(item.keys()), 2)
                continue
            self.assertEqual(len(item.keys()), len(required_fields) + 1)
            self.assertIn("id", item)
            for field in required_fields:
                self.assertIn(field, item)

        self.assertIn("createDateTime", result.additional_fields)
        self.assertIn("surgeryDateTime", result.additional_fields)

    def test_set_email_updates_user_profile_email(self):
        rsp = send_verification_token(
            flask_client=self.flask_client,
            method=Method.PHONE_NUMBER,
            phone_number=USER_PHONE_NUMBER,
            client_id="ctest1",
        )
        self.assertEqual(rsp.status_code, 200)
        rsp = phone_number_sign_in_request(
            self.flask_client, USER_PHONE_NUMBER, CONFIRMATION_CODE
        )
        self.assertEqual(rsp.status_code, 200)
        auth_token = rsp.json["authToken"]
        user_id = rsp.json["uid"]
        query = {User.ID_: ObjectId(user_id)}

        # confirming no email in user's profile
        user = self.mongo_database["user"].find_one(query)
        self.assertNotIn(User.EMAIL, user)

        set_auth_attributes(self.flask_client, auth_token, email=USER_EMAIL)

        # confirming email appeared after setting auth attributes
        user = self.mongo_database["user"].find_one(query)
        self.assertEqual(user[User.EMAIL], USER_EMAIL)
