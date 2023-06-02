import unittest
from copy import copy

from extensions.identity_verification.router.identity_verification_requests import (
    OnfidoVerificationResult,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

ONFIDO_VERIFICATION_RESULT_SAMPLE = {
    "id": "26411331-15e2-4a11-9ba0-b135d4131902",
    "created_at": "2021-02-24T20:57:56Z",
    "status": "complete",
    "redirect_uri": None,
    "result": "clear",
    "sandbox": True,
    "tags": [],
    "results_uri": "https://dashboard.onfido.com/checks/26411331-15e2-4a11-9ba0-b135d4131902",
    "form_uri": None,
    "paused": False,
    "version": "3.0",
    "report_ids": ["93bb36ee-6c7f-468a-9762-7985f4f2a0d6"],
    "href": "/v3/checks/26411331-15e2-4a11-9ba0-b135d4131902",
    "applicant_id": "some_applicant_id",
    "applicant_provides_data": False,
}


class IdentityVerificationTestCase(unittest.TestCase):
    def test_success_onfido_verification_result(self):
        res = OnfidoVerificationResult.from_dict(ONFIDO_VERIFICATION_RESULT_SAMPLE)
        self.assertIsNotNone(res)

    def test_failure_onfido_verification_result_invalid_status(self):
        sample = copy(ONFIDO_VERIFICATION_RESULT_SAMPLE)
        sample[OnfidoVerificationResult.STATUS] = "invalid_status"
        with self.assertRaises(ConvertibleClassValidationError):
            OnfidoVerificationResult.from_dict(sample)

    def test_failure_onfido_verification_result_invalid_result(self):
        sample = copy(ONFIDO_VERIFICATION_RESULT_SAMPLE)
        sample[OnfidoVerificationResult.RESULT] = "invalid_result"
        with self.assertRaises(ConvertibleClassValidationError):
            OnfidoVerificationResult.from_dict(sample)


if __name__ == "__main__":
    unittest.main()
