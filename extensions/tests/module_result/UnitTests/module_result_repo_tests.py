import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun import freeze_time

from extensions.common.sort import SortField
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode
from extensions.module_result.modules import (
    CVDRiskScoreModule,
    HighFrequencyStepModule,
    BVIModule,
)
from extensions.module_result.repository.mongo_module_result_repository import (
    MongoModuleResultRepository,
)

SAMPLE_ID = "600a8476a961574fb38157d5"
MODULE_RESULT_PATH = (
    "extensions.module_result.repository.mongo_module_result_repository"
)


class MockPrimitive:
    instance = MagicMock()
    name = MagicMock(return_value="PrimitiveName")


class MockModule:
    instance = MagicMock()
    primitives = [MockPrimitive, MockPrimitive]


class MockDeploymentService:
    instance = MagicMock()
    retrieve_modules = MagicMock(return_value=[MockModule])


class ModuleResultsTestCase(unittest.TestCase):
    def test_delete_module_results_on_user_delete(self):
        db_mock = MagicMock()
        session = MagicMock()
        repo = MongoModuleResultRepository(db_mock)
        repo.delete_user_primitive(
            user_id=SAMPLE_ID, session=session, primitive_names=[MockPrimitive.name]
        )
        user_id = ObjectId(SAMPLE_ID)
        db_mock[MockPrimitive.name].delete_many.assert_called_with(
            {"userId": user_id}, session=session
        )

    @freeze_time("2012-01-01")
    def test_success_create_primitive(self):
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        primitive_dict = {
            Primitive.USER_ID: ObjectId(SAMPLE_ID),
            Primitive.MODULE_ID: "Test Module Id",
            Primitive.DEPLOYMENT_ID: ObjectId(SAMPLE_ID),
            Primitive.VERSION: 0,
            Primitive.DEVICE_NAME: "Sample device name",
            Primitive.IS_AGGREGATED: False,
            Primitive.CREATE_DATE_TIME: datetime(2012, 1, 1, 0, 0),
            Primitive.SUBMITTER_ID: ObjectId(SAMPLE_ID),
        }
        primitive_dict[Primitive.START_DATE_TIME] = primitive_dict[
            Primitive.CREATE_DATE_TIME
        ]
        primitive = Primitive.from_dict(primitive_dict)
        repo.create_primitive(primitive)
        db["primitive"].insert_one.assert_called_with(primitive_dict)

    def test_success_retrieve_primitives(self):
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        user_id = SAMPLE_ID
        module_id = "Test_module_id"
        primitive_name = "test_primitive_name"
        skip = 5
        limit = 10
        direction = SortField.Direction.DESC
        repo.retrieve_primitives(
            user_id=user_id,
            module_id=module_id,
            primitive_name=primitive_name,
            skip=skip,
            limit=limit,
            direction=direction,
        )
        db[primitive_name].aggregate.assert_called_with(
            [
                {"$match": {"moduleId": module_id, "userId": ObjectId(user_id)}},
                {
                    "$lookup": {
                        "from": "unseenrecentresult",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "unseenFlags",
                    }
                },
                {"$addFields": {"flags": "$unseenFlags.flags"}},
                {"$unwind": {"path": "$flags", "preserveNullAndEmptyArrays": True}},
                {"$sort": {"startDateTime": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ],
            allowDiskUse=True,
        )

    def test_success_retrieve_primitives_with_excluded_modules(self):
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        user_id = SAMPLE_ID
        module_id = "Test_module_id"
        primitive_name = "test_primitive_name"
        skip = 5
        limit = 10
        direction = SortField.Direction.DESC

        ids = [
            "600a8476a961574fb38157d6",
            "600a8476a961574fb38157d7",
            "600a8476a961574fb38157d8",
            "600a8476a961574fb38157d9",
        ]

        repo.retrieve_primitives(
            user_id=user_id,
            module_id=module_id,
            primitive_name=primitive_name,
            skip=skip,
            limit=limit,
            direction=direction,
            exclude_module_ids=ids,
        )

        db[primitive_name].aggregate.assert_called_with(
            [
                {
                    "$match": {
                        "moduleId": module_id,
                        "userId": ObjectId(user_id),
                        "moduleConfigId": {"$nin": [ObjectId(id) for id in ids]},
                    }
                },
                {
                    "$lookup": {
                        "from": "unseenrecentresult",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "unseenFlags",
                    }
                },
                {"$addFields": {"flags": "$unseenFlags.flags"}},
                {"$unwind": {"path": "$flags", "preserveNullAndEmptyArrays": True}},
                {"$sort": {"startDateTime": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ],
            allowDiskUse=True,
        )

    @patch(f"{MODULE_RESULT_PATH}.Primitive")
    def test_success_retrieve_aggregated_results(self, mock_primitive):
        mock_primitive.get_class.return_value = MagicMock()
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        primitive_name = "test_primitive_name"
        aggregation_function = AggregateFunc.AVG
        mode = AggregateMode.DAILY
        repo.retrieve_aggregated_results(
            primitive_name=primitive_name,
            aggregation_function=aggregation_function,
            mode=mode,
        )
        db[primitive_name].aggregate.assert_called_once()

    @staticmethod
    def retrieve_unseen_pipeline(module_ids, enabled_module_ids):
        return [
            {
                "$match": {
                    "userId": ObjectId(SAMPLE_ID),
                    "deploymentId": ObjectId(SAMPLE_ID),
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

    def test_success_retrieve_flagged_without_modules(self):
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        user_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        repo.retrieve_unseen_results(
            user_id=user_id,
            deployment_id=deployment_id,
            module_ids=[],
        )
        db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate.assert_called_with(
            self.retrieve_unseen_pipeline([], [])
        )

    def test_success_retrieve_flagged_with_modules(self):
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        user_id = SAMPLE_ID
        sample_module_ids = [
            "600a8476a961574fb38157d6",
            "600a8476a961574fb38157d7",
            "600a8476a961574fb38157d8",
            "600a8476a961574fb38157d9",
        ]
        sample_enabled_ids = [
            "600a8476a961574fb38157d6",
            "600a8476a961574fb38157d7",
            "600a8476a961574fb38157d8",
            "600a8476a961574fb38157d9",
        ]
        deployment_id = SAMPLE_ID
        repo.retrieve_unseen_results(
            user_id=user_id,
            deployment_id=deployment_id,
            module_ids=sample_module_ids,
            enabled_module_ids=sample_enabled_ids,
        )
        module_ids = [ObjectId(id) for id in sample_module_ids]
        enabled_module_ids = [ObjectId(id) for id in sample_enabled_ids]
        db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate.assert_called_with(
            self.retrieve_unseen_pipeline(module_ids, enabled_module_ids)
        )

    @patch(f"{MODULE_RESULT_PATH}.Primitive")
    def test_success_retrieve_aggregated_results_with_module_config_id(
        self, mock_primitive
    ):
        mock_primitive.get_class.return_value = MagicMock()
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        primitive_name = "test_primitive_name"
        aggregation_function = AggregateFunc.AVG
        mode = AggregateMode.DAILY
        user_id = "611ba01148f04036c453165b"
        repo.retrieve_aggregated_results(
            primitive_name=primitive_name,
            aggregation_function=aggregation_function,
            mode=mode,
            module_config_id="some_id",
            user_id=ObjectId(user_id),
        )
        called_args = db[primitive_name].aggregate.call_args[0]
        expected_call = {
            "$match": {
                mock_primitive.USER_ID: ObjectId(user_id),
                mock_primitive.MODULE_CONFIG_ID: "some_id",
            }
        }
        self.assertIn(expected_call, called_args[0])

    @patch(f"{MODULE_RESULT_PATH}.Primitive")
    def test_retrieve_aggregated_results_with_module_config_id_no_user_id(
        self, mock_primitive
    ):
        mock_primitive.get_class.return_value = MagicMock()
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        primitive_name = "test_primitive_name"
        aggregation_function = AggregateFunc.AVG
        mode = AggregateMode.DAILY
        user_id = "611ba01148f04036c453165b"
        repo.retrieve_aggregated_results(
            primitive_name=primitive_name,
            aggregation_function=aggregation_function,
            mode=mode,
            module_config_id="some_id",
        )
        called_args = db[primitive_name].aggregate.call_args[0]
        expected_call = {
            "$match": {
                mock_primitive.USER_ID: ObjectId(user_id),
                mock_primitive.MODULE_CONFIG_ID: "some_id",
            }
        }
        self.assertNotIn(expected_call, called_args[0])

    @patch(f"{MODULE_RESULT_PATH}.Primitive")
    def test_success_retrieve_primitive(self, mock_primitive):
        mock_primitive.get_class.return_value = MagicMock()
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        primitive_name = "test_primitive_name"
        user_id = SAMPLE_ID
        primitive_id = SAMPLE_ID
        repo.retrieve_primitive(
            user_id=user_id, primitive_name=primitive_name, primitive_id=primitive_id
        )
        query = {
            mock_primitive.USER_ID: ObjectId(user_id),
            mock_primitive.ID_: ObjectId(primitive_id),
        }
        db[primitive_name].find_one.assert_called_once_with(query)

    @patch(f"{MODULE_RESULT_PATH}.Primitive")
    def test_success_retrieve_primitive_by_name(self, mock_primitive):
        mock_primitive.get_class.return_value = MagicMock()
        db = MagicMock()
        repo = MongoModuleResultRepository(db)
        user_id = SAMPLE_ID
        primitive_name = "test_primitive_name"
        repo.retrieve_primitive_by_name(user_id=user_id, primitive_name=primitive_name)
        db[primitive_name].find_one.assert_called_once_with(
            {mock_primitive.USER_ID: ObjectId(user_id)}
        )


if __name__ == "__main__":
    unittest.main()
