import unittest
from datetime import datetime, tzinfo

import pytz

from sdk.calendar.utils import get_dt_from_str
from sdk.common.utils.date_utils import rrule_replace_timezone


class DateUtilsTestCase(unittest.TestCase):
    def test_timezone(self):
        timezone = pytz.timezone("Europe/Kiev")
        end_date_time = get_dt_from_str("2021-03-01T10:00:00.000Z")
        offset = int(timezone.utcoffset(end_date_time).total_seconds() // 3600)
        actual_hour = 10
        expected_hour = actual_hour - offset
        actual_start = f"DTSTART:20210201T{actual_hour}0000\n"
        expected_start = f"DTSTART:20210201T0{expected_hour}0000\n"

        actual_until = f"UNTIL=20210301T{actual_hour}0000;"
        expected_until = f"UNTIL=20210301T0{expected_hour}0000;"
        pattern = "%sRRULE:FREQ=WEEKLY;INTERVAL=10;%s%s"

        recurrence_pattern = pattern % (
            actual_start,
            actual_until,
            f"BYHOUR={actual_hour};BYMINUTE=0",
        )
        expected_value = pattern % (
            expected_start,
            expected_until,
            f"BYHOUR={expected_hour};BYMINUTE=0",
        )

        rrule = rrule_replace_timezone(recurrence_pattern, timezone, end_date_time)
        self.assertEqual(expected_value, rrule)


if __name__ == "__main__":
    unittest.main()
