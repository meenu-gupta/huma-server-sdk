from extensions.authorization.router.user_profile_request import (
    AssignManagerRequestObject,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.status import EnableStatus
from extensions.module_result.models.module_config import ModuleConfig

from unittest.mock import MagicMock

SAMPLE_USER_ID = SAMPLE_CONFIG_ID = "5fe07f2c0d862378d70fa19b"


def get_sample_preferred_units() -> dict:
    return {
        "preferredUnits": {"BloodGlucose": "mg/dL", "Weight": "kg", "Temperature": "oC"}
    }


def get_user_notes_sample_request() -> dict:
    return {
        "userId": "5e8f0c74b50aa9656c34789b",
        "deploymentId": "5d386cc6ff885918d96edb2c",
        "skip": 0,
        "limit": 5,
    }


def get_sample_deployment_with_module_configs() -> Deployment:
    return Deployment(
        id="5d386cc6ff885918d96edb2c",
        name="deployment",
        moduleConfigs=[
            ModuleConfig(
                id="module_test1",
                configBody={
                    "questionnaireType": "OBSERVATION_NOTES",
                },
                status=EnableStatus.ENABLED,
            ),
            ModuleConfig(
                id="module_test2",
                configBody={
                    "isForManager": True,
                },
                status=EnableStatus.ENABLED,
            ),
            ModuleConfig(id="module_test3", status=EnableStatus.ENABLED),
        ],
    )


def get_sample_consent() -> dict:
    return {
        "id": "6033d04f29d73d81fca58ba1",
        "enabled": "ENABLED",
        "instituteFullName": "string",
        "instituteName": "string",
        "instituteTextDetails": "string",
        "signature": {
            "signatureTitle": "Signature",
            "signatureDetails": "Please sign using your finger in the box below",
            "nameTitle": "Medopad Consent",
            "nameDetails": "Type your full name in text fields below",
            "hasMiddleName": True,
        },
        "review": {
            "title": "Review",
            "details": "Please review the form below, and tap Agree if you are ready to continue. If you have any "
            "questions or queries, please contact us at support@medopad.com",
        },
        "sections": [
            {
                "type": "AGREEMENT",
                "title": "Agreement",
                "reviewDetails": "In order for you to register and use the Huma app, your consent is required.",
                "options": [
                    {
                        "type": 0,
                        "order": 0,
                        "text": 'I consent to Huma processing my personal information, including my health information, as described in the <a href="https://storage.googleapis.com/hu-deployment-static-content/afib/Huma_US_Privacy_Policy_incl_CCPA.pdf">Privacy Policy</a>',
                    },
                    {
                        "type": 1,
                        "order": 1,
                        "text": 'I agree to the terms of the <a href="https://storage.googleapis.com/hu-deployment-static-content/afib/Huma_EULA_Bayer_AFib.pdf">Huma End User Licence Agreement</a>',
                    },
                ],
            }
        ],
    }


def get_sample_sign_consent_request() -> dict:
    return {
        "givenName": "Test client",
        "middleName": "test",
        "familyName": "Test client",
        "sharingOption": 1,
        "agreement": True,
        "deploymentId": "5d386cc6ff885918d96edb2c",
        "userId": "60181c991975100024a700ce",
        "consentId": "6033d04f29d73d81fca58ba1",
    }


def get_sample_assign_manager_request() -> dict:
    return {
        AssignManagerRequestObject.USER_ID: "5fe07f2c0d862378d70fa19b",
        AssignManagerRequestObject.MANAGER_IDS: [
            "5fe0a9b2e9023cb3d8c3ee8b",
            "5fe0a9b9f55dff5e2406b72b",
        ],
        AssignManagerRequestObject.SUBMITTER_ID: "5fe0a9c0d4696db1c7cd759a",
    }


class MockInject:
    instance = MagicMock()
