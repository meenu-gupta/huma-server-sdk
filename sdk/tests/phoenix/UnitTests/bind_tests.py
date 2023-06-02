from unittest.mock import MagicMock

from sdk.phoenix.config.server_config import PhoenixServerConfig, Client
from sdk.phoenix.di.components import bind_sentry_adapter
from sdk.tests.constants import CLIENT_ID, PROJECT_ID


def get_config() -> PhoenixServerConfig:
    config_dict = {
        "server": {
            "project": {
                "id": PROJECT_ID,
                "clients": [
                    {
                        Client.NAME: "client",
                        Client.CLIENT_ID: CLIENT_ID,
                        Client.CLIENT_TYPE: Client.ClientType.USER_ANDROID.value,
                        Client.ROLE_IDS: ["User"],
                    },
                ],
                "masterKey": "test",
            },
            "adapters": {"sentry": {"enable": True, "dsn": ""}},
        }
    }
    return PhoenixServerConfig.from_dict(config_dict)


def test_bind_sentry_adapter_config_enabled():
    config = get_config()
    binder = MagicMock()
    bind_sentry_adapter(binder, config, server_version="1.0.0")
    binder.bind.assert_called_once()


def test_bind_sentry_adapter_config_disabled():
    config = get_config()
    config.server.adapters.sentry.enable = False
    binder = MagicMock()
    bind_sentry_adapter(binder, config, server_version="1.0.0")
    binder.bind.assert_not_called()


def test_bind_sentry_adapter_no_config():
    config = get_config()
    config.server.adapters.sentry = None
    binder = MagicMock()
    bind_sentry_adapter(binder, config, server_version="1.0.0")
    binder.bind.assert_not_called()
