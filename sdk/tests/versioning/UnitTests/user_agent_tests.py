from unittest import TestCase

from sdk.common.exceptions.exceptions import InvalidUserAgentHeaderException
from sdk.phoenix.config.server_config import Client
from sdk.versioning.models.version_field import VersionField
from sdk.versioning.user_agent_parser import UserAgent

test_data = (
    (
        "Huma-Dev/1.4.1 (bundleId: com.huma.HumaApp.dev; build:76; software: iOS 14.2.0; hardware: iPhone; component: MedopadNetworking/1.0)",
        [
            "Huma-Dev",
            VersionField("1.4.1"),
            "com.huma.HumaApp.dev",
            "76",
            "iOS",
            "14.2.0",
            "iPhone",
            "MedopadNetworking/1.0",
            Client.ClientType.USER_IOS,
        ],
    ),
    (
        "Huma-QA/1.4.0 (bundleId: com.huma.humaapp.dev; build: 1; software: Android 29 (10); hardware: samsung SM-G970F)",
        [
            "Huma-QA",
            VersionField("1.4.0"),
            "com.huma.humaapp.dev",
            "1",
            "Android",
            "29 (10)",
            "samsung SM-G970F",
            None,
            Client.ClientType.USER_ANDROID,
        ],
    ),
    (
        "Huma-Dev/1.3.1 (build: 111; software: Chrome 86.0.4240.193;)",
        [
            "Huma-Dev",
            VersionField("1.3.1"),
            None,
            "111",
            "Chrome",
            "86.0.4240.193",
            None,
            None,
            None,
        ],
    ),
)


class UserAgentTestCase(TestCase):
    ATTRIBUTES = [
        UserAgent.PRODUCT,
        UserAgent.VERSION,
        UserAgent.BUNDLE_ID,
        UserAgent.BUILD,
        UserAgent.SOFTWARE_NAME,
        UserAgent.SOFTWARE_VERSION,
        UserAgent.HARDWARE,
        UserAgent.COMPONENT,
        UserAgent.CLIENT_TYPE,
    ]

    def test_success_parse_user_agent(self):
        for test_case, results in test_data:
            agent = UserAgent.parse(test_case)
            for index, attr in enumerate(self.ATTRIBUTES):
                self.assertEqual(getattr(agent, attr), results[index])

    def test_failure_parse_user_agent(self):
        with self.assertRaises(InvalidUserAgentHeaderException) as context:
            UserAgent.parse("Huma-Dev/1.17.0")
        self.assertIn("Invalid User Agent Header", str(context.exception))

    def test_failure_parse_user_agent_with_no_version(self):
        with self.assertRaises(InvalidUserAgentHeaderException) as context:
            UserAgent.parse("Huma-Dev")
        self.assertIn("Invalid User Agent Header", str(context.exception))

    def test_failure_parse_user_agent_with_invalid_version(self):
        with self.assertRaises(InvalidUserAgentHeaderException) as context:
            UserAgent.parse("Huma-Dev/34345")
        self.assertIn("Invalid User Agent Header", str(context.exception))
