from datetime import datetime, timedelta
from unittest import TestCase

from sdk.auth.helpers.session_helpers import check_session_is_active
from sdk.common.exceptions.exceptions import SessionTimeoutException


def _prepare_kwargs(issued_delta_minutes):
    issued_at = datetime.utcnow() - timedelta(minutes=issued_delta_minutes)
    return {
        "decoded_refresh_token": {"iat": issued_at.timestamp()},
        "auth_token_inactive_after": SessionTimeoutTestCase.INACTIVITY_LIMIT,
    }


class SessionTimeoutTestCase(TestCase):
    INACTIVITY_LIMIT = 15

    def test_timeout__raises_exception_after_inactivity_period(self):
        kwargs = _prepare_kwargs(self.INACTIVITY_LIMIT + 1)
        self.assertRaises(SessionTimeoutException, check_session_is_active, **kwargs)

    def test_timeout__raises_exception_at_inactivity_period(self):
        kwargs = _prepare_kwargs(self.INACTIVITY_LIMIT)
        self.assertRaises(SessionTimeoutException, check_session_is_active, **kwargs)

    def test_timeout__valid_before_inactivity_period(self):
        kwargs = _prepare_kwargs(self.INACTIVITY_LIMIT - 1)
        result = check_session_is_active(**kwargs)
        self.assertIsNone(result)
