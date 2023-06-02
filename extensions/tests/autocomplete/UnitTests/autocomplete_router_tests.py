import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.autocomplete.router.autocomplete_router import (
    retrieve_autocomplete,
    api,
)

AUTOCOMPLETE_ROUTER_PATH = "extensions.autocomplete.router.autocomplete_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


class AutocompleteRouterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        api.policy_enabled = False

    @patch(f"{AUTOCOMPLETE_ROUTER_PATH}.jsonify")
    @patch(f"{AUTOCOMPLETE_ROUTER_PATH}.SearchAutocompleteResultUseCase")
    @patch(f"{AUTOCOMPLETE_ROUTER_PATH}.SearchAutocompleteRequestObject")
    @patch(f"{AUTOCOMPLETE_ROUTER_PATH}.g")
    def test_success_retrieve_autocomplete(self, g_mock, req_obj, use_case, jsonify):
        payload = {"a": "b"}
        g_mock.authz_user = MagicMock()
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_autocomplete()
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.LANGUAGE: g_mock.authz_user.get_language()}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)


if __name__ == "__main__":
    unittest.main()
