from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.models.primitives import (
    GroupCategory,
    VaccinationDetails,
    BackgroundInformation,
    MedicalHistory,
    PROMISGlobalHealth,
    BreastFeedingStatus,
    PregnancyStatus,
    PregnancyFollowUp,
    InfantFollowUp,
    BreastFeedingUpdate,
)
from .key_actions_trigger_tests import (
    BaseKeyActionsTriggerTests,
)


class PregnantCohort(BaseKeyActionsTriggerTests):
    def setUp(self):
        super().setUp()
        self.first_vaccine_date = datetime.utcnow().date() - relativedelta(days=1)

    def _test_all_key_actions_are_available_pregnant_cohort(self, group: GroupCategory):
        self._test_all_key_actions_are_available(group)
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

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=12, days=1)):
            self._test_available_modules([PregnancyFollowUp])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=52, days=1)):
            self._test_available_modules([InfantFollowUp])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=105, days=1)):
            # confirming we got 0 key actions after study ends
            rsp = self._key_actions_request()
            self.assertEqual(0, len(rsp.json))

    def test_success_module_result_submission(self):
        self._submit_group_information(
            GroupCategory.PREGNANT, str(self.first_vaccine_date)
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

    def test_pregnant_cohort(self):
        self._test_all_key_actions_are_available_pregnant_cohort(GroupCategory.PREGNANT)

    def test_pregnant_and_breastfeeding(self):
        self._test_all_key_actions_are_available_pregnant_cohort(
            GroupCategory.BOTH_P_AND_B
        )

        # key actions should appear in these weeks
        weeks = [1, 4, 8, 14, 26, 39, 52]
        for week in weeks:
            with freeze_time(
                self.first_vaccine_date + relativedelta(weeks=week, days=1)
            ):
                self._test_available_modules([BreastFeedingUpdate])
