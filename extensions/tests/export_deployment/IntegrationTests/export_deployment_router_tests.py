import binascii
import json
import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from shutil import copyfile
from unittest.mock import patch

import pytz
from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.common.s3object import S3Object
from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.export_deployment.tasks import run_export
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
    CreateExportProfileRequestObject,
    CheckExportDeploymentTaskStatusRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
)
from extensions.module_result.common.flatbuffer_utils import (
    process_steps_flatbuffer_file,
)
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import ECGAliveCor, Primitive, Weight
from extensions.module_result.modules.ecg_alive_cor import ECGAliveCorModule
from extensions.organization.component import OrganizationComponent
from extensions.revere.component import RevereComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values, hash_value

ORGANIZATION_USER_ID = "5e8f0c74b50aa9656c34789f"
WEIGHT = Weight.__name__
LAYER = ExportRequestObject.LAYER
QUANTITY = ExportRequestObject.QUANTITY
FORMAT = ExportRequestObject.FORMAT
VIEW = ExportRequestObject.VIEW
BINARY = ExportRequestObject.BINARY_OPTION
NESTED_LAYER = ExportRequestObject.DataLayerOption.NESTED.value
FLAT_LAYER = ExportRequestObject.DataLayerOption.FLAT.value
SINGLE_QTY = ExportRequestObject.DataQuantityOption.SINGLE.value
MULTIPLE_QTY = ExportRequestObject.DataQuantityOption.MULTIPLE.value
DAY_VIEW = ExportRequestObject.DataViewOption.DAY.value
USER_VIEW = ExportRequestObject.DataViewOption.USER.value
MODULE_VIEW = ExportRequestObject.DataViewOption.MODULE_CONFIG.value
SINGLE_VIEW = ExportRequestObject.DataViewOption.SINGLE.value
BINARY_INCLUDE = ExportRequestObject.BinaryDataOption.BINARY_INCLUDE.value
BINARY_NONE = ExportRequestObject.BinaryDataOption.NONE.value
BINARY_SIGNED_URL = ExportRequestObject.BinaryDataOption.SIGNED_URL.value
JSON_FORMAT = ExportRequestObject.DataFormatOption.JSON.value
CSV_FORMAT = ExportRequestObject.DataFormatOption.CSV.value
JSON_CSV_FORMAT = ExportRequestObject.DataFormatOption.JSON_CSV.value
INCLUDE_NULL_FIELDS = ExportRequestObject.INCLUDE_NULL_FIELDS
INCLUDE_USER_META = ExportRequestObject.INCLUDE_USER_META_DATA
MODULE_NAMES = ExportRequestObject.MODULE_NAMES
ONBOARDING_MODULE_NAMES = ExportRequestObject.ONBOARDING_MODULE_NAMES
USER_IDS = ExportRequestObject.USER_IDS
FROM_DATE = ExportRequestObject.FROM_DATE
PREFER_SHORT_CODE = ExportRequestObject.PREFER_SHORT_CODE


EXPORTABLE_USE_CASE_PATH = (
    "extensions.export_deployment.use_case.exportable.exportable_use_case"
)


def get_zip_file_checksums(response, sample_file):
    sample_file_path = Path(__file__).parent.joinpath(f"fixtures/{sample_file}")
    with open(sample_file_path, "rb") as sample:
        sample_zip_info = sorted(
            [info.CRC for info in zipfile.ZipFile(BytesIO(sample.read())).infolist()]
        )
        response_zip_info = sorted(
            [info.CRC for info in zipfile.ZipFile(BytesIO(response.data)).infolist()]
        )
        return response_zip_info, sample_zip_info


def get_json_file_checksums(response, sample_file):
    sample_file_path = Path(__file__).parent.joinpath(f"fixtures/{sample_file}")
    with open(sample_file_path, "rb") as sample:
        return binascii.crc32(response.data), binascii.crc32(sample.read())


def download_audio_mock(self, bucket_name, object_name):
    audio_sample_path = "revere/IntegrationTests/fixtures/sample.mp4"
    sample_file_path = Path(__file__).parent.parent.parent.joinpath(audio_sample_path)
    with open(sample_file_path, "rb") as sample_file:
        data = sample_file.read()
        return BytesIO(data), len(data), "audio/mp4"


