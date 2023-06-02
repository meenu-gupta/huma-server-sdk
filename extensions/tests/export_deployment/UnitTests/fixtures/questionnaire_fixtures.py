from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    QuestionnaireAnswer,
    Questionnaire,
)


def sample_multiple_choice_question_without_comma() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "Please remember to log your symptoms in the symptom tracker.",
                "id": "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
                "required": True,
                "format": "TEXTCHOICE",
                "order": 1,
                "text": "In the last month have you experienced or"
                + " are you still experiencing any possible COVID-19 symptoms?",
                "options": [
                    {"label": "Persistent cough", "value": "0", "weight": 0},
                    {"label": "Fever", "value": "1", "weight": 1},
                    {"label": "Sneezing", "value": "5", "weight": 5},
                ],
                "selectionCriteria": "MULTIPLE",
            }
        ],
        "order": 5,
    }


def sample_multiple_choice_question_with_comma() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "Please remember to log your symptoms in the symptom tracker.",
                "id": "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
                "required": True,
                "format": "TEXTCHOICE",
                "order": 1,
                "text": "In the last month have you experienced or"
                + " are you still experiencing any possible COVID-19 symptoms?",
                "options": [
                    {"label": "Persistent cough", "value": "0", "weight": 0},
                    {"label": "Fever", "value": "1", "weight": 1},
                    {
                        "label": "Hoarseness (changes to the sound of your voice, particularly becoming strained)",
                        "value": "2",
                        "weight": 2,
                    },
                    {
                        "label": "Non-persistent cough (not coughing continuously)",
                        "value": "3",
                        "weight": 3,
                    },
                    {
                        "label": "Discharge or congestion in the nose",
                        "value": "4",
                        "weight": 4,
                    },
                    {"label": "Sneezing", "value": "5", "weight": 5},
                    {"label": "Sore throat", "value": "6", "weight": 6},
                    {"label": "Feeling breathless", "value": "7", "weight": 7},
                    {
                        "label": "Wheeze (a whistling sound when breathing)",
                        "value": "8",
                        "weight": 8,
                    },
                    {"label": "Headache", "value": "9", "weight": 9},
                    {"label": "Muscle aches", "value": "10", "weight": 10},
                    {"label": "Unexplained tiredness", "value": "11", "weight": 11},
                    {
                        "label": "Being sick or feeling sick",
                        "value": "12",
                        "weight": 12,
                    },
                    {"label": "Diarrhoea", "value": "13", "weight": 13},
                    {"label": "Loss of taste or smell", "value": "14", "weight": 14},
                    {"label": "Other", "value": "15", "weight": 15},
                    {"label": "No symptoms", "value": "16", "weight": 16},
                ],
                "selectionCriteria": "MULTIPLE",
            }
        ],
        "order": 5,
    }


def sample_answer_multiple_choice_question_without_comma():
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "Persistent cough,Fever",
        QuestionnaireAnswer.QUESTION_ID: "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
        QuestionnaireAnswer.QUESTION: "In the last month have you experienced or"
        " are you still experiencing any possible COVID-19 symptoms?",
    }


def sample_answer_multiple_choice_question():
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "Persistent cough,Hoarseness (changes to the sound of your voice,"
        " particularly becoming strained),No symptoms,Not available,Sore throat,"
        "Not, available,Not, available, not",
        QuestionnaireAnswer.QUESTION_ID: "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
        QuestionnaireAnswer.QUESTION: "In the last month have you experienced or"
        " are you still experiencing any possible COVID-19 symptoms?",
    }


def sample2_answer_multiple_choice_question():
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "Not, available,Persistent cough,Hoarseness (changes to the sound of your voice,"
        " particularly becoming strained),No symptoms,Not available,Sore throat",
        QuestionnaireAnswer.QUESTION_ID: "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
        QuestionnaireAnswer.QUESTION: "In the last month have you experienced or"
        " are you still experiencing any possible COVID-19 symptoms?",
    }


def sample_answer_multiple_choice_question_with_choices():
    return {
        QuestionnaireAnswer.QUESTION_ID: "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
        QuestionnaireAnswer.QUESTION: "In the last month have you experienced or"
        " are you still experiencing any possible COVID-19 symptoms?",
        QuestionnaireAnswer.ANSWER_CHOICES: [
            {"text": "Persistent cough", "selected": True},
            {"text": "Fever", "selected": False},
            {
                "text": "Hoarseness (changes to the sound of your voice, particularly becoming strained)",
                "selected": True,
            },
            {
                "text": "Non-persistent cough (not coughing continuously)",
                "selected": False,
            },
            {"text": "Discharge or congestion in the nose", "selected": False},
            {"text": "Sneezing", "selected": False},
            {"text": "Sore throat", "selected": True},
            {"text": "Feeling breathless", "selected": False},
            {"text": "Wheeze (a whistling sound when breathing)", "selected": False},
            {"text": "Headache", "selected": False},
            {"text": "Muscle aches", "selected": False},
            {"text": "Unexplained tiredness", "selected": False},
            {"text": "Being sick or feeling sick", "selected": False},
            {"text": "Diarrhoea", "selected": False},
            {"text": "Loss of taste or smell", "selected": False},
            {"text": "Other", "selected": False},
            {"text": "No symptoms", "selected": True},
        ],
    }


def sample_answer_multiple_choice_question_without_any_selected():
    return {
        QuestionnaireAnswer.QUESTION_ID: "a4220a3a-0522-4cff-af6a-7d4fb5ef805d",
        QuestionnaireAnswer.QUESTION: "In the last month have you experienced or"
        " are you still experiencing any possible COVID-19 symptoms?",
        QuestionnaireAnswer.ANSWER_CHOICES: [
            {"text": "Persistent cough", "selected": False},
            {"text": "Fever", "selected": False},
            {
                "text": "Hoarseness (changes to the sound of your voice, particularly becoming strained)",
                "selected": False,
            },
            {
                "text": "Non-persistent cough (not coughing continuously)",
                "selected": False,
            },
            {"text": "Discharge or congestion in the nose", "selected": False},
            {"text": "Sneezing", "selected": False},
            {"text": "Sore throat", "selected": False},
            {"text": "Feeling breathless", "selected": False},
            {"text": "Wheeze (a whistling sound when breathing)", "selected": False},
            {"text": "Headache", "selected": False},
            {"text": "Muscle aches", "selected": False},
            {"text": "Unexplained tiredness", "selected": False},
            {"text": "Being sick or feeling sick", "selected": False},
            {"text": "Diarrhoea", "selected": False},
            {"text": "Loss of taste or smell", "selected": False},
            {"text": "Other", "selected": False},
            {"text": "No symptoms", "selected": False},
        ],
    }


def sample_single_choice_question() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "",
                "id": "aaafaed4-5854-4a6b-946d-8d787a78f9ad",
                "required": True,
                "format": "TEXTCHOICE",
                "order": 1,
                "text": "Please select that best describes your living situation",
                "options": [
                    {"label": "I live alone", "value": "0", "weight": 0},
                    {"label": "I live with family", "value": "1", "weight": 1},
                    {"label": "I live with friends/partner", "value": "2", "weight": 2},
                    {"label": "I live with a carer", "value": "3", "weight": 3},
                    {"label": "I am a live-in carer", "value": "4", "weight": 4},
                ],
                "selectionCriteria": "SINGLE",
            }
        ],
        "order": 10,
    }


def sample_answer_single_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "I live alone",
        QuestionnaireAnswer.QUESTION_ID: "aaafaed4-5854-4a6b-946d-8d787a78f9ad",
        QuestionnaireAnswer.QUESTION: "Please select that best describes your living situation",
    }


