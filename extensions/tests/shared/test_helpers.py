from bson import ObjectId

from extensions.module_result.models.primitives.primitive import MeasureUnit
from extensions.module_result.modules import (
    WeightModule,
    HeightModule,
    TemperatureModule,
    BloodGlucoseModule,
)
from sdk.phoenix.config.server_config import Project, Client
from sdk.tests.auth.test_helpers import (
    TEST_CLIENT_ID,
    CLIENT_ID_3,
    PROJECT_ID,
    TEST_CLIENT_ID_MINIMUM_VERSION,
)


def consent_log():
    return {
        "givenName": "Test client",
        "middleName": "test",
        "familyName": "Test client",
        "signature": {"key": "key", "region": "eu", "bucket": "bucket"},
        "sharingOption": 1,
        "agreement": True,
    }


def simple_consent() -> dict:
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
            "showFirstLastName": True,
        },
        "additionalConsentQuestions": [
            {
                "type": "isDataSharedForFutureStudies",
                "enabled": "ENABLED",
                "format": "BOOLEAN",
                "text": "Would you like your data to be used in future studies?",
                "description": 'If you give consent, the following information will be shared: your first and last name, date of birth, sex, and postcode.\n\nFull information on how Discover handles your data, including how to withdraw consent, <a href="https://sample.org">can be found here</a>.',
                "order": 2,
            },
            {
                "type": "isDataSharedForResearch",
                "enabled": "ENABLED",
                "format": "BOOLEAN",
                "text": "Do you allow the research investigators to retrieve your data from the vaccine registry?",
                "description": 'If you give consent, the following information will be shared: your first and last name, date of birth, sex, and postcode.\n\nFull information on how Discover handles your data, including how to withdraw consent, <a href="https://sample.org">can be found here</a>.',
                "order": 1,
            },
        ],
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
                "type": "TIME_COMMITMENT",
                "title": "Time Commitment",
                "details": "Time commitment",
                "reviewDetails": "Medopad ",
            },
            {
                "type": "STUDY_SURVEY",
                "title": "Study Survey",
                "details": "Study Survey",
                "reviewDetails": "Medopad ",
            },
            {
                "type": "STUDY_TASKS",
                "title": "Study Tasks",
                "details": "Study Tasks",
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
            {
                "type": "DATA_PROCESSING",
                "title": "Data Processing",
                "details": "Date processing",
                "reviewDetails": "Medopad w",
            },
            {
                "type": "FEEDBACK",
                "title": "Feedback",
                "reviewDetails": "As part of this study, you may be contracted to provide feedback on your experiences either using the Huma app.",
            },
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
            },
            {
                "type": "DATA_GATHERING",
                "title": "Your Data",
                "reviewDetails": "As part of this study, you may be contracted to provide feedback on your experiences either using the Huma app.",
            },
        ],
    }


def simple_deployment() -> dict:
    return {
        "name": "test Deployment",
        "status": "DRAFT",
        "color": "0x007AFF",
        "icon": {"bucket": "test", "key": "test", "region": "eu"},
    }


