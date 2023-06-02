import unittest
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.utils import set_proper_export_type

EXPORT_PROCESS_ID = "5d386cc6ff885918d96edb2d"
EXPORT_PROCESS_ID_OBJ = ObjectId(EXPORT_PROCESS_ID)


class MigrationsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.export_collection = MagicMock()
        self.db.get_collection.return_value = self.export_collection

    def test_set_proper_export_type(self):
        self.export_collection.aggregate.return_value = [
            {"_id": None, "ids": [EXPORT_PROCESS_ID_OBJ]}
        ]
        set_proper_export_type(self.db)

        expected_search_query = {"_id": {"$in": [EXPORT_PROCESS_ID_OBJ]}}
        expected_update_query = {
            "$set": {ExportProcess.EXPORT_TYPE: ExportProcess.ExportType.USER.value}
        }
        self.export_collection.aggregate.assert_called_once()
        self.export_collection.update_many.assert_called_with(
            expected_search_query, expected_update_query
        )
