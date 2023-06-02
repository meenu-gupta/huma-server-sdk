from datetime import datetime
from pathlib import Path

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.authorization.component import AuthorizationComponent
from extensions.autocomplete.component import AutocompleteComponent
from extensions.deployment.component import DeploymentComponent
from extensions.kardia.component import KardiaComponent
from extensions.key_action.component import KeyActionComponent
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    AZFurtherPregnancyKeyActionTrigger,
    CurrentGroupCategory,
    GroupCategory,
    VaccinationDetails,
    PostVaccination,
    BackgroundInformation,
    MedicalHistory,
    HealthStatus,
    OtherVaccine,
    FeverAndPainDrugs,
    AdditionalQoL,
    PROMISGlobalHealth,
    BreastFeedingStatus,
    PregnancyStatus,
    PregnancyFollowUp,
    InfantFollowUp,
    BreastFeedingUpdate,
    PregnancyUpdate,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_group_information,
    sample_further_information,
    sample_vaccination_details,
    sample_post_vaccination,
    sample_background_information,
    sample_medical_history,
    sample_health_status,
    sample_other_vaccine,
    sample_fever_and_pain_drugs,
    sample_promis_global_health,
    sample_breastfeeding_status,
    sample_pregnancy_status,
    sample_pregnancy_update,
    sample_breastfeeding_update,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.repo.mongo_calendar_repository import MongoCalendarRepository
from sdk.common.utils.validators import utc_date_to_str
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

KEY_ACTION_GROUPS = {
    "PREGNANT": [
        VaccinationDetails,
        PostVaccination,
        BackgroundInformation,
        MedicalHistory,
        HealthStatus,
        OtherVaccine,
        FeverAndPainDrugs,
        AdditionalQoL,
        PROMISGlobalHealth,
        BreastFeedingStatus,
        PregnancyStatus,
        PregnancyFollowUp,
        InfantFollowUp,
    ],
    "BREAST_FEEDING": [
        VaccinationDetails,
        PostVaccination,
        BackgroundInformation,
        MedicalHistory,
        HealthStatus,
        OtherVaccine,
        FeverAndPainDrugs,
        AdditionalQoL,
        PROMISGlobalHealth,
        BreastFeedingStatus,
        BreastFeedingUpdate,
        PregnancyStatus,
        PregnancyUpdate,
        AZFurtherPregnancyKeyActionTrigger,
    ],
    "BOTH_P_AND_B": [
        VaccinationDetails,
        PostVaccination,
        BackgroundInformation,
        MedicalHistory,
        HealthStatus,
        OtherVaccine,
        FeverAndPainDrugs,
        AdditionalQoL,
        PROMISGlobalHealth,
        PregnancyStatus,
        BreastFeedingStatus,
        BreastFeedingUpdate,
        PregnancyFollowUp,
        InfantFollowUp,
    ],
    "FEMALE_LESS_50_NOT_P_OR_B": [
        VaccinationDetails,
        PostVaccination,
        BackgroundInformation,
        MedicalHistory,
        HealthStatus,
        OtherVaccine,
        FeverAndPainDrugs,
        AdditionalQoL,
        PROMISGlobalHealth,
        BreastFeedingStatus,
        PregnancyStatus,
        PregnancyUpdate,
        AZFurtherPregnancyKeyActionTrigger,
    ],
    "MALE_OR_FEMALE_OVER_50": [
        VaccinationDetails,
        PostVaccination,
        BackgroundInformation,
        MedicalHistory,
        HealthStatus,
        OtherVaccine,
        FeverAndPainDrugs,
        AdditionalQoL,
        PROMISGlobalHealth,
    ],
}

KEY_ACTIONS_TO_REMOVE = {
    "BREAST_FEEDING": {
        "PREGNANT": [
            PregnancyUpdate,
            BreastFeedingUpdate,
            AZFurtherPregnancyKeyActionTrigger,
        ],
        "NOT_PREGNANT": [],
    },
    "FEMALE_LESS_50_NOT_P_OR_B": {
        "PREGNANT": [PregnancyUpdate, AZFurtherPregnancyKeyActionTrigger],
        "NOT_PREGNANT": [],
    },
}

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"


class BaseKeyActionsTriggerTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AutocompleteComponent(),
        StorageComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        KardiaComponent(),
        CalendarComponent(),
        KeyActionComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    config_file_path = Path(__file__).parent.with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.parent.joinpath("fixtures/az_deployment_dump.json"),
    ]

    def setUp(self):
        super().setUp()
        self.base_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"
        self.headers = self.get_headers_for_token(VALID_USER_ID)
        self.key_action_url = f"/api/extensions/v1beta/user/{VALID_USER_ID}/key-action"
        self.now = datetime.utcnow()
        self.first_vaccine_date = self.now - relativedelta(weeks=1)

    def _assert_all_key_actions_in_db(self, group_category: GroupCategory):
        modules = KEY_ACTION_GROUPS.get(group_category.name)

        for module in modules:
            result = self.mongo_database[
                MongoCalendarRepository.CALENDAR_COLLECTION
            ].find_one(
                {
                    f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_ID}": module.__name__,
                    KeyAction.USER_ID: ObjectId(VALID_USER_ID),
                }
            )
            self.assertIsNotNone(result)

    def _submit_group_information(
        self, group_category: GroupCategory, vaccine_date=None
    ):
        group_information = sample_group_information()
        group_information[AZGroupKeyActionTrigger.GROUP_CATEGORY] = group_category
        group_information[
            AZGroupKeyActionTrigger.FIRST_VACCINE_DATE
        ] = vaccine_date or utc_date_to_str(self.first_vaccine_date)
        rsp = self.flask_client.post(
            f"{self.base_route}/AZGroupKeyActionTrigger",
            json=[group_information],
            headers=self.headers,
        )

        return rsp

    def _submit_further_information(self, group_category: CurrentGroupCategory):
        further_information = sample_further_information()
        further_information[
            AZFurtherPregnancyKeyActionTrigger.CURRENT_GROUP_CATEGORY
        ] = group_category
        rsp = self.flask_client.post(
            f"{self.base_route}/AZFurtherPregnancyKeyActionTrigger",
            json=[further_information],
            headers=self.headers,
        )

        return rsp

    def _submit_vaccination_details(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/VaccinationDetails",
            json=[sample_vaccination_details()],
            headers=self.headers,
        )

        return rsp

    def _submit_post_vaccination(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/PostVaccination",
            json=[sample_post_vaccination()],
            headers=self.headers,
        )

        return rsp

    def _submit_background_information(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/BackgroundInformation",
            json=[sample_background_information()],
            headers=self.headers,
        )

        return rsp

    def _submit_medical_history(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/MedicalHistory",
            json=[sample_medical_history()],
            headers=self.headers,
        )

        return rsp

    def _submit_health_status(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/HealthStatus",
            json=[sample_health_status()],
            headers=self.headers,
        )

        return rsp

    def _submit_other_vaccine(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/OtherVaccine",
            json=[sample_other_vaccine()],
            headers=self.headers,
        )

        return rsp

    def _submit_fever_and_pain_drugs(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/FeverAndPainDrugs",
            json=[sample_fever_and_pain_drugs()],
            headers=self.headers,
        )

        return rsp

    def _submit_promis_global_health(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/PROMISGlobalHealth",
            json=[sample_promis_global_health()],
            headers=self.headers,
        )

        return rsp

    def _submit_breastfeeding_status(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/BreastFeedingStatus",
            json=[sample_breastfeeding_status()],
            headers=self.headers,
        )

        return rsp

    def _submit_breastfeeding_update(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/BreastFeedingUpdate",
            json=[sample_breastfeeding_update()],
            headers=self.headers,
        )

        return rsp

    def _submit_pregnancy_status(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/PregnancyStatus",
            json=[sample_pregnancy_status()],
            headers=self.headers,
        )

        return rsp

    def _submit_pregnancy_update(self):
        rsp = self.flask_client.post(
            f"{self.base_route}/PregnancyUpdate",
            json=[sample_pregnancy_update()],
            headers=self.headers,
        )

        return rsp

    def _key_actions_request(self, uid=VALID_USER_ID):
        user_key_actions_url = f"/api/extensions/v1beta/user/{uid}/key-action"
        rsp = self.flask_client.get(
            user_key_actions_url, headers=self.get_headers_for_token(uid)
        )
        return rsp

    def _test_available_modules(self, expected_modules: list):
        rsp = self._key_actions_request()
        enabled_modules = filter(lambda x: x[KeyAction.ENABLED], rsp.json)
        available_modules = set(map(lambda x: x[KeyAction.MODULE_ID], enabled_modules))

        for module in expected_modules:
            self.assertTrue(module.__name__ in available_modules, module)

    def _test_all_key_actions_are_available(self, group: GroupCategory):
        # test common key actions
        self._submit_group_information(group, utc_date_to_str(self.first_vaccine_date))

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=1, days=1)):
            self._test_available_modules(
                [HealthStatus, OtherVaccine, FeverAndPainDrugs]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=4, days=1)):
            self._test_available_modules([PostVaccination, HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=6, days=1)):
            self._test_available_modules([FeverAndPainDrugs])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=8, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=14, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=20, days=1)):
            self._test_available_modules(
                [HealthStatus, OtherVaccine, AdditionalQoL, PROMISGlobalHealth]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=26, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=39, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=52, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=65, days=1)):
            self._test_available_modules(
                [HealthStatus, OtherVaccine, AdditionalQoL, PROMISGlobalHealth]
            )

        with freeze_time(self.first_vaccine_date + relativedelta(weeks=78, days=1)):
            self._test_available_modules([HealthStatus, OtherVaccine])


