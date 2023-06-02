from datetime import datetime

from dateutil.relativedelta import relativedelta

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    HealthStatus,
    PregnancyStatus,
    AdditionalQoL,
    FeverAndPainDrugs,
    BackgroundInformation,
    InfantFollowUp,
    ChildrenItem,
    VaccinationDetails,
    BreastFeedingUpdate,
    BreastFeedingUpdateBabyDetails,
    BreastFeedingStatus,
    PregnancyUpdate,
    MedicalHistory,
    OtherVaccine,
    PregnancyFollowUp,
    PostVaccination,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionnaireMetadata,
    QuestionnaireAnswer,
)
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
    VALID_USER_ID,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_az_screening,
    sample_health_status,
    sample_pregnancy_status,
    sample_additional_qol,
    sample_fever_and_pain_drugs,
    sample_background_information,
    sample_infant_follow_up,
    sample_vaccination_details,
    sample_breastfeeding_update,
    sample_breastfeeding_status,
    sample_pregnancy_update,
    sample_medical_history,
    sample_other_vaccine,
    sample_pregnancy_follow_up,
    sample_post_vaccination,
)

from extensions.module_result.common.enums import (
    BabyGender,
    BeforeAfter,
    Employment,
    GenderIdentity,
    HealthIssueAction,
    MedicalDiagnosis,
    NewSymptomAction,
    Regularly,
    SmokingStatus,
    SmokingStopped,
    VaccineLocation,
    YesNoDont,
)
from sdk.common.utils.validators import utc_date_to_str


