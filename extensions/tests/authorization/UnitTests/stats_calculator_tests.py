import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.models.stats_calculator import UserStatsCalculator

STATS_CALC_PATH = "extensions.authorization.models.stats_calculator"


class MockCalendarService:
    retrieve_calendar_events_between_two_dates = MagicMock()
    retrieve_all_calendar_events = MagicMock()


class UserStatsCalculatorTestCase(unittest.TestCase):
    @patch(f"{STATS_CALC_PATH}.CalendarService", MockCalendarService)
    def setUp(self) -> None:
        self.user = MagicMock()
        self.auth_repo = MagicMock()
        self.calculator = UserStatsCalculator(user=self.user)

    def test_retrieve_user_stats(self):
        self.calculator.run()
        MockCalendarService.retrieve_all_calendar_events.assert_called_once()
        MockCalendarService.retrieve_calendar_events_between_two_dates.assert_called_once()


if __name__ == "__main__":
    unittest.main()
