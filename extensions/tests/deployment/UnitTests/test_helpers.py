from extensions.common.legal_documents import LegalDocument
from extensions.common.s3object import S3Object
from extensions.deployment.router.deployment_requests import (
    UpdateLocalizationsRequestObject,
)

LICENSED_SAMPLE_KEY = "test_LicenceModule_sample_key"


def get_sample_care_plan_group() -> dict:
    return {
        "groups": [
            {
                "id": "com.huma.mild",
                "name": "Mild Cases",
                "moduleConfigPatches": [
                    {
                        "moduleConfigId": "60103095db18b64247a1f44c",
                        "changeType": "PATCH",
                        "patch": [
                            {
                                "op": "replace",
                                "path": "/schedule/isoDuration",
                                "value": "P4D",
                            }
                        ],
                    }
                ],
                "default": True,
                "extensionForActivationCode": "01",
            },
            {
                "id": "com.huma.severe",
                "name": "Severe Cases",
                "moduleConfigPatches": [
                    {
                        "moduleConfigId": "60103095db18b64247a1f44c",
                        "changeType": "PATCH",
                        "patch": [
                            {
                                "op": "replace",
                                "path": "/schedule/isoDuration",
                                "value": "P4D",
                            }
                        ],
                    },
                    {
                        "moduleConfigId": "601030a0db18b64247a1f44e",
                        "changeType": "PATCH",
                        "patch": [
                            {
                                "op": "replace",
                                "path": "/schedule/timesPerDuration",
                                "value": 4,
                            }
                        ],
                    },
                ],
                "default": False,
                "extensionForActivationCode": "02",
            },
        ]
    }


def get_sample_update_care_plan_group_request_obj() -> dict:
    return {
        "userId": "60181c991975100024a700ce",
        "submitterId": "6018035b1975100024a700c7",
        "submitterName": "Test Manager",
        "note": "Moving",
        "carePlanGroupId": "com.huma.mild",
        "deploymentId": "6017fd50e96c556c3d2d1b49",
    }


def get_sample_module_config() -> dict:
    return {
        "about": "string",
        "configBody": {},
        "moduleId": "Journal",
        "moduleName": "string",
        "schedule": {
            "friendlyText": "string",
            "isoDuration": "P1D",
            "timesOfDay": ["UPON_WAKING", "BEFORE_BREAKFAST"],
            "timesPerDuration": 0,
        },
        "status": "ENABLED",
        "order": 1,
        "version": 1,
    }


def get_sample_module_config_patch() -> dict:
    return {
        "moduleConfigId": "60103095db18b64247a1f44c",
        "changeType": "PATCH",
        "patch": [{"op": "replace", "path": "/schedule/isoDuration", "value": "P4D"}],
    }


def get_sample_module_config_with_rag_threshold() -> dict:
    return {
        "moduleId": "Weight",
        "moduleName": "Weight",
        "ragThresholds": [
            {
                "color": "green",
                "severity": 1,
                "fieldName": "value",
                "type": "VALUE",
                "thresholdRange": [{"minValue": 110, "maxValue": 119}],
                "enabled": True,
            },
            {
                "color": "amber",
                "severity": 2,
                "fieldName": "value",
                "type": "VALUE",
                "thresholdRange": [{"minValue": 120, "maxValue": 130}],
                "enabled": True,
            },
        ],
    }


def get_sample_module_config_patch_with_rag_threshold() -> dict:
    return {
        "moduleConfigId": "60103095db18b64247a1f44c",
        "changeType": "PATCH",
        "patch": [{"op": "replace", "path": "/ragThresholds/0/severity", "value": "1"}],
    }


def get_sample_localizations() -> dict:
    return {
        UpdateLocalizationsRequestObject.DEPLOYMENT_ID: "6017fd50e96c556c3d2d1b49",
        UpdateLocalizationsRequestObject.LOCALIZATIONS: {
            "en": {"hu_deployment_name": "deployment 1"},
            "de": {"hu_deployment_name": "Bereitstellung 1"},
        },
    }


def get_sample_questionnaire_module_config() -> dict:
    return {
        "moduleId": "Questionnaire",
        "moduleName": "",
        "status": "ENABLED",
        "order": 8,
        "configBody": {
            "isForManager": False,
            "pages": [
                {
                    "type": "QUESTION",
                    "items": [
                        {
                            "format": "AUTOCOMPLETE_TEXT",
                            "autocomplete": {
                                "placeholder": "Search conditions",
                                "listEndpointId": "AZVaccineBatchNumber",
                                "allowFreeText": True,
                            },
                            "order": 1,
                            "required": True,
                            "placeholder": "Enter Condition",
                            "text": "What condition do you have?",
                        }
                    ],
                    "order": 1,
                },
                {
                    "type": "QUESTION",
                    "items": [
                        {
                            "logic": {"isEnabled": False},
                            "description": "In the last 7 days how has your activity changed compared to the week before?",
                            "required": True,
                            "format": "TEXTCHOICE",
                            "order": 1,
                            "text": "Overall physical activity",
                            "options": [
                                {"label": "Decreased", "value": "0", "weight": 0}
                            ],
                        }
                    ],
                    "order": 2,
                },
            ],
        },
    }


def sample_s3_object() -> dict:
    return {
        S3Object.BUCKET: "bucket_name",
        S3Object.KEY: "key_name",
        S3Object.REGION: "us",
    }


def legal_docs_s3_fields():
    return [
        LegalDocument.PRIVACY_POLICY_OBJECT,
        LegalDocument.TERM_AND_CONDITION_OBJECT,
        LegalDocument.EULA_OBJECT,
    ]


def legal_docs_url_fields():
    return [
        LegalDocument.PRIVACY_POLICY_URL,
        LegalDocument.TERM_AND_CONDITION_URL,
        LegalDocument.EULA_URL,
    ]
