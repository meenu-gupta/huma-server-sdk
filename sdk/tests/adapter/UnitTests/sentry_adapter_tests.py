import unittest
from copy import copy
from unittest.mock import patch, MagicMock

from flask import Flask

from sdk.common.adapter.monitoring_adapter import ErrorForm
from sdk.common.adapter.sentry.sentry_adapter import SentryAdapter
from sdk.common.adapter.sentry.sentry_config import SentryConfig
from sdk.common.utils.convertible import ConvertibleClassValidationError

SENTRY_PATH = "sdk.common.adapter.sentry.sentry_adapter"

CONFIG_DATA = {
    SentryConfig.DSN: "http://senty.io/push",
    SentryConfig.REQUEST_BODIES: "always",
    SentryConfig.TRACES_SAMPLE_RATE: 0.5,
    SentryConfig.ENVIRONMENT: "anyEnv",
    SentryConfig.RELEASE: "1.8.0",
    SentryConfig.EXTRA_TAGS: {"cloud": "aws", "cluster": "pp-dev"},
}


class SentryAdapterTestCase(unittest.TestCase):
    def test_success_config(self):
        config_data = copy(CONFIG_DATA)
        conf = SentryConfig.from_dict(config_data)
        self.assertEqual(conf.dsn, "http://senty.io/push")
        self.assertEqual(conf.requestBodies, SentryConfig.RequestBody.always)
        self.assertEqual(conf.tracesSampleRate, 0.5)
        self.assertEqual(conf.environment, "anyEnv")
        self.assertEqual(conf.release, "1.8.0")
        self.assertEqual(conf.extraTags, {"cloud": "aws", "cluster": "pp-dev"})

    def test_failure_config_with_missing_dsn(self):
        config_data = copy(CONFIG_DATA)
        config_data.pop(SentryConfig.DSN)
        with self.assertRaises(ConvertibleClassValidationError):
            SentryConfig.from_dict(config_data)

    def test_failure_config_with_invalid_request_bodies(self):
        config_data = copy(CONFIG_DATA)
        config_data[SentryConfig.REQUEST_BODIES] = "invalid"
        with self.assertRaises(ConvertibleClassValidationError):
            SentryConfig.from_dict(config_data)

    def test_failure_config_with_invalid_traces_sample_rate(self):
        config_data = copy(CONFIG_DATA)
        config_data[SentryConfig.TRACES_SAMPLE_RATE] = 11
        with self.assertRaises(ConvertibleClassValidationError):
            SentryConfig.from_dict(config_data)

    def test_failure_config_with_invalid_environment(self):
        config_data = copy(CONFIG_DATA)
        config_data[SentryConfig.EXTRA_TAGS] = "Invalid Environment"
        with self.assertRaises(ConvertibleClassValidationError):
            SentryConfig.from_dict(config_data)

    @patch(f"{SENTRY_PATH}.sentry_sdk")
    @patch(f"{SENTRY_PATH}.SentryAdapter._set_tags_for_active_scope")
    def test_success_push_to_active_scope_on_report_exception(
        self, set_tags, sentry_sdk
    ):
        request_body = ErrorForm(tags={"first_key": "first_value"})
        sentry_adapter = SentryAdapter(MagicMock())
        sentry_adapter.report_exception(request_body)
        sentry_sdk.push_scope.assert_called_once()
        set_tags.assert_called_with(request_body, sentry_sdk.push_scope().__enter__())

    @patch(f"{SENTRY_PATH}.sentry_sdk", MagicMock())
    def test_success_set_tags_for_active_scope_no_user(self):
        request_body = ErrorForm(tags={"first_key": "first_value"})
        scope = MagicMock()
        sentry_adapter = SentryAdapter(MagicMock())
        testapp = Flask(__name__)
        testapp.app_context().push()
        with testapp.test_request_context("/", method="GET") as _:
            sentry_adapter._set_tags_for_active_scope(request_body, scope)
            scope.set_tag.assert_called_with("first_key", "first_value")
            scope.set_user.assert_not_called()
