from datetime import datetime

from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.exceptions.exceptions import SessionTimeoutException
from sdk.common.utils.inject import autoparams


@autoparams()
def update_current_session(
    user_id: str, agent: str, auth_repo: AuthRepository, refresh_token: str = None
):
    session = DeviceSession.from_dict(
        {
            DeviceSession.USER_ID: user_id,
            DeviceSession.DEVICE_AGENT: agent,
            DeviceSession.REFRESH_TOKEN: refresh_token,
        }
    )
    auth_repo.update_device_session(session)


@autoparams()
def update_current_session_v1(
    user_id: str,
    agent: str,
    auth_repo: AuthRepository,
    refresh_token: str = None,
    new_fresh_token: str = None,
):
    session = DeviceSessionV1.from_dict(
        {
            DeviceSessionV1.USER_ID: user_id,
            DeviceSessionV1.DEVICE_AGENT: agent,
            DeviceSessionV1.REFRESH_TOKEN: new_fresh_token,
        }
    )
    auth_repo.update_device_session_v1(session, refresh_token)


@autoparams()
def register_session(user_id: str, agent: str, token: str, auth_repo: AuthRepository):
    device_session = DeviceSessionV1.from_dict(
        {
            DeviceSessionV1.USER_ID: user_id,
            DeviceSessionV1.DEVICE_AGENT: agent,
            DeviceSessionV1.REFRESH_TOKEN: token,
        }
    )
    auth_repo.register_device_session(device_session)


@autoparams()
def check_session_is_active(
    decoded_refresh_token: dict,
    auth_token_inactive_after: int,
):
    token_issued_at = datetime.fromtimestamp(decoded_refresh_token["iat"])
    now = datetime.utcnow()
    auth_token_alive_for = (now - token_issued_at).total_seconds() / 60
    if auth_token_alive_for >= auth_token_inactive_after:
        raise SessionTimeoutException
