from abc import ABC, abstractmethod
from datetime import datetime

from extensions.appointment.models.appointment import Appointment


class AppointmentRepository(ABC):
    @abstractmethod
    def create_appointment(self, appointment: Appointment) -> str:
        raise NotImplementedError

    @abstractmethod
    def unset_key_action(self, appointment_id: str) -> Appointment:
        raise NotImplementedError

    @abstractmethod
    def update_appointment(
        self, appointment_id: str, appointment: Appointment
    ) -> Appointment:
        raise NotImplementedError

    @abstractmethod
    def retrieve_appointment(self, appointment_id: str) -> Appointment:
        raise NotImplementedError

    @abstractmethod
    def retrieve_appointments_by_ids(
        self, appointment_ids: list[str]
    ) -> list[Appointment]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_appointments(
        self,
        user_id: str,
        requester_id: str,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
        status: Appointment.Status = None,
        skip: int = None,
        limit: int = None,
    ) -> list[Appointment]:
        raise NotImplementedError

    def retrieve_pending_appointment_count(self, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete_appointment(self, appointment_id: str):
        raise NotImplementedError

    @abstractmethod
    def bulk_delete_appointments(self, appointment_ids: list[str]) -> int:
        raise NotImplementedError
