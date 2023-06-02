import unittest

from sdk.calendar.router.calendar_request import ExportCalendarRequestObject
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class ExportCalendarRequestObjectTestCase(unittest.TestCase):
    def test_success_create_calendar_req_obj(self):
        try:
            ExportCalendarRequestObject.from_dict(
                {ExportCalendarRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID}
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ExportCalendarRequestObject.from_dict(
                {ExportCalendarRequestObject.TIMEZONE: "GMT"}
            )

    def test_failure_not_valid_timezone(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ExportCalendarRequestObject.from_dict(
                {
                    ExportCalendarRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    ExportCalendarRequestObject.TIMEZONE: "aaa",
                }
            )


if __name__ == "__main__":
    unittest.main()
