from collections import defaultdict
from datetime import datetime
from typing import Optional

from bson import ObjectId
from extensions.authorization.models.user import UnseenFlags
from pymongo import DESCENDING, ASCENDING
from pymongo.client_session import ClientSession
from pymongo.database import Database

from extensions.common.sort import SortField
from extensions.module_result.modules import (
    CVDRiskScoreModule,
    HighFrequencyStepModule,
    BVIModule,
)
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.module_result_utils import AggregateMode, AggregateFunc
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.adapter.mongodb.mongodb_utils import map_mongo_comparison_operators
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import convert_date_to_datetime
from sdk.common.utils.validators import remove_none_values, id_as_obj_id


class MongoModuleResultRepository(ModuleResultRepository):
    @autoparams()
    def __init__(self, database: Database):
        self._db = database

    def create_primitive(self, primitive: Primitive, save_unseen: bool = False) -> str:
        primitive.createDateTime = datetime.utcnow()
        if not primitive.startDateTime:
            primitive.startDateTime = primitive.createDateTime
        primitive.submitterId = primitive.submitterId or primitive.userId
        primitive_dict = remove_none_values(
            primitive.to_dict(
                ignored_fields=(
                    Primitive.CREATE_DATE_TIME,
                    Primitive.START_DATE_TIME,
                    Primitive.END_DATE_TIME,
                )
            )
        )
        convert_date_to_datetime(primitive_dict, type(primitive))
        if primitive.moduleConfigId:
            primitive_dict[Primitive.MODULE_CONFIG_ID] = ObjectId(
                primitive.moduleConfigId
            )
        res = self._db[primitive.class_name.lower()].insert_one(primitive_dict)
        if save_unseen:
            primitive_dict[Primitive.ID_] = res.inserted_id
            primitive_dict["primitiveName"] = primitive.class_name
            self._db[primitive.UNSEEN_PRIMITIVES_COLLECTION].insert_one(primitive_dict)
        primitive.id = str(res.inserted_id)
        return primitive.id

    def flush_unseen_results(
        self, user_id: str, start_date_time: datetime, module_id: str = None
    ) -> int:
        remove_date_time = datetime.utcnow()
        if start_date_time:
            remove_date_time = start_date_time
        query = {
            Primitive.USER_ID: ObjectId(user_id),
            Primitive.START_DATE_TIME: {"$lt": remove_date_time},
        }
        if module_id:
            query[Primitive.MODULE_ID] = module_id
        result = self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].delete_many(query)
        return result.deleted_count

    def reset_flags(
        self,
        user_id: str,
        module_id: str,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> int:
        query = {
            Primitive.USER_ID: ObjectId(user_id),
            Primitive.MODULE_ID: module_id,
            Primitive.START_DATE_TIME: {"$gte": start_date_time, "$lt": end_date_time},
        }
        update = {
            "$set": {
                Primitive.FLAGS: {
                    UnseenFlags.RED: 0,
                    UnseenFlags.GRAY: 0,
                    UnseenFlags.AMBER: 0,
                }
            }
        }
        self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].update_many(query, [update])

    def retrieve_unseen_results(
        self,
        deployment_id: str,
        user_id: str,
        module_ids: list[str] = None,
        enabled_module_ids: list[str] = None,
    ) -> list[dict]:
        module_ids = [ObjectId(m_id) for m_id in module_ids or []]
        pipeline = [
            {
                "$match": {
                    "userId": ObjectId(user_id),
                    "deploymentId": ObjectId(deployment_id),
                    "moduleConfigId": {
                        "$in": [ObjectId(id) for id in enabled_module_ids or []]
                    },
                }
            },
            {
                "$addFields": {
                    "moduleConfigCalculated": {
                        "$cond": {
                            "if": {
                                "$and": [
                                    {"$eq": ["$moduleId", "Questionnaire"]},
                                    {"$not": {"$in": ["$moduleConfigId", module_ids]}},
                                ]
                            },
                            "then": "Questionnaire",
                            "else": "$moduleConfigId",
                        }
                    }
                }
            },
            {
                "$match": {
                    "moduleId": {
                        "$nin": [
                            CVDRiskScoreModule.moduleId,
                            HighFrequencyStepModule.moduleId,
                            BVIModule.moduleId,
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "moduleId": "$moduleId",
                        "moduleConfigCalculated": "$moduleConfigCalculated",
                    },
                    "reds": {"$sum": "$flags.red"},
                    "ambers": {"$sum": "$flags.amber"},
                    "greens": {"$sum": "$flags.green"},
                    "grays": {"$sum": "$flags.gray"},
                }
            },
            {
                "$project": {
                    "moduleId": "$_id.moduleId",
                    "moduleConfigId": "$_id.moduleConfigCalculated",
                    "flags": {
                        "red": "$reds",
                        "amber": "$ambers",
                        "gray": {"$add": ["$greens", "$grays"]},
                    },
                    "_id": False,
                }
            },
            {"$sort": {"flags.red": -1, "flags.amber": -1, "flags.gray": -1}},
        ]
        return list(
            self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate(pipeline)
        )

    def calculate_unseen_flags(
        self,
        user_id: str,
        module_config_ids: list[str],
        excluded_modules_ids: list[str],
    ) -> dict:
        user_id = ObjectId(user_id)
        pipeline = [
            {
                "$match": {
                    Primitive.USER_ID: user_id,
                    Primitive.MODULE_CONFIG_ID: {
                        "$in": [ObjectId(id) for id in module_config_ids]
                    },
                    Primitive.MODULE_ID: {"$nin": excluded_modules_ids},
                }
            },
            {
                "$group": {
                    "_id": "$userId",
                    "reds": {"$sum": "$flags.red"},
                    "ambers": {"$sum": "$flags.amber"},
                    "grays": {"$sum": "$flags.gray"},
                    "greens": {"$sum": "$flags.green"},
                },
            },
        ]
        results = self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate(
            pipeline, allowDiskUse=True
        )
        reds, ambers, grays = 0, 0, 0
        for result in results:
            if result.get("_id") == user_id:
                reds, ambers, grays = (
                    result.get("reds"),
                    result.get("ambers"),
                    result.get("grays") + result.get("greens"),
                )
        unseen_flags = {
            UnseenFlags.RED: reds,
            UnseenFlags.AMBER: ambers,
            UnseenFlags.GRAY: grays,
        }
        return unseen_flags

    @id_as_obj_id
    def retrieve_first_unseen_result(
        self, deployment_id: str, user_id: str
    ) -> Optional[datetime]:
        pipeline = [
            {"$match": {"userId": user_id, "deploymentId": deployment_id}},
            {
                "$group": {
                    "_id": "$userId",
                    Primitive.START_DATE_TIME: {
                        "$min": f"${Primitive.START_DATE_TIME}"
                    },
                }
            },
        ]
        result = self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate(pipeline)
        if oldest_record := next(result, None):
            return oldest_record[Primitive.START_DATE_TIME]

    @map_mongo_comparison_operators
    def retrieve_primitives(
        self,
        user_id: str,
        module_id: str,
        primitive_name: str,
        skip: int,
        limit: int,
        direction: SortField.Direction,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
        field_filter: dict = None,
        excluded_fields: list[str] = None,
        module_config_id: str = None,
        exclude_module_ids: list[str] = None,
        only_unseen_results: bool = None,
    ) -> list[Primitive]:
        start_date_time_tag = remove_none_values(
            {"$gte": from_date_time, "$lt": to_date_time}
        )
        if len(start_date_time_tag.keys()) == 0:
            start_date_time_tag = None
        filter_options = {
            Primitive.MODULE_ID: module_id,
            Primitive.START_DATE_TIME: start_date_time_tag,
        }
        if user_id:
            filter_options[Primitive.USER_ID] = ObjectId(user_id)

        if module_config_id:
            filter_options[Primitive.MODULE_CONFIG_ID] = ObjectId(module_config_id)

        if field_filter:
            for key, item in field_filter.items():
                if key != Primitive.MODULE_CONFIG_ID:
                    continue
                if isinstance(item, dict) and "$in" in item:
                    item["$in"] = [ObjectId(i) for i in item["$in"]]

            filter_options.update(field_filter)

        if exclude_module_ids:
            filter_options.update(
                {
                    "moduleConfigId": {
                        "$nin": [ObjectId(id) for id in exclude_module_ids]
                    }
                }
            )

        order = (
            DESCENDING
            if direction and direction == SortField.Direction.DESC
            else ASCENDING
        )

        if excluded_fields:
            excluded_fields = {field: False for field in excluded_fields}

        pipeline = self._search_primitives_pipeline(
            filter_options,
            skip,
            limit,
            direction,
            order,
            excluded_fields,
            only_unseen_results,
        )
        primitive_dicts = self._db[primitive_name.lower()].aggregate(
            pipeline, allowDiskUse=True
        )
        primitives = []
        for data in primitive_dicts:
            data[Primitive.ID] = str(data.pop(Primitive.ID_))
            primitive = Primitive.create_from_dict(data, primitive_name, validate=False)
            primitives.append(primitive)

        return primitives

    @staticmethod
    def _search_primitives_pipeline(
        filter_options: dict,
        skip: int,
        limit: int,
        direction: SortField.Direction,
        order: int,
        excluded_fields: list[str] = None,
        only_unseen_results: bool = False,
    ) -> list:
        pipeline = remove_none_values(
            [
                {"$match": filter_options},
                {
                    "$lookup": {
                        "from": Primitive.UNSEEN_PRIMITIVES_COLLECTION,
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "unseenFlags",
                    }
                },
                {"$addFields": {Primitive.FLAGS: "$unseenFlags.flags"}},
                {
                    "$unwind": {
                        "path": f"${Primitive.FLAGS}",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$match": {Primitive.FLAGS: {"$ne": None}}
                    if only_unseen_results
                    else None
                },
                {"$project": excluded_fields or None},
                {"$sort": {Primitive.START_DATE_TIME: order} if direction else None},
                {"$skip": skip},
                {"$limit": limit or None},
            ],
            ignore_keys={"$ne"},
        )
        pipeline = [stage for stage in pipeline if stage]
        return pipeline

    def retrieve_aggregated_results(
        self,
        primitive_name: str,
        aggregation_function: AggregateFunc,
        mode: AggregateMode,
        start_date: datetime = None,
        end_date: datetime = None,
        skip: int = None,
        limit: int = None,
        user_id: str = None,
        module_config_id: str = None,
    ):

        module_cls = Primitive.get_class(primitive_name)

        # create options dict to filter with based on provided values
        match_options = defaultdict(dict)
        if user_id:
            match_options.update({Primitive.USER_ID: ObjectId(user_id)})
        if end_date:
            match_options[Primitive.START_DATE_TIME].update({"$lt": end_date})
        if start_date:
            match_options[Primitive.START_DATE_TIME].update({"$gte": start_date})
        if module_config_id and user_id:
            match_options.update(
                {
                    Primitive.USER_ID: ObjectId(user_id),
                    Primitive.MODULE_CONFIG_ID: module_config_id,
                }
            )

        aggregation_args = [
            {"$sort": {Primitive.START_DATE_TIME: -1}},  # to get recent results first
            {"$match": match_options},  # query by userId and time range if present
            {
                "$group": {
                    Primitive.ID_: self._date_group_data(mode),
                    **{
                        field: {
                            self._aggregation_func(aggregation_function): f"${field}"
                        }  # list all fields to aggregate
                        for field in module_cls.AGGREGATION_FIELDS
                    },
                }
            },
        ]

        # limit results if needed
        if limit:
            aggregation_args.insert(2, {"$limit": limit})
        if skip:
            aggregation_args.insert(2, {"$skip": skip})

        return self.aggregate(primitive_name.lower(), aggregation_args)

    def aggregate(self, collection: str, aggregation_args: list):
        results = self._db[collection].aggregate(aggregation_args)
        module_results = []
        for result in results:
            result["timePeriod"] = result.pop("_id")
            module_results.append(result)
        return module_results

    def _aggregation_func(self, func: AggregateFunc):
        if func == AggregateFunc.SUM:
            result = "$sum"
        elif func == AggregateFunc.MAX:
            result = "$max"
        elif func == AggregateFunc.MIN:
            result = "$min"
        elif func == AggregateFunc.AVG:
            result = "$avg"
        else:
            raise NotImplementedError
        return result

    def _date_group_data(self, mode: AggregateMode) -> dict:
        if mode == AggregateMode.NONE:
            return {}
        group_data = {
            "year": {"$year": f"${Primitive.START_DATE_TIME}"},
            "month": {"$month": f"${Primitive.START_DATE_TIME}"},
        }
        if mode == AggregateMode.DAILY:
            group_data.update(
                {
                    "hour": {"$hour": f"${Primitive.START_DATE_TIME}"},
                    "day": {"$dayOfMonth": f"${Primitive.START_DATE_TIME}"},
                }
            )
        elif mode == AggregateMode.WEEKLY:
            group_data.update({"day": {"$dayOfMonth": f"${Primitive.START_DATE_TIME}"}})
        elif mode == AggregateMode.MONTHLY:
            group_data.update({"week": {"$week": f"${Primitive.START_DATE_TIME}"}})
        else:
            raise NotImplementedError

        return group_data

    def retrieve_primitive(
        self, user_id: str, primitive_name: str, primitive_id: str
    ) -> Primitive:

        query = {
            Primitive.USER_ID: ObjectId(user_id),
            Primitive.ID_: ObjectId(primitive_id),
        }
        result = self._db[primitive_name.lower()].find_one(query)
        if not result:
            raise ObjectDoesNotExist
        return Primitive.create_from_dict(
            primitive=result, name=primitive_name, validate=False
        )

    @id_as_obj_id
    def retrieve_primitive_by_name(
        self, user_id: str, primitive_name: str, **filter_options
    ) -> Primitive:
        query = {**filter_options, Primitive.USER_ID: user_id}
        result = self._db[primitive_name.lower()].find_one(query)

        if not result:
            raise ObjectDoesNotExist
        return Primitive.create_from_dict(
            primitive=result, name=primitive_name, validate=False
        )

    @id_as_obj_id
    def delete_user_primitive(
        self, user_id: str, primitive_names: list[str], session: ClientSession = None
    ):
        for primitive in primitive_names:
            self._db[primitive].delete_many(
                {Primitive.USER_ID: user_id}, session=session
            )

    def create_indexes(self):
        self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].ensure_index(Primitive.USER_ID)
        self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].ensure_index(
            Primitive.DEPLOYMENT_ID
        )
        self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].ensure_index(
            Primitive.MODULE_ID
        )
        self._db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].ensure_index(
            Primitive.MODULE_CONFIG_ID
        )
