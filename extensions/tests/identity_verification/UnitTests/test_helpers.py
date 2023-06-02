from datetime import datetime

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment, OnboardingModuleConfig
from extensions.identity_verification.router.identity_verification_requests import (
    GenerateIdentityVerificationTokenRequestObject,
)


def get_sample_user_dict() -> dict:
    return {
        User.ID: "5e8f0c74b50aa9656c34789c",
        User.DATE_OF_BIRTH: datetime.fromtimestamp(572392800000 / 1000),
        User.GIVEN_NAME: "User",
        User.FAMILY_NAME: "Test",
        User.EMAIL: "test+user@gmail.com",
    }


def get_sample_verification_sdk_token_request() -> dict:
    return {
        GenerateIdentityVerificationTokenRequestObject.LEGAL_FIRST_NAME: "Test",
        GenerateIdentityVerificationTokenRequestObject.LEGAL_LAST_NAME: "Test",
        GenerateIdentityVerificationTokenRequestObject.USER_ID: "5e8f0c74b50aa9656c34789c",
        GenerateIdentityVerificationTokenRequestObject.APPLICATION_ID: "com.huma.HumaApp.dev",
    }


def get_sample_create_user_verification_log_request_dict() -> dict:
    return {
        "deployment": get_sample_deployment(),
        "userId": "5e8f0c74b50aa9656c34789c",
        "applicantId": "8a94ba54-161b-49ab-8c76-f0b56de3a414",
        "checkId": "checkId",
        "legalFirstName": "FirstName",
        "legalLastName": "LastName",
        "documents": ["603df5fc65e41764f9fe5345"],
    }


def get_sample_deployment() -> Deployment:
    return Deployment(
        id="60103095db18b64247a1f44c",
        name="test",
        onboardingConfigs=[
            OnboardingModuleConfig(
                onboardingId="IdentityVerification",
                status="ENABLED",
                id="604c895da1adf357ed1fe15f",
                order=2,
                version=1,
                userTypes=["User"],
                configBody={"requiredReports": ["DOCUMENT", "FACIAL_SIMILARITY_PHOTO"]},
            )
        ],
    )
