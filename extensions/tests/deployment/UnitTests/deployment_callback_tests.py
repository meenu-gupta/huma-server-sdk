import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from dateutil.relativedelta import relativedelta
from flask import Flask

from extensions.authorization.events import (
    GetDeploymentCustomRoleEvent,
    GetOrganizationCustomRoleEvent,
)
from extensions.authorization.events.pre_user_update_event import (
    PreUserProfileUpdateEvent,
)
from extensions.authorization.models.user import User, UserSurgeryDetails
from extensions.deployment.callbacks import (
    boarding_manager_check_off_boarding,
    combine_errors_and_raise,
    check_onboarding_is_required,
    validate_extra_custom_fields,
    validate_extra_custom_fields_on_user_update,
    validate_user_fields_with_profile_validators,
    validate_user_fields_with_un_editable_fields,
    custom_message_check,
    DISABLED_FEATURE_TEXT,
    DISABLED_CUSTOM_MESSAGING,
    INVALID_PREDEFINED_MSG_TEXT,
    deployment_mfa_required,
    validate_user_surgery_details_on_user_update,
    check_off_boarding,
    deployment_custom_role_callback,
    organization_custom_role_callback,
    validate_profile_fields_on_user_update,
    validate_user_surgery_date_on_user_update,
)
from extensions.deployment.models.deployment import FieldValidator
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.auth.events.mfa_required_event import MFARequiredEvent
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.inbox.events.auth_events import PreCreateMessageEvent

SAMPLE_ID = "600a8476a961574fb38157d5"
MANAGER_ID = "600a8476a961574fb38157d4"
DEPLOYMENT_ID = "600a8476a961574fb38157d3"
CALLBACK_PATH = "extensions.deployment.callbacks.callbacks"
testapp = Flask(__name__)


