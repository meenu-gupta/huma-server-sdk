from extensions.deployment.models.deployment import (
    SurgeryDetail,
    Deployment,
    SurgeryDetails,
    SurgeryDetailItem,
)
from extensions.tests.deployment.IntegrationTests.abstract_deployment_test_case_tests import (
    AbstractDeploymentTestCase,
)


def surgery_details():
    return {
        SurgeryDetails.OPERATION_TYPE: {
            SurgeryDetail.DISPLAY_STRING: "Operation Type",
            SurgeryDetail.PLACE_HOLDER: "Enter Operation Type",
            SurgeryDetail.ORDER: 2,
            SurgeryDetail.ITEMS: [
                {
                    SurgeryDetailItem.KEY: "key1",
                    SurgeryDetailItem.VALUE: "value1",
                    SurgeryDetailItem.ORDER: 0,
                }
            ],
        }
    }


class SurgeryDetailsTestCase(AbstractDeploymentTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(SurgeryDetailsTestCase, cls).setUpClass()
        cls.update_url = f"/api/extensions/v1beta/deployment/{cls.deployment_id}"

    def test_success_create_surgery_details(self):
        body = {"surgeryDetails": surgery_details()}
        rsp = self.flask_client.put(self.update_url, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment()
        self.assertDictEqual(surgery_details(), deployment["surgeryDetails"])

    def test_failure_create_surgery_details_empty_key(self):
        test_cases = [
            (SurgeryDetail.DISPLAY_STRING, ""),
            (SurgeryDetail.PLACE_HOLDER, ""),
            (SurgeryDetail.ITEMS, []),
        ]
        for key, value in test_cases:
            details = surgery_details()
            details[SurgeryDetails.OPERATION_TYPE][key] = value
            body = {Deployment.SURGERY_DETAILS: details}
            rsp = self.flask_client.put(
                self.update_url, json=body, headers=self.headers
            )
            self.assertEqual(403, rsp.status_code)
