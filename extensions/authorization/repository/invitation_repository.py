import abc
from datetime import datetime
from typing import Union

from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.common.sort import SortField


class InvitationRepository(abc.ABC):
    @abc.abstractmethod
    def create_invitation(self, invitation: Invitation) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def update_invitation(self, invitation: Invitation) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_invitation(self, invitation_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_invitation_list(
        self, invitation_id_list: list[str], invitation_type: InvitationType
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_invitation(
        self,
        email: str = None,
        code: str = None,
        invitation_id: str = None,
        shortened_code: str = None,
    ) -> Invitation:
        raise NotImplementedError

    def retrieve_universal_invitation(
        self,
        deployment_id: str,
        role_id: str,
        expires_from: datetime,
        expires_till: datetime,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_invitations(
        self,
        email: str,
        skip: int,
        limit: int,
        role_ids: list[str],
        deployment_id: str,
        organization_id: str,
        return_count: bool = False,
        invitation_type: InvitationType = None,
        sort_fields: list[SortField] = None,
    ) -> tuple[list[Invitation], Union[int, tuple[int, int]]]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_proxy_invitation(self, user_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_invitation_list_by_code_list(self, code_list: list[str]):
        raise NotImplementedError
