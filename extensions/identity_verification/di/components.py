import logging
from extensions.identity_verification.repository.mongo_verification_log_repository import (
    MongoVerificationLogRepository,
)
from extensions.identity_verification.repository.verification_log_repository import (
    VerificationLogRepository,
)
from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)
from sdk.common.adapter.onfido.onfido_adapter import OnfidoAdapter
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationAdapter
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def bind_onfido_adapter(binder: Binder, config: PhoenixServerConfig):
    binder.bind_to_provider(IdentityVerificationAdapter, lambda: OnfidoAdapter(config))
    logger.debug(f"IdentityVerificationAdapter bind to OnfidoAdapter")


def bind_identity_verification_repository(binder, conf):
    binder.bind_to_provider(
        VerificationLogRepository, lambda: MongoVerificationLogRepository()
    )

    logger.debug(
        f"User Verification Log Repository bind to Mongo Verification Log Repository"
    )


def bind_email_verification_result_email(binder: Binder, config: PhoenixServerConfig):
    binder.bind_to_provider(
        IdentityVerificationEmailAdapter, lambda: IdentityVerificationEmailAdapter()
    )
    logger.debug(
        f"IdentityVerificationEmailAdapter bind to Provider IdentityVerificationEmailAdapter"
    )
