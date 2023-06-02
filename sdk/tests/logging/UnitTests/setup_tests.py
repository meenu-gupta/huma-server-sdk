import unittest
from collections import OrderedDict
from unittest.mock import patch, mock_open, MagicMock
from sdk.common.logging.setup import init_logging, json_translate

SETUP_PATH = "sdk.common.logging.setup"


class SetupTestCase(unittest.TestCase):
    @patch(f"{SETUP_PATH}.open", mock_open())
    @patch(f"{SETUP_PATH}.logging")
    @patch(f"{SETUP_PATH}.os")
    def test_init_logging_debug_off(self, mock_os, mock_logging):
        mock_os.getenv.side_effect = [None, True]

        init_logging(debug=False)

        mock_os.getenv.assert_called()
        mock_logging.config.dictConfig.assert_called()
        mock_logging.debug.assert_called()

    @patch(f"{SETUP_PATH}.open", mock_open())
    @patch(f"{SETUP_PATH}.logging")
    @patch(f"{SETUP_PATH}.os")
    def test_init_logging_debug_on(self, mock_os, mock_logging):
        mock_os.getenv.return_value = None
        mock_logger = mock_logging.getLogger.return_value = MagicMock()
        init_logging(debug=True)

        mock_os.getenv.assert_called()
        mock_logging.getLogger.assert_called()
        mock_logger.setLevel.assert_called_with(mock_logging.DEBUG)

    @patch(f"{SETUP_PATH}.open", mock_open())
    @patch(f"{SETUP_PATH}.logging")
    @patch(f"{SETUP_PATH}.os")
    def test_init_logging_file_name_provided(self, mock_os, mock_logging):
        mock_os.getenv.return_value = "file_name"

        init_logging(debug=False)

        mock_os.getenv.assert_called()
        mock_logging.config.dictConfig.assert_called()
        mock_logging.debug.assert_called()

    @patch(f"{SETUP_PATH}.json")
    def test_json_translate(self, mock_json):
        arg = OrderedDict([("levelname", 1), ("request_id", 2)])

        json_translate(arg)
        arg["level"] = arg["severity"] = 1
        mock_json.dumps.assert_called_with(arg)


if __name__ == "__main__":
    unittest.main()
