from datetime import timedelta, datetime
from pathlib import Path

from mohawk import Sender

from extensions.authorization.models.user import AdditionalContactDetails, User
from extensions.common.s3object import FlatBufferS3Object, S3Object
from extensions.deployment.models.learn import LearnArticle, LearnArticleContent
from extensions.module_result.models.primitives import ECGReading
from sdk.auth.use_case.auth_request_objects import CreateServiceAccountRequestObject
from sdk.common.utils.validators import utc_str_field_to_val

BUCKET_NAME = "integrationtests"
TEST_FILE_NAME = "test_file.txt"
SUPER_ADMIN_ID = "5ed803dd5f2f99da73684413"
ACCOUNT_MANAGER_ID = "61cb194c630781b664bf8eb5"
ORG_OWNER_ID = "61cb194c630781b664bc7eb5"
ORG_EDITOR_ID = "61e6a8e2d9681a389f060848"

# deployment X
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_CODE = "AU15"
DEPLOYMENT_X_USER_CODE = "53924415"
DEPLOYMENT_X_MANAGER_CODE = "17781957"

CORRECT_MASTER_KEY = "12345678"
WRONG_MASTER_KEY = "1234567"

USER_1_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34789b"
USER_2_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34789c"
MANAGER_1_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34789d"
MANAGER_2_ID_DEPLOYMENT_X = "5e8f0c74b50aa9656c34788d"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
CUSTOM_ROLE_1_ID_DEPLOYMENT_X = "600720843111683010a73b4e"
CUSTOM_ROLE_2_ID_DEPLOYMENT_X = "6009d2409b0e1f2eab20bbb3"
USER_ID_WITH_VIEW_IDENTIFIER = "600720843111683010a73b4e"
USER_ID_WITH_OUT_VIEW_IDENTIFIER = "602fa576c06fe59e3556171c"
USER_WITHOUT_ROLE = "607eb479a73c845d84e2f53b"
USER_WITHOUT_ROLE_EMAIL = "user_without_role@example.com"
DEPLOYMENT_ADMINISTRATOR_ID = "5ed803dd5f2f99da73666614"
MULTI_DEPLOYMENT_ADMINISTRATOR_ID = "5ed803dd5f2f99da73666624"

# deployment Y
DEPLOYMENT_2_ID = "5ed8ae76cf99540b259a7315"
USER_1_ID_DEPLOYMENT_Y = "5eda5e367adadfb46f7ff71f"
MANAGER_2_ID_DEPLOYMENT_Y = "5eda5db67adadfb46f7ff71d"

# organization
ORGANIZATION_ID = "5fde855f12db509a2785da06"
ORGANIZATION_STAFF_ID = "5ed803dd5f2f99da73654413"
ACCESS_CONTROLLER_ID = "5ed803dd5f2f99da73654410"
DEPLOYMENT_STAFF_ID = "5ed803dd5f2f99da73654411"
CALL_CENTER_ID = "5ed803dd5f2f99da73654412"
HUMA_SUPPORT_ID = "5ed803dd5f2f99da73675513"
SUPPORT_ID = "5ed803dd5f2f99da73655513"
SUPERVISOR_ID = "5ed803dd5f2f99da73655524"
ORGANIZATION_ADMINISTRATOR_ID = "5ed803dd5f2f99da73655514"
CLINICIAN_ID = "5ed803dd5f2f99da73655147"

TEST_FILE_PATH = Path(__file__).parent.joinpath("fixtures/test_file.txt")


def now_str(delta=timedelta(days=0)):
    return utc_str_field_to_val(datetime.utcnow().replace(microsecond=0) + delta)


def content_test_file():
    with open(Path(__file__).with_name(TEST_FILE_NAME), "rb") as upload:
        return upload.read()


def get_user(email: str, name: str, validation_data: dict):
    return {
        "method": 0,
        "email": email,
        "displayName": name,
        "validationData": validation_data,
        "userAttributes": {
            "familyName": name,
            "givenName": name,
        },
        "clientId": "ctest1",
        "projectId": "ptest1",
    }


def get_sign_up_data(email: str, name: str, activation_code: str):
    return get_user(email, name, {"activationCode": activation_code})


def get_invitation_sign_up_data(
    email: str,
    name: str,
    invitation_code: str = None,
    shortened_invitation_code: str = None,
):
    validation_data = (
        {"shortenedCode": shortened_invitation_code}
        if shortened_invitation_code
        else {"invitationCode": invitation_code}
    )
    return get_user(email=email, name=name, validation_data=validation_data)


def get_service_account_signup_data(
    service_account_name: str, role_id: str, resource_id: str, master_key: str
) -> dict:
    return {
        CreateServiceAccountRequestObject.SERVICE_ACCOUNT_NAME: service_account_name,
        CreateServiceAccountRequestObject.VALIDATION_DATA: {"masterKey": master_key},
        CreateServiceAccountRequestObject.ROLE_ID: role_id,
        CreateServiceAccountRequestObject.RESOURCE_ID: resource_id,
    }


def get_deployment(name: str):
    return {
        "name": name,
        "status": "DEPLOYED",
        "color": "0x007AFF",
        "icon": {"bucket": "test", "key": "test", "region": "eu"},
    }


