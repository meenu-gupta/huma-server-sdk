import copy
import unittest
from unittest.mock import patch, MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.helpers.convertion_helpers import (
    DEFAULT_INCLUDED_FIELDS,
)
from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.module_result.models.primitives import Primitive
from extensions.organization.models.organization import Organization
from extensions.publisher.adapters.utils import transform_publisher_data
from extensions.publisher.callbacks.publisher_callback import (
    publisher_callback,
)
from extensions.publisher.models.primitive_data import PrimitiveData
from extensions.publisher.tasks import (
    match_publisher_and_event,
)
from extensions.tests.publisher.UnitTests.UnitTests.sample_data import (
    sample_event_primitives,
    sample_deployment_id,
    sample_user_id,
    sample_module_result_id,
    sample_module_config_id,
    sample_user,
    sample_publishers,
    sample_event_dicts,
)


def get_deployment():
    return Deployment(
        id="61926cbe9cb844829c967f8a",
        name="Publisher Test Deployment",
    )


def get_organization():
    return Organization(
        name="test",
        deploymentIds=["606c50a113dbea3656ff1bb0"],
        privacyPolicyUrl="privacy_url_val_organization",
        eulaUrl="eula_url_val_organization",
        termAndConditionUrl="term_val_organization",
    )


def attach_users(*args):
    data = args[4]

    for module_name, primitive_dicts in data.items():
        for primitive_dict in primitive_dicts:
            user_dict = sample_user
            primitive_dict["user"] = user_dict.copy()


