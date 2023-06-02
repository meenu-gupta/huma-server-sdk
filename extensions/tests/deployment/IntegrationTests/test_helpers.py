from extensions.deployment.models.deployment import (
    AdditionalContactDetailsItem,
    Deployment,
    EthnicityOption,
    Profile,
    ProfileFields,
)
from extensions.tests.shared.test_helpers import simple_deployment

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"


def modified_deployment() -> dict:
    return {
        Deployment.ID: DEPLOYMENT_ID,
        Deployment.NAME: "Updated Deployment",
        Deployment.STATUS: "DRAFT",
        Deployment.COLOR: "0x007AFF",
        Deployment.ICON: {"bucket": "test", "key": "test", "region": "eu"},
    }


def modified_deployment_with_gender_options() -> dict:
    deployment = modified_deployment()
    deployment["profile"] = {
        "fields": {
            "genderOptions": [
                {"displayName": "Male", "value": "MALE"},
                {"displayName": "Female", "value": "FEMALE"},
                {"displayName": "Other", "value": "OTHER"},
                {
                    "displayName": "Non-binary/genderqueer/agender/gender fluid",
                    "value": "NON_BINARY",
                },
                {"displayName": "Transgender", "value": "TRANSGENDER"},
                {"displayName": "Prefer not to say", "value": "NOT_SPECIFIED"},
            ]
        }
    }
    return deployment


def modified_deployment_with_ethnicity_options() -> dict:
    deployment = modified_deployment()
    deployment[Deployment.PROFILE] = {
        Profile.FIELDS: {
            ProfileFields.ETHNICITY_OPTIONS: [
                {
                    EthnicityOption.DISPLAY_NAME: "White",
                    EthnicityOption.VALUE: "WHITE",
                },
                {
                    EthnicityOption.DISPLAY_NAME: "Mixed",
                    EthnicityOption.VALUE: "MIXED_OR_MULTI_ETHNIC_GROUPS",
                },
                {
                    EthnicityOption.DISPLAY_NAME: "Other Ethnic Groups",
                    EthnicityOption.VALUE: "OTHER_ETHNIC_GROUPS",
                },
            ]
        }
    }
    return deployment


def modified_deployment_with_additional_contact_details(contact_fields: dict) -> dict:
    deployment = simple_deployment()
    deployment[Deployment.PROFILE] = {
        Profile.FIELDS: {
            ProfileFields.ADDITIONAL_CONTACT_DETAILS: {
                AdditionalContactDetailsItem.ALT_CONTACT_NUMBER: True,
                AdditionalContactDetailsItem.REGULAR_CONTACT_NAME: True,
                AdditionalContactDetailsItem.REGULAR_CONTACT_NUMBER: True,
                AdditionalContactDetailsItem.EMERGENCY_CONTACT_NAME: True,
                AdditionalContactDetailsItem.EMERGENCY_CONTACT_NUMBER: True,
                **contact_fields,
                AdditionalContactDetailsItem.MANDATORY_FIELDS: [
                    AdditionalContactDetailsItem.ALT_CONTACT_NUMBER,
                    AdditionalContactDetailsItem.REGULAR_CONTACT_NAME,
                    AdditionalContactDetailsItem.REGULAR_CONTACT_NUMBER,
                    AdditionalContactDetailsItem.EMERGENCY_CONTACT_NAME,
                    AdditionalContactDetailsItem.EMERGENCY_CONTACT_NUMBER,
                ],
            }
        },
    }
    return deployment


def simple_module_config() -> dict:
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
        "footnote": {"enabled": True, "text": "Footnote Text"},
    }


def simple_module_config_requiring_default_disclaimer_config() -> dict:
    return {
        "about": "string",
        "configBody": {},
        "moduleId": "Symptom",
        "moduleName": "Symptom",
        "schedule": {
            "friendlyText": "string",
            "isoDuration": "P1D",
            "timesOfDay": ["UPON_WAKING", "BEFORE_BREAKFAST"],
            "timesPerDuration": 0,
        },
        "status": "ENABLED",
    }


def simple_module_config_not_requiring_default_disclaimer_config() -> dict:
    return {
        "about": "string",
        "configBody": {},
        "moduleId": "Step",
        "moduleName": "Step",
        "schedule": {
            "friendlyText": "string",
            "isoDuration": "P1D",
            "timesOfDay": ["UPON_WAKING", "BEFORE_BREAKFAST"],
            "timesPerDuration": 0,
        },
        "status": "ENABLED",
    }


def module_config_with_config_body(option: dict = None) -> dict:
    return {
        **simple_module_config(),
        "moduleId": "Breathlessness",
        "configBody": {
            "calculatedQuestionnaire": False,
            "horizontalFlow": True,
            "isForManager": True,
            "isOnboarding": False,
            "name": "string",
            "pages": [
                {
                    "items": [
                        {
                            "description": "",
                            "format": "TEXTCHOICE",
                            "id": "89b31c9b-211b-4adb-9122-d73edbb7331a",
                            "options": [
                                option or {"label": "None", "value": "1", "weight": 1},
                                {"label": "Mild", "value": "2", "weight": 2},
                            ],
                            "order": 1,
                            "required": True,
                            "selectionCriteria": "SINGLE",
                            "text": "How breathless are you when you are walking around or walking up stairs?",
                        }
                    ],
                    "order": 1,
                    "type": "QUESTION",
                }
            ],
            "publisherName": "string",
            "region": "UK",
        },
    }


def get_sample_questionnaire_with_trademark_text() -> dict:
    return {
        "moduleId": "Questionnaire",
        "moduleName": "Questionnaire",
        "status": "ENABLED",
        "order": 1,
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
            ],
            "trademarkText": "© trademark text",
        },
    }


def get_sample_promis_pain_questionnaire() -> dict:
    return {
        "moduleId": "Questionnaire",
        "moduleName": "",
        "status": "ENABLED",
        "order": 1,
        "configBody": {
            "id": "14327a25-52af-4ec6-8bc9-6732baebba0e",
            "isForManager": False,
            "name": "PROMIS CAT Pain Interference",
            "pages": [],
            "publisherName": "RT",
            "questionnaireType": "PROMIS_PAIN",
            "scoreAvailable": True,
            "submissionPage": {
                "buttonText": "Submit",
                "description": "Scroll up to change any of your answers.Changing answers may add new questions.",
                "id": "6bc2c592-6a8f-401b-9a7d-cf6a835b37eb",
                "order": 1,
                "text": "You’ ve completed the questionnaire",
                "type": "SUBMISSION",
            },
        },
    }


def get_sample_pam_questionnaire() -> dict:
    return {
        "moduleId": "Questionnaire",
        "about": "string",
        "configBody": {
            "id": "d7c92a9e-ca3b-4f73-824e-3b1ac3b5141d",
            "isForManager": False,
            "isPAM": True,
            "name": "PAM 13",
            "pages": [],
        },
        "moduleName": "Questionnaire",
        "schedule": {
            "isoDuration": "P1W",
            "timesPerDuration": 1,
            "timesOfDay": ["BEFORE_DINNER"],
        },
        "status": "ENABLED",
    }


def get_module_config_by_id(deployment: dict, module_config_id: str):
    return next(
        filter(lambda x: x["id"] == module_config_id, deployment["moduleConfigs"])
    )
