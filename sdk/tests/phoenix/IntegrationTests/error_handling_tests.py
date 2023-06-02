from pymongo.errors import OperationFailure

from sdk.tests.test_case import SdkTestCase


class ErrorHandlingTests(SdkTestCase):
    components = []

    @classmethod
    def setUpClass(cls) -> None:
        super(ErrorHandlingTests, cls).setUpClass()

        @cls.test_app.route("/failure", methods=["POST"])
        def failure_route():
            raise OperationFailure("Some error")

    def test_operation_failure_handling(self):
        rsp = self.flask_client.post("/failure")
        self.assertEqual(200, rsp.status_code)
        self.assertEqual([], rsp.json)
