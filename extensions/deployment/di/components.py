import logging

from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.mongo_consent_repository import (
    MongoConsentRepository,
)
from extensions.deployment.repository.mongo_econsent_repository import (
    MongoEConsentRepository,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)

logger = logging.getLogger(__name__)


def bind_deployment_repository(binder, conf):
    binder.bind_to_provider(DeploymentRepository, lambda: MongoDeploymentRepository())

    logger.debug(f"Deployment Repository bind to Mongo Deployment Repository")


def bind_consent_repository(binder, conf):
    binder.bind_to_provider(ConsentRepository, lambda: MongoConsentRepository())

    logger.debug(f"Consent Repository bind to Mongo Consent Repository")


def bind_modules_manager(binder, conf):
    binder.bind(ModulesManager, ModulesManager())
    logger.debug(f"ModulesManager bind to ModulesManager")


def bind_econsent_repository(binder, conf):
    binder.bind_to_provider(EConsentRepository, lambda: MongoEConsentRepository())

    logger.debug(f"EConsent Repository bind to Mongo EConsent Repository")
