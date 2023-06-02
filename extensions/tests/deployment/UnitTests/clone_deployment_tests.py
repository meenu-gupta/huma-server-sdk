import unittest
from copy import copy

from extensions.deployment.router.deployment_requests import (
    CloneDeploymentRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_REQUEST_OBJECT = {
    CloneDeploymentRequestObject.NAME: "name",
    CloneDeploymentRequestObject.REFERENCE_ID: "60a53912a45b0ebe013750c9",
}


class CloneDeploymentRequestObjectTestCase(unittest.TestCase):
    def test_success_create(self):
        CloneDeploymentRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

    def test_failure_create_without_name(self):
        request_obj = copy(SAMPLE_REQUEST_OBJECT)
        request_obj.pop(CloneDeploymentRequestObject.NAME, None)
        with self.assertRaises(ConvertibleClassValidationError):
            CloneDeploymentRequestObject.from_dict(request_obj)

    def test_failure_create_without_reference_id(self):
        request_obj = copy(SAMPLE_REQUEST_OBJECT)
        request_obj.pop(CloneDeploymentRequestObject.REFERENCE_ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            CloneDeploymentRequestObject.from_dict(request_obj)

    def test_failure_create_with_invalid_reference_id(self):
        request_obj = copy(SAMPLE_REQUEST_OBJECT)
        request_obj[CloneDeploymentRequestObject.REFERENCE_ID] = "invalid"
        with self.assertRaises(ConvertibleClassValidationError):
            CloneDeploymentRequestObject.from_dict(request_obj)


if __name__ == "__main__":
    unittest.main()
