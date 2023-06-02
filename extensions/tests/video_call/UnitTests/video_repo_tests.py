import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from extensions.twilio_video.models.mongo_twilio_video import MongoVideoCall
from extensions.twilio_video.repository.mongo_video_repository import (
    MongoVideoCallRepository,
)

USER_ID = "600a8476a961574fb38157d5"


class VideoRepoCase(unittest.TestCase):
    @patch("extensions.twilio_video.repository.mongo_video_repository.MongoVideoCall")
    def test_delete_video_data_on_user_delete(self, mongo_db):
        session = MagicMock()
        db = MagicMock()
        mongo_db._get_db.return_value = db
        mongo_db.USER_ID = MongoVideoCall.USER_ID
        repo = MongoVideoCallRepository()
        repo.delete_user_video(user_id=USER_ID, session=session)
        user_id = ObjectId(USER_ID)
        db[repo.VIDEO_CALL_COLLECTION].delete_many.assert_called_with(
            {MongoVideoCall.USER_ID: user_id}, session=session
        )


if __name__ == "__main__":
    unittest.main()
