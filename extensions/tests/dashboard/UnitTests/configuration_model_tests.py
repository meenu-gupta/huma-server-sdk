import unittest

from extensions.dashboard.models.configuration import (
    DeploymentLevelConfiguration,
    DayAnchor,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class DeploymentConfigurationModelTestCase(unittest.TestCase):
    def test_success_create_deployment_configuration(self):
        config = self._sample_deployment_configuration_dict()
        try:
            DeploymentLevelConfiguration.from_dict(config)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_invalid_ranges_consented_monthly(self):
        values_to_test = [-1, 5001]
        for value in values_to_test:
            config = self._sample_deployment_configuration_dict(consented_monthly=value)
            with self.assertRaises(ConvertibleClassValidationError):
                DeploymentLevelConfiguration.from_dict(config)

    def test_failure_invalid_min_range_target_consented(self):
        values_to_test = [0, 5001]
        for value in values_to_test:
            config = self._sample_deployment_configuration_dict(target_consented=value)
            with self.assertRaises(ConvertibleClassValidationError):
                DeploymentLevelConfiguration.from_dict(config)

    def test_failure_invalid_ranges_target_completed(self):
        values_to_test = [0, 5001]
        for value in values_to_test:
            config = self._sample_deployment_configuration_dict(target_completed=value)
            with self.assertRaises(ConvertibleClassValidationError):
                DeploymentLevelConfiguration.from_dict(config)

    def test_failure_invalid_value_day_anchor(self):
        config = self._sample_deployment_configuration_dict(
            day_anchor="something_wrong"
        )
        with self.assertRaises(ConvertibleClassValidationError):
            DeploymentLevelConfiguration.from_dict(config)

    @staticmethod
    def _sample_deployment_configuration_dict(
        consented_monthly: int = 50,
        target_consented: int = 50,
        day_anchor: str = DayAnchor.REGISTRATION_DATE.value,
        target_completed: int = 50,
    ):
        return {
            DeploymentLevelConfiguration.TARGET_CONSENTED_MONTHLY: consented_monthly,
            DeploymentLevelConfiguration.TARGET_CONSENTED: target_consented,
            DeploymentLevelConfiguration.DAY_0_ANCHOR: day_anchor,
            DeploymentLevelConfiguration.TARGET_COMPLETED: target_completed,
        }


if __name__ == "__main__":
    unittest.main()
