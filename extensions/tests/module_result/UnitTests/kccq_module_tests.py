import unittest
from unittest.mock import MagicMock

from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.modules import KCCQQuestionnaireModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_kccq_data,
    sample_kccq_data_missing_answers,
    sample_kccq_all_zero_weight_anwsers,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField

CLIENT_ID = "c1"
PROJECT_ID = "p1"


def sample_kccq_config_body() -> dict:
    return {
        "isForManager": False,
        "publisherName": "PM",
        "questionnaireName": "KCCQ",
        "name": "KCCQ",
        "questionnaireId": "611dffd20d4e78155ae591ef",
        "pages": [
            {
                "type": "INFO",
                "id": "kccq_info_screen_1",
                "order": 1,
                "text": "<b>hu_kccq_info_text</b>",
                "description": "hu_kccq_info_description",
            },
            {
                "type": "INFO",
                "id": "kccq_physical_limitation_info",
                "order": 2,
                "text": "",
                "description": "hu_kccq_phylimit_info_description",
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1a",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_physlimit_q1atext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 3,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1b",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_phylimit_q1btext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 4,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1c",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_phylimit_q1ctext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 5,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1d",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_phylimit_q1dtext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 6,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1e",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_phylimit_q1etext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 7,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_physical_limitation_q1f",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_phylimit_q1ftext",
                        "options": [
                            {
                                "label": "hu_kccq_phylimit_q1option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_phylimit_q1option6",
                                "value": "0",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 8,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_stability_q2",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symstab_q2text",
                        "options": [
                            {
                                "label": "hu_kccq_symstab_q2option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_symstab_q2option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_symstab_q2option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_symstab_q2option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_symstab_q2option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_symstab_q2option6",
                                "value": "6",
                                "weight": 3,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 9,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_frequency_q3",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symfreq_q3text",
                        "options": [
                            {
                                "label": "hu_kccq_symfreq_q3option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_symfreq_q3option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_onetwo_times",
                                "value": "3",
                                "weight": 3,
                            },
                            {"label": "hu_kccq_less_week", "value": "4", "weight": 4},
                            {
                                "label": "hu_kccq_neverpast_2weeks",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 10,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_burden_q4",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symbur_q4text",
                        "options": [
                            {
                                "label": "hu_kccq_extremely_bothersome",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_quite_bothersome",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_moderate_bothersome",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_slight_bothersome",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_not_bothersome",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_symbur_q4option6",
                                "value": "6",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 11,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_frequency_q5",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symfreq_q5text",
                        "options": [
                            {"label": "hu_kccq_all_time", "value": "1", "weight": 1},
                            {
                                "label": "hu_kccq_several_time",
                                "value": "2",
                                "weight": 2,
                            },
                            {"label": "hu_kccq_once_day", "value": "3", "weight": 3},
                            {
                                "label": "hu_kccq_3ormore_week",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_onetwo_perweek",
                                "value": "5",
                                "weight": 5,
                            },
                            {"label": "hu_kccq_less_week", "value": "6", "weight": 6},
                            {
                                "label": "hu_kccq_neverpast_2weeks",
                                "value": "7",
                                "weight": 7,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 12,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_burden_q6",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symbur_q6text",
                        "options": [
                            {
                                "label": "hu_kccq_extremely_bothersome",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_quite_bothersome",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_moderate_bothersome",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_slight_bothersome",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_not_bothersome",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_symbur_q6option6",
                                "value": "6",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 13,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_frequency_q7",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 14,
                        "text": "hu_kccq_symfreq_q7text",
                        "options": [
                            {"label": "hu_kccq_all_time", "value": "1", "weight": 1},
                            {
                                "label": "hu_kccq_several_time",
                                "value": "2",
                                "weight": 2,
                            },
                            {"label": "hu_kccq_once_day", "value": "3", "weight": 3},
                            {
                                "label": "hu_kccq_3ormore_week",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_onetwo_perweek",
                                "value": "5",
                                "weight": 5,
                            },
                            {"label": "hu_kccq_less_week", "value": "6", "weight": 6},
                            {
                                "label": "hu_kccq_neverpast_2weeks",
                                "value": "7",
                                "weight": 7,
                            },
                        ],
                    }
                ],
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_burden_q8",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symbur_q8text",
                        "options": [
                            {
                                "label": "hu_kccq_extremely_bothersome",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_quite_bothersome",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_moderate_bothersome",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_slight_bothersome",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_not_bothersome",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_symbur_q8option6",
                                "value": "6",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 15,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_symptom_frequency_q9",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_symfreq_q9_text",
                        "options": [
                            {
                                "label": "hu_kccq_symfreq_q9option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_symfreq_q9option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_onetwo_times",
                                "value": "3",
                                "weight": 3,
                            },
                            {"label": "hu_kccq_less_week", "value": "4", "weight": 4},
                            {
                                "label": "hu_kccq_neverpast_2weeks",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 16,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_self_efficacy_q10",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_selfeff_q10text",
                        "options": [
                            {
                                "label": "hu_kccq_selfeff_q10option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_selfeff_q10option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_selfeff_q10option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_selfeff_q10option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_selfeff_q10option5",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 17,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_self_efficacy_q11",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_selfeff_q11text",
                        "options": [
                            {
                                "label": "hu_kccq_selfeff_q11option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_selfeff_q11option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_selfeff_q11option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_selfeff_q11option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_selfeff_q11option5",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 18,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_quality_of_life_q12",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_qol_q12text",
                        "options": [
                            {
                                "label": "hu_kccq_qol_q12option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_qol_q12option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_qol_q12option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_qol_q12option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_qol_q12option5",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 19,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_quality_of_life_q13",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_qol_q13text",
                        "options": [
                            {
                                "label": "hu_kccq_qol_q13option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_qol_q13option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_qol_q13option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_qol_q13option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_qol_q13option5",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 20,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_quality_of_life_q14",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_qol_q14_text",
                        "options": [
                            {
                                "label": "hu_kccq_qol_q14option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_qol_q14option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_qol_q14option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_qol_q14option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_qol_q14option5",
                                "value": "5",
                                "weight": 5,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 21,
            },
            {
                "type": "INFO",
                "id": "kccq_social_limitation_info",
                "order": 22,
                "text": "",
                "description": "hu_kccq_soclimit_infodescription",
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_social_limitation_q15a",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_soclimit_q15atext",
                        "skipByWeight": 0,
                        "options": [
                            {
                                "label": "hu_kccq_soclimit_option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_soclimit_option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_soclimit_option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_soclimit_option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_soclimit_option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_soclimit_option6",
                                "value": "6",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 23,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_social_limitation_q15b",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_soclimit_q15btext",
                        "skipByWeight": 0,
                        "options": [
                            {
                                "label": "hu_kccq_soclimit_option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_soclimit_option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_soclimit_option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_soclimit_option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_soclimit_option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_soclimit_option6",
                                "value": "6",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 24,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_social_limitation_q15c",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_soclimit_q15ctext",
                        "skipByWeight": 0,
                        "options": [
                            {
                                "label": "hu_kccq_soclimit_option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_soclimit_option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_soclimit_option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_soclimit_option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_soclimit_option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_soclimit_option6",
                                "value": "6",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 25,
            },
            {
                "type": "QUESTION",
                "items": [
                    {
                        "logic": {"isEnabled": False},
                        "description": "",
                        "id": "kccq_social_limitation_q15d",
                        "required": False,
                        "format": "TEXTCHOICE",
                        "order": 1,
                        "text": "hu_kccq_soclimit_q15dtext",
                        "skipByWeight": 0,
                        "options": [
                            {
                                "label": "hu_kccq_soclimit_option1",
                                "value": "1",
                                "weight": 1,
                            },
                            {
                                "label": "hu_kccq_soclimit_option2",
                                "value": "2",
                                "weight": 2,
                            },
                            {
                                "label": "hu_kccq_soclimit_option3",
                                "value": "3",
                                "weight": 3,
                            },
                            {
                                "label": "hu_kccq_soclimit_option4",
                                "value": "4",
                                "weight": 4,
                            },
                            {
                                "label": "hu_kccq_soclimit_option5",
                                "value": "5",
                                "weight": 5,
                            },
                            {
                                "label": "hu_kccq_soclimit_option6",
                                "value": "6",
                                "weight": 0,
                            },
                        ],
                        "selectionCriteria": "SINGLE",
                    }
                ],
                "order": 26,
            },
        ],
        "submissionPage": {
            "description": "Scroll up to change any of your answers. Changing answers may add new questions.",
            "id": "kccq_submission_page",
            "text": "You’ve completed the questionnaire",
            "buttonText": "Submit",
            "order": 27,
            "type": "SUBMISSION",
        },
    }


class KCCQModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        server_config = MagicMock()
        server_config.server = Server(hostUrl="localhost")
        version = Version(server=VersionField("1.17.1"), api="api", build="build")
        self.module_config = ModuleConfig(
            moduleId=KCCQQuestionnaireModule.__name__,
            configBody=sample_kccq_config_body(),
        )

        def configure_with_binder(binder: Binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind(Version, version)
            binder.bind(ModulesManager, ModulesManager())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_calculate_kccq_score(self):
        module = KCCQQuestionnaireModule()
        module.calculator._get_answer_weight = MagicMock(return_value=3)
        primitives = [
            Questionnaire.from_dict(
                {**sample_kccq_data(), "userId": "6131bdaaf9af87a4f08f4d02"}
            )
        ]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        kccq_primitive = primitives[1]
        self.assertEqual(kccq_primitive.physicalLimitation, 50.0)
        self.assertEqual(kccq_primitive.symptomStability, 50.0)
        self.assertEqual(kccq_primitive.symptomBurden, 50.0)
        self.assertEqual(kccq_primitive.totalSymptomScore, 45.83333333333333)
        self.assertEqual(kccq_primitive.selfEfficacy, 50.0)
        self.assertEqual(kccq_primitive.qualityOfLife, 50.0)
        self.assertEqual(kccq_primitive.clinicalSummaryScore, 47.916666666666664)

    def test_failure_not_enough_answers_kccq_questionnaire(self):
        module = KCCQQuestionnaireModule()
        module.config = self.module_config
        primitives = [
            Questionnaire.from_dict(
                {
                    **sample_kccq_data_missing_answers(),
                    "userId": "6131bdaaf9af87a4f08f4d02",
                }
            )
        ]
        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, MagicMock())

    def test_failure_answers_have_zero_weight(self):
        module = KCCQQuestionnaireModule()
        module.config = self.module_config
        primitives = [
            Questionnaire.from_dict(
                {
                    **sample_kccq_all_zero_weight_anwsers(),
                    "userId": "6131bdaaf9af87a4f08f4d02",
                }
            )
        ]
        with self.assertRaises(NotAllRequiredQuestionsAnsweredException):
            module.preprocess(primitives, MagicMock())

    def test_success_bug_irrational_number_division(self):
        module = KCCQQuestionnaireModule()
        module.calculator._get_answer_weight = MagicMock(return_value=1)
        primitives = [
            Questionnaire.from_dict(
                {**sample_kccq_data(), "userId": "6131bdaaf9af87a4f08f4d02"}
            )
        ]
        module.config = self.module_config
        module.preprocess(primitives, MagicMock())
        self.assertEqual(len(primitives), 2)
        module.calculate(primitives[1])
        kccq_primitive = primitives[1]
        self.assertEqual(kccq_primitive.physicalLimitation, 0)
        self.assertEqual(kccq_primitive.physicalLimitation, 0)
        self.assertEqual(kccq_primitive.symptomStability, 0)
        self.assertEqual(kccq_primitive.symptomBurden, 0)
        self.assertEqual(kccq_primitive.totalSymptomScore, 0)
        self.assertEqual(kccq_primitive.selfEfficacy, 0)
        self.assertEqual(kccq_primitive.qualityOfLife, 0)
        self.assertEqual(kccq_primitive.clinicalSummaryScore, 0)
