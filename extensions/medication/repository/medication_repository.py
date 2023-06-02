from abc import ABC, abstractmethod
from datetime import datetime

import pymongo
from pymongo.client_session import ClientSession

from extensions.medication.models.medication import Medication


class MedicationRepository(ABC):
    @abstractmethod
    def create_medication(self, medication: Medication) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_medications(
        self,
        user_id: str,
        skip: int,
        limit: int,
        start_date: datetime,
        only_enabled: bool = True,
        end_date: datetime = None,
        direction: int = pymongo.ASCENDING,
    ) -> list[Medication]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_medication_by_id(self, medication_id: str) -> Medication:
        raise NotImplementedError

    @abstractmethod
    def update_medication(self, medication: Medication) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_user_medication(self, user_id: str, session: ClientSession = None):
        raise NotImplementedError
