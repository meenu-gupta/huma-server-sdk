import unittest
from unittest.mock import patch, MagicMock

from sdk.common.adapter.minio.minio_utils import minio_is_ready


class ResponseMock:
    instance = MagicMock()
    status_code = 200


class MinioUtilsTestCase(unittest.TestCase):
    @patch("sdk.common.adapter.minio.minio_utils.requests")
    def test_success_minio_is_ready(self, requests):
        url = "some_url.com"
        requests.get.return_value = ResponseMock()
        res = minio_is_ready(url)
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