class DeploymentCallbackTestCase(unittest.TestCase):
    @patch(f"{CALLBACK_PATH}.BoardingManager")
    def test_success_boarding_manager_check_off_boarding(self, boarding_manager):
        authz_user = MagicMock()
        with testapp.test_request_context("/aaaa", method="GET") as _:
            boarding_manager_check_off_boarding(authz_user)
            boarding_manager().check_off_boarding_and_raise_error.assert_called_with()

    @patch(f"{CALLBACK_PATH}.g", spec={})
    @patch(f"{CALLBACK_PATH}.BoardingManager", MagicMock())
    def test_check_off_boarding(self, mock_g):
        mock_g.authz_user = MagicMock()
        with testapp.test_request_context("/aaaa", method="GET") as _:
            check_off_boarding(mock_g.authz_user)

    def test_success_combine_errors_and_raise(self):
        errors = {
            "FirstError": "some description for first error",
            "SecondError": "some description for second error",
        }
        with self.assertRaises(InvalidRequestException):
            combine_errors_and_raise(errors)

    @patch(f"{CALLBACK_PATH}.BoardingManager")
    @patch(f"{CALLBACK_PATH}.g", spec={})
    def test_success_check_onboarding_is_required(self, mock_g, boarding_manager):
        mock_g.authz_user = MagicMock()
        path = "/aaaa"
        with testapp.test_request_context(path, method="GET") as _:
            check_onboarding_is_required(MagicMock())
            boarding_manager.assert_called_with(mock_g.authz_user, path, None)
            boarding_manager().check_on_boarding_and_raise_error.assert_called_with()

    @patch(f"{CALLBACK_PATH}.validate_user_profile_field")
    def test_success_validate_extra_custom_fields(self, validate_fields):
        extra_custom_fields_dict = {"a": "b"}
        extra_custom_fields = extra_custom_fields_dict
        user = User(extraCustomFields=extra_custom_fields_dict)

        validate_extra_custom_fields(user=user, extra_custom_fields=extra_custom_fields)
        validate_fields.assert_called_with("a", "b", "b")

    @patch(f"{CALLBACK_PATH}.validate_extra_custom_fields")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_validate_extra_custom_fields_on_user_update(
        self, auth_service, authz_user, validate_custom_fields
    ):
        extra_custom_fields_dict = {"a": "b"}
        user = User(extraCustomFields=extra_custom_fields_dict, id=SAMPLE_ID)
        event = PreUserProfileUpdateEvent(user=user)
        validate_extra_custom_fields_on_user_update(event)

        auth_service().retrieve_simple_user_profile.assert_called_with(SAMPLE_ID)
        validate_custom_fields.assert_called_with(
            user, authz_user().deployment.extraCustomFields
        )

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_custom_message_check_callback(self, authz_user, _):
        predefined_text = "text"
        authz_user.deployment_id.return_value = DEPLOYMENT_ID
        authz_user().deployment.features = {}
        event = PreCreateMessageEvent(
            text=predefined_text,
            custom=True,
            submitter_id=MANAGER_ID,
            receiver_id=SAMPLE_ID,
        )
        # 1. Case when messaging feature disabled
        with self.assertRaises(InvalidRequestException) as e:
            custom_message_check(event)
        self.assertEqual(DISABLED_FEATURE_TEXT, e.exception.debug_message)

        # 2. Case when custom messaging feature disabled
        authz_user().deployment.features = MagicMock()
        messaging = authz_user().deployment.features.messaging
        messaging.enabled = True
        messaging.allowCustomMessage = False
        with self.assertRaises(InvalidRequestException) as e:
            custom_message_check(event)
        self.assertEqual(DISABLED_CUSTOM_MESSAGING, e.exception.debug_message)

        # 3. Case when predefined message not from predefined list
        event.custom = False
        messaging.messages = [predefined_text]
        custom_message_check(event)
        messaging.messages = [predefined_text + "error"]
        with self.assertRaises(InvalidRequestException) as e:
            custom_message_check(event)
        self.assertEqual(INVALID_PREDEFINED_MSG_TEXT, e.exception.debug_message)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_deployment_mfa_required_callback(self, authz_user, _):
        event = MFARequiredEvent(user_id=SAMPLE_ID)

        authz_user().deployment.security.mfaRequired = True
        self.assertEqual(deployment_mfa_required(event), True)

        authz_user().deployment.security.mfaRequired = False
        self.assertEqual(deployment_mfa_required(event), False)

        authz_user().deployment.security = None
        self.assertEqual(deployment_mfa_required(event), False)

    def test_deployment_custom_role_callback(self):
        deployment_repo = MagicMock()

        def bind_and_configure(binder):
            binder.bind(DeploymentRepository, deployment_repo)

        inject.clear_and_configure(bind_and_configure)

        event = GetDeploymentCustomRoleEvent(role_id="", resource_id="")
        try:
            deployment_custom_role_callback(event)
            deployment_repo.retrieve_deployment.assert_called_once_with(
                deployment_id=event.resource_id
            )
        except Exception as error:
            self.fail(error)

    def test_organization_custom_role_callback(self):
        org_repo = MagicMock()

        def bind_and_configure(binder):
            binder.bind(OrganizationRepository, org_repo)

        inject.clear_and_configure(bind_and_configure)

        event = GetOrganizationCustomRoleEvent(role_id="", resource_id="")
        try:
            organization_custom_role_callback(event)
            org_repo.retrieve_organization.assert_called_once_with(
                organization_id=event.resource_id
            )
        except Exception as error:
            self.fail(error)


