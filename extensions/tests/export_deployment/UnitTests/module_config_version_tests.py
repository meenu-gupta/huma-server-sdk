import unittest
from collections import defaultdict
from unittest.mock import MagicMock

from extensions.deployment.models.deployment import (
    ModuleConfig,
    DeploymentRevision,
    Deployment,
)
from extensions.export_deployment.helpers.convertion_helpers import (
    build_module_config_versions,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.questionnaire_exportable_use_case import (
    QuestionnaireModuleExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive, Questionnaire

DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789f"

EXTRA_MODULE_CONFIG_ID = "5e8f0c74b50aa9656c34789d"
MODULE_CONFIG_ID = "5e8f0c74b50aa9656c34789e"

TEST_MODULE_ID = "Test"
ANOTHER_MODULE_ID = "TestAnother"
QUESTIONNAIRE_ID = "TestQuestionnaire"


def get_module_config(version=None, config_id=MODULE_CONFIG_ID):
    return ModuleConfig(id=config_id, moduleId=TEST_MODULE_ID, version=version)


def get_questionnaire_config(
    questionnaire_id, version=None, config_id=MODULE_CONFIG_ID
):
    config_body = {ModuleConfig.CONFIG_BODY_ID: questionnaire_id}
    return ModuleConfig(
        id=config_id, moduleId=TEST_MODULE_ID, version=version, configBody=config_body
    )


def get_deployment_revision(revision_configs: list[ModuleConfig]):
    snap = Deployment(id=DEPLOYMENT_ID, moduleConfigs=revision_configs)
    revision = DeploymentRevision(snap=snap)
    return revision


def get_request_object() -> ExportableRequestObject:
    module_config_versions = defaultdict(lambda: defaultdict(dict))
    return ExportableRequestObject(moduleConfigVersions=module_config_versions)


class ModuleConfigVersionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.deployment_repo = MagicMock()
        self.use_case = ExportableUseCase(
            MagicMock(), self.deployment_repo, MagicMock()
        )
        self.use_case.request_object = get_request_object()

    def _get_config(
        self, module_configs: list, primitive: Primitive, revision_configs: list = None
    ):
        build_module_config_versions(
            self.use_case.request_object.moduleConfigVersions, module_configs
        )
        revision = DeploymentRevision(snap=Deployment(moduleConfigs=revision_configs))
        self.deployment_repo.retrieve_deployment_revision_by_module_config_version.return_value = (
            revision
        )
        return self.use_case.get_module_config(
            primitive, self.use_case.request_object.moduleConfigVersions
        )


class ExportableModuleConfigVersionTestCase(ModuleConfigVersionTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.no_version_config = get_module_config()
        cls.another_config = get_module_config(config_id=EXTRA_MODULE_CONFIG_ID)
        cls.version_1_config = get_module_config(version=1)

    def test_get_module_config_retrieves_none_when_no_module_found(self):
        module_configs = [self.another_config, self.no_version_config]
        primitive = Primitive(moduleId=TEST_MODULE_ID)
        config = self._get_config(module_configs, primitive)
        self.assertIsNone(config)

    def test_get_module_config_retrieves_proper_version__no_version(self):
        module_configs = [self.another_config, self.no_version_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id
        )
        config = self._get_config(module_configs, primitive)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_proper_version__no_version_from_revision(self):
        module_configs = [self.another_config, self.version_1_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_proper_version__version_1_from_actual(self):
        module_configs = [self.another_config, self.version_1_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=1
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.version_1_config, config)

    def test_get_module_config_retrieves_proper_version__config_removed_from_deployment(
        self,
    ):
        module_configs = [self.another_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=0
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_revision_only_once(self):
        module_configs = [self.another_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=0
        )
        revision_configs = [self.another_config, self.no_version_config]
        self._get_config(module_configs, primitive, revision_configs)
        self._get_config(module_configs, primitive, revision_configs)
        self.deployment_repo.retrieve_deployment_revision_by_module_config_version.assert_called_once()


class QuestionnaireModuleConfigVersionTestCase(ModuleConfigVersionTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.no_version_config = get_questionnaire_config(QUESTIONNAIRE_ID)
        cls.another_config = get_questionnaire_config(
            QUESTIONNAIRE_ID, config_id=EXTRA_MODULE_CONFIG_ID
        )
        cls.version_1_config = get_questionnaire_config(QUESTIONNAIRE_ID, version=1)

    def setUp(self) -> None:
        self.deployment_repo = MagicMock()
        self.use_case = QuestionnaireModuleExportableUseCase(
            MagicMock(), self.deployment_repo, MagicMock()
        )
        self.use_case.request_object = get_request_object()

    def test_get_module_config_retrieves_proper_version__no_version(self):
        module_configs = [self.another_config, self.no_version_config]
        primitive = Questionnaire(
            moduleId=TEST_MODULE_ID,
            moduleConfigId=self.no_version_config.id,
            questionnaireId=QUESTIONNAIRE_ID,
        )
        config = self._get_config(module_configs, primitive)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_proper_version__no_version_from_revision(self):
        module_configs = [self.another_config, self.version_1_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_proper_version__version_1_from_actual(self):
        module_configs = [self.another_config, self.version_1_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=1
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.version_1_config, config)

    def test_get_module_config_retrieves_proper_version__config_removed_from_deployment(
        self,
    ):
        module_configs = [self.another_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=0
        )
        revision_configs = [self.another_config, self.no_version_config]
        config = self._get_config(module_configs, primitive, revision_configs)
        self.assertEqual(self.no_version_config, config)

    def test_get_module_config_retrieves_revision_only_once(self):
        module_configs = [self.another_config]
        primitive = Primitive(
            moduleId=TEST_MODULE_ID, moduleConfigId=self.no_version_config.id, version=0
        )
        revision_configs = [self.another_config, self.no_version_config]
        self._get_config(module_configs, primitive, revision_configs)
        self._get_config(module_configs, primitive, revision_configs)
        self.deployment_repo.retrieve_deployment_revision_by_module_config_version.assert_called_once()