def simple_econsent() -> dict:
    return {
        "enabled": "ENABLED",
        "title": "Informed consent form",
        "overviewText": "To participate in the trial study, please read  the consent form through in detail. \n\nIf you have any questions, please contact your study team at studyteam@reallylongemail.com or +44 1234 567 890 providing your consent to participate.",
        "contactText": "Please contact your study team at contact@studyteam.com if you have any questions.",
        "instituteFullName": "string",
        "instituteName": "string",
        "instituteTextDetails": "string",
        "signature": {
            "signatureTitle": "Signature",
            "signatureDetails": "Please sign using your finger in the box below",
            "nameTitle": "Medopad Consent",
            "nameDetails": "Type your full name in text fields below",
            "hasMiddleName": True,
            "showFirstLastName": True,
        },
        "additionalConsentQuestions": [
            {
                "type": "isDataSharedForFutureStudies",
                "enabled": "ENABLED",
                "format": "BOOLEAN",
                "text": "Would you like your data to be used in future studies?",
                "description": 'If you give consent, the following information will be shared: your first and last name, date of birth, sex, and postcode.\n\nFull information on how Discover handles your data, including how to withdraw consent, <a href="https://sample.org">can be found here</a>.',
                "order": 2,
            },
            {
                "type": "isDataSharedForResearch",
                "enabled": "ENABLED",
                "format": "BOOLEAN",
                "text": "Do you allow the research investigators to retrieve your data from the vaccine registry?",
                "description": 'If you give consent, the following information will be shared: your first and last name, date of birth, sex, and postcode.\n\nFull information on how Discover handles your data, including how to withdraw consent, <a href="https://sample.org">can be found here</a>.',
                "order": 1,
            },
        ],
        "sections": [
            {
                "type": "INTRODUCTION",
                "title": "Introduction",
                "details": "INTRODUCTION",
                "reviewDetails": "You have been asked to participate in a clinical research study initiated, managed, and financed by ABC LAbs, who is the Sponsor of this study. Before your decide, it is important for you to understand why the research is being done and what it will involve. This informed consent form will provide you with essential information about this study and your rights as a study participant so that you can make an informed decision about your participation. Y \nYour decision to participate in this study is entirely voluntary. You will not lose any benefits to which you would otherwise be entitled if you refuse to participant. In addition, you may withdraw from the study at any time without penality or loss of benefits to which you are otherwise entitled. You will be informed in a timely manner, if any relevant new information about this drug or this study becomes available that may alter your willingness to continue to participate. If you agree, your General Practitioner will be told that you are taking part in this study.",
                "contentType": "IMAGE",
                "thumbnailLocation": {
                    "key": "deployment/<deployment_id>/<image_location>",
                    "region": "eu",
                    "bucket": "ppdeveufrankfurt",
                },
            },
            {
                "type": "PURPOSE",
                "title": "PURPOSE",
                "reviewDetails": "You are being asked to participate in this clinical research study because you have high blood pressure and are already taking prescribed commercial Cligoliob for an approved dose and indication in your countr.\nYou are eligible to participate in this study because following discussions with your own doctor you have decided to continue taking Cigoliob.\nInformation regarding the use of Cigoliob may be obtained from the patient information leaflet which accompanies your supply of Cigoliob and from your own treating physician.\nThe purpose of this study is to assess the levels of Cigoliob in blood across the course of the study in study participants with high blood pressure.\nThis study is expected to enroll approximately 100 women who have high blood pressure while takingcommercial Cigoliob across approximately 13 centers throughout Canada, USA, Swizerland and selected countries in the European Union (possible including but not necessarily limited to France, Germany, Spain or Italy).",
                "contentType": "IMAGE",
                "thumbnailUrl": "https://www.roadrunnerrecords.com/sites/g/files/g2000005056/f/sample-4.jpg",
            },
            {
                "type": "REVIEW_TO_SIGN",
                "title": "REVIEW_TO_SIGN",
                "reviewDetails": "I have read and understood this consent document. By signing this: \n• I confirm that I have had time to read carefully and understand the study participant informed consent provided for this study.\n• I confirm that I have had the opportunity to discuss the study and ask questions, and I am satisfied with the answers and explanations that I have been provided.\n• I give permission for my medical records to be reviewed by the Sponsor or designee and/or representatives of any Drug Reculatory Authorities such as the U.S. FDA and Insitutional Review Boards.\n• I understand that my participation is voluntary and that I am free to withdraw at any time without giving any reason and without my medical care or legal rights being affected.. I agree that the Sponsor can continue to use the information about my health collected during the study to preserve the integrity of the study, even if I withdraw from the study.",
                "contentType": "VIDEO",
                "videoLocation": {
                    "key": "deployment/<deployment_id>/<video_location>",
                    "region": "eu",
                    "bucket": "ppdeveufrankfurt",
                },
                "thumbnailLocation": {
                    "key": "deployment/<deployment_id>/<thumbnail_location>",
                    "region": "eu",
                    "bucket": "ppdeveufrankfurt",
                },
            },
            {
                "type": "DURING_THE_TRIAL",
                "title": "DURING_THE_TRIAL",
                "reviewDetails": "During the course of this trial, you’ll be asked to complete a series of task such as:\n• Entering your blood pressure in the morning every day in the Huma app\n•Recording your medication intake in the Huma app\n• Attending telemedicine video conferences with your study care team in the Huma app\n• Attending face-to-face appointments with your study care team every 3 months\nThere are some acitivites that you would not be able to do during the course of the trial. They are:\n• Donating blood\n• Traveling via plane or helicopter",
                "contentType": "VIDEO",
                "videoUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "thumbnailUrl": "https://www.roadrunnerrecords.com/sites/g/files/g2000005056/f/sample-4.jpg",
            },
        ],
    }


def simple_econsent_log() -> dict:
    return {
        "givenName": "givenName",
        "middleName": "middleName",
        "familyName": "familyName",
        "signature": {
            "key": "econsent_images/signature.png",
            "region": "eu",
            "bucket": "ppdeveufrankfurt",
        },
        "sharingOption": 1,
        "additionalConsentAnswers": {
            "isDataSharedForFutureStudies": False,
            "isDataSharedForResearch": True,
        },
    }


def generate_random_stringified_object_id() -> str:
    return str(ObjectId())


def get_module_config():
    return {
        "about": "string",
        "configBody": {},
        "moduleId": "Journal",
        "moduleName": "string",
        "schedule": {
            "friendlyText": "string",
            "isoDuration": "P1W",
            "timesOfDay": ["BEFORE_BREAKFAST"],
            "timesPerDuration": 0,
        },
        "status": "ENABLED",
    }


def simple_preferred_units() -> dict:
    from extensions.authorization.models.user import User

    return {
        User.PREFERRED_UNITS: {
            WeightModule.moduleId: MeasureUnit.KILOGRAM.value,
            HeightModule.moduleId: MeasureUnit.CENTIMETRE.value,
            TemperatureModule.moduleId: MeasureUnit.CELSIUS.value,
            BloodGlucoseModule.moduleId: MeasureUnit.MILLIMOLES_PER_LITRE.value,
        }
    }


def get_server_project():
    project_data = {
        Project.ID: PROJECT_ID,
        Project.MASTER_KEY: "123",
        Project.CLIENTS: [
            {
                Client.NAME: "client",
                Client.CLIENT_ID: TEST_CLIENT_ID,
                Client.CLIENT_TYPE: Client.ClientType.USER_ANDROID.value,
                Client.ROLE_IDS: ["User"],
                Client.MINIMUM_VERSION: TEST_CLIENT_ID_MINIMUM_VERSION,
            },
            {
                Client.NAME: "client3",
                Client.CLIENT_ID: CLIENT_ID_3,
                Client.CLIENT_TYPE: Client.ClientType.MANAGER_WEB.value,
                Client.ROLE_IDS: ["Manager"],
            },
        ],
    }
    return Project.from_dict(project_data)