def get_consent():
    return {
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
                "type": "OVERVIEW",
                "title": "Welcome",
                "details": "The following screens explain how Medopad works, the data it collects and privacy.",
                "reviewDetails": "Medopad helps to shar",
            },
            {
                "type": "DATA_GATHERING",
                "title": "Data gathering",
                "details": "Medopad collects information which ",
                "reviewDetails": "Medopad collects information",
            },
            {
                "type": "PRIVACY",
                "title": "Privacy",
                "details": "Your Child's clinical team can acces",
                "reviewDetails": "Medopad will always use a code",
            },
            {
                "type": "DATA_USE",
                "title": "Data Use",
                "details": "Data that You or ",
                "reviewDetails": "Medopad ",
            },
            {
                "type": "WITHDRAWING",
                "title": "Withdrawing",
                "details": "Medopad is her",
                "reviewDetails": "Medopad w",
            },
            {
                "type": "SHARING",
                "title": "Sharing Options",
                "details": "The clinical team ",
                "reviewDetails": "The clinical t",
                "options": [
                    {
                        "type": 0,
                        "text": "Share my Child's data with the clinical team and researchers",
                    },
                    {
                        "type": 1,
                        "text": "Only share my Child's data with the clinical team",
                    },
                ],
            },
        ],
    }


def get_learn_section():
    return {"title": "Test section", "order": 1}


def get_article():
    return {
        LearnArticle.TITLE: "article_ss three",
        LearnArticle.ORDER: 10,
        LearnArticle.TYPE: "SMALL",
        LearnArticle.THUMBNAIL_URL: {
            S3Object.REGION: "us-west-1",
            S3Object.KEY: "my.png",
            S3Object.BUCKET: "admin_bucket",
        },
        LearnArticle.CONTENT: {
            LearnArticleContent.TYPE: "VIDEO",
            LearnArticleContent.TIME_TO_READ: "20m",
            LearnArticleContent.TEXT_DETAILS: "Here what you read",
            LearnArticleContent.VIDEO_URL: {
                S3Object.BUCKET: "integrationtests",
                S3Object.KEY: "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
                S3Object.REGION: "cn",
            },
            LearnArticleContent.CONTENT_OBJECT: {
                S3Object.BUCKET: "integrationtests",
                S3Object.KEY: "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
                S3Object.REGION: "cn",
            },
        },
    }


def get_medication(user_id):
    return {
        "name": "Medicine",
        "userId": user_id,
        "doseQuantity": 250.0,
        "doseUnits": "mg",
        "prn": True,
        "extraProperties": {},
    }


def get_journal(deployment_id):
    return {
        "type": "Journal",
        "moduleId": "Journal",
        "deviceName": "iOS",
        "deploymentId": deployment_id,
        "startDateTime": "2020-04-28T21:13:07Z",
        "value": "Test journal",
    }


def weight_result(value, start_date_time=None, deployment_id=None):
    return {
        "type": "Weight",
        "deviceName": "iOS",
        "deploymentId": deployment_id or DEPLOYMENT_ID,
        "startDateTime": start_date_time or now_str(),
        "value": value,
    }


def ecg_result(value):
    return {
        "type": "ECGHealthKit",
        "deviceName": "iOS",
        "deploymentId": DEPLOYMENT_ID,
        "startDateTime": now_str(),
        "value": value,
        "ecgReading": {
            ECGReading.AVERAGE_HEART_RATE: 150.4,
            ECGReading.DATA_POINTS: {
                FlatBufferS3Object.KEY: "ecg_sample",
                FlatBufferS3Object.BUCKET: "integrationtests",
                FlatBufferS3Object.REGION: "sample",
                FlatBufferS3Object.FBS_VERSION: 1,
            },
        },
    }


def observation_note(deployment_id=None, start_date_time=None) -> dict:
    return {
        "type": "Questionnaire",
        "deviceName": "iOS",
        "deploymentId": deployment_id or DEPLOYMENT_ID,
        "startDateTime": start_date_time or now_str(),
        "questionnaireId": "e932907c-e2c6-4fc7-88a9-72e2bba65431",
        "questionnaireName": "Observation Notes",
        "isForManager": True,
        "answers": [
            {
                "answerText": "Answer",
                "answerScore": 55,
                "id": "5ee0d29a58e7994d8633037c",
                "questionId": "5ee0d29a58e7994d8633037c",
                "question": "Simple Question 1",
            },
            {
                "answerText": "Answer",
                "answerScore": 55,
                "id": "5ee0d29a58e7994d8633037c",
                "questionId": "5ee0d29a58e7994d8633037d",
                "question": "Simple Question 2",
            },
        ],
    }


def get_sample_preferred_units() -> dict:
    return {
        "preferredUnits": {"BloodGlucose": "mg/dL", "Weight": "kg", "Temperature": "oC"}
    }


def get_sample_additional_contact_details() -> dict:
    return {
        User.ADDITIONAL_CONTACT_DETAILS: {
            AdditionalContactDetails.REGULAR_CONTACT_NAME: "Emmanuel",
            AdditionalContactDetails.REGULAR_CONTACT_NUMBER: "+2347063335480",
            AdditionalContactDetails.EMERGENCY_CONTACT_NAME: "David",
            AdditionalContactDetails.EMERGENCY_CONTACT_NUMBER: "+2347063335480",
        }
    }


def get_request_header_hawk(
    user_key: str,
    auth_key: str,
    url: str,
    method: str,
    content: bytes,
    content_type: str,
) -> str:
    sender = Sender(
        {"id": user_key, "key": auth_key, "algorithm": "sha256"},
        url=url,
        method=method,
        content=content,
        content_type=content_type,
    )

    return sender.request_header


def get_sample_labels():
    return [
        {
            "id": "5e8eeae1b707216625ca4202",
            "text": "RECOVERED",
            "authorId": "5e8f0c74b50aa9656c34789b",
            "createDateTime": "2022-04-12T11:35:21.435000Z",
        },
        {
            "id": "5d386cc6ff885918d96edb2c",
            "text": "IN TREATMENT",
            "authorId": "5e8f0c74b50aa9656c34789b",
            "createDateTime": "2022-04-12T11:35:21.435000Z",
        },
    ]
