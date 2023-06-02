from abc import ABC, abstractmethod


class AuditLogRepository(ABC):  # pragma: no cover
    @abstractmethod
    def create_log(self, data: dict) -> str:
        raise NotImplementedError
