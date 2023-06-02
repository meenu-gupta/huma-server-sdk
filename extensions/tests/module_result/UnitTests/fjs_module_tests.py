import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from extensions.deployment.models.status import EnableStatus
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.modules import FJSHipScoreModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_fjs_hip_score_data,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

CLIENT_ID = "c1"
PROJECT_ID = "p1"
USER_ID = "6131bdaaf9af87a4f08f4d02"


class FJSModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=FJSHipScoreModule.moduleId, configBody={}
        )
        self.module_config.status = EnableStatus.ENABLED

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_fjs_module_score(self):
        module = FJSHipScoreModule()
        module.config = self.module_config
        module.calculator._get_answer_weight = MagicMock(return_value=1)
        primitives = [
            Questionnaire.from_dict(
                {**sample_fjs_hip_score_data(), Primitive.USER_ID: USER_ID}
            )
        ]
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 1)
        module.calculate(primitives[0])
        questionnaire_primitive = primitives[0]
        self.assertEqual(questionnaire_primitive.value, 100.0)

    def test_failure_not_enough_answers_fjs_hip_questionnaire(self):
        module = FJSHipScoreModule()
        module.config = self.module_config
        data = sample_fjs_hip_score_data()
        data = {**data, Questionnaire.ANSWERS: data[Questionnaire.ANSWERS][:7]}
        primitives = [
            Questionnaire.from_dict(
                {
                    **data,
                    Primitive.USER_ID: USER_ID,
                }
            )
        ]
        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, MagicMock())

    def test_extract_fjs_hip_module_config(self):
        module = FJSHipScoreModule()
        module.config = module.extract_module_config(
            module_configs=[self.module_config],
            primitive=None,
            module_config_id=self.module_config.id,
        )
        # result_config_body = module.config.configBody
        # TODO Needs to to enable FJSHip as licensed questionnaire module
        #  expected_config_body = self._retrieve_expected_json("FJSHip/v1/config_body")
        #  self.assertEqual(expected_config_body, result_config_body)

    def _retrieve_expected_json(self, config_name: str):
        module_path = f"{Path(__file__).parents[4]}/extensions/module_result/modules/licensed_configs/{config_name}.json"
        with open(module_path) as file:
            return json.load(file)


if __name__ == "__main__":
    unittest.main()
