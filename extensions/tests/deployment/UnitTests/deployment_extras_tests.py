import unittest

from extensions.deployment.deployment_extras import DeploymentExtras
from sdk.common.utils.convertible import ConvertibleClassValidationError


class DeploymentExtrasTestCase(unittest.TestCase):
    def test_success_create_deployment_extras(self):
        try:
            DeploymentExtras.from_dict(
                {
                    DeploymentExtras.HAS_DEVICE_INTEGRATION: True,
                    DeploymentExtras.HAS_CLINICIAN_SEEN_INDICATOR: True,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_wrong_types(self):
        with self.assertRaises(ConvertibleClassValidationError):
            DeploymentExtras.from_dict(
                {
                    DeploymentExtras.HAS_DEVICE_INTEGRATION: "",
                    DeploymentExtras.HAS_CLINICIAN_SEEN_INDICATOR: True,
                }
            )

        with self.assertRaises(ConvertibleClassValidationError):
            DeploymentExtras.from_dict(
                {
                    DeploymentExtras.HAS_DEVICE_INTEGRATION: True,
                    DeploymentExtras.HAS_CLINICIAN_SEEN_INDICATOR: "",
                }
            )


if __name__ == "__main__":
    unittest.main()
