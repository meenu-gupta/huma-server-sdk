import unittest
from extensions.tests.deployment.UnitTests.deployment_model_tests import (
    CommonDeploymentTestCase,
)


class LocalizableTestCase(CommonDeploymentTestCase):
    def test_get_localized_path_with_learn_and_module_config(self):
        expected_res = [
            "deployment.learn.sections.title",
            "deployment.learn.sections.articles.title",
            "deployment.moduleConfigs.about",
        ]
        res = self.deployment.get_localized_path(path="deployment")
        for item in expected_res:
            self.assertIn(item, res)


if __name__ == "__main__":
    unittest.main()
