import unittest
import time
from unittest.mock import MagicMock, patch

from freezegun import freeze_time
from gobiko.apns.exceptions import BadDeviceToken, PartialBulkMessage

from sdk.common.adapter.apns.apns_push_adapter import APNSPushAdapter
from sdk.common.utils.validators import remove_none_values

APNS_PUSH_ADAPTER_PATH = "sdk.common.adapter.apns.apns_push_adapter"
APNS_MESSAGE = MagicMock(
    notification=MagicMock(title="Title", body="Message body"),
    data={"test": 1},
    priority=10,
    type="voip",
    badge=1,
)

TTL = 1
ARGUMENTS = {
    "alert": {
        "title": APNS_MESSAGE.notification.title,
        "body": APNS_MESSAGE.notification.body,
    },
    "extra": APNS_MESSAGE.data,
    "expiration": None,
    "priority": APNS_MESSAGE.priority,
    "push_type": APNS_MESSAGE.type,
    "badge": APNS_MESSAGE.badge,
    "topic": None,
}


class APNSPushAdapterTestCase(unittest.TestCase):
    @freeze_time("2012-01-01")
    @patch(f"{APNS_PUSH_ADAPTER_PATH}.APNsClient", MagicMock())
    def test_send_message_to_identities_one(self):
        apns_push_adapter = APNSPushAdapter(config=MagicMock())
        apns_push_adapter.apns_client = MagicMock(bundle_id="bundle_id")

        identities = ["one"]
        ARGUMENTS["expiration"] = int(time.time()) + TTL
        ARGUMENTS["topic"] = apns_push_adapter.apns_client.bundle_id + ".voip"

        output = apns_push_adapter.send_message_to_identities(
            identities=identities, message=APNS_MESSAGE, ttl=TTL
        )

        apns_push_adapter.apns_client.send_message.assert_called_once_with(
            identities[0], **remove_none_values(ARGUMENTS)
        )
        assert output == []

    @patch(f"{APNS_PUSH_ADAPTER_PATH}.APNsClient", MagicMock())
    def test_send_message_to_identities_one_exception(self):
        apns_push_adapter = APNSPushAdapter(config=MagicMock())
        apns_push_adapter.apns_client = MagicMock()

        identities = ["one"]

        apns_push_adapter.apns_client.send_message.side_effect = BadDeviceToken()

        output = apns_push_adapter.send_message_to_identities(
            identities=identities, message=APNS_MESSAGE
        )

        assert output == identities

    @freeze_time("2012-01-01")
    @patch(f"{APNS_PUSH_ADAPTER_PATH}.APNsClient", MagicMock())
    def test_send_message_to_identities_multiple(self):
        apns_push_adapter = APNSPushAdapter(config=MagicMock())
        apns_push_adapter.apns_client = MagicMock()

        identities = ["one", "two"]
        expected_output = []
        ARGUMENTS["expiration"] = int(time.time()) + TTL
        ARGUMENTS["topic"] = apns_push_adapter.apns_client.bundle_id + ".voip"

        apns_push_adapter.send_message_to_identities(
            identities=identities, message=APNS_MESSAGE, ttl=TTL
        )

        assert apns_push_adapter.apns_client.send_bulk_message.call_count == 1
        output = apns_push_adapter.send_message_to_identities(
            identities=identities, message=APNS_MESSAGE
        )
        assert output == expected_output

    @patch(f"{APNS_PUSH_ADAPTER_PATH}.APNsClient", MagicMock())
    def test_send_message_to_identities_multiple_exception(self):
        apns_push_adapter = APNSPushAdapter(config=MagicMock())
        apns_push_adapter.apns_client = MagicMock()

        identities = ["one", "two"]
        expected_output = ["one"]

        apns_push_adapter.apns_client.send_bulk_message.side_effect = (
            PartialBulkMessage(bad_registration_ids=["one"], message="error")
        )

        output = apns_push_adapter.send_message_to_identities(
            identities=identities, message=APNS_MESSAGE
        )

        assert output == expected_output


if __name__ == "__main__":
    unittest.main()
