import datetime
import unittest
from unittest.mock import MagicMock

import pytz

from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.flask_request_utils import (
    get_key_value_from_request,
    get_request_json_dict_or_raise_exception,
    get_request_json_list_or_raise_exception,
    get_http_user_agent_from_request,
    PhoenixJsonEncoder,
    validate_request_body_type_is_object,
)

# This payload is real traceback from Sentry issues:
# https://sentry.io/organizations/huma-therapeutics-ltd-qc/issues/2600313243/?environment=qa&project=5738131
SAMPLE_STRINGFIED_PAYLOAD = [
    "{legAffected=2,"
    "startDateTime=2021-08-24T09:55:57.895Z,"
    "deploymentId=***,"
    "questionnaireId=***,"
    "type=OxfordKneeScore,"
    "deviceName=Android,"
    "version=1,"
    "questionnaireName=Oxford Knee Score}"
]


class FlaskRequestUtilsTestCase(unittest.TestCase):
    def test_get_json_body_in_wrong_format(self):
        req = MagicMock(json=SAMPLE_STRINGFIED_PAYLOAD)
        with self.assertRaises(InvalidRequestException):
            get_key_value_from_request(req, "a")

    def test_success_get_request_json_or_raise_exception_dict(self):
        body = {"a": "b"}
        req = MagicMock(json=body)
        res = get_request_json_dict_or_raise_exception(req)
        self.assertEqual(res, body)

    def test_success_get_request_json_or_raise_exception_list(self):
        body = [{"a": "b"}]
        req = MagicMock(json=body)
        res = get_request_json_list_or_raise_exception(req)
        self.assertEqual(res, body)

    def test_failure_get_request_json_or_raise_exception_list_but_dict_was_passed(self):
        body = {"a": "b"}
        req = MagicMock(json=body)
        with self.assertRaises(InvalidRequestException):
            get_request_json_list_or_raise_exception(req)

    def test_failure_get_request_json_or_raise_exception_dict_but_list_was_passed(self):
        body = [{"a": "b"}]
        req = MagicMock(json=body)
        with self.assertRaises(InvalidRequestException):
            get_request_json_dict_or_raise_exception(req)

    def test_success_validate_request_body_type(self):
        body = {"a": "b"}
        req = MagicMock(json=body)
        res = validate_request_body_type_is_object(req)
        self.assertEqual(res, body)

    def test_success_validate_request_body_type_empty_body(self):
        body = {}
        req = MagicMock(json=body)
        res = validate_request_body_type_is_object(req)
        self.assertEqual(res, body)

    def test_failure_validate_request_body_type_when_body_type_is_list(self):
        body = [{"a": "b"}]
        req = MagicMock(json=body)
        with self.assertRaises(InvalidRequestException):
            validate_request_body_type_is_object(req)

    @staticmethod
    def _mock_request_with_environ(user_agent: dict) -> MagicMock:
        req = MagicMock(json={})
        req.headers = MagicMock()
        req.headers.get.return_value = user_agent
        return req

    def test_failure_get_http_user_agent_from_request_no_user_agent(self):
        req = self._mock_request_with_environ({})
        with self.assertRaises(InvalidRequestException):
            get_http_user_agent_from_request(req)

    def test_success_get_http_user_agent_from_request(self):
        user_agent = {"HTTP_USER_AGENT": "werkzeug/1.0.1"}
        req = self._mock_request_with_environ(user_agent)
        rsp = get_http_user_agent_from_request(req)
        self.assertEqual(rsp, user_agent)

    def test_pheonix_custom_encoder_datetime_conversion(self):
        datetime_object = datetime.datetime(2020, 5, 17, 1, tzinfo=pytz.UTC)
        test_date_str = "2020-05-17T01:00:00.000000Z"
        datetime_str = PhoenixJsonEncoder().default(datetime_object)
        self.assertEqual(test_date_str, datetime_str)


if __name__ == "__main__":
    unittest.main()
