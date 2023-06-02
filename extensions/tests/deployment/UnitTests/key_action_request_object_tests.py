import unittest

from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.router.deployment_requests import (
    CreateKeyActionConfigRequestObject,
    UpdateKeyActionConfigRequestObject,
)
from extensions.tests.deployment.IntegrationTests.key_action_tests import (
    KEY_ACTION_MODULE_TYPE,
    created_key_action_config,
    simple_key_action_config,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

VALID_KEY_ACTION_ID = "5e9443789911c97c0b639374"
KEY_ACTION_LEARN_TYPE = KeyActionConfig.Type.LEARN.value


class CreateKeyActionConfigRequestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.key_action_module_dict = created_key_action_config()
        self.key_action_learn_dict = simple_key_action_config(
            type_=KEY_ACTION_LEARN_TYPE
        )
        return super().setUp()

    def test_success_create_key_action_request_object(self):
        try:
            CreateKeyActionConfigRequestObject.from_dict(self.key_action_module_dict)
        except ConvertibleClassValidationError:
            self.fail()

        try:
            CreateKeyActionConfigRequestObject.from_dict(self.key_action_module_dict)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_key_action_request_object(self):
        key_action_config_invalid_duration_iso = {
            **self.key_action_module_dict,
            KeyActionConfig.DURATION_ISO: "P0DT0M0S",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration_iso
        )
        key_action_config_invalid_duration_iso = {
            **self.key_action_module_dict,
            KeyActionConfig.NOTIFY_EVERY: "P0DT0M0S",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration_iso
        )

    def test_successful_create_key_action_request_object_without_notify_every(self):
        key_action_config = {
            **self.key_action_module_dict,
        }
        key_action_config.pop(KeyActionConfig.NOTIFY_EVERY, None)
        key_action_config_request = CreateKeyActionConfigRequestObject.from_dict(
            key_action_config
        )
        self.assertIsNone(key_action_config_request.notifyEvery)

    def test_failure_create_key_action_request_object_invalid_duration(self):
        key_action_config_invalid_duration = {
            **self.key_action_module_dict,
            KeyActionConfig.INSTANCE_EXPIRES_IN: "PT6D22H40M",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration
        )
        key_action_config_invalid_duration = {
            **self.key_action_module_dict,
            KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration
        )

    def test_failure_create_key_action_request_object_invalid_type(self):
        key_action_module_config_invalid_type = {
            **self.key_action_module_dict,
            KeyActionConfig.TYPE: KEY_ACTION_LEARN_TYPE,
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_module_config_invalid_type
        )
        key_action_learn_config_invalid_type = {
            **self.key_action_learn_dict,
            KeyActionConfig.TYPE: KEY_ACTION_MODULE_TYPE,
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_learn_config_invalid_type
        )

    def test_failure_create_key_action_request_object_contains_module_learn(self):
        key_action_module_config = {
            **self.key_action_module_dict,
            KeyActionConfig.LEARN_ARTICLE_ID: self.key_action_learn_dict[
                KeyActionConfig.LEARN_ARTICLE_ID
            ],
        }
        self._assert_convertible_class_validation_error_raised(key_action_module_config)

    def test_failure_create_key_action_request_object_contains_id(self):
        key_action_module_config = {
            **self.key_action_module_dict,
            KeyActionConfig.ID: VALID_KEY_ACTION_ID,
        }
        self._assert_convertible_class_validation_error_raised(key_action_module_config)

    def _assert_convertible_class_validation_error_raised(
        self, key_action_config: dict
    ):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateKeyActionConfigRequestObject.from_dict(key_action_config)


class UpdateKeyActionConfigRequestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.key_action_module_dict = {
            **created_key_action_config(),
            KeyActionConfig.ID: VALID_KEY_ACTION_ID,
        }
        self.key_action_learn_dict = {
            **simple_key_action_config(type_=KEY_ACTION_LEARN_TYPE),
            KeyActionConfig.ID: VALID_KEY_ACTION_ID,
        }
        return super().setUp()

    def test_success_update_key_action_request_object(self):
        try:
            UpdateKeyActionConfigRequestObject.from_dict(self.key_action_module_dict)
        except ConvertibleClassValidationError:
            self.fail()

        try:
            UpdateKeyActionConfigRequestObject.from_dict(self.key_action_learn_dict)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_update_key_action_request_object(self):
        key_action_config_invalid_duration_iso = {
            **self.key_action_module_dict,
            KeyActionConfig.DURATION_ISO: "P0DT0M0S",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration_iso
        )
        key_action_config_invalid_duration_iso = {
            **self.key_action_module_dict,
            KeyActionConfig.NOTIFY_EVERY: "P0DT0M0S",
        }
        self._assert_convertible_class_validation_error_raised(
            key_action_config_invalid_duration_iso
        )

    def test_failure_update_key_action_request_object_no_id(self):
        key_action_config_dict = self.key_action_module_dict
        key_action_config_dict.pop(UpdateKeyActionConfigRequestObject.ID)
        self._assert_convertible_class_validation_error_raised(key_action_config_dict)

    def _assert_convertible_class_validation_error_raised(self, key_action_config):
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateKeyActionConfigRequestObject.from_dict(key_action_config)
