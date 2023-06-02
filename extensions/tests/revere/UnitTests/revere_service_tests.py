import unittest
from unittest.mock import MagicMock, patch

from extensions.revere.repository.mongo_revere_repository import (
    MongoRevereTestRepository,
)
from extensions.revere.repository.revere_repository import RevereTestRepository
from extensions.revere.service.revere_service import RevereTestService
from extensions.tests.revere.IntegrationTests.revere_router_tests import (
    retrieve_audio_file,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

MONGO_REPO_PATH = "extensions.revere.repository.mongo_revere_repository"
SAMPLE_ID = "600a8476a961574fb38157d5"
REVERE_COLLECTION = MongoRevereTestRepository.REVERE_TEST_COLLECTION
RETRIEVE_AUDIO_PATH = (
    "extensions.revere.service.revere_service.RevereTestService.retrieve_audio_file"
)


class MockInject(MagicMock):
    instance = MagicMock()


@patch(f"{MONGO_REPO_PATH}.inject", MagicMock())
class RevereServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:

        server_config = MagicMock()

        def bind(binder):
            binder.bind(PhoenixServerConfig, server_config)
            binder.bind_to_provider(RevereTestRepository, MagicMock())

        inject.clear_and_configure(bind)
        self.repo = MockInject.instance(RevereTestRepository)
        self.fs = MagicMock()

        return super().setUp()

    def expect_process_audio_result_failure(self):
        revere_service = RevereTestService(repo=self.repo, fs=self.fs)
        s3_object = MagicMock()

        with self.assertRaises(InvalidRequestException):
            revere_service.process_audio_result(s3_audio_file=s3_object)

    @patch(RETRIEVE_AUDIO_PATH)
    def test_failure_processing_wrong_audio_format(self, retrieve_audio_file_service):
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/sample.wav"
        )
        self.expect_process_audio_result_failure()

    @patch(RETRIEVE_AUDIO_PATH)
    def test_failure_processing_wrong_audio_format_with_wrong_extension(
        self, retrieve_audio_file_service
    ):
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/wrong_extension_sample.mp4"
        )
        self.expect_process_audio_result_failure()


if __name__ == "__main__":
    unittest.main()