class ProfileValidationTestCase(unittest.TestCase):
    def test_success_validate_user_fields_with_profile_validators_min(self):
        min_date = datetime.utcnow() - relativedelta(years=5)
        validators = {User.DATE_OF_BIRTH: FieldValidator(min=min_date)}
        user = User(dateOfBirth=min_date + relativedelta(years=1))

        try:
            validate_user_fields_with_profile_validators(user, validators)
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_success_validate_user_fields_with_profile_validators_max(self):
        max_date = datetime.utcnow() + relativedelta(years=5)
        validators = {User.DATE_OF_BIRTH: FieldValidator(max=max_date)}
        user = User(dateOfBirth=max_date - relativedelta(years=1))

        try:
            validate_user_fields_with_profile_validators(user, validators)
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_failure_validate_user_fields_with_profile_validators_min(self):
        min_date = datetime.utcnow() - relativedelta(years=5)
        validators = {User.DATE_OF_BIRTH: FieldValidator(min=min_date)}
        user = User(dateOfBirth=min_date - relativedelta(years=1))

        with self.assertRaises(ConvertibleClassValidationError):
            validate_user_fields_with_profile_validators(user, validators)

    def test_failure_validate_user_fields_with_profile_validators_max(self):
        max_date = datetime.utcnow() + relativedelta(years=5)
        validators = {User.DATE_OF_BIRTH: FieldValidator(max=max_date)}
        user = User(dateOfBirth=max_date + relativedelta(years=1))

        with self.assertRaises(ConvertibleClassValidationError):
            validate_user_fields_with_profile_validators(user, validators)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_validate_profile_fields_on_user_update(self, mock_auth_user, _):
        event = PreUserProfileUpdateEvent(user=MagicMock())

        mock_auth_user().is_user.return_value = True
        validate_profile_fields_on_user_update(event)

        mock_auth_user().is_user.return_value = False

        class MockDeployment(MagicMock):
            profile = None

        mock_auth_user().deployment = MockDeployment()
        validate_profile_fields_on_user_update(event)

    @patch(f"{CALLBACK_PATH}.g", spec={})
    def test_validate_user_surgery_date_on_user_update(self, _):
        class MockUser(MagicMock):
            surgeryDateTime = None

        user = MockUser()
        event = PreUserProfileUpdateEvent(user=user)
        validate_user_surgery_date_on_user_update(event)

    def test_validate_user_fields_with_un_editable_fields(self):
        user = User(id="testUserId", nhsId="myNewNshId")
        old_user = User(id="testUserId", nhsId="newmyNewNshId", givenName="test")
        un_editable_fields = ["nhsId"]
        with self.assertRaises(ConvertibleClassValidationError):
            validate_user_fields_with_un_editable_fields(
                user, old_user, un_editable_fields
            )

    def test_validate_user_fields_with_un_editable_fields_first_time_update(self):
        user = User(id="testUserId")
        old_user = User(id="testUserId", nhsId="myNewNshId", givenName="test")
        un_editable_fields = ["nhsId"]
        try:
            validate_user_fields_with_un_editable_fields(
                user, old_user, un_editable_fields
            )
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_validate_user_fields_with_un_editable_fields_value_unchanged(self):
        user = User(id="testUserId", nhsId="myNewNshId")
        old_user = User(id="testUserId", nhsId="myNewNshId", givenName="test")
        un_editable_fields = ["nhsId"]
        try:
            validate_user_fields_with_un_editable_fields(
                user, old_user, un_editable_fields
            )
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_validate_user_fields_with_un_editable_fields_empty_list(self):
        user = User(id="testUserId", nhsId="myNewNshId")
        old_user = User(id="testUserId", nhsId="myNewNshId")
        un_editable_fields = []
        try:
            validate_user_fields_with_un_editable_fields(
                user, old_user, un_editable_fields
            )
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_validate_user_fields_with_un_editable_fields_no_match(self):
        user = User(id="testUserId", nhsId="myNewNshId")
        old_user = User(id="testUserId", nhsId="myNewNshId")
        un_editable_fields = ["email"]
        try:
            validate_user_fields_with_un_editable_fields(
                user, old_user, un_editable_fields
            )
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_validate_user_surgery_details_on_user_update(self, authz_user, _):
        user = User(
            surgeryDetails=UserSurgeryDetails.from_dict(
                {
                    UserSurgeryDetails.OPERATION_TYPE: "ss",
                    UserSurgeryDetails.IMPLANT_TYPE: "ss",
                    UserSurgeryDetails.ROBOTIC_ASSISTANCE: "ss",
                }
            )
        )
        event = PreUserProfileUpdateEvent(user=user)

        class MockSurgery(MagicMock):
            validate_input = MagicMock(return_value={})

        authz_user().deployment.surgeryDetails = MockSurgery()
        try:
            validate_user_surgery_details_on_user_update(event)
        except InvalidRequestException:
            self.fail()

        authz_user().deployment.surgeryDetails.validate_input = MagicMock(
            return_value={"error": "error"}
        )
        with self.assertRaises(InvalidRequestException):
            validate_user_surgery_details_on_user_update(event)


if __name__ == "__main__":
    unittest.main()