def sample_answer_single_question_with_choices() -> dict:
    return {
        QuestionnaireAnswer.QUESTION_ID: "aaafaed4-5854-4a6b-946d-8d787a78f9ad",
        QuestionnaireAnswer.QUESTION: "Please select that best describes your living situation",
        QuestionnaireAnswer.ANSWER_CHOICES: [
            {"text": "I live alone", "selected": True},
            {"text": "I live with family", "selected": False},
            {"text": "I live with friends/partner", "selected": False},
            {"text": "I live with a carer", "selected": False},
            {"text": "I am a live-in carer", "selected": False},
        ],
    }


def sample_boolean_question() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {
                    "isEnabled": False,
                },
                "description": "",
                "id": "1de25bbb-abce-4d7a-bad9-b267dac0876d",
                "required": True,
                "format": "BOOLEAN",
                "order": 1,
                "text": "Have you had a test for COVID-19?",
            }
        ],
        "order": 3,
    }


def sample_answer_boolean_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "No",
        QuestionnaireAnswer.QUESTION_ID: "1de25bbb-abce-4d7a-bad9-b267dac0876d",
        QuestionnaireAnswer.QUESTION: "Have you had a test for COVID-19?",
    }


def sample_text_question() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "If you have more than one please separate them with a full stop.",
                "id": "a0c705c5-1292-4fa6-80a2-5fb33ba942ef",
                "required": False,
                "format": "TEXT",
                "order": 1,
                "text": "Please enter any other symptoms.",
            }
        ],
        "order": 6,
    }


def sample_answer_text_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "Nothing",
        QuestionnaireAnswer.QUESTION_ID: "a0c705c5-1292-4fa6-80a2-5fb33ba942ef",
        QuestionnaireAnswer.QUESTION: "Please enter any other symptoms.",
    }


def sample_number_question() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "",
                "id": "6040287a-1126-48ff-9675-9785d4b742f2",
                "required": True,
                "format": "NUMERIC",
                "order": 1,
                "text": "What is your age in years?",
                "allowsIntegersOnly": True,
                "lowerBound": 0,
                "upperBound": 100,
            }
        ],
        "order": 2,
    }


def sample_answer_number_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "16.0",
        QuestionnaireAnswer.QUESTION_ID: "6040287a-1126-48ff-9675-9785d4b742f2",
        QuestionnaireAnswer.QUESTION: "What is your age in years?",
    }


def sample_scale_question() -> dict:
    return {
        "type": "QUESTION",
        "order": 1,
        "items": [
            {
                "logic": {
                    "isEnabled": True,
                },
                "id": "7c50c7d5-6f4e-4c0b-aeaf-c266eafd056e",
                "format": "SCALE",
                "order": 1,
                "text": "In the last month, how frequently did you complete your scheduled medication and supplements routine?",
                "description": "Indicate your adherence on a scale of 0 (never) to 100 (always).",
                "required": True,
                "lowerBound": "0",
                "upperBound": "100",
            }
        ],
    }


def sample_answer_scale_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "23",
        QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafd056e",
        QuestionnaireAnswer.QUESTION: "In the last month, how frequently did you complete your scheduled medication and supplements routine?",
    }


def sample_date_question() -> dict:
    return {
        "type": "QUESTION",
        "items": [
            {
                "logic": {"isEnabled": False},
                "description": "",
                "id": "ebeb1822-3697-455b-8623-429b7c69054d",
                "required": True,
                "format": "DATE",
                "order": 1,
                "text": "When did your possible COVID-19 symptoms start?",
            }
        ],
        "order": 25,
    }


def sample_answer_date_question() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "2020-10-09",
        QuestionnaireAnswer.QUESTION_ID: "ebeb1822-3697-455b-8623-429b7c69054d",
        QuestionnaireAnswer.QUESTION: "When did your possible COVID-19 symptoms start?",
    }


def sample_unknown_answer() -> dict:
    return {
        QuestionnaireAnswer.ANSWER_TEXT: "2020-10-09",
        QuestionnaireAnswer.QUESTION_ID: "abeb1822-3697-455b-8623-429b7c69054d",
        QuestionnaireAnswer.QUESTION: "When did your possible COVID-19 symptoms start?",
    }


def sample_symptoms() -> dict:
    return {
        "complexSymptoms": [
            {
                "name": "Persistent cough",
                "scale": [
                    {"severity": 1, "value": "Mild"},
                    {"severity": 2, "value": "Moderate"},
                    {"severity": 3, "value": "Severe"},
                ],
            },
            {
                "name": "Discharge or congestion in the nose",
                "scale": [
                    {"severity": 1, "value": "Mild"},
                    {"severity": 2, "value": "Moderate"},
                    {"severity": 3, "value": "Severe"},
                ],
            },
            {
                "name": "Sneezing",
                "scale": [
                    {"severity": 1, "value": "Mild"},
                    {"severity": 2, "value": "Moderate"},
                    {"severity": 3, "value": "Severe"},
                ],
            },
            {
                "name": "Headache",
                "scale": [
                    {"severity": 1, "value": "Mild"},
                    {"severity": 2, "value": "Moderate"},
                    {"severity": 3, "value": "Severe"},
                ],
            },
        ]
    }


def sample_symptoms_result() -> dict:
    return {
        "complexValues": [
            {"name": "Persistent cough", "severity": "3"},
            {"name": "Loss of taste or smell", "severity": "1"},
            {"name": "Sneezing", "severity": "2"},
            {"name": "Other", "severity": "1"},
        ]
    }


