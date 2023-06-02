from extensions.module_result.models.primitives import VaccinationDetails
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_vaccination_details,
)


class FirstVaccinationModuleTest(BaseModuleResultTest):
    def test_batch_number_validation(self):
        batch_numbers = [
            {
                VaccinationDetails.BATCH_NUMBER: "ABC565",
                VaccinationDetails.IS_BATCH_NUMBER_VALID: False,
            },
            {
                VaccinationDetails.BATCH_NUMBER: "ABV4678",
                VaccinationDetails.IS_BATCH_NUMBER_VALID: True,
            },
            {
                VaccinationDetails.BATCH_NUMBER: "99",
                VaccinationDetails.IS_BATCH_NUMBER_VALID: False,
            },
        ]

        for batch_number in batch_numbers:
            data = sample_vaccination_details()
            data[VaccinationDetails.BATCH_NUMBER] = batch_number.get(
                VaccinationDetails.BATCH_NUMBER
            )
            self.flask_client.post(
                f"{self.base_route}/{VaccinationDetails.__name__}",
                json=[data],
                headers=self.headers,
            )

            rsp = self.flask_client.post(
                f"{self.base_route}/{VaccinationDetails.__name__}/search",
                headers=self.headers,
            )

            last_value = rsp.json[VaccinationDetails.__name__][-1]
            self.assertEqual(
                last_value[VaccinationDetails.IS_BATCH_NUMBER_VALID],
                batch_number.get(VaccinationDetails.IS_BATCH_NUMBER_VALID),
            )

    def test_failure_upload_with_is_valid_field(self):
        data = sample_vaccination_details()
        data[VaccinationDetails.IS_BATCH_NUMBER_VALID] = True
        rsp = self.flask_client.post(
            f"{self.base_route}/{VaccinationDetails.__name__}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
