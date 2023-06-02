from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Set

from pymongo.client_session import ClientSession

from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog


class EConsentRepository(ABC):
    session = None

    @abstractmethod
    def create_econsent(
        self, deployment_id: str, econsent: EConsent, session: ClientSession = None
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_latest_econsent(self, deployment_id: str) -> EConsent:
        raise NotImplementedError

    @abstractmethod
    def retrieve_log_count(self, consent_id: str, revision: int, user_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_econsent_log(self, deployment_id: str, econsent_log: EConsentLog) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_signed_econsent_log(self, user_id: str, log_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_econsent_pdfs(self, econsent_id: str, user_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_user_econsent_pdf_location(self, pdf_location: dict, inserted_id: str):
        raise NotImplementedError

    @abstractmethod
    def retrieve_consented_users(self, econsent_id: str) -> Set[str]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_signed_econsent_logs(self, econsent_id: str, user_id: str):
        raise NotImplementedError

    @abstractmethod
    def withdraw_econsent(self, econsent_id: str, user_id: str, log_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_consented_users_count(self, econsent_id: str) -> dict[date, int]:
        raise NotImplementedError
