from unittest import TestCase

from extensions.module_result.router.module_result_requests import (
    SearchModuleResultsRequestObject,
    RetrieveModuleResultRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_USER_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_DEPLOYMENT_ID = "5fe0a9c0d4696db1c7cd759a"
MODULE_RESULT_ID = "602f641b90517902d644eff2"


class TestSearchModuleResultsRequestObject(TestCase):
    def test_failure_no_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SearchModuleResultsRequestObject.from_dict(
                {
                    SearchModuleResultsRequestObject.MODULES: ["first_id", "second_id"],
                    SearchModuleResultsRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                    SearchModuleResultsRequestObject.ROLE: "role",
                }
            )

    def test_failure_no_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SearchModuleResultsRequestObject.from_dict(
                {
                    SearchModuleResultsRequestObject.MODULES: ["first_id", "second_id"],
                    SearchModuleResultsRequestObject.USER_ID: SAMPLE_USER_ID,
                    SearchModuleResultsRequestObject.ROLE: "role",
                }
            )

    def test_failure_no_role(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SearchModuleResultsRequestObject.from_dict(
                {
                    SearchModuleResultsRequestObject.MODULES: ["first_id", "second_id"],
                    SearchModuleResultsRequestObject.USER_ID: SAMPLE_USER_ID,
                    SearchModuleResultsRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                }
            )

    def test_failure_no_modules(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SearchModuleResultsRequestObject.from_dict(
                {
                    SearchModuleResultsRequestObject.USER_ID: SAMPLE_USER_ID,
                    SearchModuleResultsRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                    SearchModuleResultsRequestObject.ROLE: "role",
                }
            )

    def test_success_create_search_module_results_request_object(self):
        request_object = SearchModuleResultsRequestObject.from_dict(
            {
                SearchModuleResultsRequestObject.MODULES: ["first_id", "second_id"],
                SearchModuleResultsRequestObject.USER_ID: SAMPLE_USER_ID,
                SearchModuleResultsRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                SearchModuleResultsRequestObject.ROLE: "role",
            }
        )
        self.assertIsNotNone(request_object)


class TestRetrieveModuleResultRequestObject(TestCase):
    def test_success_create_retrieve_module_result_req_obj(self):
        request_object = RetrieveModuleResultRequestObject.from_dict(
            {
                RetrieveModuleResultRequestObject.USER_ID: SAMPLE_USER_ID,
                RetrieveModuleResultRequestObject.MODULE_RESULT_ID: MODULE_RESULT_ID,
                RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: "some_primitive_type",
            }
        )
        self.assertIsNotNone(request_object)

    def test_failure_no_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveModuleResultRequestObject.from_dict(
                {
                    RetrieveModuleResultRequestObject.MODULE_RESULT_ID: MODULE_RESULT_ID,
                    RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: "some_primitive_type",
                }
            )

    def test_failure_not_valid_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveModuleResultRequestObject.from_dict(
                {
                    RetrieveModuleResultRequestObject.USER_ID: "ggg",
                    RetrieveModuleResultRequestObject.MODULE_RESULT_ID: MODULE_RESULT_ID,
                    RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: "some_primitive_type",
                }
            )

    def test_failure_no_module_result_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveModuleResultRequestObject.from_dict(
                {
                    RetrieveModuleResultRequestObject.USER_ID: SAMPLE_USER_ID,
                    RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: "some_primitive_type",
                }
            )

    def test_failure_no_primitive_type(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveModuleResultRequestObject.from_dict(
                {
                    RetrieveModuleResultRequestObject.USER_ID: SAMPLE_USER_ID,
                    RetrieveModuleResultRequestObject.MODULE_RESULT_ID: MODULE_RESULT_ID,
                }
            )
