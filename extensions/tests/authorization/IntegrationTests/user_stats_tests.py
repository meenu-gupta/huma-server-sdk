from datetime import datetime
from pathlib import Path

import freezegun
from dateutil.relativedelta import relativedelta

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.tasks import calculate_stats_per_user
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    GroupCategory,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_sign_up_data,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_group_information,
    sample_pregnancy_status,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.utils import inject
from sdk.common.utils.validators import utc_date_to_str
from sdk.versioning.component import VersionComponent

USER_ACTIVATION_CODE = "11000175"


class UserStatsTest(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        CalendarComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        KeyActionComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/user_stats.json")]

    def setUp(self):
        super().setUp()
        self.now = datetime.utcnow()
        self.first_vaccine_date = self.now - relativedelta(weeks=1)
        self.user_id = self._signup()

        self.module_result_route = (
            f"/api/extensions/v1beta/user/{self.user_id}/module-result"
        )
        self.headers = self.get_headers_for_token(self.user_id)

    def _signup(self):
        # signup a day before so all key actions will appear
        with freezegun.freeze_time(self.now - relativedelta(days=1)):
            user = get_sign_up_data("user1@example.com", "user1", USER_ACTIVATION_CODE)
            rsp = self.flask_client.post("/api/auth/v1beta/signup", json=user)
            return rsp.json["uid"]

    @property
    def user(self):
        repo = inject.instance(AuthorizationRepository)
        return repo.retrieve_user(user_id=self.user_id)

    def _submit_group_information(
        self, group_category: GroupCategory, vaccine_date=None
    ):
        group_information = sample_group_information()
        group_information[AZGroupKeyActionTrigger.GROUP_CATEGORY] = group_category
        group_information[AZGroupKeyActionTrigger.FIRST_VACCINE_DATE] = vaccine_date
        rsp = self.flask_client.post(
            f"{self.module_result_route}/AZGroupKeyActionTrigger",
            json=[group_information],
            headers=self.headers,
        )

        return rsp

    def _submit_pregnancy_status(self):
        rsp = self.flask_client.post(
            f"{self.module_result_route}/PregnancyStatus",
            json=[sample_pregnancy_status()],
            headers=self.headers,
        )

        return rsp

    def test_success_calculate_user_stats(self):
        self.assertIsNone(self.user.stats)
        calculate_stats_per_user()
        self.assertIsNotNone(self.user.stats)

    def test_stats_expiring_key_actions(self):
        vaccine_date = self.now - relativedelta(weeks=3, days=6)
        self._submit_group_information(
            GroupCategory.BREAST_FEEDING, utc_date_to_str(vaccine_date)
        )

        calculate_stats_per_user()
        compliance = self.user.stats.taskCompliance
        self.assertEqual(54, compliance.total)
        self.assertEqual(1, compliance.current)
        self.assertEqual(5, compliance.due)

    def test_stats_update_on_module_result_submission(self):
        calculate_stats_per_user()
        compliance = self.user.stats.taskCompliance
        self.assertEqual(2, compliance.total)
        self.assertEqual(0, compliance.current)
        self.assertEqual(0, compliance.due)

        initial_update_dt = compliance.updateDateTime

        self._submit_group_information(
            GroupCategory.PREGNANT, utc_date_to_str(self.first_vaccine_date)
        )
        compliance = self.user.stats.taskCompliance
        self.assertEqual(33, compliance.total)
        self.assertEqual(1, compliance.current)
        self.assertEqual(0, compliance.due)

        further_update_dt = compliance.updateDateTime
        self.assertGreater(further_update_dt, initial_update_dt)

        self._submit_pregnancy_status()
        compliance = self.user.stats.taskCompliance
        self.assertEqual(33, compliance.total)
        self.assertEqual(2, compliance.current)
        self.assertEqual(0, compliance.due)

        self.assertGreater(compliance.updateDateTime, further_update_dt)
