import logging

from bson.errors import InvalidId
from typing import Optional, Union

from bson import ObjectId
from mongoengine.context_managers import switch_collection
from pymongo.client_session import ClientSession
from pymongo.database import Database

from sdk.calendar.models.calendar_event import CalendarEvent, CalendarEventLog
from sdk.calendar.models.mongo_calendar_event import (
    MongoCalendarEvent,
    MongoCalendarEventLog,
)
from sdk.calendar.repo.calendar_repository import CalendarRepository
from sdk.common.adapter.mongodb.mongodb_utils import (
    convert_kwargs,
    map_mongo_comparison_operators,
)
from sdk.common.exceptions.exceptions import ObjectDoesNotExist, InvalidRequestException
from sdk.common.monitoring.monitoring import report_exception
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import MongoPhoenixDocument
from sdk.common.utils.validators import id_as_obj_id
from sdk.common.utils.validators import remove_none_values

logger = logging.getLogger(__name__)


def to_calendar_event(mongo_event: MongoCalendarEvent) -> CalendarEvent:
    event_dict = mongo_event.to_dict()
    return CalendarEvent.from_dict(event_dict)


def to_mongo_calendar_event(event: CalendarEvent) -> MongoCalendarEvent:
    event = to_primary_event(event)
    event_dict = event.to_dict(include_none=False)
    odd_keys = {key for key in event_dict if key not in MongoCalendarEvent.fields()}
    for key in odd_keys:
        event_dict.pop(key, None)

    return MongoCalendarEvent(**event_dict)


def to_primary_event(event: CalendarEvent):
    cls_ = CalendarEvent.child(event.model)
    if cls_ != type(event):
        event_dict = event.to_dict(include_none=False)
        primary_event = cls_.from_dict(event_dict)
    else:
        primary_event = event
    return primary_event