def download_file_mock(*args):
    sample_file_path = Path(__file__).parent.joinpath("fixtures/ecg_sample.pdf")
    with open(sample_file_path, "rb") as sample_file:
        data = sample_file.read()
        return BytesIO(data), len(data), "application/pdf"


class ExportTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        ExportDeploymentComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        CalendarComponent(),
        RevereComponent(),
        OrganizationComponent(),
    ]
    migration_path: str = str(Path(__file__).parent.parent.parent) + "/migrations"
    VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
    EXISTING_DATE = "2020-07-08"
    EXISTING_MODULE_ID = "Weight"
    VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
    API_URL = f"/api/extensions/v1beta/export/deployment/{VALID_DEPLOYMENT_ID}"
    COMMON_API_URL = f"/api/extensions/v1beta/export/"
    fixtures = [Path(__file__).parent.joinpath("fixtures/data.json")]

    def setUp(self):
        super().setUp()

        jwt_adapter = inject.instance(TokenAdapter)
        ref_token = jwt_adapter.create_access_token(identity=self.VALID_USER_ID)
        self.headers = {"Authorization": f"Bearer {ref_token}"}

    @staticmethod
    def download_csv_translations_mocked(*args):
        sample_file_path = Path(__file__).parent.joinpath(
            "fixtures/translation_sample.csv"
        )
        with open(sample_file_path, "rb") as sample_file:
            data = sample_file.read()
            return BytesIO(data), len(data), "text/csv"

    @staticmethod
    def download_json_translations_mocked(*args):
        sample_file_path = Path(__file__).parent.joinpath(
            "fixtures/translation_sample.json"
        )
        with open(sample_file_path, "rb") as sample_file:
            data = sample_file.read()
            return BytesIO(data), len(data), "text/json"

    def get_export_archive_from_response(self, response):
        """Returns json content from response zip file"""
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/zip", response.content_type)
        return zipfile.ZipFile(BytesIO(response.data))

    def get_single_json_data_from_response_archive(self, response):
        archive = self.get_export_archive_from_response(response)
        return json.loads(archive.read("data.json"))

    def request_export(self, request_data: dict, user_id: str = ORGANIZATION_USER_ID):
        headers = self.get_headers_for_token(user_id)
        return self.flask_client.post(
            self.COMMON_API_URL, headers=headers, json=request_data
        )

    def assert_zips_are_equal(self, response, sample):
        response_info, sample_info = get_zip_file_checksums(response, sample)
        self.assertEqual(sample_info, response_info)

    def assert_jsons_are_equal(self, response, sample):
        response_info, sample_info = get_json_file_checksums(response, sample)
        self.assertEqual(sample_info, response_info)

    @staticmethod
    def get_sample_request_data(
        organization_id: str = None,
        deployment_id: str = None,
        deployment_ids: list[str] = None,
        deidentified: bool = None,
    ):
        request_data = {
            VIEW: USER_VIEW,
            BINARY: BINARY_NONE,
            LAYER: FLAT_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.DEPLOYMENT_ID: deployment_id,
            ExportRequestObject.DEPLOYMENT_IDS: deployment_ids,
            ExportRequestObject.ORGANIZATION_ID: organization_id,
            ExportRequestObject.DEIDENTIFIED: deidentified,
            INCLUDE_USER_META: False,
            INCLUDE_NULL_FIELDS: False,
        }
        return remove_none_values(request_data)

    def create_export_profile(
        self, data: dict, organization_id=None, deployment_id=None, name="default"
    ):
        url = f"{self.COMMON_API_URL}profile"
        data = {
            CreateExportProfileRequestObject.ORGANIZATION_ID: organization_id,
            CreateExportProfileRequestObject.DEPLOYMENT_ID: deployment_id,
            CreateExportProfileRequestObject.CONTENT: data,
            CreateExportProfileRequestObject.NAME: name,
            CreateExportProfileRequestObject.DEFAULT: True,
        }
        self.flask_client.post(url, json=remove_none_values(data))


