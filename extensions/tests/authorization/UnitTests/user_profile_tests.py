from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

import pytz
from freezegun import freeze_time
from freezegun.api import FakeDate

from extensions.authorization.models.user import User, BoardingStatus, RoleAssignment
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.use_cases.update_user_profile_use_case import (
    UpdateUserProfileUseCase,
)
from extensions.deployment.validators import validate_surgery_date
from extensions.deployment.models.deployment import (
    SurgeryDateRule,
    Features,
    AdditionalContactDetailsItem,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.exceptions import InvalidSurgeryDateError
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.authorization.UnitTests.test_helpers import (
    get_sample_preferred_units,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder

SAMPLE_STR_OBJECT_ID = "60cefee91dbe84aad14374de"


class MockAuthService(MagicMock):
    validate_user_preferred_units = MagicMock()
    update_covid_risk_score = MagicMock()


class MockRetrieveDeployment:
    instance = MagicMock()
    features = Features()


class UpdateUserProfileTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def configure_with_binder(binder: Binder):
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    @patch(
        "extensions.authorization.use_cases.update_user_profile_use_case.AuthorizationService",
        MockAuthService,
    )
    def test_success_update_user_profile_request_with_preferred_units(self):
        use_case = UpdateUserProfileUseCase(
            repo=MagicMock(), deployment_id="deployment_id"
        )
        request_object = UpdateUserProfileRequestObject.from_dict(
            get_sample_preferred_units()
        )
        use_case.execute(request_object)
        MockAuthService().validate_user_preferred_units.assert_called_once()
        MockAuthService().update_covid_risk_score.assert_called_once()


class GetFullNameTests(TestCase):
    def test_success_get_full_name(self):
        given_name = "givenName"
        family_name = "familyName"
        user = User(givenName="givenName", familyName="familyName")
        self.assertEqual(given_name + " " + family_name, user.get_full_name())


class UserStrTests(TestCase):
    def test_user_str(self):
        user = User()
        user.id = "ID"
        user.roles = [
            RoleAssignment(
                roleId="ADMIN",
                resource=f"deployment/1",
            ),
        ]
        user.timezone = pytz.UTC
        user.lastLoginDateTime = datetime.now()
        user.finishedOnboarding = True
        user.boardingStatus = BoardingStatus()
        user_expected_str = (
                f"[{User.__name__} {User.ID}: {user.id}, "
                f"{User.ROLES}: {[role.roleId for role in user.roles]}, "
                f"{User.TIMEZONE}: {user.timezone}, "
                f"{User.LAST_LOGIN_DATE_TIME}: {user.lastLoginDateTime}, "
                f"{User.FINISHED_ONBOARDING}: {user.finishedOnboarding}, "
        )

        # Scenario 1: Active
        user.boardingStatus.status = user.boardingStatus.Status.ACTIVE
        self.assertEqual(
            f"{user}",
            user_expected_str +
            f"{User.BOARDING_STATUS}: {user.boardingStatus.status.name}]"
        )
        
        # Scenario 2: Off boarded
        user.boardingStatus.status = user.boardingStatus.Status.OFF_BOARDED
        user.boardingStatus.reasonOffBoarded = (
            user.boardingStatus.ReasonOffBoarded(
                user.boardingStatus.ReasonOffBoarded.USER_NO_CONSENT
            )
        )
        self.assertEqual(
            f"{user}",
            user_expected_str +
            (
                f"{User.BOARDING_STATUS}: {user.boardingStatus.status.name}"
                + (
                    f", {User.BOARDING_STATUS}.{BoardingStatus.REASON_OFF_BOARDED}: "
                    f"{user.boardingStatus.reasonOffBoarded.name}]"
                )
            ),
        )


class UserProfileRequestTestCase(TestCase):
    @freeze_time("2012-01-01")
    def test_success_validate_surgery_date(self):
        surgery_dt = FakeDate(2012, 1, 1)
        surgery_date_rule = None
        try:
            validate_surgery_date(surgery_dt, surgery_date_rule)
        except InvalidSurgeryDateError:
            self.fail()

    @freeze_time("2012-01-01")
    def test_failure_surgery_date_less_than_min_range(self):
        surgery_dt = FakeDate(2009, 1, 1)
        surgery_date_rule = None
        with self.assertRaises(InvalidSurgeryDateError):
            validate_surgery_date(surgery_dt, surgery_date_rule)

    @freeze_time("2012-01-01")
    def test_success_validate_surgery_date_lower_date_rule(self):
        surgery_dt = FakeDate(2012, 1, 1)
        surgery_date_rule = SurgeryDateRule(maxPastRange="P1W")
        try:
            validate_surgery_date(surgery_dt, surgery_date_rule)
        except InvalidSurgeryDateError:
            self.fail()

    @freeze_time("2012-01-01")
    def test_failure_validate_surgery_date_lower_date_rule(self):
        surgery_dt = FakeDate(2011, 1, 1)
        surgery_date_rule = SurgeryDateRule(maxPastRange="P1W")
        with self.assertRaises(InvalidSurgeryDateError):
            validate_surgery_date(surgery_dt, surgery_date_rule)

    @freeze_time("2012-01-01")
    def test_success_validate_surgery_date_upper_date_rule(self):
        surgery_dt = FakeDate(2012, 1, 4)
        surgery_date_rule = SurgeryDateRule(maxFutureRange="P1W")
        try:
            validate_surgery_date(surgery_dt, surgery_date_rule)
        except InvalidSurgeryDateError:
            self.fail()

    @freeze_time("2012-01-01")
    def test_failure_validate_surgery_date_upper_date_rule(self):
        surgery_dt = FakeDate(2016, 1, 1)
        surgery_date_rule = SurgeryDateRule(maxFutureRange="P1W")
        with self.assertRaises(InvalidSurgeryDateError):
            validate_surgery_date(surgery_dt, surgery_date_rule)

    @freeze_time("2012-01-01")
    def test_success_validate_surgery_date_default_lower_date_rule(self):
        surgery_dt = FakeDate(2011, 1, 1)
        try:
            validate_surgery_date(surgery_dt, None)
        except InvalidSurgeryDateError:
            self.fail()

    @freeze_time("2012-01-01")
    def test_failure_validate_surgery_date_default_lower_date_rule(self):
        surgery_dt = FakeDate(2010, 1, 1)
        with self.assertRaises(InvalidSurgeryDateError):
            validate_surgery_date(surgery_dt, None)

    @freeze_time("2012-01-01")
    def test_success_validate_surgery_date_default_upper_date_rule(self):
        surgery_dt = FakeDate(2013, 1, 4)
        try:
            validate_surgery_date(surgery_dt, None)
        except InvalidSurgeryDateError:
            self.fail()

    @freeze_time("2012-01-01")
    def test_failure_validate_surgery_date_default_upper_date_rule(self):
        surgery_dt = FakeDate(2016, 1, 1)
        with self.assertRaises(InvalidSurgeryDateError):
            validate_surgery_date(surgery_dt, None)

    def test_success_create_additional_contact_details_nothing_required(self):
        AdditionalContactDetailsItem.from_dict({})
