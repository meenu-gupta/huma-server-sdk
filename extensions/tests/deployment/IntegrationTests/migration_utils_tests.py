from pathlib import Path

from bson import ObjectId
from extensions.deployment.models.deployment import (
    Deployment,
    Features,
    Messaging,
    Location,
)
from extensions.tests.test_case import ExtensionTestCase
from tools.mongodb_script.add_message_to_deployment_without_message import (
    ENABLED_KEY,
    MESSAGES_KEY,
    set_predefined_message_for_deployment_without_message,
)
from tools.mongodb_script.migrate_country_to_location_in_deployment import (
    move_country_to_location,
)
from tools.mongodb_script.move_labels_from_feature_to_deployment_level import (
    move_labels_from_feature_to_deployment_level,
)

DEPLOYMENT_MESSAGING_MESSAGES_MISSING = ObjectId("627b65f6670a244cc036b6b8")
DEPLOYMENT_MESSAGING_MESSAGES_EMPTY_LIST = ObjectId("5ff4a07b0318f65610aa0dec")


class MigrationUtilsTest(ExtensionTestCase):
    components = []
    deployment_collection = Deployment.__name__.lower()
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/only_deployment_dump.json"),
    ]

    def test_set_predefined_message_for_deployment_without_message(self):
        affected_query = {ENABLED_KEY: True, MESSAGES_KEY: {"$in": [None, []]}}

        affected_deployment = self._retrieve_deployment_from_db(affected_query)
        self.assertEqual(2, affected_deployment.count())

        set_predefined_message_for_deployment_without_message(
            self.mongo_database, Messaging._default_message
        )
        affected_deployment = self._retrieve_deployment_from_db(affected_query)
        self.assertEqual(0, affected_deployment.count())

        self._assert_default_message_set(DEPLOYMENT_MESSAGING_MESSAGES_MISSING)
        self._assert_default_message_set(DEPLOYMENT_MESSAGING_MESSAGES_EMPTY_LIST)

    def test_move_labels_from_features_to_deployment_level(self):

        affected_query = {
            f"{Deployment.FEATURES}.{Deployment.LABELS}": {"$exists": True}
        }

        affected_deployment = self._retrieve_deployment_from_db(affected_query)
        self.assertEqual(2, affected_deployment.count())

        actual_result = self._retrieve_deployments_with_labels_in_root_level()
        self.assertEqual(0, actual_result.count())

        move_labels_from_feature_to_deployment_level(self.mongo_database)

        actual_result = self._retrieve_deployments_with_labels_in_root_level()
        self.assertEqual(2, actual_result.count())

    def test_move_country_to_location(self):
        country_field = "country"
        deployment = self._retrieve_deployment_from_db({})[0]
        self.assertIn(country_field, deployment)
        self.assertNotIn(Deployment.LOCATION, deployment)

        move_country_to_location(self.mongo_database)
        deployment = self._retrieve_deployment_from_db({})[0]
        expected_location = {
            Location.ADDRESS: "London, United Kingdom",
            Location.COUNTRY: "United Kingdom",
            Location.COUNTRY_CODE: "GB",
            Location.CITY: "London",
            Location.LATITUDE: 51.5,
            Location.LONGITUDE: -0.083333,
        }
        self.assertEqual(expected_location, deployment[Deployment.LOCATION])
        self.assertIn(country_field, deployment)

    def _retrieve_deployments_with_labels_in_root_level(self):
        filter_query = {f"{Deployment.LABELS}": {"$exists": True}}
        affected_deployment = self._retrieve_deployment_from_db(filter_query)
        return affected_deployment

    def _retrieve_deployment_from_db(self, query):
        return self.mongo_database[self.deployment_collection].find(query)

    def _assert_default_message_set(self, deployment_id):
        deployment = self.mongo_database[self.deployment_collection].find_one(
            {Deployment.ID_: deployment_id}
        )
        self.assertListEqual(
            Messaging._default_message,
            deployment[Deployment.FEATURES][Features.MESSAGING][Messaging.MESSAGES],
        )
