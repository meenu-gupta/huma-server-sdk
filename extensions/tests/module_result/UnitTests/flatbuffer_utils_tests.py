import unittest
from unittest.mock import patch, MagicMock

from freezegun.api import FakeDatetime

from extensions.module_result.common.flatbuffer_utils import (
    ecg_data_points_to_array,
    process_steps_flatbuffer_file,
    _convert_flatbuffer_to_json,
)

PATH = "extensions.module_result.common.flatbuffer_utils"
TEST_FILE_DIR = "test_file_dir"
TEST_FILE_NAME = "test_file_name"
TEST_FILE_PATH = f"{TEST_FILE_DIR}/{TEST_FILE_NAME}.json"


class MockObjectToFolder(MagicMock):
    return_value = (TEST_FILE_DIR, TEST_FILE_NAME)


data = {
    "stepCounterData": [{"startDateTime": 1325545200, "endDateTime": 1327964400.0}],
    "platform": [],
}


class FlatBufferUtilsTestCase(unittest.TestCase):
    @patch(f"{PATH}.json", MagicMock(return_value={}))
    @patch(f"{PATH}.os")
    @patch(f"{PATH}.subprocess")
    def test___convert_flatbuffer_to_json(self, subprocess, os):
        schema_filename = "test_schema_filename"
        os.path.join.return_value = schema_filename
        _convert_flatbuffer_to_json(
            file_dir=TEST_FILE_DIR,
            filename=TEST_FILE_NAME,
            schema_filename=schema_filename,
        )
        subprocess.run.assert_called_with(
            [
                schema_filename,
                "--json",
                "--raw-binary",
                schema_filename,
                "--",
                TEST_FILE_NAME,
                "--strict-json",
            ],
            capture_output=True,
            cwd=TEST_FILE_DIR,
        )
        os.remove.assert_called_with(f"{TEST_FILE_DIR}/{TEST_FILE_NAME}")

    @patch(f"{PATH}.json", MagicMock(return_value={}))
    @patch(f"{PATH}.os")
    @patch(f"{PATH}.open")
    @patch(f"{PATH}.download_object_to_folder", MockObjectToFolder())
    @patch(f"{PATH}._convert_flatbuffer_to_json")
    def test_ecg_data_points_to_array(self, flatbuffer_to_json, open, os):
        schema_file = "ecg.fbs"
        flatbuffer_to_json.return_value = {}
        s3_obj = MagicMock()
        ecg_data_points_to_array(s3_obj)
        flatbuffer_to_json.assert_called_with(
            TEST_FILE_DIR, TEST_FILE_NAME, schema_file
        )
        open.assert_called_with(TEST_FILE_PATH, "rb")
        os.remove.assert_called_with(TEST_FILE_PATH)

    @patch(f"{PATH}.json")
    @patch(f"{PATH}.open")
    @patch(f"{PATH}._convert_flatbuffer_to_json")
    def test_process_steps_flatbuffer_file(self, flatbuffer_to_json, open, json):
        json.loads.return_value = data
        schema_file = "steps.fbs"
        flatbuffer_to_json.return_value = {}
        process_steps_flatbuffer_file(
            file_dir=TEST_FILE_DIR,
            filename=TEST_FILE_NAME,
            from_date=FakeDatetime(2012, 1, 1, 0, 0),
            to_date=FakeDatetime(2012, 2, 1, 0, 0),
        )
        flatbuffer_to_json.assert_called_with(
            TEST_FILE_DIR, TEST_FILE_NAME, schema_file
        )
        open.assert_called_with(TEST_FILE_PATH, "w")
