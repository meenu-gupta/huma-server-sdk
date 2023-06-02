import unittest
from unittest.mock import MagicMock

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)
from extensions.identity_verification.repository.mongo_verification_log_repository import (
    MongoVerificationLogRepository,
)

VERIFICATION_LOG_PATH = (
    "extensions.identity_verification.repository.mongo_verification_log_repository"
)
COLLECTION = MongoVerificationLogRepository.VERIFICATION_LOG_COLLECTION
SAMPLE_ID = "600a8476a961574fb38157d5"


class MongoVerificationLogTestCase(unittest.TestCase):
    def test_success_retrieve_verification_log(self):
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        db = MagicMock()
        config = MagicMock()
        repo = MongoVerificationLogRepository(database=db, config=config)
        repo.retrieve_verification_log(user_id=user_id, deployment_id=deployment_id)
        db[COLLECTION].find_one.assert_called_with(
            {
                VerificationLog.USER_ID: ObjectId(user_id),
                VerificationLog.DEPLOYMENT_ID: ObjectId(deployment_id),
            }
        )

    @freeze_time("2012-01-01")
    def test_success_create_or_update_verification_log(self):
        verification_log = MagicMock()
        verification_log.userId = SAMPLE_ID
        verification_log.deploymentId = SAMPLE_ID
        db = MagicMock()
        config = MagicMock()
        repo = MongoVerificationLogRepository(database=db, config=config)
        repo.create_or_update_verification_log(verification_log)
        db[COLLECTION].update_one.assert_called_with(
            {
                VerificationLog.USER_ID: ObjectId(verification_log.userId),
                VerificationLog.DEPLOYMENT_ID: ObjectId(verification_log.deploymentId),
            },
            {
                "$set": {
                    VerificationLog.DOCUMENTS: verification_log.to_dict()
                    .__getitem__()
                    .__add__(),
                    VerificationLog.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                }
            },
            upsert=True,
        )


if __name__ == "__main__":
    unittest.main()
