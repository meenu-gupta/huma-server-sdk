from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.models.primitives import (
    GroupCategory,
    BreastFeedingUpdate,
    VaccinationDetails,
    BackgroundInformation,
    MedicalHistory,
    PROMISGlobalHealth,
    BreastFeedingStatus,
    PregnancyStatus,
    HealthStatus,
    OtherVaccine,
    FeverAndPainDrugs,
    AZFurtherPregnancyKeyActionTrigger,
    PregnancyUpdate,
    PostVaccination,
    AdditionalQoL,
    CurrentGroupCategory,
    PregnancyFollowUp,
    InfantFollowUp,
)
from .key_actions_trigger_tests import (
    BaseKeyActionsTriggerTests,
)


class FemaleLessThan50Cohort(BaseKeyActionsTriggerTests):
    def setUp(self):
        super().setUp()
        self.first_vaccine_date = datetime.utcnow().date() - relativedelta(days=1)

    def _test_all_key_actions_are_available(self, group: GroupCategory):
        self._submit_group_information(group, str(self.first_vaccine_date))
        # 6 modules should be available immediately
        self._test_available_modules(
            [
                VaccinationDetails,
                BackgroundInformation,
                MedicalHistory,
                PROMISGlobalHealth,
                BreastFeedingStatus,
                PregnancyStatus,
            ]
        )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=1, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    FeverAndPainDrugs,
                    AZFurtherPregnancyKeyActionTrigger,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=4, days=1)):
            self._test_available_modules(
                [
                    PostVaccination,
                    HealthStatus,
                    OtherVaccine,
                    AZFurtherPregnancyKeyActionTrigger,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=6, days=1)):
            self._test_available_modules([FeverAndPainDrugs])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=8, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    PregnancyUpdate,
                    AZFurtherPregnancyKeyActionTrigger,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=14, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    PregnancyUpdate,
                    AZFurtherPregnancyKeyActionTrigger,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=20, days=1)):
            self._test_available_modules(
                [HealthStatus, OtherVaccine, AdditionalQoL, PROMISGlobalHealth]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=26, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    PregnancyUpdate,
                    AZFurtherPregnancyKeyActionTrigger,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=39, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    PregnancyUpdate,
                    AZFurtherPregnancyKeyActionTrigger,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=52, days=1)):
            self._test_available_modules(
                [
                    HealthStatus,
                    OtherVaccine,
                    PregnancyUpdate,
                    AZFurtherPregnancyKeyActionTrigger,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=65, days=1)):
            self._test_available_modules(
                [HealthStatus, OtherVaccine, AdditionalQoL, PROMISGlobalHealth]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=78, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine, PregnancyUpdate])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=84, days=1)):
            # confirming we got 0 key actions after study ends
            rsp = self._key_actions_request()
            self.assertEqual(0, len(rsp.json))

    def test_success_module_result_submission(self):
        self._submit_group_information(
            GroupCategory.FEMALE_LESS_50_NOT_P_OR_B, str(self.first_vaccine_date)
        )

        rsp = self._key_actions_request()
        self.assertEqual(6, len(rsp.json))

        #  submit available modules
        self._submit_vaccination_details()
        self._submit_background_information()
        self._submit_medical_history()
        self._submit_promis_global_health()
        self._submit_breastfeeding_status()
        self._submit_pregnancy_status()

        # each module should be disabled now
        rsp = self._key_actions_request()
        available_modules = [key_action[KeyAction.ENABLED] for key_action in rsp.json]
        self.assertFalse(any(available_modules))

    def test_not_pregnant_or_breastfeeding_cohort(self):
        self._test_all_key_actions_are_available(
            GroupCategory.FEMALE_LESS_50_NOT_P_OR_B
        )

    def test_breastfeeding_cohort(self):
        self._test_all_key_actions_are_available(GroupCategory.BREAST_FEEDING)

        # key actions should appear in these weeks
        weeks = [1, 4, 8, 14, 26, 39, 52]
        for week in weeks:
            with freeze_time(
                self.first_vaccine_date + relativedelta(weeks=week, days=1)
            ):
                self._test_available_modules([BreastFeedingUpdate])


class CohortChangeTestCase(BaseKeyActionsTriggerTests):
    def setUp(self):
        super().setUp()
        # set vaccine date to previous week so we can submit further_information
        self.first_vaccine_date = datetime.utcnow().date() - relativedelta(days=8)

    def _test_not_available_modules(self, expected_modules: list):
        rsp = self._key_actions_request()
        enabled_modules = filter(lambda x: x[KeyAction.ENABLED], rsp.json)
        available_modules = set(map(lambda x: x[KeyAction.MODULE_ID], enabled_modules))

        for module in expected_modules:
            self.assertFalse(module.__name__ in available_modules, module)

    def test_cohort_change(self):
        self._submit_group_information(
            GroupCategory.FEMALE_LESS_50_NOT_P_OR_B, str(self.first_vaccine_date)
        )

        # change cohort
        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        self._test_not_available_modules(
            [
                AZFurtherPregnancyKeyActionTrigger,
                BreastFeedingUpdate,
                PregnancyUpdate,
            ]
        )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=4, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=8, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=12, days=1)):
            # pregnancy follow up should appear on the 12th week
            self._test_available_modules([PregnancyFollowUp])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=14, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=26, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=39, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=52, days=1)):
            self._test_not_available_modules(
                [
                    AZFurtherPregnancyKeyActionTrigger,
                    BreastFeedingUpdate,
                    PregnancyUpdate,
                ]
            )
            # pregnancy follow up should appear on the 52nd week
            self._test_available_modules([InfantFollowUp])
