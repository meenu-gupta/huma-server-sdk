from unittest import TestCase
from unittest.mock import MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.status import EnableStatus
from extensions.module_result.models.module_config import ModuleConfig
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder


class DeploymentTestCase(TestCase):
    def setUp(self) -> None:
        def configure_with_binder(binder: Binder):
            binder.bind(FileStorageAdapter, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    def test_convert_to_multi_language_az_pregnancy(self):
        # here we do not have anything to translate => translation dict is empty
        module = ModuleConfig(
            id="module4",
            moduleId="AZFurtherPregnancyKeyActionTrigger",
            localizationPrefix="AZFurtherPregnancyKeyActionTrigger",
            status=EnableStatus.ENABLED,
            configBody={
                "keyActions": {
                    "NOT_PREGNANT": [],
                    "PREGNANT": ["PregnancyFollowUp", "InfantFollowUp"],
                },
                "keyActionsToRemove": {
                    "BREAST_FEEDING": {
                        "NOT_PREGNANT": [],
                        "PREGNANT": [
                            "PregnancyUpdate",
                            "BreastFeedingUpdate",
                            "AZFurtherPregnancyKeyActionTrigger",
                        ],
                    },
                    "FEMALE_LESS_50_NOT_P_OR_B": {
                        "NOT_PREGNANT": [],
                        "PREGNANT": [
                            "PregnancyUpdate",
                            "AZFurtherPregnancyKeyActionTrigger",
                        ],
                    },
                },
            },
            moduleName="Some Questionnaire with translation",
        )
        deployment = Deployment(
            id="deploymentId",
            moduleConfigs=[module],
        )
        res = deployment.generate_deployment_multi_language_state()
        expected_en_localization = {}
        self.assertEqual(expected_en_localization, res.localizations[Language.EN])
