from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, Type, Union

from extensions.authorization.models.user import User
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportProcess,
)
from extensions.module_result.models.primitives import Primitive, Questionnaire

ExportTypes = list[ExportProcess.ExportType]


class ExportDeploymentRepository(ABC):
    @abstractmethod
    def retrieve_users(
        self, deployment_id: str = None, user_ids: list[str] = None
    ) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_consent_logs(
        self,
        consent_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_ids: Optional[list] = None,
        use_creation_time: Optional[bool] = None,
    ) -> list[ConsentLog]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_econsent_logs(self, econsent_id: str) -> list[EConsentLog]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_primitives(
        self,
        primitive_class: Type[Union[Primitive, Questionnaire]],
        module_id: str,
        deployment_id: str,
        start_date: date,
        end_date: date,
        partly_date_range: bool = False,
        user_ids: Optional[list] = None,
        use_creation_time: Optional[bool] = None,
    ) -> list[Primitive]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_export_profiles(
        self, name_contains: str, deployment_id: str = None, organization_id: str = None
    ) -> list[ExportProfile]:
        raise NotImplementedError

    @abstractmethod
    def create_export_profile(self, export_profile: ExportProfile) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_export_profile(self, export_profile_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_export_profile(self, export_profile: ExportProfile) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_export_profile(
        self,
        deployment_id: str = None,
        organization_id: str = None,
        profile_id: str = None,
        profile_name: str = None,
        default: bool = None,
    ) -> ExportProfile:
        raise NotImplementedError

    @abstractmethod
    def create_export_process(self, export_process: ExportProcess) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_export_process(
        self, export_process_id: str, export_process: ExportProcess
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_export_processes(
        self,
        deployment_id: str = None,
        user_id: str = None,
        export_type: ExportTypes = None,
        status: ExportProcess.ExportStatus = None,
        till_date: datetime = None,
    ) -> list[ExportProcess]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_export_process(self, export_process_id: str) -> ExportProcess:
        raise NotImplementedError

    @abstractmethod
    def retrieve_unseen_export_process_count(self, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def check_export_process_already_running_for_user(self, requester_id: str):
        raise NotImplementedError

    @abstractmethod
    def delete_export_process(self, export_process_id: str):
        raise NotImplementedError

    @abstractmethod
    def mark_export_processes_seen(
        self, export_process_ids: list[str], requester_id: str
    ):
        raise NotImplementedError
