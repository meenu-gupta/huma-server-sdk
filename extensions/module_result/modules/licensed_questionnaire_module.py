import os
from os import listdir
from pathlib import Path
from typing import Optional

from tomlkit._utils import merge_dicts

from extensions.deployment.models.status import EnableStatus
from extensions.module_result.exceptions import InvalidModuleConfiguration
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.questionnaire import QuestionnaireModule

from sdk.common.localization.utils import Language
from sdk.common.utils.validators import read_json_file

BASE_LICENSED_QUESTIONNAIRE_DIR = "./licensed_configs"


class LicensedQuestionnaireModule(QuestionnaireModule):
    """Licensed Questionnaire Module adds to Module subclasses
    to behave as a licensed hardcoded module.

    Config body is loaded from the local licensed questionnaire folder under
    'module_result/modules'. Each licensed questionnaire module should have its folder
    named after its moduleId. It contains version folders. In each version
    folder, there are 'config_body.json' and 'localization' folders. Each
    localization file should be named in '<language-abbreviation>.json'
    format.
    i.e.:
        licensed_configs/
            sample/
                config_body.json
                localization/
                    en.json
                    fr.json
    """

    validation_schema_path = "schemas/licensed_questionnaire_schema.json"
    config_version = "1"
    moduleId = "LicensedQuestionnaire"  # needed to be properly excluded from export

    def extract_module_config(
        self,
        module_configs: list[ModuleConfig],
        primitive: Optional[Primitive],
        module_config_id: str = None,
    ):
        module_config = super().extract_module_config(
            module_configs, primitive, module_config_id
        )
        module_config_from_file = self._get_config_json()
        module_config = module_config.to_dict(include_none=False)
        merge_dicts(module_config, module_config_from_file)

        return ModuleConfig.from_dict(module_config, use_validator_field=False)

    def _get_config_json(self):
        config_path = f"{BASE_LICENSED_QUESTIONNAIRE_DIR}/{self.moduleId}/v{self.config_version}/config_body.json"
        try:
            return read_json_file(config_path, Path(__file__).parent)
        except FileNotFoundError:
            raise InvalidModuleConfiguration(
                f"Config Body file not found for {self.moduleId}"
            )

    def get_localization(self, user_language: str) -> dict:
        try:
            return _get_localization(user_language, self.moduleId, self.config_version)
        except FileNotFoundError:
            raise InvalidModuleConfiguration(
                f"Localization file not found for {self.moduleId}"
            )

    def validate_config_body(self, module_config: ModuleConfig):
        super(QuestionnaireModule, self).validate_config_body(module_config)


def _get_localization(user_language: str, module_id: str, config_version: str) -> dict:
    translation_dir_path = (
        f"{BASE_LICENSED_QUESTIONNAIRE_DIR}/{module_id}/v{config_version}/localization"
    )
    file_path = f"{translation_dir_path}/{user_language}.json"
    if not os.path.exists(f"{Path(__file__).parent}/{file_path}"):
        file_path = f"{translation_dir_path}/{Language.EN}.json"

    return read_json_file(file_path, Path(__file__).parent)


# TODO: Need to implement config version in moduleConfig
LICENSED_QUESTIONNAIRE_CONFIG_VERSION = "1"


def get_localizations(user_language: str, module_configs: list[ModuleConfig]):
    """Loads all localizations regarding user_language from licensed questionnaire modules folders."""
    licensed_questionnaire_dir_list = listdir(
        Path(Path(__file__).parent).joinpath(BASE_LICENSED_QUESTIONNAIRE_DIR)
    )
    localizations = {}
    if not module_configs:
        return localizations
    if not isinstance(module_configs, list):
        module_configs = [module_configs]
    for module_config in module_configs:
        if (
            module_config.status == EnableStatus.ENABLED
            and module_config.moduleId in licensed_questionnaire_dir_list
        ):
            try:
                localizations.update(
                    _get_localization(
                        user_language,
                        module_config.moduleId,
                        LICENSED_QUESTIONNAIRE_CONFIG_VERSION,
                    )
                )
            except FileNotFoundError:
                raise InvalidModuleConfiguration(
                    f"Config Body file not found for {module_config.moduleId}"
                )

    return localizations


def get_licensed_questionnaire_dir():
    return Path(Path(__file__).parent).joinpath(BASE_LICENSED_QUESTIONNAIRE_DIR)


def get_licensed_questionnaires_dir_list():
    return listdir(get_licensed_questionnaire_dir())


def get_licensed_questionnaires_config_path(module_id: str):
    return f"/{module_id}/v{LICENSED_QUESTIONNAIRE_CONFIG_VERSION}/config_body.json"
