import unittest
from unittest.mock import MagicMock

from pymongo.database import Database
from sdk.common.utils import inject

SAMPLE_ID = "6284a61b0fdb62fd01bb3ef0"


class DashboardMongoRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

        def bind(binder):
            binder.bind(Database, self.db)

        inject.clear_and_configure(bind)


if __name__ == "__main__":
    unittest.main()
