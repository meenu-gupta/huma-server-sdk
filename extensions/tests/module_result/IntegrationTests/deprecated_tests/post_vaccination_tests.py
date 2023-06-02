from extensions.module_result.models.primitives import PostVaccination
from extensions.tests.module_result.IntegrationTests.module_result_tests import (
    BaseModuleResultTest,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_post_vaccination,
)


class PostVaccinationModuleTest(BaseModuleResultTest):
    def test_batch_number_validation(self):
        batch_numbers = [
            {
                PostVaccination.BATCH_NUMBER_VACCINE: "ABC565",
                PostVaccination.IS_BATCH_NUMBER_VALID: False,
            },
            {
                PostVaccination.BATCH_NUMBER_VACCINE: "ABV4678",
                PostVaccination.IS_BATCH_NUMBER_VALID: True,
            },
            {
                PostVaccination.BATCH_NUMBER_VACCINE: "abv4678",
                PostVaccination.IS_BATCH_NUMBER_VALID: True,
            },
            {
                PostVaccination.BATCH_NUMBER_VACCINE: "aBv4678",
                PostVaccination.IS_BATCH_NUMBER_VALID: True,
            },
        ]

        for batch_number in batch_numbers:
            data = sample_post_vaccination()
            data[PostVaccination.BATCH_NUMBER_VACCINE] = batch_number.get(
                PostVaccination.BATCH_NUMBER_VACCINE
            )
            self.flask_client.post(
                f"{self.base_route}/{PostVaccination.__name__}",
                json=[data],
                headers=self.headers,
            )

            rsp = self.flask_client.post(
                f"{self.base_route}/{PostVaccination.__name__}/search",
                headers=self.headers,
            )

            last_value = rsp.json[PostVaccination.__name__][-1]
            self.assertEqual(
                last_value[PostVaccination.IS_BATCH_NUMBER_VALID],
                batch_number.get(PostVaccination.IS_BATCH_NUMBER_VALID),
                batch_number[PostVaccination.BATCH_NUMBER_VACCINE],
            )

    def test_failure_upload_with_is_valid_field(self):
        data = sample_post_vaccination()
        data[PostVaccination.IS_BATCH_NUMBER_VALID] = True
        rsp = self.flask_client.post(
            f"{self.base_route}/{PostVaccination.__name__}",
            json=[data],
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
