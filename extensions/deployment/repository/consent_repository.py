from abc import ABC, abstractmethod
from typing import Set

from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog


class ConsentRepository(ABC):
    session = None

    @abstractmethod
    def create_consent(self, deployment_id: str, consent: Consent) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_consent_log(self, deployment_id: str, consent_log: ConsentLog) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_log_count(self, consent_id: str, revision: int, user_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def retrieve_consented_users(self, consent_id: str) -> Set[str]:
        raise NotImplementedError
