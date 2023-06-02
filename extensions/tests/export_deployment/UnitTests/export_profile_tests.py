import unittest
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.export_deployment.models.export_deployment_models import (
    ExportParameters,
    DEFAULT_DEIDENTIFY_REMOVE_FIELDS,
    DEFAULT_DEIDENTIFY_HASH_FIELDS,
    DEFAULT_EXCLUDE_FIELDS,
)
from extensions.export_deployment.use_case.export_profile_use_cases import (
    CreateExportProfileUseCase,
    UpdateExportProfileUseCase,
    DeleteExportProfileUseCase,
    RetrieveExportProfilesUseCase,
)
from extensions.export_deployment.use_case.export_request_objects import (
    CreateExportProfileRequestObject,
    UpdateExportProfileRequestObject,
    DeleteExportProfileRequestObject,
    RetrieveExportProfilesRequestObject,
)

PROFILE_NAME = "test"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
PROFILE_ID = "5d386cc6ff885918d96edb2d"


class ExportProfilesTestCase(unittest.TestCase):
    def test_create_export_profile_use_case_valid(self):
        request_data = {
            CreateExportProfileRequestObject.NAME: PROFILE_NAME,
            CreateExportProfileRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            CreateExportProfileRequestObject.CONTENT: {
                ExportParameters.VIEW: ExportParameters.DataViewOption.DAY.value
            },
        }
        request_object = CreateExportProfileRequestObject.from_dict(request_data)
        mocked_export_repo = MagicMock()
        mocked_export_repo.create_export_profile.return_value = str(ObjectId())
        use_case = CreateExportProfileUseCase(mocked_export_repo)
        use_case.execute(request_object)
        mocked_export_repo.create_export_profile.assert_called_with(request_object)

    def test_update_export_profile_use_case__name_only_valid(self):
        request_data = {
            UpdateExportProfileRequestObject.NAME: PROFILE_NAME,
            UpdateExportProfileRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            UpdateExportProfileRequestObject.ID: PROFILE_ID,
        }
        request_object = UpdateExportProfileRequestObject.from_dict(request_data)
        mocked_export_repo = MagicMock()
        use_case = UpdateExportProfileUseCase(mocked_export_repo)
        use_case.execute(request_object)
        mocked_export_repo.update_export_profile.assert_called_with(request_object)

    def test_update_export_profile_use_case__content_only_valid(self):
        request_data = {
            UpdateExportProfileRequestObject.CONTENT: {},
            UpdateExportProfileRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            UpdateExportProfileRequestObject.ID: PROFILE_ID,
        }
        request_object = UpdateExportProfileRequestObject.from_dict(request_data)
        mocked_export_repo = MagicMock()
        use_case = UpdateExportProfileUseCase(mocked_export_repo)
        use_case.execute(request_object)
        mocked_export_repo.update_export_profile.assert_called_with(request_object)

    def test_delete_export_profile_use_case_valid(self):
        request_data = {
            DeleteExportProfileRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            DeleteExportProfileRequestObject.PROFILE_ID: PROFILE_ID,
        }
        request_object = DeleteExportProfileRequestObject.from_dict(request_data)
        mocked_export_repo = MagicMock()
        use_case = DeleteExportProfileUseCase(mocked_export_repo)
        use_case.execute(request_object)
        mocked_export_repo.delete_export_profile.assert_called_with(
            request_object.profileId
        )

    def test_retrieve_export_profile_use_case_valid(self):
        request_data = {
            RetrieveExportProfilesRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            RetrieveExportProfilesRequestObject.NAME_CONTAINS: "some",
        }
        request_object = RetrieveExportProfilesRequestObject.from_dict(request_data)
        mocked_export_repo = MagicMock()
        use_case = RetrieveExportProfilesUseCase(mocked_export_repo)
        use_case.execute(request_object)
        mocked_export_repo.retrieve_export_profiles.assert_called_with(
            request_object.nameContains, request_object.deploymentId, None
        )

    def test_default_deidentify_export_fields(self):
        default_params = ExportParameters()
        self.assertEqual(
            DEFAULT_DEIDENTIFY_REMOVE_FIELDS, default_params.deIdentifyRemoveFields
        )
        self.assertEqual(
            DEFAULT_DEIDENTIFY_HASH_FIELDS, default_params.deIdentifyHashFields
        )
        self.assertEqual(DEFAULT_EXCLUDE_FIELDS, default_params.excludeFields)


if __name__ == "__main__":
    unittest.main()
