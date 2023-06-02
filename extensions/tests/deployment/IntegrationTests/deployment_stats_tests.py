from datetime import datetime
from pathlib import Path

from bson import ObjectId
from dateutil.relativedelta import relativedelta

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.tasks import calculate_stats_per_deployment
from extensions.key_action.models.key_action_log import KeyAction
from extensions.organization.component import OrganizationComponent
from extensions.organization.models.organization import Organization, ViewType
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.models.calendar_event import CalendarEventLog
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.utils import inject

USER_ID = "5e8f0c74b50aa9656c34789b"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
ORGANIZATION_ID = "5fde855f12db509a2785da06"
DEPLOYMENT_DURATION = "P6M"
DEPLOYMENT_COLLECTION_NAME = "deployment"
USER_COLLECTION_NAME = "user"
ORGANIZATION_COLLECTION_NAME = "organization"
ID = "id"


class DeploymentStatsTest(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        CalendarComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployment_stats_dump.json")]

    @classmethod
    def setUpClass(cls) -> None:
        return super(DeploymentStatsTest, cls).setUpClass()

    @property
    def deployment_collection(self):
        return self.mongo_database.get_collection(DEPLOYMENT_COLLECTION_NAME)

    @property
    def user_collection(self):
        return self.mongo_database.get_collection(USER_COLLECTION_NAME)

    @property
    def deployment(self):
        repo = inject.instance(DeploymentRepository)
        return repo.retrieve_deployment(deployment_id=DEPLOYMENT_ID)

    def add_user_to_db_one_month_before(self):
        user = {
            "givenName": "User",
            "familyName": "Test",
            "email": "userTest@test.com",
            "roles": [
                {"roleId": "User", "resource": "deployment/5d386cc6ff885918d96edb2c"}
            ],
            "timezone": "UTC",
            "finishedOnboarding": True,
            "createDateTime": datetime.utcnow() - relativedelta(months=1),
        }
        self.user_collection.insert_one(user)

    def update_organization_view_type(self, view_type: ViewType):
        repo = inject.instance(OrganizationRepository)
        data = {
            ID: ORGANIZATION_ID,
            Organization.VIEW_TYPE: view_type.value,
        }
        organization = Organization.from_dict(data)
        return repo.update_organization(organization=organization)

    @staticmethod
    def add_e_consent_to_deployment():
        repo = inject.instance(EConsentRepository)
        data = {
            EConsent.TITLE: "Test",
            EConsent.OVERVIEW_TEXT: "Test",
            EConsent.CONTACT_TEXT: "Test",
            EConsent.ENABLED: "ENABLED",
            EConsent.SECTIONS: [
                {
                    EConsentSection.SECTION_TYPE: EConsentSection.EConsentSectionType.INTRODUCTION.name,
                    EConsentSection.CONTENT_TYPE: EConsentSection.ContentType.IMAGE.value,
                }
            ],
        }
        e_consent = EConsent.from_dict(data)
        return repo.create_econsent(deployment_id=DEPLOYMENT_ID, econsent=e_consent)

    def sign_e_consent(
        self,
        e_consent_id: str,
        consent_option: EConsentLog.EConsentOption = EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT,
    ):
        repo = inject.instance(EConsentRepository)
        data = {
            EConsentLog.USER_ID: USER_ID,
            EConsentLog.DEPLOYMENT_ID: DEPLOYMENT_ID,
            EConsentLog.ECONSENT_ID: e_consent_id,
            EConsentLog.CONSENT_OPTION: consent_option,
        }
        log = EConsentLog.from_dict(data)
        return repo.create_econsent_log(deployment_id=DEPLOYMENT_ID, econsent_log=log)

    def users_count(self):
        return self.user_collection.count_documents({})

    def test_success_calculate_enrolled_users_count_stats(self):
        self.assertIsNone(self.deployment.stats)
        calculate_stats_per_deployment()
        self.assertEqual(2, self.deployment.stats.enrolledCount.value)
        self.assertEqual("", self.deployment.stats.enrolledCount.unit)

    def test_success_calculate_completed_users_count_stats(self):
        self.assertIsNone(self.deployment.stats)
        calculate_stats_per_deployment()
        self.assertEqual(3, self.deployment.stats.completedCount.value)
        self.assertEqual("", self.deployment.stats.completedCount.unit)

        start_users_count = self.users_count()
        self.add_user_to_db_one_month_before()
        self.assertGreater(self.users_count(), start_users_count)

        calculate_stats_per_deployment()
        self.assertEqual(3, self.deployment.stats.completedCount.value)

    def test_success_calculate_consented_users_count_stats(self):
        self.assertIsNone(self.deployment.stats)

        # add e_consent which is not signed by users so consented count should be 0
        e_consent_id = self.add_e_consent_to_deployment()
        calculate_stats_per_deployment()
        self.assertEqual(0, self.deployment.stats.consentedCount.value)

        # sign e-consent
        self.sign_e_consent(e_consent_id)
        calculate_stats_per_deployment()
        self.assertEqual(1, self.deployment.stats.consentedCount.value)

    def test_success_only_patient_count_returned_if_view_type_is_rpm(self):
        self.assertIsNone(self.deployment.stats)
        self.update_organization_view_type(view_type=ViewType.RPM)
        calculate_stats_per_deployment()
        self.assertEqual(3, self.deployment.stats.patientCount.value)
        self.assertEqual("", self.deployment.stats.patientCount.unit)

        # check if other calculations were returned
        self.assertIsNone(self.deployment.stats.enrolledCount)
        self.assertIsNone(self.deployment.stats.completedTask)
        self.assertIsNone(self.deployment.stats.consentedCount)

    def test_success_default_calculation_returned_if_view_type_is_dct(self):
        self.assertIsNone(self.deployment.stats)
        self.update_organization_view_type(view_type=ViewType.DCT)

        calculate_stats_per_deployment()
        self.assertIsNotNone(self.deployment.stats)
        self.assertIsNone(self.deployment.stats.patientCount)

    def test_success_calculate_completed_task_stats(self):
        self.assertIsNone(self.deployment.stats)
        calculate_stats_per_deployment()
        expected_compliance = round(1 / 3 * 100)  # 1 completed event of 3 total
        self.assertEqual(expected_compliance, self.deployment.stats.completedTask.value)
        self.assertEqual("%", self.deployment.stats.completedTask.unit)
        log_dict = {
            CalendarEventLog.MODEL: KeyAction.__name__,
            CalendarEventLog.PARENT_ID: "5f9975bae2db2e007f8ad118",
            CalendarEventLog.START_DATE_TIME: "2020-08-19T10:00:59.000Z",
            CalendarEventLog.END_DATE_TIME: "2020-08-26T09:59:59.000Z",
            CalendarEventLog.USER_ID: USER_ID,
        }
        CalendarService().create_calendar_event_log(
            CalendarEventLog.from_dict(log_dict)
        )
        calculate_stats_per_deployment()
        expected_compliance = round(2 / 3 * 100)  # 2 completed event of 3 total
        self.assertEqual(expected_compliance, self.deployment.stats.completedTask.value)
        self.assertEqual("%", self.deployment.stats.completedTask.unit)

    def test_success_calculate_completed_task_stats_timezone(self):
        self.assertIsNone(self.deployment.stats)
        calculate_stats_per_deployment()
        expected_compliance = round(1 / 3 * 100)  # 1 completed event of 3 total
        self.assertEqual(expected_compliance, self.deployment.stats.completedTask.value)
        self.assertEqual("%", self.deployment.stats.completedTask.unit)
        # update timezone
        timezone = "Asia/Kolkata"
        self.mongo_database.user.update_one(
            {"_id": ObjectId(USER_ID)},
            {"$set": {User.TIMEZONE: timezone}},
        )

        calculate_stats_per_deployment()
        expected_compliance = 0  # timezone invalidated all records
        self.assertEqual(expected_compliance, self.deployment.stats.completedTask.value)
        self.assertEqual("%", self.deployment.stats.completedTask.unit)

        log_dict = {
            CalendarEventLog.MODEL: KeyAction.__name__,
            CalendarEventLog.PARENT_ID: "5f9975bae2db2e007f8ad118",
            CalendarEventLog.START_DATE_TIME: "2020-08-19T10:00:00.000Z",
            CalendarEventLog.END_DATE_TIME: "2020-08-26T09:59:00.000Z",
            CalendarEventLog.USER_ID: USER_ID,
        }
        CalendarService().create_calendar_event_log(
            CalendarEventLog.from_dict(log_dict)
        )
        calculate_stats_per_deployment()
        expected_compliance_with_new_timezone = round(1 / 3 * 100)  # percents
        self.assertEqual(
            expected_compliance_with_new_timezone,
            self.deployment.stats.completedTask.value,
        )
        self.assertEqual("%", self.deployment.stats.completedTask.unit)

    def test_success_calculate_didnt_sign_econsent(self):
        # add e_consent which is not signed by users so consented count should decrease to 0
        e_consent_id = self.add_e_consent_to_deployment()
        self.assertIsNone(self.deployment.stats)
        calculate_stats_per_deployment()
        self.assertEqual(0, self.deployment.stats.consentedCount.value)

        # don't accept
        self.sign_e_consent(
            e_consent_id, consent_option=EConsentLog.EConsentOption.NOT_PARTICIPATE
        )
        calculate_stats_per_deployment()
        self.assertEqual(0, self.deployment.stats.consentedCount.value)

    def test_success_calculate_stats_doesnt_set_update_date_time(self):
        self.assertIsNone(self.deployment.stats)
        old_update_date_time = self.deployment.updateDateTime
        calculate_stats_per_deployment()
        self.assertEqual(old_update_date_time, self.deployment.updateDateTime)
