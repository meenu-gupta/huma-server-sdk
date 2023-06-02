from functools import cached_property
from typing import Any, Iterable
import pymongo
from extensions.module_result.models.primitives import Primitive
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.common_functions_utils import mute_error, find

unseen_primitive_collection = "unseenrecentresult"


class MigrationNotRequiredException(Exception):
    pass


class Migration(BaseMigration):
    valid_config_ids = None
    max_db_lock_ttl = 1600

    @mute_error(MigrationNotRequiredException)
    def upgrade(self):
        self.ensure_questionnaire_index()
        self.clean_db_from_old_invalid_records()

        self.fetch_module_configs()
        for collection in self.primitive_collections:
            self.copy_unseen_primitives_for_collection(collection)

    def downgrade(self):
        pass

    def ensure_questionnaire_index(self):
        collection_name = "questionnaire"
        collection = self.db.get_collection(collection_name)
        if not collection:
            self.db.create_collection(collection_name)
            collection = self.db.get_collection(collection_name)
        collection.create_index(
            [
                ("userId", pymongo.DESCENDING),
                ("isForManager", pymongo.DESCENDING),
                ("createDateTime", pymongo.DESCENDING),
            ]
        )

    def clean_db_from_old_invalid_records(self):
        self.db[unseen_primitive_collection].delete_many({})

    def fetch_module_configs(self):
        pipeline = [
            {"$match": {"$expr": {"$not": {"$in": ["$moduleConfigs", [None, []]]}}}},
            {"$unwind": "$moduleConfigs"},
            {"$replaceRoot": {"newRoot": "$moduleConfigs"}},
            {"$project": {"id": 1}},
        ]
        result = self.db.deployment.aggregate(pipeline)
        self.valid_config_ids = [item["id"] for item in result]

    def copy_unseen_primitives_for_collection(self, collection: str):
        primitives = self._get_all_records_with_valid_module_config_id_after_users_last_observation_note(
            collection
        )
        for batch in _in_batches_of(1000, primitives):
            if batch:
                self.db[unseen_primitive_collection].insert_many(batch)

    def _get_all_records_with_valid_module_config_id_after_users_last_observation_note(
        self, primitive: str
    ):
        pipeline = [
            # filter our observation notes
            {
                "$match": {
                    "isForManager": {"$ne": True},
                    "moduleConfigId": {"$in": self.valid_config_ids},
                }
            },
            # look up latest observation note per user and get its date
            {
                "$lookup": {
                    "from": "questionnaire",
                    "let": {"uid": "$userId"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$userId", "$$uid"]},
                                "isForManager": True,
                            }
                        },
                        {"$sort": {"createDateTime": -1}},
                        {
                            "$group": {
                                "_id": "$userId",
                                "createdAt": {"$first": "$$ROOT.startDateTime"},
                            }
                        },
                    ],
                    "as": "observationNote",
                }
            },
            {
                "$unwind": {
                    "path": "$observationNote",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$addFields": {
                    "observationNoteCreatedAt": "$observationNote.createdAt",
                    "primitiveName": primitive,
                }
            },
            # filter records with no observation note or after observation date
            {
                "$match": {
                    "$expr": {
                        "$or": [
                            {"$eq": ["$observationNoteCreatedAt", None]},
                            {"$gt": ["$createDateTime", "$observationNoteCreatedAt"]},
                        ]
                    }
                }
            },
            # clear temp fields
            {
                "$unset": [
                    "observationNote",
                    "observationNoteCreatedAt",
                    "ragThreshold",
                    "flags",
                ]
            },
        ]
        return self.db[primitive.lower()].aggregate(pipeline)

    @cached_property
    def primitive_collections(self):
        if not (collections := self.existing_collections):
            raise MigrationNotRequiredException
        return [
            cls.__name__
            for cls in Primitive.__subclasses__()
            if find(lambda c: c == cls.__name__.lower(), collections)
        ]

    @cached_property
    def existing_collections(self):
        collections = self.db.list_collection_names()
        return [col for col in collections if not col.startswith("_")]


def _in_batches_of(size: int, iterable: Iterable[Any]):
    items = []
    for i, item in enumerate(iterable):
        items.append(item)
        if i % size == 0:
            yield items
            items.clear()
    yield items
