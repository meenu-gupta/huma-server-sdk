import unittest
from unittest.mock import patch, mock_open

from sdk.common.utils.file_utils import load_json_file, load_mongo_dump_file

FILE_UTILS_PATH = "sdk.common.utils.file_utils"


class FileUtilsTestCase(unittest.TestCase):
    @patch(f"{FILE_UTILS_PATH}.json")
    @patch(f"{FILE_UTILS_PATH}.Path")
    def test_load_json_file(self, mock_path, mock_json):
        path = "path_to_file"

        load_json_file(path=path)

        mock_json.loads.assert_called_once_with(mock_path().read_text())

    @patch(f"{FILE_UTILS_PATH}.open", mock_open())
    @patch(f"{FILE_UTILS_PATH}.logger")
    @patch(f"{FILE_UTILS_PATH}.json")
    @patch(f"{FILE_UTILS_PATH}.Database")
    def test_load_mongo_dump_file(self, mock_db, mock_json, mock_logger):
        user_1 = {"_id": 1, "name": "Name #1"}
        user_2 = {"_id": 2, "name": "Name #2"}

        mock_json.load.return_value = {0: [user_1], 1: [user_2]}

        file_path = "path_to_file"

        load_mongo_dump_file(file_path=file_path, database=mock_db)

        mock_db[2].update_one.assert_called_with(
            {"_id": user_2["_id"]}, {"$set": user_2}, upsert=True
        )
        mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
