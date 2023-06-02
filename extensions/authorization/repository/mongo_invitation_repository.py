from datetime import datetime
from typing import Union

from bson import ObjectId
from mongoengine import NotUniqueError
from pymongo import WriteConcern, MongoClient
from pymongo.database import Database

from extensions.authorization.exceptions import InvitationDoesNotExistException
from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.models.mongo_invitation import MongoInvitation
from extensions.authorization.models.user import RoleAssignment
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.common.sort import SortField
from extensions.utils import format_sort_fields
from sdk.common.utils.common_functions_utils import escape
from sdk.common.utils.inject import autoparams
from sdk.common.exceptions.exceptions import (
    ObjectDoesNotExist,
    InternalServerErrorException,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import (
    remove_none_values,
    validate_object_id,
)
from sdk.common.utils.string_utils import generate_random_url_safe_string
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoInvitationRepository(InvitationRepository):
    INVITATION_COLLECTION = "invitation"

    @autoparams()
    def __init__(
        self, database: Database, config: PhoenixServerConfig, client: MongoClient
    ):
        self._config = config
        self._db = database
        self._client = client

    def create_invitation(self, invitation: Invitation) -> str:
        max_retries = 100
        for _ in range(max_retries):
            invitation.shortenedCode = generate_random_url_safe_string(
                self._config.server.invitation.shortenedCodeLength
            )
            try:
                id = MongoInvitation(**invitation.to_dict(include_none=False)).save().id
            except NotUniqueError:
                continue
            break
        else:
            raise InternalServerErrorException("Could not create new invitation")
        return str(id)

    @staticmethod
    def validate_invitation_id(invitation_id: str):
        if not validate_object_id(invitation_id):
            raise ConvertibleClassValidationError(
                f"Invitation [{invitation_id}] is not a valid InvitationId"
            )

    def retrieve_invitation(
        self,
        email: str = None,
        code: str = None,
        invitation_id: str = None,
        shortened_code: str = None,
    ) -> Invitation:
        query = remove_none_values(
            {
                f"{Invitation.EMAIL}__iexact": email,
                Invitation.CODE: code,
                Invitation.SHORTENED_CODE: shortened_code,
                Invitation.ID: invitation_id,
            }
        )

        if Invitation.ID in query:
            self.validate_invitation_id(query[Invitation.ID])

        invitation = MongoInvitation.objects(**query).first()
        if not invitation:
            raise InvitationDoesNotExistException
        return Invitation.from_dict(invitation.to_dict())

    def retrieve_invitation_list_by_code_list(
        self,
        code_list: list[str],
    ) -> list[Invitation]:
        query = {Invitation.CODE: {"$in": code_list}}
        invitation_list = MongoInvitation.objects(**query)
        if not invitation_list or len(invitation_list) != len(code_list):
            raise InvitationDoesNotExistException
        return [
            Invitation.from_dict(invitation.to_dict()) for invitation in invitation_list
        ]

    def update_invitation(self, invitation: Invitation) -> str:
        invitation_obj = MongoInvitation.objects(id=invitation.id).first()
        if not invitation_obj:
            raise ObjectDoesNotExist
        data = invitation.to_dict(include_none=False)
        if Invitation.TYPE in data:
            data[f"{Invitation.TYPE}__"] = data.pop(Invitation.TYPE)
        invitation_obj.update(**data)
        return str(invitation_obj.id)

    def delete_invitation(self, invitation_id: str):
        self.validate_invitation_id(invitation_id)
        deleted = MongoInvitation.objects(id=invitation_id).delete()
        if not deleted:
            raise InvitationDoesNotExistException

    def delete_invitation_list(
        self, invitation_id_list: list[str], invitation_type: InvitationType
    ):
        """Deletes list of invitations that are the same type.
        To be backward compatible, the data without type considered as
        'PERSONAL'."""
        for invitation_id in invitation_id_list:
            self.validate_invitation_id(invitation_id)
        obj_id_list = list(map(ObjectId, invitation_id_list))
        if invitation_type == InvitationType.PERSONAL:
            query = {
                Invitation.ID_: {"$in": obj_id_list},
                "$or": [
                    {Invitation.TYPE: InvitationType.PERSONAL.value},
                    {Invitation.TYPE: {"$exists": False}},
                ],
            }
        else:
            query = {
                Invitation.ID_: {"$in": obj_id_list},
                Invitation.TYPE: invitation_type.value,
            }

        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[self.INVITATION_COLLECTION].delete_many(
                    query, session=session
                )
                if not len(set(invitation_id_list)) == result.deleted_count:
                    raise InvitationDoesNotExistException
        return result.deleted_count

    def retrieve_proxy_invitation(self, user_id: str):
        invitation = MongoInvitation.objects(roles__resource=f"user/{user_id}").first()
        if not invitation:
            raise ObjectDoesNotExist

        return Invitation.from_dict(invitation.to_dict())

    def retrieve_universal_invitation(
        self,
        deployment_id: str,
        role_id: str,
        expires_from: datetime,
        expires_till: datetime,
    ):
        invitation = MongoInvitation.objects(
            roles__resource=f"deployment/{deployment_id}",
            roles__roleId=role_id,
            expiresAt__gte=expires_from,
            expiresAt__lt=expires_till,
            type=InvitationType.UNIVERSAL.value,
        ).first()
        if not invitation:
            raise ObjectDoesNotExist
        return Invitation.from_dict(invitation.to_dict())

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
        main_aggregation = []
        filter_options = {}
        resource_ids = []

        if deployment_id:
            resource_ids.append(f"deployment/{deployment_id}")
        if organization_id:
            resource_ids.append(f"organization/{organization_id}")
        if role_ids:
            filter_options[f"{Invitation.ROLES}.{RoleAssignment.ROLE_ID}"] = {
                "$in": role_ids
            }
        if resource_ids:
            filter_options[f"{Invitation.ROLES}.{RoleAssignment.RESOURCE}"] = {
                "$in": resource_ids
            }
        if email:
            filter_options[Invitation.EMAIL] = {
                "$regex": escape(email),
                "$options": "i",
            }
        if invitation_type:
            filter_options[Invitation.INVITATION_TYPE] = invitation_type.value
        if sort_fields:
            formatted_sort = format_sort_fields(
                sort_fields=sort_fields,
                valid_sort_fields=Invitation.VALID_SORT_FIELDS,
            )
            main_aggregation.append({"$sort": dict(formatted_sort)})

        main_aggregation.append({"$skip": skip or 0})
        if limit:
            main_aggregation.append({"$limit": limit})

        aggregation = [
            {
                "$addFields": {
                    "id": {"$toString": "$_id"},
                    "senderId": {"$toString": "$senderId"},
                }
            },
            {"$match": filter_options},
            {
                "$facet": {
                    "results": main_aggregation,
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        result = next(self._db[self.INVITATION_COLLECTION].aggregate(aggregation))
        invitations = [self.invitation_from_document(i) for i in result["results"]]

        if not result["totalCount"]:
            return invitations, (0, 0)

        filtered = result["totalCount"][0]["count"]
        if return_count:
            if email:
                aggregation[1]["$match"].pop(Invitation.EMAIL)
                result = next(
                    self._db[self.INVITATION_COLLECTION].aggregate(aggregation)
                )
                total = result["totalCount"][0]["count"]
            else:
                total = filtered
            return invitations, (filtered, total)

        return invitations, filtered

    @staticmethod
    def invitation_from_document(doc: dict) -> Invitation:
        invitation = Invitation.from_dict(doc, use_validator_field=False)
        invitation.id = str(doc[Invitation.ID_])
        return invitation