class PublisherTestCase(unittest.TestCase):
    @patch("extensions.publisher.callbacks.publisher_callback.publish_data_task")
    def test_publisher_callback(self, mocked_publish_data_task):
        event = PostCreateModuleResultBatchEvent(
            primitives=sample_event_primitives,
            deployment_id=sample_deployment_id,
            user_id=sample_user_id,
            module_id="BloodPressure",
            module_result_id=sample_module_result_id,
            module_config_id=sample_module_config_id,
            device_name="iOS",
            start_date_time="2021-11-09T14:28:37.630000Z",
        )

        publisher_callback(event)

        primitive_data = {
            PrimitiveData.USER_ID: "615db4dd92a28f0cee2e14c1",
            PrimitiveData.NAME: "BloodPressure",
            PrimitiveData.ID: "618a8595a57e07e2de456e33",
        }
        mocked_publish_data_task.delay.assert_called_once_with(
            [primitive_data],
            event.module_id,
            event.device_name,
            event.module_config_id,
            event.deployment_id,
        )

    @patch("extensions.publisher.adapters.utils.get_consents_meta_data_with_deployment")
    @patch(
        "extensions.publisher.adapters.utils.attach_users",
        side_effect=attach_users,
    )
    def test_transform_publisher_data(
        self, mocked_attach_users, mocked_get_consents_meta_data
    ):
        mocked_deployment_repo = MagicMock()
        mocked_deployment_repo.retrieve_deployment.return_value = get_deployment()
        mocked_get_consents_meta_data.return_value = None, None

        for sample_event_dict in sample_event_dicts:
            for sample_publisher in sample_publishers:
                sample = copy.deepcopy(sample_event_dict)

                for primitive in sample["primitives"]:
                    self.assertNotIn("user", primitive)

                transform_publisher_data(
                    sample_publisher, sample, mocked_deployment_repo
                )

                self.assertEqual(
                    len(sample["primitives"]), len(sample_event_dict["primitives"])
                )
                self.assertEqual(sample["moduleId"], sample_event_dict["moduleId"])

                if sample_publisher.transform.includeUserMetaData:
                    mocked_attach_users.assert_called_once()
                    mocked_attach_users.call_count = 0

                    for primitive in sample["primitives"]:
                        self.assertIn("user", primitive)
                else:
                    mocked_attach_users.assert_not_called()

                    for primitive in sample["primitives"]:
                        self.assertNotIn("user", primitive)

                if sample_publisher.transform.deIdentified:
                    for idx, primitive in enumerate(sample["primitives"]):
                        for field in sample_publisher.transform.deIdentifyHashFields:
                            self.assertIn(field, primitive)
                            self.assertNotEqual(
                                primitive[field],
                                sample_event_dict["primitives"][idx][field],
                            )
                    for idx, primitive in enumerate(sample["primitives"]):
                        for field in sample_publisher.transform.deIdentifyRemoveFields:
                            self.assertNotIn(field, primitive)
                            assert_not_in_or_null(
                                self,
                                sample_publisher.transform.includeNullFields,
                                field,
                                primitive["user"],
                            )
                else:
                    for idx, primitive in enumerate(sample["primitives"]):
                        for field in sample_publisher.transform.deIdentifyHashFields:
                            self.assertIn(field, primitive)
                            self.assertEqual(
                                primitive[field],
                                sample_event_dict["primitives"][idx][field],
                            )
                for idx, primitive in enumerate(sample["primitives"]):
                    for field in sample_publisher.transform.excludeFields:
                        if len(field.split(".")) == 1:
                            self.assertNotIn(field, primitive)
                        elif len(field.split(".")) == 2:
                            if field.split(".")[0] in primitive:
                                self.assertNotIn(
                                    field.split(".")[1], primitive[field.split(".")[0]]
                                )

    @patch("extensions.publisher.adapters.utils.get_consents_meta_data_with_deployment")
    @patch(
        "extensions.publisher.adapters.utils.attach_users",
        side_effect=attach_users,
    )
    def test_transform_publisher_data_include_fields(
        self, mocked_attach_users, mocked_get_consents_meta_data
    ):
        mocked_deployment_repo = MagicMock()
        mocked_deployment_repo.retrieve_deployment.return_value = get_deployment()
        mocked_get_consents_meta_data.return_value = None, None

        for sample_event_dict in sample_event_dicts:
            for sample_publisher in sample_publishers:
                sample = copy.deepcopy(sample_event_dict)

                for primitive in sample["primitives"]:
                    self.assertNotIn("user", primitive)

                transform_publisher_data(
                    sample_publisher, sample, mocked_deployment_repo
                )

                if sample_publisher.transform.includeFields:
                    for idx, primitive in enumerate(sample["primitives"]):
                        for field in DEFAULT_INCLUDED_FIELDS:
                            self.assertIn(field, primitive)
                        for field in sample_publisher.transform.includeFields:
                            self.assertIn(field, primitive)
                        self.assertNotIn(Primitive.DEPLOYMENT_ID, primitive)

    def test_match_publisher_and_event(self):
        org_repo = MagicMock()
        org_repo.retrieve_organization.return_value = get_organization()

        # in case event deploymentId exists in deploymentIds
        matched = match_publisher_and_event(
            sample_publishers[0], sample_event_dicts[0], org_repo
        )
        self.assertEqual(True, matched)

        # in case event deploymentId don't exists in deploymentIds
        matched = match_publisher_and_event(
            sample_publishers[0], sample_event_dicts[1], org_repo
        )
        self.assertEqual(False, matched)

        # in case we search in organizationId
        matched = match_publisher_and_event(
            sample_publishers[1], sample_event_dicts[0], org_repo
        )
        self.assertEqual(False, matched)

        # in case we don't provide deploymentIds and we search in organizationId
        matched = match_publisher_and_event(
            sample_publishers[1], sample_event_dicts[2], org_repo
        )
        self.assertEqual(True, matched)

        # in case none of the organizationId and deploymentIds provided and listener set to gobal it should return True
        matched = match_publisher_and_event(
            sample_publishers[2], sample_event_dicts[2], org_repo
        )
        self.assertEqual(True, matched)

        # in case moduleName get match
        matched = match_publisher_and_event(
            sample_publishers[3], sample_event_dicts[2], org_repo
        )
        self.assertEqual(True, matched)

        # in case moduleName don't get match
        matched = match_publisher_and_event(
            sample_publishers[4], sample_event_dicts[2], org_repo
        )
        self.assertEqual(False, matched)

        # in case exludeModuleName get match
        matched = match_publisher_and_event(
            sample_publishers[5], sample_event_dicts[2], org_repo
        )
        self.assertEqual(False, matched)


def assert_not_in_or_null(self, is_null, member, container):
    if not is_null:
        self.assertNotIn(member, container)
    else:
        if member in container:
            self.assertIsNone(container[member])


if __name__ == "__main__":
    unittest.main()