class ModuleResultBasicsTest(BaseModuleResultTest):
    NAME = "name"
    PRIMITIVE = "primitive"
    EXPECTED_RESULT_VALUE = "expectedResultValue"
    VALUE = "value"

    module_maps = {
        "HealthStatus": {
            NAME: "HealthStatus",
            PRIMITIVE: "HealthStatus",
            VALUE: sample_health_status(),
            EXPECTED_RESULT_VALUE: {
                HealthStatus.NEW_OR_WORSE_SYMPTOMS: NewSymptomAction.CONSULT_DOCTOR,
                HealthStatus.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: " How intense was your headache?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Severe",
                        }
                    ]
                },
            },
        },
        "PregnancyStatus": {
            NAME: "PregnancyStatus",
            PRIMITIVE: "PregnancyStatus",
            VALUE: sample_pregnancy_status(),
            EXPECTED_RESULT_VALUE: {
                PregnancyStatus.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                        }
                    ]
                },
            },
        },
        "AdditionalQoL": {
            NAME: "AdditionalQoL",
            PRIMITIVE: "AdditionalQoL",
            VALUE: sample_additional_qol(),
            EXPECTED_RESULT_VALUE: {
                AdditionalQoL.VIEW_FAMILY: Regularly.STRONGLY_DISAGREE,
                AdditionalQoL.CONTACT_PROFESSIONALS: Regularly.AGREE,
                AdditionalQoL.CONTRIBUTE_ACTIVITIES: Regularly.NEITHER_AGREE_DISAGREE,
                AdditionalQoL.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "30cad609-cd6a-418d-a1de-6eacfa3a2d9d",
                            QuestionnaireAnswer.QUESTION: "I am able to see my friends and family more in person",
                            QuestionnaireAnswer.ANSWER_TEXT: "AGREE",
                        }
                    ]
                },
            },
        },
        "FeverAndPainDrugs": {
            NAME: "FeverAndPainDrugs",
            PRIMITIVE: "FeverAndPainDrugs",
            VALUE: sample_fever_and_pain_drugs(),
            EXPECTED_RESULT_VALUE: {
                FeverAndPainDrugs.HAS_ANTI_FEVER_PAIN_DRUGS: True,
                FeverAndPainDrugs.MED_STARTED_BEFORE_AFTER: BeforeAfter.BEFORE,
                FeverAndPainDrugs.DAYS_BEFORE_VAC_MEDICATION: 4,
                FeverAndPainDrugs.DAYS_AFTER_VAC_MEDICATION: 5,
                FeverAndPainDrugs.IS_UNDER_MEDICATION: True,
                FeverAndPainDrugs.DAYS_COUNT_MEDICATION: 12,
                FeverAndPainDrugs.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "cf323797-9909-4500-933e-16854d2b0d77",
                            QuestionnaireAnswer.QUESTION: "In order to prevent/treat symptoms that could be related to vaccination, did you take any anti-fever or pain-relieving medication such as paracetamol (e.g. Doliprane or Dafalgan) or ibuprofen (e.g. Advil or Nurofen) within five days of your dose of COVID-19 vaccine?",
                            QuestionnaireAnswer.ANSWER_TEXT: "true",
                        }
                    ]
                },
            },
        },
        "BackgroundInformation": {
            NAME: "BackgroundInformation",
            PRIMITIVE: "BackgroundInformation",
            VALUE: sample_background_information(),
            EXPECTED_RESULT_VALUE: {
                BackgroundInformation.SEX_AT_BIRTH: BabyGender.MALE,
                BackgroundInformation.GENDER_IDENTITY: GenderIdentity.MALE,
                BackgroundInformation.RESIDENCY_COUNTRY: "Germany",
                BackgroundInformation.BIRTH_COUNTRY: "Germany",
                BackgroundInformation.EMPLOYMENT: Employment.STUDENT,
                BackgroundInformation.SMOKING_STATUS: SmokingStatus.FORMER,
                BackgroundInformation.SMOKING_STOPPED: SmokingStopped.ONE_TO_FIVE,
                BackgroundInformation.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                            QuestionnaireAnswer.QUESTION: "How old are you?",
                            QuestionnaireAnswer.ANSWER_TEXT: "19",
                        },
                    ]
                },
            },
        },
        "InfantFollowUp": {
            NAME: "InfantFollowUp",
            PRIMITIVE: "InfantFollowUp",
            VALUE: sample_infant_follow_up(),
            EXPECTED_RESULT_VALUE: {
                InfantFollowUp.IS_COV_PREG_LIVE_BIRTH: True,
                InfantFollowUp.CHILDREN: [
                    {
                        ChildrenItem.ISSUES: ["ADHD", "Cerebral Palsy"],
                        ChildrenItem.HAS_CHILD_DEVELOP_ISSUES: True,
                    }
                ],
                InfantFollowUp.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "fbeeb07a-64c4-409d-aac7-c929674022a1",
                            QuestionnaireAnswer.QUESTION: "Are you aware or has a medical doctor informed you of any developmental issues with your first child from this pregnancy?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                        }
                    ]
                },
            },
        },
        "VaccinationDetails": {
            NAME: "VaccinationDetails",
            PRIMITIVE: "VaccinationDetails",
            VALUE: sample_vaccination_details(),
            EXPECTED_RESULT_VALUE: {
                VaccinationDetails.VACCINATED_PLACE: VaccineLocation.HOSPITAL,
                VaccinationDetails.VACCINATION_LOCATION: "NHS",
                VaccinationDetails.VACCINATION_CITY: "London",
                VaccinationDetails.BATCH_NUMBER: "ABV3922",
                VaccinationDetails.IS_SECOND_DOSE_VACC: YesNoDont.YES,
                VaccinationDetails.IS_SEASON_FLU_VAC: False,
                VaccinationDetails.IS_OTHER_SPECIFIED_VACC: True,
                VaccinationDetails.IS_ALLERGIC_REACTION_VACC: YesNoDont.DONT_KNOW,
                VaccinationDetails.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "032db29f-363c-418f-b626-2fa21adcc557",
                            QuestionnaireAnswer.QUESTION: "Where were you vaccinated?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Hospital",
                        },
                        {
                            QuestionnaireAnswer.QUESTION_ID: "1d8efcfc-02c8-4153-95c3-f9bdb32499e0",
                            QuestionnaireAnswer.QUESTION: "Please specify where",
                            QuestionnaireAnswer.ANSWER_TEXT: "NHS",
                        },
                        {
                            QuestionnaireAnswer.QUESTION_ID: "3ce7cf65-f3d6-4bd0-8e67-fd9c98b636fd",
                            QuestionnaireAnswer.QUESTION: "Please specify the city/town.",
                            QuestionnaireAnswer.ANSWER_TEXT: "London",
                        },
                    ]
                },
            },
        },
        "BreastFeedingUpdate": {
            NAME: "BreastFeedingUpdate",
            PRIMITIVE: "BreastFeedingUpdate",
            VALUE: sample_breastfeeding_update(),
            EXPECTED_RESULT_VALUE: {
                BreastFeedingUpdate.IS_BREASTFEEDING_NOW: True,
                BreastFeedingUpdate.STOP_DATE: utc_date_to_str(
                    datetime.utcnow() - relativedelta(months=3)
                ),
                BreastFeedingUpdate.NOW_OR_WORSE_SYMPTOM: [
                    NewSymptomAction.DISABILITY_INCAPACITATION
                ],
                BreastFeedingUpdate.BREASTFEEDING_BABY_DETAILS: [
                    {
                        BreastFeedingUpdateBabyDetails.HEALTH_ISSUE: [],
                        BreastFeedingUpdateBabyDetails.HEALTH_ISSUE_ACTION: [
                            HealthIssueAction.CONSULT_DOCTOR,
                            HealthIssueAction.VISIT_ER,
                        ],
                        BreastFeedingUpdateBabyDetails.HAS_RECEIVED_DIAGNOSIS: True,
                        BreastFeedingUpdateBabyDetails.DIAGNOSIS_LIST: [],
                    }
                ],
                BreastFeedingUpdate.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                            QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                        }
                    ]
                },
            },
        },
        "BreastFeedingStatus": {
            NAME: "BreastFeedingStatus",
            PRIMITIVE: "BreastFeedingStatus",
            VALUE: sample_breastfeeding_status(),
            EXPECTED_RESULT_VALUE: {
                BreastFeedingStatus.IS_BREASTFEEDING_CURRENTLY: False,
                BreastFeedingStatus.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                            QuestionnaireAnswer.QUESTION: "Are you currently breastfeeding?",
                            QuestionnaireAnswer.ANSWER_TEXT: "No",
                        },
                    ]
                },
            },
        },
        "PregnancyUpdate": {
            NAME: "PregnancyUpdate",
            PRIMITIVE: "PregnancyUpdate",
            VALUE: sample_pregnancy_update(),
            EXPECTED_RESULT_VALUE: {
                PregnancyUpdate.HAS_MENSTRUAL_PERIOD: True,
                PregnancyUpdate.LAST_MENSTRUAL_PERIOD_DATE_DAY1: "2021-01-01",
                PregnancyUpdate.BECAME_PREGNANT: False,
                PregnancyUpdate.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "a285d625-54d1-421f-ba5e-d9748690c461",
                            QuestionnaireAnswer.QUESTION: "Have you had your menstrual period in the last year?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                        },
                        {
                            QuestionnaireAnswer.QUESTION_ID: "de8a8e98-81a7-42be-a33f-0b8f0393ada1",
                            QuestionnaireAnswer.QUESTION: "What was the first day of your last menstrual period date? ",
                            QuestionnaireAnswer.ANSWER_TEXT: "2021-01-01T00:00:00Z",
                        },
                        {
                            QuestionnaireAnswer.QUESTION_ID: "0f473b35-1dc9-40de-af16-17eaa4f4ff7f",
                            QuestionnaireAnswer.QUESTION: "Are you currently pregnant?",
                            QuestionnaireAnswer.ANSWER_TEXT: "No",
                        },
                    ]
                },
            },
        },
        "MedicalHistory": {
            NAME: "MedicalHistory",
            PRIMITIVE: "MedicalHistory",
            VALUE: sample_medical_history(),
            EXPECTED_RESULT_VALUE: {
                MedicalHistory.MEDICAL_DIAGNOSIS: [MedicalDiagnosis.DIABETES],
                MedicalHistory.TAKING_IMMUNO_SUPPRESSANTS: YesNoDont.YES,
                MedicalHistory.IMMUNO_SUPPRESSANTS_MEDICATION_LIST: ["Test"],
                MedicalHistory.IS_COVID_INFECTED_IN_PAST: True,
                MedicalHistory.IS_COVID_TOLD_BY_DOCTOR: False,
                MedicalHistory.TAKEN_COVID_TEST: YesNoDont.NO,
                MedicalHistory.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "7c50c7d5-6f4e-4c0b-aeaf-c266eafdt587",
                            QuestionnaireAnswer.QUESTION: "Please specify which type of cancer?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Colorectal Cancer",
                        }
                    ]
                },
                MedicalHistory.IS_DIAGNOSED_WITH_CANCER: False,
            },
        },
        "OtherVaccine": {
            NAME: "OtherVaccine",
            PRIMITIVE: "OtherVaccine",
            VALUE: sample_other_vaccine(),
            EXPECTED_RESULT_VALUE: {
                OtherVaccine.HAS_OTHER_VACCINE: True,
                OtherVaccine.FLU_VACCINE_DATE: "2021-03-30",
                OtherVaccine.HAS_FLU_VACCINE: True,
                OtherVaccine.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "fb529e6f-6c89-475f-a4cc-dc50741ea091",
                            QuestionnaireAnswer.QUESTION: "Have you received the seasonal flu vaccine since the last time we asked?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Yes",
                        },
                    ]
                },
            },
        },
        "PregnancyFollowUp": {
            NAME: "PregnancyFollowUp",
            PRIMITIVE: "PregnancyFollowUp",
            VALUE: sample_pregnancy_follow_up(),
            EXPECTED_RESULT_VALUE: {
                PregnancyFollowUp.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: "What was the method of delivery?",
                            QuestionnaireAnswer.ANSWER_TEXT: "Caesarean section",
                        },
                    ]
                },
            },
        },
        "PostVaccination": {
            NAME: "PostVaccination",
            PRIMITIVE: "PostVaccination",
            VALUE: sample_post_vaccination(),
            EXPECTED_RESULT_VALUE: {
                PostVaccination.METADATA: {
                    QuestionnaireMetadata.ANSWERS: [
                        {
                            QuestionnaireAnswer.QUESTION_ID: "5e94b2007773091c9a592651",
                            QuestionnaireAnswer.QUESTION: "Please provide the date of your second COVID-19 vaccination dose.",
                            QuestionnaireAnswer.ANSWER_TEXT: "2019-06-30",
                        }
                    ]
                },
            },
        },
    }

    def test_success_retrieve_az_screening_module_result(self):
        data = sample_az_screening()
        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}",
            json=[data],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.base_route}/{data['type']}/search", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        module_result_id = rsp.json[data["type"]][0]["id"]
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/primitive/{data['type']}/{module_result_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json[ModuleConfig.MODULE_ID], data["type"])

    def test_upload_download_module_results(self):
        self.mongo_database["weight"].delete_many({})
        for i, module in enumerate(self.module_maps.values()):
            module_id = module[self.NAME]
            self.post_results(module_id, module[self.VALUE])

            result = self.retrieve_result(module_id, module[self.PRIMITIVE])
            expected = dict(result, **module[self.EXPECTED_RESULT_VALUE])
            self.assertDictEqual(expected, result, f"Error: {module_id}")
