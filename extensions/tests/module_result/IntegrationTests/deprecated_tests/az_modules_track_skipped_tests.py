from extensions.module_result.models.primitives import (
    PregnancyStatus,
    BreastFeedingUpdate,
    BackgroundInformation,
    InfantFollowUp,
    MedicalHistory,
    PregnancyFollowUp,
    PregnancyUpdate,
    VaccinationDetails,
    FeverAndPainDrugs,
    HealthStatus,
    OtherVaccine,
    PostVaccination,
    AdditionalQoL,
    BreastFeedingStatus,
)
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_breastfeeding_update,
    sample_pregnancy_status,
    sample_fever_and_pain_drugs,
    sample_background_information,
    sample_health_status,
    sample_infant_follow_up,
    sample_medical_history,
    sample_other_vaccine,
    sample_post_vaccination,
    sample_pregnancy_follow_up,
    sample_pregnancy_update,
    sample_additional_qol,
    sample_vaccination_details,
    sample_breastfeeding_status,
)
from sdk.common.exceptions.exceptions import ErrorCodes


class AzModulesSkippedFieldsTest(BaseModuleResultTest):

    NAME = "name"
    PRIMITIVE = "primitive"
    EXPECTED_SKIPPED_VALUE = "expectedSkippedValue"
    VALUE = "value"

    module_maps = {
        BreastFeedingStatus.__name__: {
            NAME: BreastFeedingStatus.__name__,
            PRIMITIVE: BreastFeedingStatus,
            VALUE: sample_breastfeeding_status(),
            EXPECTED_SKIPPED_VALUE: {
                BreastFeedingStatus.HAS_RISK_CONDITIONS,
                BreastFeedingStatus.FAMILY_HISTORY_OF_DEFECTS,
                BreastFeedingStatus.NUMBER_OF_WEEKS_AT_CHILD_BIRTH,
                BreastFeedingStatus.BREASTFEEDING_BABY_DETAILS,
                BreastFeedingStatus.HIGH_RISK_CONDITIONS,
                BreastFeedingStatus.HAS_RISK_CONDITIONS,
                BreastFeedingStatus.COMPLICATION_LIST,
                BreastFeedingStatus.FAMILY_HISTORY_OF_DEFECTS_LIST,
                BreastFeedingStatus.HAD_COMPLICATIONS_AT_BIRTH,
            },
        },
        BreastFeedingUpdate.__name__: {
            NAME: BreastFeedingUpdate.__name__,
            PRIMITIVE: BreastFeedingUpdate,
            VALUE: sample_breastfeeding_update(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        PregnancyStatus.__name__: {
            NAME: PregnancyStatus.__name__,
            PRIMITIVE: PregnancyStatus,
            VALUE: sample_pregnancy_status(),
            EXPECTED_SKIPPED_VALUE: {
                PregnancyStatus.HAS_OTHER_MEDICAL_FERTILITY_PROCEDURE,
                PregnancyStatus.PREGNANCY_TIMES,
            },
        },
        FeverAndPainDrugs.__name__: {
            NAME: FeverAndPainDrugs.__name__,
            PRIMITIVE: FeverAndPainDrugs,
            VALUE: sample_fever_and_pain_drugs(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        BackgroundInformation.__name__: {
            NAME: BackgroundInformation.__name__,
            PRIMITIVE: BackgroundInformation,
            VALUE: sample_background_information(),
            EXPECTED_SKIPPED_VALUE: {BackgroundInformation.OTHER_EMPLOYMENT},
        },
        HealthStatus.__name__: {
            NAME: HealthStatus.__name__,
            PRIMITIVE: HealthStatus,
            VALUE: sample_health_status(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        InfantFollowUp.__name__: {
            NAME: InfantFollowUp.__name__,
            PRIMITIVE: InfantFollowUp,
            VALUE: sample_infant_follow_up(),
            EXPECTED_SKIPPED_VALUE: {
                InfantFollowUp.COUNT_COV_PREG,
                InfantFollowUp.IS_MORE_THAN_1_CHILD_COV_VAC,
            },
        },
        MedicalHistory.__name__: {
            NAME: MedicalHistory.__name__,
            PRIMITIVE: MedicalHistory,
            VALUE: sample_medical_history(),
            EXPECTED_SKIPPED_VALUE: {
                MedicalHistory.OTHER_COVID_SYMPTOMS,
                MedicalHistory.COVID_TEST_DATE,
                MedicalHistory.COVID_INFECTED_DATE,
                MedicalHistory.COVID_SYMPTOMS_ACTION,
                MedicalHistory.COVID_TEST_METHOD,
                MedicalHistory.COVID_TEST_RESULT,
                MedicalHistory.MEDICAL_CONDITION,
                MedicalHistory.HAD_OTHER_COVID_SYMPTOMS,
                MedicalHistory.COVID_TOLD_BY_DOCTOR_DATE,
                MedicalHistory.HAD_COVID_SYMPTOMS,
                MedicalHistory.COVID_TEST_OTHER,
                MedicalHistory.COVID_SYMPTOMS,
                MedicalHistory.CANCER_TYPE,
            },
        },
        OtherVaccine.__name__: {
            NAME: OtherVaccine.__name__,
            PRIMITIVE: OtherVaccine,
            VALUE: sample_other_vaccine(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        PostVaccination.__name__: {
            NAME: PostVaccination.__name__,
            PRIMITIVE: PostVaccination,
            VALUE: sample_post_vaccination(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        PregnancyFollowUp.__name__: {
            NAME: PregnancyFollowUp.__name__,
            PRIMITIVE: PregnancyFollowUp,
            VALUE: sample_pregnancy_follow_up(),
            EXPECTED_SKIPPED_VALUE: {PregnancyFollowUp.PRESCRIPTION_MEDICATIONS},
        },
        PregnancyUpdate.__name__: {
            NAME: PregnancyUpdate.__name__,
            PRIMITIVE: PregnancyUpdate,
            VALUE: sample_pregnancy_update(),
            EXPECTED_SKIPPED_VALUE: {
                PregnancyUpdate.HAS_OTHER_PREGNANCY_OUTCOME,
                PregnancyUpdate.OTHER_PRENATAL_SCREENING,
                PregnancyUpdate.HAS_SCREENING_PROBLEM,
                PregnancyUpdate.HIGH_RISK_CONDITION,
                PregnancyUpdate.PREGNANCY_TIMES,
                PregnancyUpdate.HAS_OTHER_PRENATAL_SCREENING,
                PregnancyUpdate.SCREENING_PROBLEM_TEXT,
                PregnancyUpdate.PRENATAL_SCREENING_ANSWERS,
                PregnancyUpdate.PAST_PREGNANCY_ELECTIVE_TERMINATION,
                PregnancyUpdate.PAST_BABY_COUNT,
                PregnancyUpdate.PREGNANCY_MORE_THAN1,
                PregnancyUpdate.HIGH_RISK_CONDITION_ANSWERS,
                PregnancyUpdate.FAMILY_HISTORY_DEFECTS_ANSWERS,
                PregnancyUpdate.FAMILY_HISTORY_DEFECTS,
                PregnancyUpdate.HAS_PAST_PREGNANCY,
                PregnancyUpdate.IS_PREGNANCY_CURRENT,
                PregnancyUpdate.PAST_PREGNANCY_WEEKS,
                PregnancyUpdate.EXPECTED_DUE_DATE,
                PregnancyUpdate.PAST_PREGNANCY_MORE_THAN_1,
                PregnancyUpdate.PAST_PREGNANCY_ECTOPIC,
                PregnancyUpdate.OTHER_PREGNANCY_RESULT,
                PregnancyUpdate.PAST_PREGNANCY_MISCARRIAGE,
                PregnancyUpdate.HAS_VISIT_MEDICAL_PROFESSIONAL,
                PregnancyUpdate.BABY_COUNT,
                PregnancyUpdate.HAS_PRENATAL_SCREENING,
                PregnancyUpdate.PAST_PREGNANCY_STILL_BORN,
                PregnancyUpdate.PAST_PREGNANCY_LIFE_BIRTH,
                PregnancyUpdate.IS_EXPECTED_DUE_DATE_AVAILABLE,
                PregnancyUpdate.PREGNANCY_RESULT,
            },
        },
        AdditionalQoL.__name__: {
            NAME: AdditionalQoL.__name__,
            PRIMITIVE: AdditionalQoL,
            VALUE: sample_additional_qol(),
            EXPECTED_SKIPPED_VALUE: set(),
        },
        VaccinationDetails.__name__: {
            NAME: VaccinationDetails.__name__,
            PRIMITIVE: VaccinationDetails,
            VALUE: sample_vaccination_details(),
            EXPECTED_SKIPPED_VALUE: {
                VaccinationDetails.SECOND_VAC_SCHEDULE_DATE,
                VaccinationDetails.ALLERGIC_REACTION,
                VaccinationDetails.OTHER_SPECIFIED_VACC,
                VaccinationDetails.OTHER_VACC_CATEGORY,
                VaccinationDetails.SEASON_FLU_VAC_DATE,
                VaccinationDetails.ALLERGIC_REACTION_VACC,
            },
        },
    }

    def test_skipped_fields_names_az_modules(self):
        for module in self.module_maps.values():
            rsp = self.flask_client.post(
                f"{self.base_route}/{module[self.NAME]}",
                json=[module[self.VALUE]],
                headers=self.headers,
            )
            self.assertEqual(201, rsp.status_code)
            self.assertEqual(len(rsp.json.get("errors") or []), 0)

            rsp = self.flask_client.post(
                f"{self.base_route}/{module['name']}/search", headers=self.headers
            )
            last_value = rsp.json[module[self.NAME]][0]
            self.assertSetEqual(
                module[self.EXPECTED_SKIPPED_VALUE], set(last_value["skipped"])
            )

    def test_failure_pass_skipped_field_in_request(self):
        for module in self.module_maps.values():
            rsp = self.flask_client.post(
                f"{self.base_route}/{module[self.NAME]}",
                json=[{**module[self.VALUE], module[self.PRIMITIVE].SKIPPED: ["test"]}],
                headers=self.headers,
            )

            self.assertEqual(403, rsp.status_code)
            self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])
