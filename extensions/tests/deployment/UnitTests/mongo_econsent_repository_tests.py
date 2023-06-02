import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from bson import ObjectId
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.mongo_econsent_repository import (
    MongoEConsentRepository,
)
from extensions.exceptions import EconsentWithdrawalError
from pymongo import ReturnDocument
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.validators import remove_none_values

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"
SAMPLE_VALID_OBJ_ID_2 = "60a20766c85cd55b38c89e12"
MONGO_ECONSENT_REPO_PATH = "extensions.deployment.repository.mongo_econsent_repository"


class MockPhoenixServerConfig:
    instance = MagicMock()


def deployment():
    return {
        Deployment.ID: SAMPLE_VALID_OBJ_ID,
        Deployment.ECONSENT: {
            EConsent.REVISION: 1,
            EConsent.ENABLED: EnableStatus.ENABLED.name,
            EConsent.TITLE: "Test Title",
            EConsent.OVERVIEW_TEXT: "Test Overview Text",
            EConsent.CONTACT_TEXT: "Test Contact Text",
            EConsent.SECTIONS: [
                {
                    EConsentSection.SECTION_TYPE: EConsentSection.EConsentSectionType.INTRODUCTION.name,
                    EConsentSection.CONTENT_TYPE: EConsentSection.ContentType.IMAGE.value,
                }
            ],
        },
    }


class MockDeploymentRepository:
    instance = MagicMock()
    retrieve_deployment = MagicMock(return_value=Deployment.from_dict(deployment()))


class MongoEConsentRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.deployment_repo = MockDeploymentRepository()
        self.repo = MongoEConsentRepository(
            database=self.db,
            config=MockPhoenixServerConfig(),
            repo=self.deployment_repo,
        )

    def test_success_retrieve_log_count(self):

        self.repo.retrieve_log_count(
            consent_id=SAMPLE_VALID_OBJ_ID, revision=1, user_id=SAMPLE_VALID_OBJ_ID
        )
        filter_options = {
            EConsentLog.ECONSENT_ID: ObjectId(SAMPLE_VALID_OBJ_ID),
            EConsentLog.USER_ID: ObjectId(SAMPLE_VALID_OBJ_ID),
            EConsentLog.REVISION: 1,
        }
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].count_documents.assert_called_with(filter_options)

    def test_success_retrieve_latest_econsent(self):
        self.repo.retrieve_latest_econsent(deployment_id=ObjectId(SAMPLE_VALID_OBJ_ID))
        self.deployment_repo.retrieve_deployment.assert_called_with(
            deployment_id=SAMPLE_VALID_OBJ_ID
        )

    def test_create_econsent_log(self):
        econsent_log = EConsentLog.from_dict(
            {
                EConsentLog.ECONSENT_ID: SAMPLE_VALID_OBJ_ID,
                EConsentLog.USER_ID: SAMPLE_VALID_OBJ_ID,
                EConsentLog.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID,
            }
        )
        deployment_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        self.db[self.repo.DEPLOYMENT_COLLECTION].find_one.return_value = {
            Deployment.ID: SAMPLE_VALID_OBJ_ID,
            Deployment.ECONSENT: {
                EConsent.REVISION: 1,
                EConsent.ENABLED: EnableStatus.ENABLED.name,
                EConsent.ID: SAMPLE_VALID_OBJ_ID,
            },
        }
        self.repo.create_econsent_log(
            deployment_id=deployment_id, econsent_log=econsent_log
        )
        self.db[self.repo.DEPLOYMENT_COLLECTION].find_one.assert_called_with(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.ECONSENT}.{EConsent.ID}": ObjectId(
                    econsent_log.econsentId
                ),
            }
        )
        econsent_user_dict = econsent_log.to_dict(
            ignored_fields=(EConsentLog.CREATE_DATE_TIME,)
        )
        self.db[
            MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        ].insert_one.assert_called_with(
            remove_none_values(econsent_user_dict), session=None
        )

    def test_success_retrieve_consented_users(self):
        db = MagicMock()
        deployment_repo = MockDeploymentRepository()
        repo = MongoEConsentRepository(
            database=db,
            config=MockPhoenixServerConfig(),
            repo=deployment_repo,
        )
        econsent_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        repo.retrieve_consented_users(econsent_id=econsent_id)
        query = {
            "$match": {
                EConsentLog.ECONSENT_ID: econsent_id,
                "$or": [
                    {EConsentLog.CONSENT_OPTION: None},
                    {
                        EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                    },
                ],
            }
        }
        aggregate_options = [query, {"$group": {"_id": "$userId"}}]
        db[
            MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        ].aggregate.assert_called_with(aggregate_options)

    def test_success_create_econsent(self):
        dep = deployment()
        dep[Deployment.ID_] = dep.pop(Deployment.ID)
        self.db.deployment.find_one.return_value = dep
        deployment_id = SAMPLE_VALID_OBJ_ID
        econsent = EConsent.from_dict(
            {
                EConsent.REVISION: 1,
                EConsent.ENABLED: EnableStatus.ENABLED.name,
                EConsent.TITLE: "Test Title",
                EConsent.OVERVIEW_TEXT: "Test Overview Text",
                EConsent.CONTACT_TEXT: "Test Contact Text",
                EConsent.SECTIONS: [
                    {
                        EConsentSection.SECTION_TYPE: EConsentSection.EConsentSectionType.INTRODUCTION.name,
                        EConsentSection.CONTENT_TYPE: EConsentSection.ContentType.IMAGE.value,
                    }
                ],
            }
        )
        self.repo.create_econsent(
            deployment_id=ObjectId(deployment_id), econsent=econsent
        )
        expected_call = econsent.to_dict(ignored_fields=(EConsent.CREATE_DATE_TIME,))
        expected_call[EConsent.ID] = ObjectId(expected_call[EConsent.ID])
        query = {"$set": {Deployment.ECONSENT: remove_none_values(expected_call)}}
        self.db[
            MongoEConsentRepository.DEPLOYMENT_COLLECTION
        ].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)}, query, session=None
        )

    def test_success_update_user_econsent_pdf_location(self):
        pdf_location = "test_location/"
        inserted_id = SAMPLE_VALID_OBJ_ID
        self.repo.update_user_econsent_pdf_location(
            pdf_location=pdf_location, inserted_id=inserted_id
        )
        self.db[
            MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        ].update_one.assert_called_with(
            {EConsentLog.ID_: ObjectId(inserted_id)},
            {"$set": {EConsentLog.PDF_LOCATION: pdf_location}},
            session=None,
        )

    @patch(f"{MONGO_ECONSENT_REPO_PATH}.datetime")
    def test_success_retrieve_econsent_pdfs(self, datetime_patch):
        datetime_isoformat = datetime.utcnow().isoformat()
        datetime_patch.utcnow.return_value.isoformat.return_value = datetime_isoformat

        econsent_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        user_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        self.repo.retrieve_econsent_pdfs(econsent_id=econsent_id, user_id=user_id)
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].find.assert_called_with(
            {
                EConsentLog.USER_ID: user_id,
                EConsentLog.ECONSENT_ID: econsent_id,
                "$or": [
                    {EConsentLog.END_DATE_TIME: None},
                    {EConsentLog.END_DATE_TIME: {"$gt": datetime_isoformat}},
                ],
            }
        )

    @patch(f"{MONGO_ECONSENT_REPO_PATH}.datetime")
    def test_success_withdraw_econsent(self, datetime_patch):
        datetime_format = datetime.utcnow()
        datetime_patch.utcnow.return_value = datetime_format
        mock_object_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        self.repo.withdraw_econsent(log_id=mock_object_id)
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].update_one.assert_called_with(
            {EConsentLog.ID_: mock_object_id},
            {"$set": {EConsentLog.END_DATE_TIME: datetime_format}},
        )

    @patch(f"{MONGO_ECONSENT_REPO_PATH}.datetime")
    def test_success_retrieve_signed_econsent_log(self, datetime_patch):
        datetime_isoformat = datetime.utcnow().isoformat()
        datetime_patch.utcnow.return_value.isoformat.return_value = datetime_isoformat
        mock_object_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.repo.retrieve_signed_econsent_log(
            log_id=mock_object_id, user_id=mock_object_id
        )
        self.db[collection].find_one.assert_called_with(
            {
                EConsentLog.ID_: mock_object_id,
                EConsentLog.USER_ID: mock_object_id,
                "$and": [
                    {
                        "$or": [
                            {EConsentLog.CONSENT_OPTION: None},
                            {
                                EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                            },
                        ]
                    },
                    {
                        "$or": [
                            {EConsentLog.END_DATE_TIME: None},
                            {EConsentLog.END_DATE_TIME: {"$gt": datetime_isoformat}},
                        ]
                    },
                ],
            },
        )

    def test_failure_retrieve_signed_econsent_log(self):
        mock_object_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].find_one.return_value = None
        with self.assertRaises(ObjectDoesNotExist):
            self.repo.retrieve_signed_econsent_log(
                log_id=mock_object_id, user_id=mock_object_id
            )

    @patch(f"{MONGO_ECONSENT_REPO_PATH}.datetime")
    def test_success_retrieve_user_econsent_logs(self, datetime_patch):
        datetime_isoformat = datetime.utcnow().isoformat()
        datetime_patch.utcnow.return_value.isoformat.return_value = datetime_isoformat
        econsent_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        user_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        self.repo.retrieve_signed_econsent_logs(
            econsent_id=econsent_id, user_id=user_id
        )
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].find.assert_called_with(
            {
                EConsentLog.ECONSENT_ID: econsent_id,
                EConsentLog.USER_ID: user_id,
                "$and": [
                    {
                        "$or": [
                            {EConsentLog.CONSENT_OPTION: None},
                            {
                                EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                            },
                        ]
                    },
                    {
                        "$or": [
                            {EConsentLog.END_DATE_TIME: None},
                            {EConsentLog.END_DATE_TIME: {"$gt": datetime_isoformat}},
                        ]
                    },
                ],
            }
        )

    @patch(f"{MONGO_ECONSENT_REPO_PATH}.datetime")
    def test_success_retrieve_econsent_logs(self, datetime_patch):
        datetime_isoformat = datetime.utcnow().isoformat()
        datetime_patch.utcnow.return_value.isoformat.return_value = datetime_isoformat
        econsent_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        self.repo.retrieve_signed_econsent_logs(econsent_id=econsent_id, user_id=None)
        collection = MongoEConsentRepository.ECONSENT_LOG_COLLECTION
        self.db[collection].find.assert_called_with(
            {
                EConsentLog.ECONSENT_ID: econsent_id,
                "$and": [
                    {
                        "$or": [
                            {EConsentLog.CONSENT_OPTION: None},
                            {
                                EConsentLog.CONSENT_OPTION: EConsentLog.EConsentOption.UNDERSTAND_AND_ACCEPT
                            },
                        ]
                    },
                    {
                        "$or": [
                            {EConsentLog.END_DATE_TIME: None},
                            {EConsentLog.END_DATE_TIME: {"$gt": datetime_isoformat}},
                        ]
                    },
                ],
            }
        )


if __name__ == "__main__":
    unittest.main()
