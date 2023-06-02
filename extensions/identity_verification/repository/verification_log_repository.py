from abc import ABC, abstractmethod

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)


class VerificationLogRepository(ABC):
    @abstractmethod
    def retrieve_verification_log(self, user_id: str, deployment_id: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_or_update_verification_log(
        self, verification_log: VerificationLog
    ) -> str:
        raise NotImplementedError
