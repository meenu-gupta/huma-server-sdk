import json
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3 import Retry

from extensions.common.monitoring import report_exception
from extensions.publisher.adapters.publisher_adapter import (
    PublisherAdapter,
    DEPLOYMENT_ID,
    DEVICE_NAME,
    MODULE_CONFIG_ID,
    MODULE_ID,
    PRIMITIVES,
)
from extensions.publisher.adapters.utils import transform_publisher_data
from extensions.publisher.models.publisher import Publisher
from extensions.publisher.models.webhook import Webhook
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__name__)


class WebhookAdapter(PublisherAdapter):
    @autoparams()
    def __init__(self, publisher: Publisher):
        self._publisher = publisher

    def transform_publisher_data(self, event: dict):
        transform_publisher_data(self._publisher, event)

    def prepare_publisher_data(self, event: dict) -> bool:
        self._headers = {"Content-Type": "application/json; charset=UTF-8"}

        self._message = {
            PRIMITIVES: event["primitives"],
            MODULE_ID: event["moduleId"],
            DEPLOYMENT_ID: event["deploymentId"],
            DEVICE_NAME: event["deviceName"],
            MODULE_CONFIG_ID: event["moduleConfigId"],
        }
        return True

    def send_publisher_data(self):
        url = self._publisher.target.webhook.endpoint
        retry = self._publisher.target.retry

        self.send_data(url, retry)

    def send_data(self, url, retry):
        username = self._publisher.target.webhook.username
        password = self._publisher.target.webhook.password
        auth_type = self._publisher.target.webhook.authType

        session = requests.session()
        retries = Retry(
            total=retry,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=False,
        )
        retries.BACKOFF_MAX = 600

        session.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            if username and password and auth_type is Webhook.WebhookAuthType.BASIC:
                response = session.request(
                    url=url,
                    method="POST",
                    headers=self._headers,
                    auth=HTTPBasicAuth(username, password),
                    data=json.dumps(self._message),
                )
            else:
                response = session.request(
                    url=url,
                    method="POST",
                    headers=self._headers,
                    data=json.dumps(self._message),
                )
            if response.status_code != 200:
                message = f"Failed to publish event to webhook with publisher name: {self._publisher.name} with error: {response.reason}"

                logger.debug(message)
                exception = Exception(message)

                report_exception(
                    error=exception,
                    context_name="Publisher",
                    context_content={
                        "publisherName": self._publisher.name,
                        "publisherType": self._publisher.target.publisherType,
                    },
                )
            else:
                logger.debug(
                    f"Successfully published event to webhook with publisher name: {self._publisher.name}"
                )
        except Exception as error:
            logger.error(
                f"Failed to publish event to webhook with publisher name:"
                f" {self._publisher.name}  with error [{error}]"
            )

    def send_ping(self):
        self._headers = {"Content-Type": "application/json; charset=UTF-8"}
        self._message = {"ping": "pong"}

        self.send_publisher_data()
