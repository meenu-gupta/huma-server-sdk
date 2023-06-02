from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.models.primitives import (
    GroupCategory,
    PROMISGlobalHealth,
    VaccinationDetails,
    BackgroundInformation,
    MedicalHistory,
)
from .key_actions_trigger_tests import (
    BaseKeyActionsTriggerTests,
)
from sdk.common.utils.validators import utc_date_to_str


class MaleOrFemaleOver50TestCase(BaseKeyActionsTriggerTests):
    def setUp(self):
        super().setUp()
        self.first_vaccine_date = self.now - relativedelta(days=1)

    def test_all_key_actions_are_available(self):
        self._test_all_key_actions_are_available(GroupCategory.MALE_OR_FEMALE_OVER_50)

        # 4 modules should be available immediately
        self._test_available_modules(
            [
                VaccinationDetails,
                BackgroundInformation,
                MedicalHistory,
                PROMISGlobalHealth,
            ]
        )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=84, days=1)):
            # confirming we got 0 key actions after study ends
            rsp = self._key_actions_request()
            self.assertEqual(0, len(rsp.json))

    def test_success_module_result_submission(self):
        self._submit_group_information(
            GroupCategory.MALE_OR_FEMALE_OVER_50,
            utc_date_to_str(self.first_vaccine_date),
        )

        rsp = self._key_actions_request()
        self.assertEqual(4, len(rsp.json))

        #  submit available modules
        self._submit_vaccination_details()
        self._submit_background_information()
        self._submit_medical_history()
        self._submit_promis_global_health()

        # each module should be disabled now
        rsp = self._key_actions_request()
        available_modules = [key_action[KeyAction.ENABLED] for key_action in rsp.json]
        self.assertFalse(any(available_modules))
