import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun.api import FakeDatetime
from pymongo import MongoClient
from pymongo.database import Database

from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.repository.mongo_invitation_repository import (
    MongoInvitationRepository,
)
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import PhoenixServerConfig

INVITATION_REPO_PATH = "extensions.authorization.repository.mongo_invitation_repository"
SAMPLE_INVITATION_ID = "600a8476a961574fb38157d5"
SAMPLE_USER_ID = "5e8f0c74b50aa9656c34789a"
SAMPLE_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789b"
SAMPLE_ORGANIZATION_ID = "5e8f0c74b50aa9656c34789c"
EMAIL = "test@gmail.com"
CODE = "Some invitation code"
SHORTENED_CODE = "3lLFJ_d18m3MxMK6"
INVITATION_CODE = "5e8f0c74b50aa9656c34789a"


def sample_invitation():
    return {
        Invitation.ID: SAMPLE_INVITATION_ID,
        Invitation.CODE: CODE,
        Invitation.SHORTENED_CODE: SHORTENED_CODE,
        Invitation.EXPIRES_AT: FakeDatetime(2012, 1, 1, 0, 0),
    }


class MongoInvitationRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.server.invitation.shortenedCodeLength = 16
        self.client = MagicMock()
        self.db = MagicMock()

        def bind(binder):
            binder.bind_to_provider(InvitationRepository, MagicMock())
            binder.bind(PhoenixServerConfig, self.config)
            binder.bind(MongoClient, self.client)
            binder.bind(Database, self.db)

        inject.clear_and_configure(bind)

    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_create_invitation(self, document):
        repo = MongoInvitationRepository()
        invitation = Invitation.from_dict(sample_invitation())
        repo.create_invitation(invitation)
        document.assert_called_with(**invitation.to_dict(include_none=False))

    @patch(f"{INVITATION_REPO_PATH}.Invitation", MagicMock())
    @patch(f"{INVITATION_REPO_PATH}.remove_none_values")
    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_retrieve_invitation(self, document, remove_none_values):
        repo = MongoInvitationRepository()
        query = {
            f"{Invitation.EMAIL}__iexact": EMAIL,
            Invitation.CODE: CODE,
            Invitation.SHORTENED_CODE: SHORTENED_CODE,
            Invitation.ID: SAMPLE_INVITATION_ID,
        }
        remove_none_values.return_value = query
        repo.retrieve_invitation(
            email=EMAIL,
            code=CODE,
            shortened_code=SHORTENED_CODE,
            invitation_id=SAMPLE_INVITATION_ID,
        )
        document.objects.assert_called_with(**query)
        document.objects().first.assert_called_once()

    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_update_invitation(self, document):
        repo = MongoInvitationRepository()
        invitation = Invitation.from_dict(sample_invitation())
        repo.update_invitation(invitation)
        document.objects.assert_called_with(id=invitation.id)
        document.objects().first().update.assert_called_once()

    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_delete_invitation(self, document):
        repo = MongoInvitationRepository()
        repo.delete_invitation(invitation_id=SAMPLE_INVITATION_ID)
        document.objects.assert_called_with(id=SAMPLE_INVITATION_ID)
        document.objects().delete.assert_called_once()

    @patch(f"{INVITATION_REPO_PATH}.Invitation", MagicMock())
    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_retrieve_proxy_invitation(self, document):
        repo = MongoInvitationRepository()
        repo.retrieve_proxy_invitation(user_id=SAMPLE_USER_ID)
        resource = f"user/{SAMPLE_USER_ID}"
        document.objects.assert_called_with(roles__resource=resource)
        document.objects().first.assert_called_once()

    @patch(f"{INVITATION_REPO_PATH}.Invitation", MagicMock())
    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_retrieve_universal_invitation(self, document):
        repo = MongoInvitationRepository()
        deployment_id = SAMPLE_DEPLOYMENT_ID
        role_resource = f"deployment/{deployment_id}"
        role_id = "User"
        expires_from = FakeDatetime(2012, 1, 1, 0, 0)
        expires_till = FakeDatetime(2012, 2, 2, 0, 0)

        repo.retrieve_universal_invitation(
            deployment_id, role_id, expires_from, expires_till
        )
        document.objects.assert_called_with(
            roles__resource=role_resource,
            roles__roleId=role_id,
            expiresAt__gte=expires_from,
            expiresAt__lt=expires_till,
            type=InvitationType.UNIVERSAL.value,
        )
        document.objects().first.assert_called_once()

    def test_retrieve_invitations(self):
        role_ids = ["User"]
        skip = 0
        limit = 1
        repo = MongoInvitationRepository()
        repo.retrieve_invitations(
            EMAIL, skip, limit, role_ids, SAMPLE_DEPLOYMENT_ID, SAMPLE_ORGANIZATION_ID
        )
        expected_call = [
            {
                "$addFields": {
                    "id": {"$toString": "$_id"},
                    "senderId": {"$toString": "$senderId"},
                }
            },
            {
                "$match": {
                    "roles.roleId": {"$in": role_ids},
                    "roles.resource": {
                        "$in": [
                            "deployment/5e8f0c74b50aa9656c34789b",
                            "organization/5e8f0c74b50aa9656c34789c",
                        ]
                    },
                    "email": {"$regex": "test@gmail\\.com", "$options": "i"},
                }
            },
            {
                "$facet": {
                    "results": [{"$skip": 0}, {"$limit": 1}],
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        self.db[repo.INVITATION_COLLECTION].aggregate.assert_called_with(expected_call)

    @patch(f"{INVITATION_REPO_PATH}.Invitation")
    @patch(f"{INVITATION_REPO_PATH}.MongoInvitation")
    def test_retrieve_invitation_list_by_code_list(self, document, mock_invitation):
        repo = MongoInvitationRepository()
        code_list = [CODE]
        mock_invitation.CODE = Invitation.CODE
        query = {Invitation.CODE: {"$in": code_list}}
        document.objects.return_value = [Invitation(code=CODE)]
        repo.retrieve_invitation_list_by_code_list(code_list=code_list)
        document.objects.assert_called_with(**query)
        document.objects.assert_called_once()

    def test_delete_invitation_list(self):

        db = MagicMock()
        collection = MagicMock()
        collection.delete_many.return_value = MagicMock(deleted_count=1)
        validation_find = MagicMock()
        validation_find.count.return_value = 1
        collection.find.return_value = validation_find
        collections = {MongoInvitationRepository.INVITATION_COLLECTION: collection}
        db.__getitem__.side_effect = collections.__getitem__
        mock_client = MagicMock()
        repo = MongoInvitationRepository(
            database=db, config=MagicMock(), client=mock_client
        )

        result = repo.delete_invitation_list(
            [INVITATION_CODE], invitation_type=InvitationType.PERSONAL
        )
        collection.delete_many.assert_called_with(
            {
                Invitation.ID_: {"$in": [ObjectId(INVITATION_CODE)]},
                "$or": [
                    {Invitation.TYPE: InvitationType.PERSONAL.value},
                    {Invitation.TYPE: {"$exists": False}},
                ],
            },
            session=mock_client.start_session().__enter__(),
        )
        self.assertEqual(1, result)

    def test_delete_invitation_list_failure_validation(self):

        db = MagicMock()
        collection = MagicMock()
        collection.delete_many.return_value = MagicMock(deleted_count=1)
        collections = {MongoInvitationRepository.INVITATION_COLLECTION: collection}
        db.__getitem__.side_effect = collections.__getitem__
        repo = MongoInvitationRepository(
            database=db, config=MagicMock(), client=MagicMock()
        )

        invalid_invitation_code = "invalid invitation code"
        with self.assertRaises(ConvertibleClassValidationError):
            repo.delete_invitation_list(
                [INVITATION_CODE, invalid_invitation_code],
                invitation_type=InvitationType.PERSONAL,
            )
