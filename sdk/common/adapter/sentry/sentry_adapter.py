import sentry_sdk
from flask import g, has_request_context
from sentry_sdk import Scope
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from sdk.common.adapter.monitoring_adapter import MonitoringAdapter, ErrorForm
from sdk.common.adapter.sentry.sentry_config import SentryConfig


class SentryAdapter(MonitoringAdapter):
    """
    how to configure it through config file:
    > sentry:
    >   dsn: !ENV ${SENTRY_DSN}
    >   requestBodies: (never, small, medium, always)
    >   tracesSampleRate: (0, 1)
    >   environment: (DEV, QA, Demo, Production)
    >   release: (1.8.0, 1.9.0, ...)

    how to use it:
    > monitoring: MonitoringAdapter = inject.instance('MonitoringAdapter')
    > monitoring.report_error(error=error)
    """

    USER_ID = "id"

    def __init__(self, config: SentryConfig = None):
        self._config = config
        if not config:
            return

        sentry_sdk.utils.MAX_STRING_LENGTH = 8192
        sentry_sdk.init(
            dsn=self._config.dsn,
            integrations=[FlaskIntegration(), CeleryIntegration()],
            environment=self._config.environment,
            request_bodies=self._config.requestBodies.value,
            traces_sample_rate=self._config.tracesSampleRate,
            release=self._config.release,
        )
        if self._config.extraTags:
            for tag_key, tag_value in self._config.extraTags.items():
                sentry_sdk.set_tag(tag_key, tag_value)

    def is_configured(self) -> bool:
        return bool(self._config)

    def report_exception(self, request_body: ErrorForm):
        if request_body.context:
            sentry_sdk.set_context(
                request_body.context.name, request_body.context.content
            )

        with sentry_sdk.push_scope() as scope:
            self._set_tags_for_active_scope(request_body, scope)
            sentry_sdk.capture_exception(request_body.error)

    @staticmethod
    def _set_tags_for_active_scope(request_body: ErrorForm, scope: Scope):
        if has_request_context():
            if g.get("uuid"):
                scope.set_tag("requestId", g.uuid)

            if g.get("auth_user"):
                scope.set_user({SentryAdapter.USER_ID: g.auth_user.id})

        if not request_body.tags:
            return

        for key, value in request_body.tags.items():
            scope.set_tag(key, value)
