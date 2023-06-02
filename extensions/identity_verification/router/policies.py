from flask import request
from onfido.webhook_event_verifier import WebhookEventVerifier

from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig


def check_onfido_signature():
    onfido_headers = request.headers.get("X-SHA2-Signature")
    config = inject.instance(PhoenixServerConfig)
    webtoken = config.server.adapters.onfido.webhookToken
    token_verifier = WebhookEventVerifier(webtoken)
    payload = request.data.decode("utf-8")
    token_verifier.read_payload(payload, onfido_headers)
