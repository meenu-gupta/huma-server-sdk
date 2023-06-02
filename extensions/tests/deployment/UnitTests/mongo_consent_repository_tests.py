import unittest
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.mongo_consent_repository import (
    MongoConsentRepository,
)
from sdk.common.utils.validators import remove_none_values

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class MockPhoenixServerConfig:
    instance = MagicMock()


def test_deployment():
    return {
        Deployment.ID: SAMPLE_VALID_OBJ_ID,
        Deployment.CONSENT: {
            Consent.REVISION: 1,
            Consent.ENABLED: EnableStatus.ENABLED.name,
        },
    }


class MongoConsentRepositoryTestCase(unittest.TestCase):
    def test_success_retrieve_log_count(self):
        db = MagicMock()
        repo = MongoConsentRepository(
            database=db,
            config=MockPhoenixServerConfig(),
        )
        consent_id = SAMPLE_VALID_OBJ_ID
        user_id = SAMPLE_VALID_OBJ_ID
        revision = 1
        repo.retrieve_log_count(
            consent_id=consent_id, revision=revision, user_id=user_id
        )
        db[
            MongoConsentRepository.CONSENT_LOG_COLLECTION
        ].count_documents.assert_called_with(
            {
                ConsentLog.CONSENT_ID: ObjectId(consent_id),
                ConsentLog.USER_ID: ObjectId(user_id),
                ConsentLog.REVISION: revision,
            }
        )

    def test_success_retrieve_consented_users(self):
        db = MagicMock()
        repo = MongoConsentRepository(database=db, config=MockPhoenixServerConfig())
        consent_id = ObjectId(SAMPLE_VALID_OBJ_ID)
        aggregate_options = [
            {"$match": {ConsentLog.CONSENT_ID: consent_id}},
            {"$group": {"_id": "$userId"}},
        ]
        repo.retrieve_consented_users(consent_id=consent_id)
        db[MongoConsentRepository.CONSENT_LOG_COLLECTION].aggregate.assert_called_with(
            aggregate_options
        )

    def test_success_create_consent_log(self):
        db = MagicMock()
        repo = MongoConsentRepository(
            database=db,
            config=MockPhoenixServerConfig(),
        )
        deployment_id = SAMPLE_VALID_OBJ_ID
        consent_log = ConsentLog.from_dict(
            {
                ConsentLog.CONSENT_ID: SAMPLE_VALID_OBJ_ID,
                ConsentLog.DEPLOYMENT_ID: SAMPLE_VALID_OBJ_ID,
                ConsentLog.USER_ID: SAMPLE_VALID_OBJ_ID,
            }
        )
        db[repo.DEPLOYMENT_COLLECTION].find_one.return_value = {
            Deployment.ID: SAMPLE_VALID_OBJ_ID,
            Deployment.CONSENT: {
                Consent.REVISION: 1,
                Consent.ENABLED: EnableStatus.ENABLED.name,
            },
        }
        repo.create_consent_log(deployment_id=deployment_id, consent_log=consent_log)
        db[MongoConsentRepository.DEPLOYMENT_COLLECTION].find_one.assert_called_with(
            {
                Deployment.ID_: ObjectId(deployment_id),
                f"{Deployment.CONSENT}.{Consent.ID}": ObjectId(consent_log.consentId),
            }
        )
        db[MongoConsentRepository.CONSENT_LOG_COLLECTION].insert_one.assert_called_with(
            remove_none_values(
                consent_log.to_dict(ignored_fields=(Consent.CREATE_DATE_TIME,))
            ),
            session=None,
        )

    def test_success_create_consent(self):
        db = MagicMock()
        db.deployment.find_one.return_value = test_deployment()
        repo = MongoConsentRepository(
            database=db,
            config=MockPhoenixServerConfig(),
        )
        deployment_id = SAMPLE_VALID_OBJ_ID
        consent = Consent.from_dict({Consent.ENABLED: EnableStatus.ENABLED.name})
        repo.create_consent(deployment_id=deployment_id, consent=consent)
        consent_dict = remove_none_values(
            {
                **consent.to_dict(ignored_fields=(Consent.CREATE_DATE_TIME,)),
                Consent.ID: ObjectId(consent.id),
            }
        )
        db[MongoConsentRepository.DEPLOYMENT_COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {"$set": {Deployment.CONSENT: consent_dict}},
            session=None,
        )


if __name__ == "__main__":
    unittest.main()
