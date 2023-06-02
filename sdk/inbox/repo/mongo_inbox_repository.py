from datetime import datetime

from bson import ObjectId
from pymongo import WriteConcern, InsertOne, MongoClient
from pymongo.database import Database
from pymongo.read_concern import ReadConcern
from sdk.common.exceptions.exceptions import InternalServerErrorException
from sdk.common.utils.inject import autoparams
from sdk.inbox.models.message import MessageStatusType, Message, SubmitterMessageReport
from sdk.inbox.repo.inbox_repository import InboxRepository
from sdk.inbox.repo.models.mongo_message import MongoMessageDocument
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoInboxRepository(InboxRepository):
    @autoparams()
    def __init__(
        self, database: Database, config: PhoenixServerConfig, client: MongoClient
    ):
        self._config = config
        self._db = database
        self._client = client

    def create_message(self, message: Message) -> str:
        message.userId = ObjectId(message.userId)
        return str(
            MongoMessageDocument(**message.to_dict(include_none=False)).save().id
        )

    def create_message_from_list(self, message_list: list[Message]):
        if not len(message_list):
            return
        insert_ops = []
        now_date_time = datetime.utcnow()
        for message in message_list:
            insert_query = {
                MongoMessageDocument.USER_ID: ObjectId(message.userId),
                MongoMessageDocument.SUBMITTER_ID: ObjectId(message.submitterId),
                MongoMessageDocument.TEXT: message.text,
                MongoMessageDocument.CUSTOM: message.custom,
                MongoMessageDocument.SUBMITTER_NAME: message.submitterName,
                MongoMessageDocument.CREATE_DATE_TIME: now_date_time,
                MongoMessageDocument.UPDATE_DATE_TIME: now_date_time,
                MongoMessageDocument.STATUS: MessageStatusType.DELIVERED.value,
                "_cls": MongoMessageDocument.__name__,
            }
            insert_ops.append(InsertOne(insert_query))

        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[MongoMessageDocument.INBOX_COLLECTION].bulk_write(
                    insert_ops, ordered=False, session=session
                )
                if result.inserted_count != len(message_list):
                    raise InternalServerErrorException

    def mark_messages_as_read(
        self, message_owner_id: str, message_ids: list[str]
    ) -> int:
        message_ids = [ObjectId(m) for m in message_ids]
        invalid_message_count = MongoMessageDocument.objects(
            id__in=message_ids, userId__ne=message_owner_id
        ).count()
        if invalid_message_count > 0:
            raise PermissionError

        return MongoMessageDocument.objects(
            id__in=message_ids, userId=message_owner_id
        ).update(status=MessageStatusType.READ.value, updateDateTime=datetime.utcnow())

    def retrieve_submitters_first_messages(
        self, user_id: str
    ) -> list[SubmitterMessageReport]:
        unread_count_formula = {
            "$sum": {
                "$cond": [{"$eq": ["$status", MessageStatusType.DELIVERED.value]}, 1, 0]
            }
        }
        sorting_query = {
            "$sort": {
                f"{SubmitterMessageReport.LATEST_MESSAGE}.{Message.CREATE_DATE_TIME}": -1
            }
        }
        empty_flag_formula = {"$cond": [{"$eq": ["$custom", True]}, True, False]}
        result = MongoMessageDocument.objects(userId=user_id).aggregate(
            [
                {"$sort": {Message.CREATE_DATE_TIME: -1}},
                {"$addFields": {Message.CUSTOM: empty_flag_formula}},
                {
                    "$group": {
                        "_id": {
                            "_id": f"${Message.SUBMITTER_ID}",
                            "custom": f"${Message.CUSTOM}",
                        },
                        SubmitterMessageReport.UNREAD_MESSAGE_COUNT: unread_count_formula,
                        SubmitterMessageReport.LATEST_MESSAGE: {"$first": "$$ROOT"},
                    }
                },
                sorting_query,
            ]
        )

        return [self._report_from_dict(r) for r in list(result)]

    def retrieve_submitter_all_messages(
        self, user_id: str, submitter_id: str, skip: int, limit: int, custom: bool
    ) -> list[Message]:
        result = MongoMessageDocument.objects(
            userId=user_id, submitterId=submitter_id, custom=custom
        ).order_by("-createDateTime")[skip : skip + limit]
        return [Message.from_dict(m.to_dict()) for m in result]

    def retrieve_user_unread_messages_count(self, user_id: str) -> int:
        return MongoMessageDocument.objects(
            userId=user_id, status=MessageStatusType.DELIVERED.value
        ).count()

    @staticmethod
    def _report_from_dict(report: dict) -> SubmitterMessageReport:
        count = report[SubmitterMessageReport.UNREAD_MESSAGE_COUNT]
        latest_dict = report[SubmitterMessageReport.LATEST_MESSAGE]
        latest_dict[Message.ID] = str(latest_dict.pop("_id"))
        latest_dict[Message.USER_ID] = str(latest_dict.pop(Message.USER_ID))
        latest_dict[Message.SUBMITTER_ID] = str(latest_dict.pop(Message.SUBMITTER_ID))
        latest_message = Message.from_dict(latest_dict)
        data = {
            SubmitterMessageReport.LATEST_MESSAGE: latest_message,
            SubmitterMessageReport.UNREAD_MESSAGE_COUNT: count,
        }
        return SubmitterMessageReport.from_dict(data)
