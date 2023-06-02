import abc
from abc import ABC
from datetime import datetime
from typing import Any, Union

from pymongo.client_session import ClientSession

from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.manager_assigment import ManagerAssignment
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import (
    User,
    PersonalDocument,
)
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
)
from extensions.deployment.models.deployment import Label


class AuthorizationRepository(ABC):
    @abc.abstractmethod
    def create_user(self, user: User, **kwargs) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def update_user_unseen_flags(self, user_id: str, unseen_flags: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_invitation_with_session(
        self, invitation_id: str, session: ClientSession
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def create_tag(self, user_id: str, tags: dict, tags_author_id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def assign_labels_to_user(
        self, user_id: str, labels: list[Label], assignee_id: str
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def bulk_assign_labels_to_users(
        self, user_ids: list[str], labels: list[Label], assignee_id: str
    ) -> list[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def unassign_label_from_users(
        self,
        label_id: str,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_users_per_label_count(self, deployment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def create_label_logs(self, label_logs: list[LabelLog]) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def create_tag_log(self, tag_log: TagLog) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def assign_managers_and_create_log(self, manager_assigment: ManagerAssignment):
        raise NotImplementedError

    @abc.abstractmethod
    def assign_managers_to_users(
        self, manager_ids: list[str], user_ids: list[str], submitter_id: str
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_assigned_managers_ids(self, user_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_all_user_profiles(self, role: str = None):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_user_ids_in_deployment(
        self, deployment_id: str, user_type: str = Role.UserType.USER
    ) -> list[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_users_by_id_list(
        self, user_id_list: [str] = None, **kwargs
    ) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_assigned_managers_ids_for_multiple_users(
        self, user_ids: list[str]
    ) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_user_ids_with_assigned_manager(self, manager_id: str) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_profiles_with_assigned_manager(self, manager_id: str) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_assigned_patients_count(self):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_assigned_to_user_proxies(self, user_id: str) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_user(
        self, phone_number: str = None, email: str = None, user_id: str = None, **kwargs
    ) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_user_profiles(
        self,
        deployment_id: str,
        search: str,
        role: str = RoleName.USER,
        sort: list = None,
        skip: int = None,
        limit: int = None,
        search_ignore_keys: str = None,
        manager_id: str = None,
        filters: dict = None,
        enabled_module_ids: list[str] = None,
        return_count: bool = False,
        manager_deployment_ids: list[str] = None,
        sort_extra=None,
        is_common_role: bool = False,
    ) -> Union[
        tuple[list[User], Union[str, None]],
        tuple[list[User], Union[str, None], tuple[int, int]],
    ]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_staff(
        self, organization_id: str, search: str, is_common_role: bool = False
    ) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_simple_user_profile(self, user_id: str = None, email: str = None):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_simple_user_profiles_by_ids(self, ids: set[str]) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_users_count(
        self,
        from_: datetime = None,
        to: datetime = None,
        deployment_id: str = None,
        role: str = None,
        **options,
    ) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_users_with_user_role_including_only_fields(
        self, fields: tuple, to_model: bool
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_user_profiles_by_ids(
        self, ids: set[str], role: str = None
    ) -> list[User]:
        raise NotImplementedError

    @abc.abstractmethod
    def update_user_profile(self, user: User) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def update_user_profiles(self, users: list[User]):
        raise NotImplementedError

    @abc.abstractmethod
    def update_user_onfido_verification_status(
        self, applicant_id: str, verification_status: int
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_tag(self, user_id: str, tags_author_id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def check_ip_allowed_create_super_admin(self, master_key: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def create_care_plan_group_log(self, log: CarePlanGroupLog):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_users_timezones(self, user_ids: list[str] = None, **options) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user(self, user_id: str, session: ClientSession = None):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user_from_care_plan_log(
        self, user_id: str, session: ClientSession = None
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user_from_patient(self, user_id: str, session: ClientSession = None):
        raise NotImplementedError

    @abc.abstractmethod
    def create_personal_document(self, user_id: str, personal_doc: PersonalDocument):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_personal_documents(self, user_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def create_helper_agreement_log(
        self, helper_agreement_log: HelperAgreementLog
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_helper_agreement_log(
        self, user_id: str, deployment_id: str
    ) -> HelperAgreementLog:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_grouped_signed_up_user_count_by_month(self, deployment_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def create_indexes(self):
        raise NotImplementedError
