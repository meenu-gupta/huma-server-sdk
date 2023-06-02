import unittest
from unittest.mock import patch, MagicMock

from sdk.common.exceptions.exceptions import BucketFileDoesNotExist
from sdk.common.adapter.gcp.gcs_config import GCSConfig
from sdk.common.adapter.gcp.gcs_file_storage_adapter import GCSFileStorageAdapter

GCS_CONFIG = {GCSConfig.SERVICE_ACCOUNT_KEY_FILE_PATH: ""}


class GCSFileStorageAdapterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gcs_config = GCSConfig.from_dict(GCS_CONFIG)

    @patch("sdk.common.adapter.gcp.gcs_file_storage_adapter.storage")
    def _gcs_adapter_with_none_blob(self, mock_storage):
        gcs_adapter = GCSFileStorageAdapter(self.gcs_config)
        mock_gcs_client = mock_storage.Client.return_value
        mock_bucket = MagicMock()
        mock_bucket.get_blob.return_value = None
        mock_gcs_client.bucket.return_value = mock_bucket
        return gcs_adapter

    def test_failure_download_file(self):
        gcs_adapter = self._gcs_adapter_with_none_blob()
        with self.assertRaises(BucketFileDoesNotExist):
            gcs_adapter.download_file("", "object_name")

    def test_failure_generate_presigned_url__no_file_exists(self):
        gcs_adapter = self._gcs_adapter_with_none_blob()
        with self.assertRaises(BucketFileDoesNotExist):
            gcs_adapter.get_pre_signed_url("", "object_name")


if __name__ == "__main__":
    unittest.main()
