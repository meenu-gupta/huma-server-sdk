import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime

from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.mongo_manager_assigment import (
    MongoManagerAssignment,
)
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import (
    User,
    PersonalDocument,
    RoleAssignment,
    UserLabel,
)
from extensions.authorization.repository.mongo_auth_repository import (
    MongoAuthorizationRepository,
)
from extensions.authorization.router.user_profile_request import SortParameters
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_sample_labels,
)
from extensions.deployment.models.deployment import Label
from extensions.module_result.models.primitives import Primitive
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.validators import remove_none_values

SAMPLE_ID = "600a8476a961574fb38157d5"
AUTH_REPO_PATH = "extensions.authorization.repository.mongo_auth_repository"


class MockConfig:
    instance = MagicMock()
    masterKey = MagicMock(return_value=1111)
    project = MagicMock(return_value=masterKey)
    server = MagicMock(return_value=project)


class MockDeploymentRepo:
    instance = MagicMock()


class AuthRepoTestCase(unittest.TestCase):
    def expected_add_fields(self):
        return {
            "$addFields": {
                "idStr": {"$toString": "$_id"},
                "enrolmentStr": {"$toString": "$enrollmentId"},
                "givenN": {"$toLower": "$givenName"},
                "hasGivenName": {
                    "$cond": [
                        {"$ne": [{"$ifNull": ["$givenName", None]}, None]},
                        2,
                        1,
                    ]
                },
                "familyN": {"$toLower": "$familyName"},
                "hasFamilyName": {
                    "$cond": [
                        {"$ne": [{"$ifNull": ["$familyName", None]}, None]},
                        2,
                        1,
                    ]
                },
                "DOB": {"$ifNull": ["$dateOfBirth", datetime(5000, 12, 30, 0, 0)]},
                "boardingStatus.detailsOffBoarded_NULL": {
                    "$ifNull": ["$boardingStatus.detailsOffBoarded", ""]
                },
                "surgeryDateRearranged": {
                    "$ifNull": [
                        "$surgeryDateTime",
                        datetime(5000, 12, 30, 0, 0),
                    ]
                },
                "fullName": {
                    "$concat": [
                        {"$toLower": "$givenName"},
                        " ",
                        {"$toLower": "$familyName"},
                    ]
                },
                "onboardingStatus": {
                    "$cond": [
                        {"$eq": ["$boardingStatus.status", 1]},
                        1,
                        {"$cond": [{"$eq": ["$finishedOnboarding", True]}, 3, 2]},
                    ]
                },
            }
        }

    def test_success_delete_user_within_session(self):
        db_mock = MagicMock()
        db_session = MagicMock()
        repo = MongoAuthorizationRepository(database=db_mock, config=MockConfig())
        repo.delete_user(session=db_session, user_id=SAMPLE_ID)
        user_id = ObjectId(SAMPLE_ID)
        db_mock[repo.USER_COLLECTION].delete_one.assert_called_with(
            {User.ID_: user_id}, session=db_session
        )

    def test_success_delete_user_care_plan_group_log_within_session(self):
        db_mock = MagicMock()
        db_session = MagicMock()
        repo = MongoAuthorizationRepository(database=db_mock, config=MockConfig())
        repo.delete_user_from_care_plan_log(session=db_session, user_id=SAMPLE_ID)
        user_id = ObjectId(SAMPLE_ID)
        db_mock[repo.CARE_PLAN_GROUP_LOG_COLLECTION].delete_many.assert_called_with(
            {CarePlanGroupLog.USER_ID: user_id}, session=db_session
        )

    def test_success_delete_user_from_patient_within_session(self):
        db_mock = MagicMock()
        db_session = MagicMock()
        repo = MongoAuthorizationRepository(database=db_mock, config=MockConfig())
        repo.delete_user_from_patient(session=db_session, user_id=SAMPLE_ID)
        user_id = ObjectId(SAMPLE_ID)
        db_mock[
            MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
        ].delete_many.assert_called_with(
            {MongoManagerAssignment.USER_ID: user_id}, session=db_session
        )
        db_mock[
            MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
        ].update_many.assert_called_with(
            {MongoManagerAssignment.MANAGERS_ID: user_id},
            {"$pull": {MongoManagerAssignment.MANAGERS_ID: user_id}},
            session=db_session,
        )

    def test_success_retrieve_helper_agreement_log(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        repo.retrieve_helper_agreement_log(user_id=user_id, deployment_id=deployment_id)
        db[
            MongoAuthorizationRepository.HELPER_AGREEMENT_LOG_COLLECTION
        ].find_one.assert_called_with(
            {
                HelperAgreementLog.USER_ID: ObjectId(user_id),
                HelperAgreementLog.DEPLOYMENT_ID: ObjectId(deployment_id),
            }
        )

    def test_success_create_helper_agreement_log(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        helper_agreement_log_dict = {
            HelperAgreementLog.USER_ID: ObjectId(SAMPLE_ID),
            HelperAgreementLog.DEPLOYMENT_ID: ObjectId(SAMPLE_ID),
            HelperAgreementLog.STATUS: HelperAgreementLog.Status.AGREE_AND_ACCEPT.name,
        }
        helper_agreement_log = HelperAgreementLog.from_dict(helper_agreement_log_dict)
        repo.create_helper_agreement_log(helper_agreement_log=helper_agreement_log)
        helper_agreement_log_dict = remove_none_values(helper_agreement_log_dict)
        collection = MongoAuthorizationRepository.HELPER_AGREEMENT_LOG_COLLECTION
        db[collection].insert_one.assert_called_with(helper_agreement_log_dict)

    def test_success_retrieve_personal_documents(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        repo.retrieve_personal_documents(user_id=user_id)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].find_one.assert_called_with({User.ID_: ObjectId(user_id)})

    @freeze_time("2012-01-01")
    def test_success_create_personal_document(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        personal_document_dict = {
            PersonalDocument.NAME: "Test Name",
            PersonalDocument.FILE_TYPE: PersonalDocument.PersonalDocumentMediaType.PDF.name,
            PersonalDocument.FILE_OBJECT: {"bucket": "bucket_name", "key": "key"},
            PersonalDocument.CREATE_DATE_TIME: "2012-01-01T00:00:00.000000Z",
            PersonalDocument.UPDATE_DATE_TIME: "2012-01-01T00:00:00.000000Z",
        }
        personal_doc = PersonalDocument.from_dict(personal_document_dict)
        repo.create_personal_document(user_id=user_id, personal_doc=personal_doc)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].update.assert_called_with(
            {User.ID_: ObjectId(user_id)},
            {"$push": {User.PERSONAL_DOCUMENTS: personal_document_dict}},
            upsert=True,
        )

    def test_success_create_care_plan_group_log(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        log_dict = {CarePlanGroupLog.USER_ID: ObjectId(SAMPLE_ID)}
        log = CarePlanGroupLog.from_dict(log_dict)
        repo.create_care_plan_group_log(log=log)
        collection = MongoAuthorizationRepository.CARE_PLAN_GROUP_LOG_COLLECTION
        db[collection].insert_one.assert_called_with(remove_none_values(log_dict))

    def test_success_update_user_onfido_verification_status(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        applicant_id = SAMPLE_ID
        verification_status = 1
        repo.update_user_onfido_verification_status(
            applicant_id=applicant_id, verification_status=verification_status
        )
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].update_one.assert_called_with(
            {User.ONFIDO_APPLICANT_ID: applicant_id},
            {"$set": {User.VERIFICATION_STATUS: verification_status}},
        )

    def test_success_retrieve_simple_user_profile(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        repo.retrieve_simple_user_profile(user_id=user_id)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].find_one.assert_called_with(
            {User.ID_: ObjectId(user_id)},
            {
                User.TAGS: 0,
                User.TAGS_AUTHOR_ID: 0,
                User.RECENT_MODULE_RESULTS: 0,
            },
        )

    def test_success_retrieve_user(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        repo.retrieve_user(user_id=user_id)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].find_one.assert_called_with(filter={User.ID_: ObjectId(user_id)})

    def test_success_retrieve_all_user_profiles(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        role = Role.UserType.USER
        repo.retrieve_all_user_profiles(role=role)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].aggregate.assert_called_with(
            [
                self.expected_add_fields(),
                {
                    "$match": {
                        "roles.roleId": role,
                        "roles.userType": {
                            "$nin": [
                                Role.UserType.SERVICE_ACCOUNT,
                                Role.UserType.SUPER_ADMIN,
                            ]
                        },
                    }
                },
            ],
            allowDiskUse=True,
        )

    def test_success_retrieve_user_profiles_by_ids(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        ids = {SAMPLE_ID}
        repo.retrieve_user_profiles_by_ids(ids=ids)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].aggregate.assert_called_with(
            [
                self.expected_add_fields(),
                {"$match": {User.ID_: {"$in": [ObjectId(SAMPLE_ID)]}}},
            ],
            allowDiskUse=True,
        )

    def test_failure_retrieve_user_profiles_by_ids(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        INVALID_ID = "60c74f06616ac18c843f7a4"
        ids = {INVALID_ID}
        with self.assertRaises(InvalidRequestException):
            repo.retrieve_user_profiles_by_ids(ids=ids)

    def test_success_retrieve_assigned_to_user_proxies(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        repo.retrieve_assigned_to_user_proxies(user_id=user_id)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].find.assert_called_with(
            {
                User.ROLES: {
                    "$elemMatch": {
                        RoleAssignment.ROLE_ID: RoleName.PROXY,
                        RoleAssignment.RESOURCE: f"user/{user_id}",
                    }
                }
            }
        )

    @patch(f"{AUTH_REPO_PATH}.inject", MagicMock())
    def test_success_retrieve_staff(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        organization_id = SAMPLE_ID
        repo.retrieve_staff(organization_id=organization_id)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].aggregate.assert_called_with(
            [
                self.expected_add_fields(),
                {
                    "$match": {
                        "$and": [
                            {
                                "$or": [
                                    {
                                        "roles.roleId": {"$in": []},
                                        "roles.resource": "organization/600a8476a961574fb38157d5",
                                    },
                                    {
                                        "$and": [
                                            {"roles.resource": {"$in": []}},
                                            {"roles.roleId": {"$in": []}},
                                        ]
                                    },
                                ]
                            }
                        ]
                    }
                },
            ],
            allowDiskUse=True,
        )

    @patch(f"{AUTH_REPO_PATH}.MongoManagerAssignment")
    def test_success_retrieve_assigned_managers_ids_for_multiple_users(
        self, mongo_manager_mock
    ):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_ids = [SAMPLE_ID]
        repo.retrieve_assigned_managers_ids_for_multiple_users(user_ids=user_ids)
        mongo_manager_mock.objects.assert_called_with(userId__in=user_ids)

    @patch(f"{AUTH_REPO_PATH}.MongoManagerAssignment")
    def test_success_retrieve_assigned_managers_ids(self, mongo_manager_mock):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_id = SAMPLE_ID
        repo.retrieve_assigned_managers_ids(user_id=user_id)
        mongo_manager_mock.objects.assert_called_with(userId=user_id)

    @patch(f"{AUTH_REPO_PATH}.MongoManagerAssignment")
    def test_success_create_assignment_log(self, mongo_manager_mock):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        repo.create_assignment_log(mongo_manager_mock)
        mongo_manager_mock.save.assert_called_once()

    @patch(f"{AUTH_REPO_PATH}.MongoTagLog")
    def test_success_create_tag_log(self, tag_log_mock):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        tag_log = TagLog()
        repo.create_tag_log(tag_log)
        tag_log_mock.assert_called_once()

    def test_success_retrieve_users_with_user_role_including_only_fields(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        fields = (User.EMAIL, User.STATUS)
        repo.retrieve_users_with_user_role_including_only_fields(fields=fields)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].find.assert_called_with(
            {User.ROLES: {"$elemMatch": {"roleId": RoleName.USER}}},
            {User.EMAIL: 1},
        )

    def test_success_retrieve_users_count(self):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        repo.retrieve_users_count()
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].count_documents.assert_called_with(
            {
                "roles.roleId": {"$nin": [RoleName.SUPER_ADMIN, RoleName.HUMA_SUPPORT]},
                "roles.userType": {
                    "$nin": [Role.UserType.SERVICE_ACCOUNT, Role.UserType.SUPER_ADMIN]
                },
            }
        )

    @freeze_time("2012-01-01")
    @patch(f"{AUTH_REPO_PATH}.ObjectId")
    def test_success_create_user(self, mock_obj_id):
        mock_obj_id.return_value = SAMPLE_ID
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        user_dict = {
            User.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            User.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            User.EMAIL: "some_test_email@mail.com",
            User.ID_: SAMPLE_ID,
        }
        user = User.from_dict(user_dict)
        repo.create_user(user)
        collection = MongoAuthorizationRepository.USER_COLLECTION
        db[collection].insert_one.assert_called_with(user_dict, session=None)

    def test_fix_sort_params_for_module_sort(self):
        repo = MongoAuthorizationRepository(MagicMock(), MagicMock())
        sort = [("module", -1)]
        extra = SortParameters.Extra.from_dict(
            {
                Primitive.MODULE_ID: "testModule",
                Primitive.MODULE_CONFIG_ID: "61e0303f3547262976bd66bb",
            }
        )
        result = repo._fix_sort_params(sort, extra)
        self.assertEqual(
            [("recentModuleResults.61e0303f3547262976bd66bb.0.testModule.value", -1)],
            result,
        )

    @freeze_time("2012-01-01")
    def test_success_assign_user_labels(self):
        user_id = SAMPLE_ID
        assignee_id = SAMPLE_ID
        labels_dicts = get_sample_labels()
        labels = [Label.from_dict(label) for label in labels_dicts]

        expected_list = [
            {
                **label_dict,
                UserLabel.ASSIGNED_BY: ObjectId(assignee_id),
                UserLabel.ASSIGN_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
            }
            for label_dict in labels_dicts
        ]
        for label_dict in expected_list:
            label_dict.pop(Label.TEXT)
            label_dict.pop(Label.CREATE_DATE_TIME)
            label_dict.pop(Label.AUTHOR_ID)
            label_dict[UserLabel.LABEL_ID] = ObjectId(label_dict.pop(Label.ID))
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        collection = MongoAuthorizationRepository.USER_COLLECTION
        repo.assign_labels_to_user(user_id, labels=labels, assignee_id=assignee_id)
        db[collection].update_one.assert_called_with(
            {User.ID_: ObjectId(user_id)},
            {
                "$set": {
                    User.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                    User.LABELS: expected_list,
                }
            },
        )

    @patch(f"{AUTH_REPO_PATH}.MongoLabelLog")
    def test_success_create_label_log(self, label_log_mock):
        db = MagicMock()
        repo = MongoAuthorizationRepository(database=db, config=MockConfig())
        label_log = [LabelLog()]
        repo.create_label_logs(label_log)
        label_log_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