def sample_baseline_questionnaire() -> Questionnaire:
    return Questionnaire.from_dict(
        {
            Questionnaire.ID: "60f159aa7e3f76060d0743f4",
            Questionnaire.USER_ID: "60f1586735080b15129f3883",
            Questionnaire.MODULE_ID: "Questionnaire",
            Questionnaire.MODULE_CONFIG_ID: "5f68a280dfd88db0d721963a",
            Questionnaire.DEPLOYMENT_ID: "5f21e1d605f94e9073a8c964",
            Questionnaire.VERSION: 0,
            Questionnaire.DEVICE_NAME: "Android",
            Questionnaire.IS_AGGREGATED: False,
            Questionnaire.START_DATE_TIME: "2021-07-16T10:04:24.491000Z",
            Questionnaire.CREATE_DATE_TIME: "2021-07-16T10:04:26.196000Z",
            Questionnaire.SUBMITTER_ID: "60f1586735080b15129f3883",
            Questionnaire.ANSWERS: [
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "45.0",
                    QuestionnaireAnswer.QUESTION_ID: "6040287a-1126-48ff-9675-9785d4b742f2",
                    QuestionnaireAnswer.QUESTION: "What is your age in years?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "45.0",
                    QuestionnaireAnswer.QUESTION_ID: "9a848031-134d-47d2-9cb8-2f0e667567ac",
                    QuestionnaireAnswer.QUESTION: "What is your height, in cm?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Male",
                    QuestionnaireAnswer.QUESTION_ID: "4c8c1265-770c-48af-8e16-524afb86abae",
                    QuestionnaireAnswer.QUESTION: "What is your sex?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                    QuestionnaireAnswer.QUESTION_ID: "a1c39177-ab08-4e19-bc9a-990c9fb0f315",
                    QuestionnaireAnswer.QUESTION: "Have you had a test for COVID-19?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                    QuestionnaireAnswer.QUESTION_ID: "08071fdc-93e8-49d9-b9f3-2a4278d0673c",
                    QuestionnaireAnswer.QUESTION: "Did you test positive for COVID-19?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes, I still do",
                    QuestionnaireAnswer.QUESTION_ID: "abbad5fd-0e03-479b-af9b-8371d48dd857",
                    QuestionnaireAnswer.QUESTION: "Have you ever smoked?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "More than 20",
                    QuestionnaireAnswer.QUESTION_ID: "f4cdeaee-be18-4cf4-b2ee-13ce47c10f71",
                    QuestionnaireAnswer.QUESTION: "Roughly how many cigarettes do you smoke a day?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "More than 15 years",
                    QuestionnaireAnswer.QUESTION_ID: "6d3d7560-e9ee-44c3-816f-5c1047edf6b3",
                    QuestionnaireAnswer.QUESTION: "For how many years have you been a smoker?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Yes, I still do",
                    QuestionnaireAnswer.QUESTION_ID: "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                    QuestionnaireAnswer.QUESTION: "Have you ever vaped?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Regularly",
                    QuestionnaireAnswer.QUESTION_ID: "62220451-f356-4ae1-b1d0-1420843186c4",
                    QuestionnaireAnswer.QUESTION: "How often do you vape?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "More than 15 years",
                    QuestionnaireAnswer.QUESTION_ID: "3cbcaf66-e762-4947-b13e-36ec00e491dc",
                    QuestionnaireAnswer.QUESTION: "How many years have you vaped?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Excellent",
                    QuestionnaireAnswer.QUESTION_ID: "bb2ce7f9-649a-4254-9029-7b132b58ed97",
                    QuestionnaireAnswer.QUESTION: "Overall, how would you rate your health?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Chronic lung disease such as COPD, bronchitis or emphysema,Asthma,Heart disease such as previous heart attack or heart failure,Stroke,High blood pressure,Diabetes,Chronic kidney disease,Chronic liver disease,Cancer,Weakened immune system/reduced ability to deal with infections, such as HIV, chemotherapy or transplant,Anaemia,Condition affecting the brain and nerves such as dementia, Parkinson’s or multiple sclerosis,Depression,Anxiety,Psychiatric disorder,Recent major surgery in the last 2 weeks",
                    QuestionnaireAnswer.QUESTION_ID: "a2299a28-27e7-458c-8e3b-b63f964de43c",
                    QuestionnaireAnswer.QUESTION: "Do you have any of the following conditions? ",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "asdfasdf",
                    QuestionnaireAnswer.QUESTION_ID: "cf9d8d89-657a-4f90-8ff1-b7c2e46ca989",
                    QuestionnaireAnswer.QUESTION: "Please enter any other existing condition(s) that you have?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "No",
                    QuestionnaireAnswer.QUESTION_ID: "89de44ac-1647-4ae3-a91a-cdd1e7310de6",
                    QuestionnaireAnswer.QUESTION: "Are there any medical conditions that run in your family?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "No",
                    QuestionnaireAnswer.QUESTION_ID: "cd7972ce-fc56-4aa1-9cb4-23365ee45595",
                    QuestionnaireAnswer.QUESTION: "Do you have any allergies?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Persistent cough,Fever,Hoarseness (changes to the sound of your voice, particularly becoming strained),Non-persistent cough (not coughing continuously),Discharge or congestion in the nose,Sneezing,Sore throat,Feeling breathless,Wheeze (a whistling sound when breathing),Headache,Muscle aches,Unexplained tiredness,Being sick or feeling sick,Diarrhoea,Loss of taste or smell",
                    QuestionnaireAnswer.QUESTION_ID: "bfaa0cfa-9952-4347-89d1-c97ed3c9d953",
                    QuestionnaireAnswer.QUESTION: "In the last month have you experienced or are you still experiencing any possible COVID-19 symptoms?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: 'asdf.asddf.asdf.asddf.asddf(*&"$*&"(*&$(*"&$(*&"(*$&("*&$&(*&"&($*&"(*&$("$',
                    QuestionnaireAnswer.QUESTION_ID: "d7138d89-dbbe-4b8b-934a-ee76382b06c2",
                    QuestionnaireAnswer.QUESTION: "Please enter any other symptoms.",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "2009-07-16",
                    QuestionnaireAnswer.QUESTION_ID: "ebeb1822-3697-455b-8623-429b7c69054d",
                    QuestionnaireAnswer.QUESTION: "When did your possible COVID-19 symptoms start?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Had close contact with an individual who was confirmed with the diagnosis of COVID-19",
                    QuestionnaireAnswer.QUESTION_ID: "4f638b20-31fb-4b78-b9db-3906ee175bf1",
                    QuestionnaireAnswer.QUESTION: "In the past month or since first onset of your possible COVID-19 symptoms have you:",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "I live with family",
                    QuestionnaireAnswer.QUESTION_ID: "44b599b8-e665-48e4-8cd5-92dab32eb52f",
                    QuestionnaireAnswer.QUESTION: "Please select which best describes your living situation",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "No, I feel well enough to do all of my usual daily activities",
                    QuestionnaireAnswer.QUESTION_ID: "b7461478-c7cc-45b3-ac5a-2d82f0cf5bd6",
                    QuestionnaireAnswer.QUESTION: "How are you feeling physically right now?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Decreased",
                    QuestionnaireAnswer.QUESTION_ID: "1dbb4b98-74af-4470-8e37-34d456e01fe5",
                    QuestionnaireAnswer.QUESTION: "Overall physical activity",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "0690cb3f-45e5-4337-a0fc-4483664216dd",
                    QuestionnaireAnswer.QUESTION: "Activity at home e.g. gardening or DIY (do-it-yourself activities)",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "ace842e9-6a34-408f-95ad-d53951f43524",
                    QuestionnaireAnswer.QUESTION: "Exercise habits e.g. walking or running for pleasure",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "29dc00d5-4bb5-4f14-b1ad-495bc58f4fea",
                    QuestionnaireAnswer.QUESTION: "Transport-related physical activity e.g. walking or cycling to/from the local shop or work",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "f164c235-93a6-4292-84cb-fa8e5c0d13de",
                    QuestionnaireAnswer.QUESTION: "Work-related physical activity e.g. amount of walking or lifting",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "4dc8a282-cdec-400c-aa5f-ce1e91c5c72a",
                    QuestionnaireAnswer.QUESTION: "Time spent sitting",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "51bfe895-2517-4edd-a156-fe3c0d57d744",
                    QuestionnaireAnswer.QUESTION: "Time spent sleeping",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "6258dd65-a236-4d7d-a4d0-f6c8a4cbe224",
                    QuestionnaireAnswer.QUESTION: "Meat – red and processed e.g. beef, pork, lamb, burger, bacon or sausages",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "1c09bfb0-2dba-4135-8f49-da60d68b184b",
                    QuestionnaireAnswer.QUESTION: "Fish or seafood (fresh, frozen or tinned)",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "e58703f7-cc99-4950-ac90-c072e0f10b49",
                    QuestionnaireAnswer.QUESTION: "Dairy products e.g. yoghurt, cheese or milk",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Decreased",
                    QuestionnaireAnswer.QUESTION_ID: "6502453f-60e8-4d07-a916-6eec06b6ce9f",
                    QuestionnaireAnswer.QUESTION: "Fruits (fresh, frozen, tinned or dried)",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Decreased",
                    QuestionnaireAnswer.QUESTION_ID: "32c011c4-c61a-44f8-9311-a5fe019efada",
                    QuestionnaireAnswer.QUESTION: "Vegetables or beans / legumes (fresh, frozen or tinned); NOT including potatoes",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "46bb8682-ffae-4c01-8c9c-b85f6d9550dd",
                    QuestionnaireAnswer.QUESTION: "Savoury or sweet snacks e.g. crisps, confectionary, biscuits or cakes",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Increased",
                    QuestionnaireAnswer.QUESTION_ID: "ec0bb308-1f9c-4208-8b9a-c7112cf9e0b9",
                    QuestionnaireAnswer.QUESTION: "Wine",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Decreased",
                    QuestionnaireAnswer.QUESTION_ID: "89363249-dcda-4b19-98f2-70000d018e11",
                    QuestionnaireAnswer.QUESTION: "Beer, lager, cider, or spirits e.g. gin, vodka or whisky",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "eec63fc3-791c-442f-ba1c-7ce472e7dd71",
                    QuestionnaireAnswer.QUESTION: "Sweetened drinks e.g. cola, lemonade, cordial, juice or tea/coffee with added sugar",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Unchanged",
                    QuestionnaireAnswer.QUESTION_ID: "dddb332e-baa0-4e75-b265-116e9ebc0d8b",
                    QuestionnaireAnswer.QUESTION: "Fresh foods (rather than long-life or tinned/frozen foods and drinks) e.g. fresh vegetables, fruits or fresh milk",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "More than 5 times",
                    QuestionnaireAnswer.QUESTION_ID: "9a1dfea2-737d-4f73-887c-022297366d09",
                    QuestionnaireAnswer.QUESTION: "In the last 7 days how often have you consumed take-away or home-delivery meals?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "More than 5 times",
                    QuestionnaireAnswer.QUESTION_ID: "6e5a2623-f628-4097-808f-a5de449b919c",
                    QuestionnaireAnswer.QUESTION: "In the last 7 days how often did you consume meals made at home?",
                },
                {
                    QuestionnaireAnswer.ANSWER_TEXT: "Understood, I will enter them in the medication tracker",
                    QuestionnaireAnswer.QUESTION_ID: "8cfad741-a3dd-4fff-a8dc-6852542adf74",
                    QuestionnaireAnswer.QUESTION: "Are you on any regular medication(s) or supplements (nutrition or other supplements)?",
                },
            ],
            Questionnaire.QUESTIONNAIRE_ID: "f4c2f219-e0c5-462f-afc3-e8955cb2dae8",
            Questionnaire.QUESTIONNAIRE_NAME: "Baseline COVID-19 Questionnaire",
        }
    )


def sample_splitted_baseline_questionnaire_answers():
    return [
        {
            QuestionnaireAnswer.ANSWER_TEXT: "45.0",
            QuestionnaireAnswer.QUESTION_ID: "6040287a-1126-48ff-9675-9785d4b742f2",
            QuestionnaireAnswer.QUESTION: "What is your age in years?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "45.0",
            QuestionnaireAnswer.QUESTION_ID: "9a848031-134d-47d2-9cb8-2f0e667567ac",
            QuestionnaireAnswer.QUESTION: "What is your height, in cm?",
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "4c8c1265-770c-48af-8e16-524afb86abae",
            QuestionnaireAnswer.QUESTION: "What is your sex?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Male", "selected": True},
                {"text": "Female", "selected": False},
                {"text": "Prefer not to say", "selected": False},
                {"text": "Other", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
            QuestionnaireAnswer.QUESTION_ID: "a1c39177-ab08-4e19-bc9a-990c9fb0f315",
            QuestionnaireAnswer.QUESTION: "Have you had a test for COVID-19?",
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "08071fdc-93e8-49d9-b9f3-2a4278d0673c",
            QuestionnaireAnswer.QUESTION: "Did you test positive for COVID-19?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Yes", "selected": True},
                {"text": "No", "selected": False},
                {"text": "Waiting for results", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "abbad5fd-0e03-479b-af9b-8371d48dd857",
            QuestionnaireAnswer.QUESTION: "Have you ever smoked?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Yes, I still do", "selected": True},
                {"text": "Yes, but I quit", "selected": False},
                {"text": "No", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "f4cdeaee-be18-4cf4-b2ee-13ce47c10f71",
            QuestionnaireAnswer.QUESTION: "Roughly how many cigarettes do you smoke a day?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "1 to 10", "selected": False},
                {"text": "10 to 20", "selected": False},
                {"text": "More than 20", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "6d3d7560-e9ee-44c3-816f-5c1047edf6b3",
            QuestionnaireAnswer.QUESTION: "For how many years have you been a smoker?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Less than 1 year", "selected": False},
                {"text": "1 to 5 years", "selected": False},
                {"text": "6 to 10 years", "selected": False},
                {"text": "11 to 15 years", "selected": False},
                {"text": "More than 15 years", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
            QuestionnaireAnswer.QUESTION: "Have you ever vaped?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Yes, I still do", "selected": True},
                {"text": "Yes, but I quit", "selected": False},
                {"text": "No", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "62220451-f356-4ae1-b1d0-1420843186c4",
            QuestionnaireAnswer.QUESTION: "How often do you vape?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Rarely", "selected": False},
                {"text": "Occasionally", "selected": False},
                {"text": "Often", "selected": False},
                {"text": "Regularly", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "3cbcaf66-e762-4947-b13e-36ec00e491dc",
            QuestionnaireAnswer.QUESTION: "How many years have you vaped?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Less than 1 year", "selected": False},
                {"text": "1 to 5 years", "selected": False},
                {"text": "6 to 10 years", "selected": False},
                {"text": "11 to 15 years", "selected": False},
                {"text": "More than 15 years", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "bb2ce7f9-649a-4254-9029-7b132b58ed97",
            QuestionnaireAnswer.QUESTION: "Overall, how would you rate your health?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Poor", "selected": False},
                {"text": "Fair", "selected": False},
                {"text": "Good", "selected": False},
                {"text": "Excellent", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "a2299a28-27e7-458c-8e3b-b63f964de43c",
            QuestionnaireAnswer.QUESTION: "Do you have any of the following conditions? ",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {
                    "text": "Chronic lung disease such as COPD, bronchitis or emphysema",
                    "selected": True,
                },
                {"text": "Asthma", "selected": True},
                {
                    "text": "Heart disease such as previous heart attack or heart failure",
                    "selected": True,
                },
                {"text": "Stroke", "selected": True},
                {"text": "High blood pressure", "selected": True},
                {"text": "Diabetes", "selected": True},
                {"text": "Chronic kidney disease", "selected": True},
                {"text": "Chronic liver disease", "selected": True},
                {"text": "Cancer", "selected": True},
                {
                    "text": "Weakened immune system/reduced ability to deal with infections, such as HIV, chemotherapy or transplant",
                    "selected": True,
                },
                {"text": "Anaemia", "selected": True},
                {
                    "text": "Condition affecting the brain and nerves such as dementia, Parkinson’s or multiple sclerosis",
                    "selected": True,
                },
                {"text": "Depression", "selected": True},
                {"text": "Anxiety", "selected": True},
                {"text": "Psychiatric disorder", "selected": True},
                {"text": "Recent major surgery in the last 2 weeks", "selected": True},
                {"text": "Other", "selected": False},
                {"text": "None of these apply to me", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "asdfasdf",
            QuestionnaireAnswer.QUESTION_ID: "cf9d8d89-657a-4f90-8ff1-b7c2e46ca989",
            QuestionnaireAnswer.QUESTION: "Please enter any other existing condition(s) that you have?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "No",
            QuestionnaireAnswer.QUESTION_ID: "89de44ac-1647-4ae3-a91a-cdd1e7310de6",
            QuestionnaireAnswer.QUESTION: "Are there any medical conditions that run in your family?",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "No",
            QuestionnaireAnswer.QUESTION_ID: "cd7972ce-fc56-4aa1-9cb4-23365ee45595",
            QuestionnaireAnswer.QUESTION: "Do you have any allergies?",
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "bfaa0cfa-9952-4347-89d1-c97ed3c9d953",
            QuestionnaireAnswer.QUESTION: "In the last month have you experienced or are you still experiencing any possible COVID-19 symptoms?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Persistent cough", "selected": True},
                {"text": "Fever", "selected": True},
                {
                    "text": "Hoarseness (changes to the sound of your voice, particularly becoming strained)",
                    "selected": True,
                },
                {
                    "text": "Non-persistent cough (not coughing continuously)",
                    "selected": True,
                },
                {"text": "Discharge or congestion in the nose", "selected": True},
                {"text": "Sneezing", "selected": True},
                {"text": "Sore throat", "selected": True},
                {"text": "Feeling breathless", "selected": True},
                {"text": "Wheeze (a whistling sound when breathing)", "selected": True},
                {"text": "Headache", "selected": True},
                {"text": "Muscle aches", "selected": True},
                {"text": "Unexplained tiredness", "selected": True},
                {"text": "Being sick or feeling sick", "selected": True},
                {"text": "Diarrhoea", "selected": True},
                {"text": "Loss of taste or smell", "selected": True},
                {"text": "Other", "selected": False},
                {"text": "No symptoms", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: 'asdf.asddf.asdf.asddf.asddf(*&"$*&"(*&$(*"&$(*&"(*$&("*&$&(*&"&($*&"(*&$("$',
            QuestionnaireAnswer.QUESTION_ID: "d7138d89-dbbe-4b8b-934a-ee76382b06c2",
            QuestionnaireAnswer.QUESTION: "Please enter any other symptoms.",
        },
        {
            QuestionnaireAnswer.ANSWER_TEXT: "2009-07-16",
            QuestionnaireAnswer.QUESTION_ID: "ebeb1822-3697-455b-8623-429b7c69054d",
            QuestionnaireAnswer.QUESTION: "When did your possible COVID-19 symptoms start?",
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "4f638b20-31fb-4b78-b9db-3906ee175bf1",
            QuestionnaireAnswer.QUESTION: "In the past month or since first onset of your possible COVID-19 symptoms have you:",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {
                    "text": "Had close contact with an individual who was confirmed with the diagnosis of COVID-19",
                    "selected": True,
                },
                {
                    "text": "Had close contact with an individual with signs or symptoms of fever, cough, chest infection",
                    "selected": False,
                },
                {"text": "None of the above apply to me", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "44b599b8-e665-48e4-8cd5-92dab32eb52f",
            QuestionnaireAnswer.QUESTION: "Please select which best describes your living situation",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "I live alone", "selected": False},
                {"text": "I live with family", "selected": True},
                {"text": "I live with friends/partner", "selected": False},
                {"text": "I live with a carer", "selected": False},
                {"text": "I am a live-in carer", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "b7461478-c7cc-45b3-ac5a-2d82f0cf5bd6",
            QuestionnaireAnswer.QUESTION: "How are you feeling physically right now?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {
                    "text": "No, I feel well enough to do all of my usual daily activities",
                    "selected": True,
                },
                {
                    "text": "No, I feel well enough to do most of my usual daily activities",
                    "selected": False,
                },
                {
                    "text": "I feel unwell but can still do some of my usual daily activities",
                    "selected": False,
                },
                {
                    "text": "Yes, I’ve stopped doing everything I usually do",
                    "selected": False,
                },
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "1dbb4b98-74af-4470-8e37-34d456e01fe5",
            QuestionnaireAnswer.QUESTION: "Overall physical activity",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": True},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "0690cb3f-45e5-4337-a0fc-4483664216dd",
            QuestionnaireAnswer.QUESTION: "Activity at home e.g. gardening or DIY (do-it-yourself activities)",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "ace842e9-6a34-408f-95ad-d53951f43524",
            QuestionnaireAnswer.QUESTION: "Exercise habits e.g. walking or running for pleasure",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "29dc00d5-4bb5-4f14-b1ad-495bc58f4fea",
            QuestionnaireAnswer.QUESTION: "Transport-related physical activity e.g. walking or cycling to/from the local shop or work",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "f164c235-93a6-4292-84cb-fa8e5c0d13de",
            QuestionnaireAnswer.QUESTION: "Work-related physical activity e.g. amount of walking or lifting",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "4dc8a282-cdec-400c-aa5f-ce1e91c5c72a",
            QuestionnaireAnswer.QUESTION: "Time spent sitting",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "51bfe895-2517-4edd-a156-fe3c0d57d744",
            QuestionnaireAnswer.QUESTION: "Time spent sleeping",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "6258dd65-a236-4d7d-a4d0-f6c8a4cbe224",
            QuestionnaireAnswer.QUESTION: "Meat – red and processed e.g. beef, pork, lamb, burger, bacon or sausages",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "1c09bfb0-2dba-4135-8f49-da60d68b184b",
            QuestionnaireAnswer.QUESTION: "Fish or seafood (fresh, frozen or tinned)",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "e58703f7-cc99-4950-ac90-c072e0f10b49",
            QuestionnaireAnswer.QUESTION: "Dairy products e.g. yoghurt, cheese or milk",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "6502453f-60e8-4d07-a916-6eec06b6ce9f",
            QuestionnaireAnswer.QUESTION: "Fruits (fresh, frozen, tinned or dried)",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": True},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "32c011c4-c61a-44f8-9311-a5fe019efada",
            QuestionnaireAnswer.QUESTION: "Vegetables or beans / legumes (fresh, frozen or tinned); NOT including potatoes",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": True},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "46bb8682-ffae-4c01-8c9c-b85f6d9550dd",
            QuestionnaireAnswer.QUESTION: "Savoury or sweet snacks e.g. crisps, confectionary, biscuits or cakes",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "ec0bb308-1f9c-4208-8b9a-c7112cf9e0b9",
            QuestionnaireAnswer.QUESTION: "Wine",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": True},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "89363249-dcda-4b19-98f2-70000d018e11",
            QuestionnaireAnswer.QUESTION: "Beer, lager, cider, or spirits e.g. gin, vodka or whisky",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": True},
                {"text": "Unchanged", "selected": False},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "eec63fc3-791c-442f-ba1c-7ce472e7dd71",
            QuestionnaireAnswer.QUESTION: "Sweetened drinks e.g. cola, lemonade, cordial, juice or tea/coffee with added sugar",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "dddb332e-baa0-4e75-b265-116e9ebc0d8b",
            QuestionnaireAnswer.QUESTION: "Fresh foods (rather than long-life or tinned/frozen foods and drinks) e.g. fresh vegetables, fruits or fresh milk",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Decreased", "selected": False},
                {"text": "Unchanged", "selected": True},
                {"text": "Increased", "selected": False},
                {"text": "Not Applicable", "selected": False},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "9a1dfea2-737d-4f73-887c-022297366d09",
            QuestionnaireAnswer.QUESTION: "In the last 7 days how often have you consumed take-away or home-delivery meals?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Never", "selected": False},
                {"text": "1-2 times", "selected": False},
                {"text": "3-5 times", "selected": False},
                {"text": "More than 5 times", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "6e5a2623-f628-4097-808f-a5de449b919c",
            QuestionnaireAnswer.QUESTION: "In the last 7 days how often did you consume meals made at home?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {"text": "Never", "selected": False},
                {"text": "1-2 times", "selected": False},
                {"text": "3-5 times", "selected": False},
                {"text": "More than 5 times", "selected": True},
            ],
        },
        {
            QuestionnaireAnswer.QUESTION_ID: "8cfad741-a3dd-4fff-a8dc-6852542adf74",
            QuestionnaireAnswer.QUESTION: "Are you on any regular medication(s) or supplements (nutrition or other supplements)?",
            QuestionnaireAnswer.ANSWER_CHOICES: [
                {
                    "text": "Understood, I will enter them in the medication tracker",
                    "selected": True,
                }
            ],
        },
    ]


def sample_baseline_questionnaire_module_config() -> ModuleConfig:
    return ModuleConfig.from_dict(
        {
            ModuleConfig.ID: "5f68a280dfd88db0d721963a",
            ModuleConfig.UPDATE_DATE_TIME: "2020-12-10T16:24:57.954000Z",
            ModuleConfig.CREATE_DATE_TIME: "2020-07-29T20:53:54.231000Z",
            ModuleConfig.MODULE_ID: "Questionnaire",
            ModuleConfig.MODULE_NAME: "",
            ModuleConfig.STATUS: "ENABLED",
            ModuleConfig.CONFIG_BODY: {
                "id": "f4c2f219-e0c5-462f-afc3-e8955cb2dae8",
                "name": "Baseline COVID-19 Questionnaire",
                "isForManager": False,
                "publisherName": "AB",
                "isOnboarding": True,
                "pages": [
                    {
                        "type": "INFO",
                        "id": "ef0969b8-7e52-45d5-8c6f-90ecc48ffce81",
                        "order": 1,
                        "text": "Welcome to the Huma app. Thank you for participating in the Fenland COVID-19 study. We would first like to know some information about you.",
                        "description": "Please scroll up and tap if you would like to change any answers",
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "6040287a-1126-48ff-9675-9785d4b742f2",
                                "required": True,
                                "format": "NUMERIC",
                                "order": 1,
                                "text": "What is your age in years?",
                            }
                        ],
                        "order": 2,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "9a848031-134d-47d2-9cb8-2f0e667567ac",
                                "required": True,
                                "format": "NUMERIC",
                                "order": 1,
                                "text": "What is your height, in cm?",
                            }
                        ],
                        "order": 3,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "neq": 1,
                                                    QuestionnaireAnswer.QUESTION_ID: "4c8c1265-770c-48af-8e16-524afb86abae",
                                                }
                                            ],
                                            "jumpToId": "a1c39177-ab08-4e19-bc9a-990c9fb0f315",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "4c8c1265-770c-48af-8e16-524afb86abae",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "What is your sex?",
                                "userProfileFieldToUpdate": "gender",
                                "options": [
                                    {"label": "Male", "value": "0", "weight": 1},
                                    {"label": "Female", "value": "1", "weight": 2},
                                    {
                                        "label": "Prefer not to say",
                                        "value": "2",
                                        "weight": 3,
                                    },
                                    {"label": "Other", "value": "3", "weight": 4},
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
                                "id": "eb4fd7cf-a425-45d5-b17b-c62f808da7f3",
                                "required": True,
                                "format": "BOOLEAN",
                                "order": 1,
                                "text": "Are you pregnant?",
                            }
                        ],
                        "order": 5,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": "false",
                                                    QuestionnaireAnswer.QUESTION_ID: "a1c39177-ab08-4e19-bc9a-990c9fb0f315",
                                                }
                                            ],
                                            "jumpToId": "abbad5fd-0e03-479b-af9b-8371d48dd857",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "a1c39177-ab08-4e19-bc9a-990c9fb0f315",
                                "required": True,
                                "format": "BOOLEAN",
                                "order": 1,
                                "text": "Have you had a test for COVID-19?",
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
                                "id": "08071fdc-93e8-49d9-b9f3-2a4278d0673c",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Did you test positive for COVID-19?",
                                "options": [
                                    {"label": "Yes", "value": "0", "weight": 1},
                                    {"label": "No", "value": "1", "weight": 2},
                                    {
                                        "label": "Waiting for results",
                                        "value": "2",
                                        "weight": 3,
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
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 2,
                                                    QuestionnaireAnswer.QUESTION_ID: "abbad5fd-0e03-479b-af9b-8371d48dd857",
                                                }
                                            ],
                                            "jumpToId": "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                                        },
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 1,
                                                    QuestionnaireAnswer.QUESTION_ID: "abbad5fd-0e03-479b-af9b-8371d48dd857",
                                                }
                                            ],
                                            "jumpToId": "41cee8e6-b866-48d1-8b2b-dc71d0c88b5b",
                                        },
                                    ],
                                },
                                "description": "",
                                "id": "abbad5fd-0e03-479b-af9b-8371d48dd857",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Have you ever smoked?",
                                "options": [
                                    {
                                        "label": "Yes, I still do",
                                        "value": "0",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "Yes, but I quit",
                                        "value": "1",
                                        "weight": 2,
                                    },
                                    {"label": "No", "value": "2", "weight": 3},
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
                                "id": "f4cdeaee-be18-4cf4-b2ee-13ce47c10f71",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Roughly how many cigarettes do you smoke a day?",
                                "options": [
                                    {"label": "1 to 10", "value": "0", "weight": 1},
                                    {"label": "10 to 20", "value": "1", "weight": 2},
                                    {
                                        "label": "More than 20",
                                        "value": "2",
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
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 0,
                                                    QuestionnaireAnswer.QUESTION_ID: "6d3d7560-e9ee-44c3-816f-5c1047edf6b3",
                                                },
                                                {
                                                    "neq": 0,
                                                    QuestionnaireAnswer.QUESTION_ID: "6d3d7560-e9ee-44c3-816f-5c1047edf6b3",
                                                },
                                            ],
                                            "jumpToId": "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "6d3d7560-e9ee-44c3-816f-5c1047edf6b3",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "For how many years have you been a smoker?",
                                "options": [
                                    {
                                        "label": "Less than 1 year",
                                        "value": "0",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "1 to 5 years",
                                        "value": "1",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "6 to 10 years",
                                        "value": "2",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "11 to 15 years",
                                        "value": "3",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "More than 15 years",
                                        "value": "4",
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
                                "id": "41cee8e6-b866-48d1-8b2b-dc71d0c88b5b",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "How long ago did you quit?",
                                "options": [
                                    {
                                        "label": "Less than 1 year",
                                        "value": "0",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "1 to 5 years",
                                        "value": "1",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "6 to 10 years",
                                        "value": "2",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "11 to 15 years",
                                        "value": "3",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "More than 15 years",
                                        "value": "4",
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
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 1,
                                                    QuestionnaireAnswer.QUESTION_ID: "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                                                }
                                            ],
                                            "jumpToId": "213cfd6e-4ee3-4ac9-b1a4-31c69d324ca2",
                                        },
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 2,
                                                    QuestionnaireAnswer.QUESTION_ID: "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                                                }
                                            ],
                                            "jumpToId": "bb2ce7f9-649a-4254-9029-7b132b58ed97",
                                        },
                                    ],
                                },
                                "description": "",
                                "id": "fb84e8f6-9ae2-46e2-b703-c8b99d6359b0",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Have you ever vaped?",
                                "options": [
                                    {
                                        "label": "Yes, I still do",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "Yes, but I quit",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {"label": "No", "value": "2", "weight": 2},
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
                                "id": "62220451-f356-4ae1-b1d0-1420843186c4",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "How often do you vape?",
                                "options": [
                                    {"label": "Rarely", "value": "0", "weight": 0},
                                    {
                                        "label": "Occasionally",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {"label": "Often", "value": "2", "weight": 2},
                                    {"label": "Regularly", "value": "3", "weight": 3},
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
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 0,
                                                    QuestionnaireAnswer.QUESTION_ID: "3cbcaf66-e762-4947-b13e-36ec00e491dc",
                                                },
                                                {
                                                    "neq": 0,
                                                    QuestionnaireAnswer.QUESTION_ID: "3cbcaf66-e762-4947-b13e-36ec00e491dc",
                                                },
                                            ],
                                            "jumpToId": "bb2ce7f9-649a-4254-9029-7b132b58ed97",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "3cbcaf66-e762-4947-b13e-36ec00e491dc",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "How many years have you vaped?",
                                "options": [
                                    {
                                        "label": "Less than 1 year",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "1 to 5 years",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "6 to 10 years",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "11 to 15 years",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "More than 15 years",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 14,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "213cfd6e-4ee3-4ac9-b1a4-31c69d324ca2",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "How long ago did you quit vaping?",
                                "options": [
                                    {
                                        "label": "Less than 1 year",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "1 to 5 years",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "6 to 10 years",
                                        "value": "2",
                                        "weight": 2,
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
                                "id": "bb2ce7f9-649a-4254-9029-7b132b58ed97",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Overall, how would you rate your health?",
                                "options": [
                                    {"label": "Poor", "value": "0", "weight": 0},
                                    {"label": "Fair", "value": "1", "weight": 1},
                                    {"label": "Good", "value": "2", "weight": 2},
                                    {"label": "Excellent", "value": "3", "weight": 3},
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
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 17,
                                                    QuestionnaireAnswer.QUESTION_ID: "a2299a28-27e7-458c-8e3b-b63f964de43c",
                                                }
                                            ],
                                            "jumpToId": "89de44ac-1647-4ae3-a91a-cdd1e7310de6",
                                        }
                                    ],
                                },
                                "description": " Select all which apply:",
                                "id": "a2299a28-27e7-458c-8e3b-b63f964de43c",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Do you have any of the following conditions? ",
                                "options": [
                                    {
                                        "label": "Chronic lung disease such as COPD, bronchitis or emphysema",
                                        "value": "0",
                                        "weight": 1,
                                    },
                                    {"label": "Asthma", "value": "1", "weight": 2},
                                    {
                                        "label": "Heart disease such as previous heart attack or heart failure",
                                        "value": "2",
                                        "weight": 3,
                                    },
                                    {"label": "Stroke", "value": "3", "weight": 4},
                                    {
                                        "label": "High blood pressure",
                                        "value": "4",
                                        "weight": 5,
                                    },
                                    {"label": "Diabetes", "value": "5", "weight": 6},
                                    {
                                        "label": "Chronic kidney disease",
                                        "value": "6",
                                        "weight": 7,
                                    },
                                    {
                                        "label": "Chronic liver disease",
                                        "value": "7",
                                        "weight": 8,
                                    },
                                    {"label": "Cancer", "value": "8", "weight": 9},
                                    {
                                        "label": "Weakened immune system/reduced ability to deal with infections, such as HIV, chemotherapy or transplant",
                                        "value": "9",
                                        "weight": 10,
                                    },
                                    {"label": "Anaemia", "value": "10", "weight": 11},
                                    {
                                        "label": "Condition affecting the brain and nerves such as dementia, Parkinson’s or multiple sclerosis",
                                        "value": "11",
                                        "weight": 12,
                                    },
                                    {
                                        "label": "Depression",
                                        "value": "12",
                                        "weight": 13,
                                    },
                                    {"label": "Anxiety", "value": "13", "weight": 14},
                                    {
                                        "label": "Psychiatric disorder",
                                        "value": "14",
                                        "weight": 15,
                                    },
                                    {
                                        "label": "Recent major surgery in the last 2 weeks",
                                        "value": "15",
                                        "weight": 16,
                                    },
                                    {"label": "Other", "value": "16", "weight": 17},
                                    {
                                        "label": "None of these apply to me",
                                        "value": "17",
                                        "weight": 18,
                                    },
                                ],
                                "selectionCriteria": "MULTIPLE",
                            }
                        ],
                        "order": 17,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "If you have more than one please separate them with a full stop.",
                                "id": "cf9d8d89-657a-4f90-8ff1-b7c2e46ca989",
                                "required": False,
                                "format": "TEXT",
                                "order": 1,
                                "text": "Please enter any other existing condition(s) that you have?",
                            }
                        ],
                        "order": 18,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": "false",
                                                    QuestionnaireAnswer.QUESTION_ID: "89de44ac-1647-4ae3-a91a-cdd1e7310de6",
                                                }
                                            ],
                                            "jumpToId": "cd7972ce-fc56-4aa1-9cb4-23365ee45595",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "89de44ac-1647-4ae3-a91a-cdd1e7310de6",
                                "required": True,
                                "format": "BOOLEAN",
                                "order": 1,
                                "text": "Are there any medical conditions that run in your family?",
                            }
                        ],
                        "order": 19,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "If you have more than one please separate them with a full stop.",
                                "id": "9700b697-62cf-4f9f-be46-3a9d63e92685",
                                "required": True,
                                "format": "TEXT",
                                "order": 1,
                                "text": "Please list any medical conditions that run in your family?",
                            }
                        ],
                        "order": 20,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": "false",
                                                    QuestionnaireAnswer.QUESTION_ID: "cd7972ce-fc56-4aa1-9cb4-23365ee45595",
                                                }
                                            ],
                                            "jumpToId": "bfaa0cfa-9952-4347-89d1-c97ed3c9d953",
                                        }
                                    ],
                                },
                                "description": "",
                                "id": "cd7972ce-fc56-4aa1-9cb4-23365ee45595",
                                "required": True,
                                "format": "BOOLEAN",
                                "order": 1,
                                "text": "Do you have any allergies?",
                            }
                        ],
                        "order": 21,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "If you have more than one please separate them with a full stop.",
                                "id": "eb7d84e1-b43a-4307-bbad-10b6619c5e4b",
                                "required": True,
                                "format": "TEXT",
                                "order": 1,
                                "text": "Please list your allergies.",
                            }
                        ],
                        "order": 22,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {
                                    "isEnabled": True,
                                    "rules": [
                                        {
                                            "anyOf": [
                                                {
                                                    "eq": 16,
                                                    "questionId": "bfaa0cfa-9952-4347-89d1-c97ed3c9d953",
                                                }
                                            ],
                                            "jumpToId": "4f638b20-31fb-4b78-b9db-3906ee175bf1",
                                        }
                                    ],
                                },
                                "description": "Please select those which apply: \n",
                                "id": "bfaa0cfa-9952-4347-89d1-c97ed3c9d953",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "In the last month have you experienced or are you still experiencing any possible COVID-19 symptoms?",
                                "options": [
                                    {
                                        "label": "Persistent cough",
                                        "value": "0",
                                        "weight": 1,
                                    },
                                    {"label": "Fever", "value": "1", "weight": 2},
                                    {
                                        "label": "Hoarseness (changes to the sound of your voice, particularly becoming strained)",
                                        "value": "2",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "Non-persistent cough (not coughing continuously)",
                                        "value": "3",
                                        "weight": 4,
                                    },
                                    {
                                        "label": "Discharge or congestion in the nose",
                                        "value": "4",
                                        "weight": 5,
                                    },
                                    {"label": "Sneezing", "value": "5", "weight": 6},
                                    {"label": "Sore throat", "value": "6", "weight": 7},
                                    {
                                        "label": "Feeling breathless",
                                        "value": "7",
                                        "weight": 8,
                                    },
                                    {
                                        "label": "Wheeze (a whistling sound when breathing)",
                                        "value": "8",
                                        "weight": 9,
                                    },
                                    {"label": "Headache", "value": "9", "weight": 10},
                                    {
                                        "label": "Muscle aches",
                                        "value": "10",
                                        "weight": 11,
                                    },
                                    {
                                        "label": "Unexplained tiredness",
                                        "value": "11",
                                        "weight": 12,
                                    },
                                    {
                                        "label": "Being sick or feeling sick",
                                        "value": "12",
                                        "weight": 13,
                                    },
                                    {"label": "Diarrhoea", "value": "13", "weight": 14},
                                    {
                                        "label": "Loss of taste or smell",
                                        "value": "14",
                                        "weight": 15,
                                    },
                                    {"label": "Other", "value": "15", "weight": 16},
                                    {
                                        "label": "No symptoms",
                                        "value": "16",
                                        "weight": 17,
                                    },
                                ],
                                "selectionCriteria": "MULTIPLE",
                            }
                        ],
                        "order": 23,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "If you have more than one please separate them with a full stop.",
                                "id": "d7138d89-dbbe-4b8b-934a-ee76382b06c2",
                                "required": False,
                                "format": "TEXT",
                                "order": 1,
                                "text": "Please enter any other symptoms.",
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
                                "id": "ebeb1822-3697-455b-8623-429b7c69054d",
                                "required": True,
                                "format": "DATE",
                                "order": 1,
                                "text": "When did your possible COVID-19 symptoms start?",
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
                                "id": "4f638b20-31fb-4b78-b9db-3906ee175bf1",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "In the past month or since first onset of your possible COVID-19 symptoms have you:",
                                "options": [
                                    {
                                        "label": "Had close contact with an individual who was confirmed with the diagnosis of COVID-19",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "Had close contact with an individual with signs or symptoms of fever, cough, chest infection",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "None of the above apply to me",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 26,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "44b599b8-e665-48e4-8cd5-92dab32eb52f",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Please select which best describes your living situation",
                                "options": [
                                    {
                                        "label": "I live alone",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "I live with family",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I live with friends/partner",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "I live with a carer",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                    {
                                        "label": "I am a live-in carer",
                                        "value": "4",
                                        "weight": 4,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 27,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "Are you so ill that you've stopped doing all of your usual daily activities, such as watch TV, use your phone, read or get out of bed?",
                                "id": "b7461478-c7cc-45b3-ac5a-2d82f0cf5bd6",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "How are you feeling physically right now?",
                                "options": [
                                    {
                                        "label": "No, I feel well enough to do all of my usual daily activities",
                                        "value": "0",
                                        "weight": 0,
                                    },
                                    {
                                        "label": "No, I feel well enough to do most of my usual daily activities",
                                        "value": "1",
                                        "weight": 1,
                                    },
                                    {
                                        "label": "I feel unwell but can still do some of my usual daily activities",
                                        "value": "2",
                                        "weight": 2,
                                    },
                                    {
                                        "label": "Yes, I’ve stopped doing everything I usually do",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 28,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has your activity changed compared to before the COVID-19 virus outbreak?",
                                "id": "1dbb4b98-74af-4470-8e37-34d456e01fe5",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Overall physical activity",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 29,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has your activity changed compared to before the COVID-19 virus outbreak?",
                                "id": "0690cb3f-45e5-4337-a0fc-4483664216dd",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Activity at home e.g. gardening or DIY (do-it-yourself activities)",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 30,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has your activity changed compared to before the COVID-19 virus outbreak?",
                                "id": "ace842e9-6a34-408f-95ad-d53951f43524",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Exercise habits e.g. walking or running for pleasure",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 31,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has your activity changed compared to before the COVID-19 virus outbreak?",
                                "id": "29dc00d5-4bb5-4f14-b1ad-495bc58f4fea",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Transport-related physical activity e.g. walking or cycling to/from the local shop or work",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 32,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has your activity changed compared to before the COVID-19 virus outbreak?",
                                "id": "f164c235-93a6-4292-84cb-fa8e5c0d13de",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Work-related physical activity e.g. amount of walking or lifting",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 33,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this changed compared to before the COVID-19 virus outbreak?",
                                "id": "4dc8a282-cdec-400c-aa5f-ce1e91c5c72a",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Time spent sitting",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 34,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this changed compared to before the COVID-19 virus outbreak?",
                                "id": "51bfe895-2517-4edd-a156-fe3c0d57d744",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Time spent sleeping",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 35,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "6258dd65-a236-4d7d-a4d0-f6c8a4cbe224",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Meat – red and processed e.g. beef, pork, lamb, burger, bacon or sausages",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 4,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 36,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "1c09bfb0-2dba-4135-8f49-da60d68b184b",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Fish or seafood (fresh, frozen or tinned)",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 37,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "e58703f7-cc99-4950-ac90-c072e0f10b49",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Dairy products e.g. yoghurt, cheese or milk",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 38,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "6502453f-60e8-4d07-a916-6eec06b6ce9f",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Fruits (fresh, frozen, tinned or dried)",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 3},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 4,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 39,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "32c011c4-c61a-44f8-9311-a5fe019efada",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Vegetables or beans / legumes (fresh, frozen or tinned); NOT including potatoes",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 40,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "46bb8682-ffae-4c01-8c9c-b85f6d9550dd",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Savoury or sweet snacks e.g. crisps, confectionary, biscuits or cakes",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 41,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "ec0bb308-1f9c-4208-8b9a-c7112cf9e0b9",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Wine",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 42,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "89363249-dcda-4b19-98f2-70000d018e11",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Beer, lager, cider, or spirits e.g. gin, vodka or whisky",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 43,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "eec63fc3-791c-442f-ba1c-7ce472e7dd71",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Sweetened drinks e.g. cola, lemonade, cordial, juice or tea/coffee with added sugar",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 44,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "In the last 7 days how has this part of your diet changed compared to before the COVID-19 virus outbreak?",
                                "id": "dddb332e-baa0-4e75-b265-116e9ebc0d8b",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Fresh foods (rather than long-life or tinned/frozen foods and drinks) e.g. fresh vegetables, fruits or fresh milk",
                                "options": [
                                    {"label": "Decreased", "value": "0", "weight": 0},
                                    {"label": "Unchanged", "value": "1", "weight": 1},
                                    {"label": "Increased", "value": "2", "weight": 2},
                                    {
                                        "label": "Not Applicable",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 45,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "9a1dfea2-737d-4f73-887c-022297366d09",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "In the last 7 days how often have you consumed take-away or home-delivery meals?",
                                "options": [
                                    {"label": "Never", "value": "0", "weight": 0},
                                    {"label": "1-2 times", "value": "1", "weight": 1},
                                    {"label": "3-5 times", "value": "2", "weight": 2},
                                    {
                                        "label": "More than 5 times",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 46,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "",
                                "id": "6e5a2623-f628-4097-808f-a5de449b919c",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "In the last 7 days how often did you consume meals made at home?",
                                "options": [
                                    {"label": "Never", "value": "0", "weight": 0},
                                    {"label": "1-2 times", "value": "1", "weight": 1},
                                    {"label": "3-5 times", "value": "2", "weight": 2},
                                    {
                                        "label": "More than 5 times",
                                        "value": "3",
                                        "weight": 3,
                                    },
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 47,
                    },
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "logic": {"isEnabled": False},
                                "description": "Please remember to log these in the medication tracker when you complete this questionnaire.  ",
                                "id": "8cfad741-a3dd-4fff-a8dc-6852542adf74",
                                "required": True,
                                "format": "TEXTCHOICE",
                                "order": 1,
                                "text": "Are you on any regular medication(s) or supplements (nutrition or other supplements)?",
                                "options": [
                                    {
                                        "label": "Understood, I will enter them in the medication tracker",
                                        "value": "0",
                                        "weight": 0,
                                    }
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                        "order": 48,
                    },
                ],
                "submissionPage": {
                    "description": "Scroll up to change any of your answers. Changing answers may add new questions.",
                    "id": "19c9cfcd-c87d-4bad-ba70-421bbd619962",
                    "text": "You’ve completed the questionnaire",
                    "buttonText": "Submit",
                    "order": 49,
                    "type": "SUBMISSION",
                },
            },
            ModuleConfig.ABOUT: "",
            ModuleConfig.RAG_THRESHOLDS: [],
            ModuleConfig.VERSION: 0,
        }
    )
