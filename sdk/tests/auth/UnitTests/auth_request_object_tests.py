from unittest import TestCase

from sdk.auth.use_case.auth_request_objects import SignOutRequestObjectV1
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.tests.auth.test_helpers import sample_sign_out_req_obj_v1


class TestSignOutRequestObjectV1(TestCase):
    def test_success_sign_out_req_obj(self):
        try:
            SignOutRequestObjectV1.from_dict(sample_sign_out_req_obj_v1())
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_refresh_token(self):
        sign_out_dict = sample_sign_out_req_obj_v1()
        sign_out_dict.pop(SignOutRequestObjectV1.REFRESH_TOKEN)
        with self.assertRaises(ConvertibleClassValidationError):
            SignOutRequestObjectV1.from_dict(sign_out_dict)

    def test_failure_no_user_id(self):
        sign_out_dict = sample_sign_out_req_obj_v1()
        sign_out_dict.pop(SignOutRequestObjectV1.USER_ID)
        with self.assertRaises(ConvertibleClassValidationError):
            SignOutRequestObjectV1.from_dict(sign_out_dict)
