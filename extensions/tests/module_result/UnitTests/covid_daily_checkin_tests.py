import unittest

from extensions.module_result.models.primitives import Primitive, Covid19DailyCheckIn
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class CovidDailyCheckInTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        contact_type = (
            Covid19DailyCheckIn.ContactTypeWithCovid19Person.FACE_TO_FACE_CONTACT_WITH_SUCH_PERSON.value
        )
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            Covid19DailyCheckIn.CONTACT_TYPE: contact_type,
        }

    def test_success_create_covid_daily_checkin_primitive(self):
        data = self._sample_data()
        try:
            Covid19DailyCheckIn.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_covid_daily_checkin__no_required_fields(self):
        data = self._sample_data()
        data.pop(Covid19DailyCheckIn.CONTACT_TYPE)
        with self.assertRaises(ConvertibleClassValidationError):
            Covid19DailyCheckIn.from_dict(data)


if __name__ == "__main__":
    unittest.main()