class ExportDeploymentsTestCase(ExportTestCase):
    def test_export_deployment_data_view_option_valid(self):
        # testing USER view is valid
        data = {
            VIEW: USER_VIEW,
            BINARY: BINARY_NONE,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertIn(self.EXISTING_MODULE_ID, export_data[self.VALID_USER_ID])
        self.assertEqual(3, len(export_data[self.VALID_USER_ID]))

        # testing DAY view is valid
        data[VIEW] = DAY_VIEW
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertIn(self.EXISTING_MODULE_ID, export_data[self.EXISTING_DATE])
        self.assertEqual(
            1, len(export_data[self.EXISTING_DATE][self.EXISTING_MODULE_ID])
        )

        # testing MODULE_CONFIG view is valid
        data[VIEW] = MODULE_VIEW
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertIn(self.EXISTING_MODULE_ID, export_data)
        self.assertEqual(2, len(export_data[self.EXISTING_MODULE_ID][Weight.__name__]))

    def test_export_deployment_date_range_option_valid(self):
        data = {
            ExportRequestObject.FROM_DATE: "2020-07-01",
            ExportRequestObject.TO_DATE: "2020-08-07",
            VIEW: USER_VIEW,
            BINARY: BINARY_NONE,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
            INCLUDE_USER_META: False,
        }

        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(1, len(export_data[self.VALID_USER_ID]))

        # testing that only "from" date filters data properly
        data.pop(ExportRequestObject.TO_DATE)
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(3, len(export_data[self.VALID_USER_ID]))

        # testing that only "to" date filters data properly
        data.pop(ExportRequestObject.FROM_DATE)
        data[ExportRequestObject.TO_DATE] = "2020-07-09"
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(1, len(export_data[self.VALID_USER_ID]))

    def test_export_deployment_with_datetime(self):
        data = {
            ExportRequestObject.FROM_DATE: "2020-07-08T19:55:00Z",
            ExportRequestObject.TO_DATE: "2020-07-08T19:56:00Z",
            VIEW: USER_VIEW,
            BINARY: BINARY_NONE,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(1, len(export_data[self.VALID_USER_ID][WEIGHT]))

        # test that data is retrieved correctly irrespective of timezone
        data[ExportRequestObject.FROM_DATE] = "2020-07-09T01:24:00+05:30"
        data[ExportRequestObject.TO_DATE] = "2020-07-09T01:27:00+05:30"
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(1, len(export_data[self.VALID_USER_ID][WEIGHT]))

        # test backward compatibility
        data[ExportRequestObject.FROM_DATE] = "2020-07-08"
        data[ExportRequestObject.TO_DATE] = "2020-07-08"
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(1, len(export_data))

    @patch("os.remove")
    def test_convert_flatbuffer_to_json(self, mock_remove):
        # this test is used to check if "flatc" is working and can convert flatbuffer file to json
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_file_name = "flatbuffer_sample"
            sample_file_dir = Path(__file__).parent.joinpath("fixtures")
            src_path = os.path.join(sample_file_dir, sample_file_name)
            dest_path = os.path.join(tmp_dir, sample_file_name)
            # copying sample file for processing into temp dir, cause it will be deleted after
            copyfile(src_path, dest_path)
            now = datetime.now().replace(tzinfo=pytz.utc)
            # start/end dates doesn't matter here for this test
            process_steps_flatbuffer_file(
                tmp_dir, sample_file_name, now - timedelta(days=7), now
            )
            mock_remove.assert_called_once()

    def test_export_deployment_binary_option_valid(self):
        data = {
            VIEW: MODULE_VIEW,
            BINARY: BINARY_INCLUDE,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
        }

        # testing that S3Object fields are saved to zip when BINARY_INCLUDE option selected
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            download_file_mock,
        ):
            resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
            self.assertEqual(200, resp.status_code)
            self.assertEqual("application/zip", resp.content_type)
            archive_files = zipfile.ZipFile(BytesIO(resp.data)).namelist()
            self.assertIn("binaries/", archive_files)
            self.assertIn("binaries/ecg_sample.pdf", archive_files)

        # testing that S3Object fields are converted to signed url when SIGNED_URL binary option selected
        with patch.object(
            MinioFileStorageAdapter, "get_pre_signed_url"
        ) as get_signed_url_mock:
            get_signed_url_mock.return_value = (
                fake_url_value
            ) = "https://dummystorage.com/some"
            data[BINARY] = BINARY_SIGNED_URL

            resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
            self.assertEqual(200, resp.status_code)
            archive = self.get_export_archive_from_response(resp)
            self.assertNotIn("binaries/", archive.namelist())
            self.assertNotIn("binaries/ecg_sample.pdf", archive.namelist())
            archive_data = json.loads(archive.read("data.json"))
            ecg_results = archive_data[ECGAliveCorModule.moduleId]
            signed_url_value = ecg_results[ECGAliveCor.__name__][0][
                ECGAliveCor.S3_OBJECT
            ]
            self.assertEqual(1, len(ecg_results))
            self.assertEqual(fake_url_value, signed_url_value)

        # testing that S3Object fields left as is when NONE binary option selected
        data[BINARY] = BINARY_NONE

        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        archive = self.get_export_archive_from_response(resp)
        self.assertNotIn("binaries/", archive.namelist())
        self.assertNotIn("binaries/ecg_sample.pdf", archive.namelist())
        archive_data = json.loads(archive.read("data.json"))
        ecg_results = archive_data[ECGAliveCorModule.moduleId]
        signed_url_value = ecg_results[ECGAliveCor.__name__][0][ECGAliveCor.S3_OBJECT]

        self.assertEqual(1, len(ecg_results))
        self.assertEqual(dict, type(signed_url_value))

    def test_export_deployment_binary_option_with_deidentified_valid(self):
        hashed_user_id = hash_value(self.VALID_USER_ID)
        data = {
            VIEW: USER_VIEW,
            BINARY: BINARY_INCLUDE,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.DEIDENTIFIED: True,
        }

        # testing that S3Object fields are saved to zip when BINARY_INCLUDE option selected
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            download_file_mock,
        ):
            resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
            self.assertEqual(200, resp.status_code)
            self.assertEqual("application/zip", resp.content_type)
            archive_files = zipfile.ZipFile(BytesIO(resp.data)).namelist()
            self.assertEqual(7, len(archive_files))
            self.assertIn(f"{hashed_user_id}/", archive_files)
            self.assertIn(f"{hashed_user_id}/binaries/ecg_sample.pdf", archive_files)

    def test_export_deployment_include_null_option_valid(self):
        # Testing that null fields are present in result
        data = {
            VIEW: USER_VIEW,
            ExportRequestObject.INCLUDE_NULL_FIELDS: False,
            BINARY: BINARY_NONE,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(3, len(export_data[self.VALID_USER_ID]))
        self.assertNotIn(
            Primitive.AGGREGATION_PRECISION,
            export_data[self.VALID_USER_ID][ECGAliveCor.__name__][0],
        )

        # Testing that null fields are removed from result
        data[ExportRequestObject.INCLUDE_NULL_FIELDS] = True
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        export_data = self.get_single_json_data_from_response_archive(resp)
        self.assertEqual(3, len(export_data[self.VALID_USER_ID]))
        self.assertIn(
            Primitive.AGGREGATION_PRECISION,
            export_data[self.VALID_USER_ID][ECGAliveCor.__name__][0],
        )

    def test_export_csv_nested_multiple_format(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: CSV_FORMAT,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.QUESTIONNAIRE_PER_NAME: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }

        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_nested_multiple_csv.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_export_csv_flat_single_data(self):
        data = {
            VIEW: MODULE_VIEW,
            FORMAT: CSV_FORMAT,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
            BINARY: BINARY_NONE,
            ExportRequestObject.INCLUDE_FIELDS: [],
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_flat_single_csv.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_export_json_data(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_FORMAT,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
            ExportRequestObject.QUESTIONNAIRE_PER_NAME: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        # flat single
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_flat_single_json.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        # flat multiple
        data[QUANTITY] = MULTIPLE_QTY
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_flat_multiple_json.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        # nested multiple
        data[LAYER] = NESTED_LAYER
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_nested_multiple_json.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        # nested single
        data[QUANTITY] = SINGLE_QTY
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_nested_single_json.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_split_answer_choices(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_CSV_FORMAT,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.SPLIT_MULTIPLE_CHOICES: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_split_answers_json_csv.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_split_answer_choices_flat(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_FORMAT,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.SPLIT_MULTIPLE_CHOICES: True,
            ExportRequestObject.USE_FLAT_STRUCTURE: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_split_answers_json_flat.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_translate_option(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_CSV_FORMAT,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.TRANSLATE_PRIMITIVES: True,
            BINARY: BINARY_NONE,
            ExportRequestObject.TRANSLATION_SHORT_CODES_OBJECT: {
                S3Object.KEY: "test",
                S3Object.REGION: "test",
                S3Object.BUCKET: "test",
            },
            ExportRequestObject.TRANSLATION_SHORT_CODES_OBJECT_FORMAT: CSV_FORMAT,
            ExportRequestObject.QUESTIONNAIRE_PER_NAME: True,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        translations_api_url = (
            f"/api/extensions/v1beta/export/deployment/5d386cc6ff885918d96edb2f"
        )

        # test with csv translation file
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            ExportTestCase.download_csv_translations_mocked,
        ):
            resp = self.flask_client.post(
                translations_api_url, headers=self.headers, json=data
            )
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "translation.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        data[ExportRequestObject.TRANSLATION_SHORT_CODES_OBJECT_FORMAT] = JSON_FORMAT
        # test with json translation file
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            ExportTestCase.download_json_translations_mocked,
        ):
            resp = self.flask_client.post(
                translations_api_url, headers=self.headers, json=data
            )
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "translation.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

    def test_split_symptoms_option(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_FORMAT,
            LAYER: NESTED_LAYER,
            QUANTITY: MULTIPLE_QTY,
            ExportRequestObject.SPLIT_SYMPTOMS: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_split_symptoms_json.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        # testing same for CSV
        data[FORMAT] = CSV_FORMAT
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_split_symptoms_csv.zip"
        )
        self.assertEqual(sample_zip_info, response_zip_info)

        # testing that result differs when option is False
        data[ExportRequestObject.TRANSLATE_PRIMITIVES] = False
        resp = self.flask_client.post(self.API_URL, headers=self.headers, json=data)
        self.assertEqual(200, resp.status_code)
        response_zip_info, sample_zip_info = get_zip_file_checksums(
            resp, "sample_nested_multiple_csv.zip"
        )
        self.assertNotEqual(sample_zip_info, response_zip_info)

    @patch("extensions.export_deployment.router.export_deployment_routers.g")
    @patch("extensions.export_deployment.tasks.run_export.apply_async")
    def test_run_async_export(self, mock_run_export_task, mock_g):
        mock_g.user.id = ObjectId()
        data = {VIEW: USER_VIEW}

        resp = self.flask_client.post(
            f"{self.API_URL}/task", headers=self.headers, json=data
        )
        self.assertEqual(200, resp.status_code)
        export_process_id = resp.json.get(
            CheckExportDeploymentTaskStatusRequestObject.EXPORT_PROCESS_ID
        )
        self.assertIsNotNone(export_process_id)
        mock_run_export_task.assert_called_once()

        with patch.object(ExportDeploymentUseCase, "execute") as mocked_export_execute:
            run_export(export_process_id)

        mocked_export_execute.assert_called_once()

    def test_export_revere_deployment(self):
        revere_deployment_id = "5d386cc6ff885918d96edb2d"
        data = {VIEW: USER_VIEW, INCLUDE_NULL_FIELDS: False, INCLUDE_USER_META: False}

        with patch.object(
            MinioFileStorageAdapter, "download_file", download_audio_mock
        ):
            resp = self.flask_client.post(
                f"/api/extensions/v1beta/export/deployment/{revere_deployment_id}",
                headers=self.headers,
                json=data,
            )
            self.assertEqual(200, resp.status_code)
        response_zip_info = sorted(
            [info.CRC for info in zipfile.ZipFile(BytesIO(resp.data)).infolist()]
        )
        sample_revere_checksums = [
            0,
            0,
            403201069,
            1761955573,
            2075876601,
            2075876601,
            2075876601,
            2075876601,
            2075876601,
            2075876601,
            2075876601,
            2075876601,
            3761241261,
        ]
        self.assertEqual(sample_revere_checksums, response_zip_info)

    def test_export_json_data_for_wrong_deployment(self):
        data = {
            VIEW: DAY_VIEW,
            FORMAT: JSON_FORMAT,
            LAYER: FLAT_LAYER,
            QUANTITY: SINGLE_QTY,
            ExportRequestObject.QUESTIONNAIRE_PER_NAME: True,
            BINARY: BINARY_NONE,
            INCLUDE_NULL_FIELDS: False,
            INCLUDE_USER_META: False,
        }
        # flat single
        invalid_deployment_id = "0Lg715rA5mxX"
        API_URL = f"/api/extensions/v1beta/export/deployment/{invalid_deployment_id}"
        resp = self.flask_client.post(API_URL, headers=self.headers, json=data)
        self.assertEqual(403, resp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, resp.json["code"])
