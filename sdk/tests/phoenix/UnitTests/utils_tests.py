import uuid
from unittest import TestCase
from unittest.mock import MagicMock

from flask import Response

from sdk.common.utils.flask_request_utils import dump_response, dump_request


class MockRequest:
    instance = MagicMock()
    url = MagicMock(return_value="/")
    method = MagicMock(return_value="GET")
    cookies = MagicMock(return_value=None)
    data = MagicMock(return_value=None)
    headers = MagicMock(return_value=None)
    args = MagicMock(return_value=None)
    form = MagicMock(return_value=None)
    remote_addr = MagicMock(return_value=None)
    files = MagicMock(return_value=None)


class DumpRequestTest(TestCase):
    def test_success_dump_req_data(self):
        res = dump_response(req_uuid=uuid.uuid4().hex, resp=Response(status=200))
        keywords_to_be_present = ["request_id", "status_code", "status", "headers"]
        for keyword in keywords_to_be_present:
            self.assertIn(keyword, res)


class DumpResponse(TestCase):
    def test_success_dump_response_data(self):
        res = dump_request(req_uuid=uuid.uuid4().hex, req=MockRequest())
        keywords_to_be_present = [
            "request_id",
            "url",
            "cookies",
            "method",
            "headers",
            "args",
            "form",
            "remote_addr",
            "files",
        ]
        for keyword in keywords_to_be_present:
            self.assertIn(keyword, res)