class MongoCalendarRepository(CalendarRepository):
    CACHE_CALENDAR_COLLECTION = "nextdayevent"
    CALENDAR_COLLECTION = "calendar"

    @autoparams()
    def __init__(self, db: Database):
        self.db = db

    def create_calendar_event(self, event: CalendarEvent) -> str:
        primary_event = to_primary_event(event)
        new_event: MongoPhoenixDocument = MongoCalendarEvent(
            **primary_event.to_dict(include_none=False)
        )
        return str(new_event.save().id)

    def create_calendar_event_log(self, event_log: CalendarEventLog) -> str:
        new_event: MongoPhoenixDocument = MongoCalendarEventLog(
            **event_log.to_dict(include_none=False)
        )
        return str(new_event.save().id)

    def create_next_day_events(self, events: list[CalendarEvent]):
        mongo_events = [to_mongo_calendar_event(event) for event in events]
        with switch_collection(MongoCalendarEvent, self.CACHE_CALENDAR_COLLECTION):
            return MongoCalendarEvent.objects.insert(mongo_events)

    def batch_create_calendar_events(self, events):
        if not events:
            return 0
        primary_events = [to_primary_event(event) for event in events]
        mongo_events = [
            MongoCalendarEvent(**primary_event.to_dict(include_none=False))
            for primary_event in primary_events
        ]
        return MongoCalendarEvent.objects.insert(mongo_events)

    def retrieve_calendar_event(self, event_id: str) -> CalendarEvent:
        if not ObjectId.is_valid(event_id):
            raise ObjectDoesNotExist
        event: MongoCalendarEvent = MongoCalendarEvent.objects(id=event_id).first()
        if not event:
            raise ObjectDoesNotExist
        return to_calendar_event(event)

    @map_mongo_comparison_operators
    @convert_kwargs
    def retrieve_calendar_events(
        self, mute_errors=False, **options
    ) -> list[Union[dict, CalendarEvent]]:
        """
        @param options: mongoengine ORM filter options to filter events. Example: {"model": "KeyAction"}
        @return: list of filtered events converted to proper model based on model name
        """
        to_model = options.pop("to_model", True)
        raw_events = self.db["calendar"].find(remove_none_values(options))
        events = [MongoCalendarEvent(**event).to_dict() for event in raw_events]
        result = []
        if to_model:
            for event in events:
                try:
                    result.append(CalendarEvent.from_dict(event))
                except Exception as error:
                    if not mute_errors:
                        raise error
                    self._report_error(event, error)
            return result
        return events

    @staticmethod
    def _report_error(event: dict, error: Exception):
        user_id = str(event.get("userId"))
        logger.error(
            f"An error occurred when convert {event.get('model')}[id={user_id}] to CalenderEvent with error: [{error}]"
        )
        context_name = "CalendarEvent"
        context_content = {"event": event}
        tags = {
            "calendarEventId": event.get("id"),
            "userId": user_id,
        }

        report_exception(
            error,
            context_name=context_name,
            context_content=context_content,
            tags=tags,
        )

    @map_mongo_comparison_operators
    def retrieve_calendar_event_logs(self, **options) -> list[CalendarEventLog]:
        converted_options = {}
        for key, value in options.items():
            if isinstance(value, dict) and "$in" in value:
                new_key = f"{key}__in"
                converted_options.update({new_key: value["$in"]})
                continue
            if key == MongoCalendarEventLog.USER_ID:
                try:
                    ObjectId(value)
                except InvalidId:
                    raise InvalidRequestException(message="Invalid User Id")
            converted_options.update({key: value})

        mongo_logs = MongoCalendarEventLog.objects(**converted_options)
        return [CalendarEventLog.from_dict(log.to_dict()) for log in mongo_logs]

    def retrieve_next_day_events(self, filter_options) -> list[CalendarEvent]:
        events = self.db[self.CACHE_CALENDAR_COLLECTION].find(filter_options)
        mongo_events = []
        for event in events:
            event["id"] = event.pop("_id")
            mongo_events.append(MongoCalendarEvent(**event))
        return [to_calendar_event(mongo_event) for mongo_event in mongo_events]

    def update_calendar_event(
        self, event_id: str, event: CalendarEvent
    ) -> CalendarEvent:
        if not ObjectId.is_valid(event_id):
            raise InvalidRequestException("Event id is not valid")
        old_event = MongoCalendarEvent.objects(id=event_id).first()
        if not old_event:
            raise ObjectDoesNotExist
        primary_event = to_primary_event(event)
        data = primary_event.to_dict(include_none=False)
        old_event.update(**data)
        event_dict = old_event.to_dict()
        updated_event = CalendarEvent.from_dict({**event_dict, **data})
        return updated_event

    def delete_calendar_event(self, event_id: str) -> int:
        result = MongoCalendarEvent.objects(id=event_id).delete()
        if not result:
            raise ObjectDoesNotExist
        return result

    def batch_delete_calendar_events(self, filter_options: dict) -> Optional[list[str]]:
        """Delete events matching filter options. Return ids of deleted items if any."""
        processed_options = {}
        for key, value in filter_options.items():
            if (
                key.endswith("Id")
                and isinstance(value, str)
                and CalendarEvent.EXTRA_FIELDS not in key
            ):
                processed_options[key] = ObjectId(value)
            else:
                processed_options[key] = value

        result = self.db[self.CALENDAR_COLLECTION].find(processed_options, {"_id": 1})
        event_ids = list(result)
        result = self.db[self.CALENDAR_COLLECTION].delete_many(processed_options)
        if result.deleted_count:
            return [str(event["_id"]) for event in event_ids]
        return None

    def batch_delete_next_day_events_by_parent_ids(self, parent_ids: list[str]):
        parent_obj_ids = [ObjectId(parent_id) for parent_id in parent_ids]
        filter_options = {CalendarEvent.PARENT_ID: {"$in": parent_obj_ids}}
        return self.batch_delete_next_day_event_raw(filter_options)

    def batch_delete_next_day_events(self, event_ids: list[str]):
        event_obj_ids = [ObjectId(event_id) for event_id in event_ids]
        filter_options = {"_id": {"$in": event_obj_ids}}
        return self.batch_delete_next_day_event_raw(filter_options)

    def batch_delete_next_day_events_for_user(self, user_id: str):
        options = {CalendarEvent.USER_ID: ObjectId(user_id)}
        return self.batch_delete_next_day_event_raw(options)

    def batch_delete_next_day_event_raw(self, filter_options: dict):
        collection = self.db[self.CACHE_CALENDAR_COLLECTION]
        return collection.delete_many(filter_options).deleted_count

    def clear_cached_events(self):
        options = {"_id": {"$ne": None}}
        return self.batch_delete_next_day_event_raw(options)

    @id_as_obj_id
    def delete_user_events(self, user_id: str, session: ClientSession = None):
        self.db[self.CALENDAR_COLLECTION].delete_many(
            {CalendarEvent.USER_ID: user_id}, session=session
        )
        self.db[self.CACHE_CALENDAR_COLLECTION].delete_many(
            {CalendarEvent.USER_ID: user_id}, session=session
        )

    @id_as_obj_id
    def batch_delete_calendar_events_by_ids(self, ids: list[str]):
        ids = [ObjectId(id_) for id_ in ids]
        query = {f"{CalendarEvent.ID_}": {"$in": ids}}

        self.db[self.CALENDAR_COLLECTION].delete_many(query)

    def update_events_status(self, filter_options: dict, status: bool) -> int:
        converted_options = {}
        for key, value in filter_options.items():
            if isinstance(value, list):
                converted_options[f"{key}__in"] = value
            else:
                converted_options[key] = value

        return MongoCalendarEvent.objects(**converted_options).update(enabled=status)
