from datetime import datetime, date

from flask import jsonify

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import default_field

from sdk.common.utils.flask_request_utils import PhoenixJsonEncoder
from sdk.common.utils.validators import (
    utc_str_val_to_field,
    utc_str_to_date,
)
from sdk.tests.test_case import SdkTestCase


@convertibleclass
class TestModel:
    START_DATE_TIME = "startDateTime"
    BIRTH_DATE = "birthDate"

    startDateTime: datetime = default_field(
        metadata=meta(value_to_field=utc_str_val_to_field)
    )
    birthDate: date = default_field(metadata=meta(value_to_field=utc_str_to_date))


def sample_test_model():
    return {
        TestModel.START_DATE_TIME: "2020-05-17T01:00:00.000000Z",
        TestModel.BIRTH_DATE: "2020-05-17",
    }


class EncoderTestCase(SdkTestCase):
    components = []
    API_URL = "/test-model"

    def setUp(self):
        super().setUp()
        self.test_app.json_encoder = PhoenixJsonEncoder

        @self.test_app.route(self.API_URL)
        def model_response():
            response = TestModel.from_dict(sample_test_model())
            return jsonify(response.to_dict()), 200

    def test_retrieve_test_model(self):
        resp = self.flask_client.get(self.API_URL)
        self.assertDictEqual(sample_test_model(), resp.json)
        self.assertEqual(200, resp.status_code)