class KeyActionsTriggerTests(BaseKeyActionsTriggerTests):
    def test_success_create_calender_events_group_trigger(self):
        rsp = self._submit_group_information(GroupCategory.BREAST_FEEDING)
        self.assertEqual(201, rsp.status_code)
        self._assert_all_key_actions_in_db(GroupCategory.BREAST_FEEDING)

    def test_success_create_calender_events_pregnancy_trigger(self):
        self._submit_group_information(GroupCategory.BREAST_FEEDING)
        self._submit_further_information(CurrentGroupCategory.PREGNANT)
        self._assert_all_key_actions_in_db(GroupCategory.PREGNANT)

    def _test_cohort_change(self, previous_group: GroupCategory):
        vaccine_date = self.now - relativedelta(days=8)
        self._submit_group_information(previous_group, utc_date_to_str(vaccine_date))

        self._submit_pregnancy_update()
        self._submit_breastfeeding_update()

        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        key_actions_to_remove = KEY_ACTIONS_TO_REMOVE.get(previous_group.name)
        modules = key_actions_to_remove.get(CurrentGroupCategory.PREGNANT.name)

        for module in modules:
            result = self.mongo_database[
                MongoCalendarRepository.CALENDAR_COLLECTION
            ].count_documents(
                {
                    f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_ID}": module.__name__,
                    KeyAction.USER_ID: ObjectId(VALID_USER_ID),
                }
            )
            self.assertEqual(1, result, module.__name__)

        self._assert_all_key_actions_in_db(GroupCategory.PREGNANT)

    def test_success_cohort_change_from_breastfeeding(self):
        self._test_cohort_change(previous_group=GroupCategory.BREAST_FEEDING)

    def test_success_cohort_change_from_female_less_50(self):
        self._test_cohort_change(previous_group=GroupCategory.FEMALE_LESS_50_NOT_P_OR_B)

    def _get_key_actions(self):
        rsp = self.flask_client.get(
            self.key_action_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )

        return rsp

    def test_submitted_key_actions_are_not_removed(self):
        vaccine_date = self.now - relativedelta(days=8)
        self._submit_group_information(
            GroupCategory.BREAST_FEEDING, utc_date_to_str(vaccine_date)
        )

        self._submit_pregnancy_update()
        self._submit_breastfeeding_update()
        # change cohort
        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        result = self.mongo_database[
            MongoCalendarRepository.CALENDAR_COLLECTION
        ].count_documents(
            {
                f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_ID}": {
                    "$in": [
                        PregnancyUpdate.__name__,
                        BreastFeedingUpdate.__name__,
                        AZFurtherPregnancyKeyActionTrigger.__name__,
                    ]
                },
                KeyAction.USER_ID: ObjectId(VALID_USER_ID),
            }
        )
        self.assertEqual(result, 3)

    def test_submitted_further_information_remains_in_key_actions_list(self):
        vaccine_date = self.now - relativedelta(days=8)
        self._submit_group_information(
            GroupCategory.BREAST_FEEDING, utc_date_to_str(vaccine_date)
        )

        rsp = self._get_key_actions()

        key_actions = filter(
            lambda k: k[KeyAction.MODULE_ID]
            == AZFurtherPregnancyKeyActionTrigger.__name__,
            rsp.json,
        )
        key_action = next(key_actions)
        self.assertTrue(key_action[KeyAction.ENABLED])

        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        rsp = self._get_key_actions()

        key_actions = filter(
            lambda k: k[KeyAction.MODULE_ID]
            == AZFurtherPregnancyKeyActionTrigger.__name__,
            rsp.json,
        )
        key_action = next(key_actions)
        self.assertFalse(key_action[KeyAction.ENABLED])

        with freeze_time(vaccine_date + relativedelta(weeks=4, days=1)):
            # it should not not appear again in 4 weeks
            rsp = self._get_key_actions()
            key_actions = filter(
                lambda k: k[KeyAction.MODULE_ID]
                == AZFurtherPregnancyKeyActionTrigger.__name__,
                rsp.json,
            )
            key_action = next(key_actions, None)
            self.assertIsNone(key_action)

    def test_failure_missing_group_primitive(self):
        rsp = self._submit_further_information(CurrentGroupCategory.NOT_PREGNANT)
        self.assertIsNotNone(rsp.json["errors"])

    def test_duplicate_group_primitive_submission(self):
        self._submit_group_information(
            GroupCategory.MALE_OR_FEMALE_OVER_50, utc_date_to_str(self.now)
        )
        initial_count = self.mongo_database[
            MongoCalendarRepository.CALENDAR_COLLECTION
        ].count_documents({KeyAction.USER_ID: ObjectId(VALID_USER_ID)})

        # duplicate submissions
        self._submit_group_information(
            GroupCategory.MALE_OR_FEMALE_OVER_50, utc_date_to_str(self.now)
        )

        count = self.mongo_database[
            MongoCalendarRepository.CALENDAR_COLLECTION
        ].count_documents({KeyAction.USER_ID: ObjectId(VALID_USER_ID)})

        self.assertEqual(initial_count, count)

    def test_duplicate_further_information_submission(self):
        self._submit_group_information(
            GroupCategory.FEMALE_LESS_50_NOT_P_OR_B, utc_date_to_str(self.now)
        )

        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        initial_count = self.mongo_database[
            MongoCalendarRepository.CALENDAR_COLLECTION
        ].count_documents({KeyAction.USER_ID: ObjectId(VALID_USER_ID)})

        #  duplicate submission
        self._submit_further_information(CurrentGroupCategory.PREGNANT)

        count = self.mongo_database[
            MongoCalendarRepository.CALENDAR_COLLECTION
        ].count_documents({KeyAction.USER_ID: ObjectId(VALID_USER_ID)})

        self.assertEqual(initial_count, count)
