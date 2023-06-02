import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, TaskCompliance
from extensions.deployment.models.stats_calculator import DeploymentStatsCalculator

STATS_CALC_PATH = "extensions.deployment.models.stats_calculator"


class DeploymentStatsCalculatorTestCase(unittest.TestCase):
    @patch(f"{STATS_CALC_PATH}.DeploymentService", MagicMock())
    def setUp(self) -> None:
        self.deployment = MagicMock()
        self.auth_repo = MagicMock()
        self.consent_repo = MagicMock()
        self.econsent_repo = MagicMock()
        self.organisation_repo = MagicMock()
        self.calculator = DeploymentStatsCalculator(
            self.deployment,
            self.auth_repo,
            self.consent_repo,
            self.econsent_repo,
            self.organisation_repo,
        )

    @patch(f"{STATS_CALC_PATH}.Stats")
    @patch(f"{STATS_CALC_PATH}.DeploymentStatsCalculator.retrieve_task_compliance_rate")
    @patch(
        f"{STATS_CALC_PATH}.DeploymentStatsCalculator.retrieve_completed_users_count"
    )
    @patch(
        f"{STATS_CALC_PATH}.DeploymentStatsCalculator.retrieve_consented_users_count"
    )
    @patch(f"{STATS_CALC_PATH}.DeploymentStatsCalculator.retrieve_enrolled_users_count")
    def test_success_run(
        self,
        retrieve_enrolled_users_count,
        retrieve_consented_users_count,
        retrieve_completed_users_count,
        retrieve_task_compliance_rate,
        stats,
    ):
        self.calculator.run()

        retrieve_enrolled_users_count.assert_called_once_with()
        retrieve_consented_users_count.assert_called_once_with()
        retrieve_completed_users_count.assert_called_once_with()
        retrieve_task_compliance_rate.assert_called_once_with()

    def test_success_retrieve_enrolled_users_count(self):
        self.calculator.retrieve_enrolled_users_count()
        self.auth_repo.retrieve_users_count.assert_called_with(
            deployment_id=self.deployment.id,
            role=RoleName.USER,
            finishedOnboarding=True,
        )

    @patch(f"{STATS_CALC_PATH}.isodate")
    def test_success_retrieve_completed_users_count(self, isodate):
        self.calculator.retrieve_completed_users_count()
        self.auth_repo.retrieve_users_count.assert_called_with(
            None,
            isodate.parse_duration().__rsub__(),
            self.deployment.id,
            RoleName.USER,
        )

    @patch(f"{STATS_CALC_PATH}.DeploymentStatsCalculator._retrieve_consented_users")
    @patch(f"{STATS_CALC_PATH}.DeploymentStatsCalculator._retrieve_e_consented_users")
    def test_success_retrieve_consented_users_count(
        self, _retrieve_e_consented_users, _retrieve_consented_users
    ):
        self.calculator.retrieve_consented_users_count()
        _retrieve_e_consented_users.assert_called_once_with()

    def test_success_retrieve_e_consented_users(self):
        self.calculator._retrieve_e_consented_users()
        self.econsent_repo.retrieve_consented_users.assert_called_with(
            econsent_id=self.deployment.econsent.id
        )

    def test_success_retrieve_patient_count(self):
        self.calculator.retrieve_patient_count()
        self.auth_repo.retrieve_users_count.assert_called_with(
            deployment_id=self.deployment.id,
            role=RoleName.USER,
        )

    def test_success_retrieve_organisation_view_type(self):
        self.calculator.retrieve_organisation_view_type()
        self.organisation_repo.retrieve_organization_by_deployment_id.assert_called_with(
            deployment_id=self.deployment.id,
        )

    @patch(f"{STATS_CALC_PATH}.RoleAssignment")
    def test_success_retrieve_user_timezones(self, role_assignment):
        self.calculator._retrieve_user_timezones()
        role_assignment.create_role.assert_called_with(
            RoleName.USER, self.deployment.id
        )
        filter_options = {
            f"{User.ROLES}.resource": role_assignment.create_role().resource
        }
        self.auth_repo.retrieve_users_timezones.assert_called_with(**filter_options)

    def test_percentage_calculation(self):
        task_dict = {TaskCompliance.CURRENT: 20, TaskCompliance.TOTAL: 100}
        sample = TaskCompliance.from_dict(task_dict)
        self.assertEqual(20, sample.percentage)

    def test_percentage_calculation_without_total(self):
        task_dict = {
            TaskCompliance.CURRENT: 20,
        }
        sample = TaskCompliance.from_dict(task_dict)
        self.assertIsNone(sample.percentage)

    def test_percentage_calculation_without_current(self):
        task_dict = {
            TaskCompliance.TOTAL: 20,
        }
        sample = TaskCompliance.from_dict(task_dict)
        self.assertIsNone(sample.percentage)

    def test_percentage_calculation_without_data(self):
        task_dict = {}
        sample = TaskCompliance.from_dict(task_dict)
        self.assertIsNone(sample.percentage)


if __name__ == "__main__":
    unittest.main()
