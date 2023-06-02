import unittest
from unittest.mock import MagicMock

from extensions.authorization.tasks import calculate_stats_for_user

SAMPLE_ID = "6172725949407a22f04b182f"


class MockUser:
    instance = MagicMock()
    id = SAMPLE_ID


class TasksTestCase(unittest.TestCase):
    def test_success_calculate_stats_for_user(self):
        user = MockUser()
        auth_service = MagicMock()
        stats_calc = MagicMock()
        req_obj = MagicMock()
        task = user, auth_service, stats_calc, req_obj
        calculate_stats_for_user(task)
        stats_calc().run.assert_called_once()
        req_obj.from_dict.assert_called_with(
            {req_obj.ID: SAMPLE_ID, req_obj.STATS: stats_calc().run()}
        )
        auth_service().update_user_profile.assert_called_with(req_obj.from_dict())


if __name__ == "__main__":
    unittest.main()
