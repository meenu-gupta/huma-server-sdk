import unittest

from extensions.deployment.models.deployment import Deployment, ExtraCustomFieldConfig
from sdk.common.utils.convertible import dict_field, meta, convertibleclass
from sdk.common.utils.validators import validate_len


class DeploymentDefaultFactoryTestCase(unittest.TestCase):
    def test_success_with_default_factory(self):
        @convertibleclass
        class DeploymentSampleWithDefaultFactory(Deployment):
            extraCustomFields: dict = dict_field(
                default_factory=dict,
                nested_cls=ExtraCustomFieldConfig,
                metadata=meta(validate_len(0, 5)),
            )

        req_obj = DeploymentSampleWithDefaultFactory.from_dict(
            {DeploymentSampleWithDefaultFactory.NAME: "New Name"}
        )
        updated_dep = req_obj.to_dict(include_none=False)
        # actually extraCustomFields should not be exist in updated_dep because it is not set -> means default_factory is wrong
        self.assertIn(
            DeploymentSampleWithDefaultFactory.EXTRA_CUSTOM_FIELDS, updated_dep
        )
        self.assertEqual(
            updated_dep[DeploymentSampleWithDefaultFactory.EXTRA_CUSTOM_FIELDS], {}
        )
