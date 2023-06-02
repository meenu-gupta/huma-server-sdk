import logging

from extensions.kardia.router.kardia_requests import RetrieveSingleEcgPdfRequestObject
from extensions.kardia.use_case.base_kardia_use_case import BaseKardiaUseCase
from extensions.module_result.models.primitives import ECGAliveCor
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.date_utils import get_dt_now_as_str
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.storage.use_case.storage_request_objects import UploadFileRequestObject
from sdk.storage.use_case.storage_use_cases import UploadFileUseCase

logger = logging.getLogger(__name__)


class RetrieveSingleEcgPdfUseCase(BaseKardiaUseCase):

    request_object: RetrieveSingleEcgPdfRequestObject

    @autoparams()
    def __init__(
        self,
        module_result_repo: ModuleResultRepository,
        server_config: PhoenixServerConfig,
    ):
        super(RetrieveSingleEcgPdfUseCase, self).__init__()
        self._module_result_repo = module_result_repo
        self._server_config = server_config

    def execute(self, request_object):
        self.request_object = request_object
        return super(RetrieveSingleEcgPdfUseCase, self).execute(request_object)

    def _get_default_bucket(self):
        return self._server_config.server.storage.defaultBucket

    def _retrieve_primitives(self):
        # retrieve existing ecg alivecor record
        field_filter = {ECGAliveCor.KARDIA_ECG_RECORD_ID: self.request_object.recordId}
        return self._module_result_repo.retrieve_primitives(
            user_id=self.request_object.userId,
            module_id=ECGAliveCor.__name__,
            primitive_name=ECGAliveCor.__name__,
            skip=None,
            limit=None,
            direction=None,
            from_date_time=None,
            to_date_time=None,
            field_filter=field_filter,
        )

    @staticmethod
    def _upload_file(bucket, file_name, file_data):
        req = UploadFileRequestObject.from_dict(
            {
                UploadFileRequestObject.BUCKET: bucket,
                UploadFileRequestObject.FILENAME: file_name,
                UploadFileRequestObject.FILE_DATA: file_data,
            }
        )
        UploadFileUseCase().execute(req)

    def _create_ecg_alive_cor(self, bucket, file_name):
        primitive = ECGAliveCor.from_dict(
            {
                ECGAliveCor.USER_ID: self.request_object.userId,
                ECGAliveCor.MODULE_ID: ECGAliveCor.__name__,
                ECGAliveCor.DEPLOYMENT_ID: self.request_object.deploymentId,
                ECGAliveCor.DEVICE_NAME: "Alivecor App",
                ECGAliveCor.S3_OBJECT: {"bucket": bucket, "key": file_name},
                ECGAliveCor.KARDIA_ECG_RECORD_ID: self.request_object.recordId,
                ECGAliveCor.START_DATE_TIME: get_dt_now_as_str(),
            }
        )

        primitive_id = self._module_result_repo.create_primitive(primitive=primitive)

        logger.info(f"ECGAliveCor {primitive_id} created.")

        return primitive

    def process_request(self, request_object: RetrieveSingleEcgPdfRequestObject):
        ecg_alivecor_record = self._retrieve_primitives()
        if ecg_alivecor_record:
            return ecg_alivecor_record

        # retrieve ecg pdf from Alivecor and create new primitive
        file_data = self._kardia_integration_client.retrieve_single_ecg_pdf(
            request_object.recordId
        )

        # upload file onto cloud file storage service
        bucket = self._get_default_bucket()

        file_name = (
            f"user/{request_object.userId}/ECGAliveCor/{request_object.recordId}.pdf"
        )

        self._upload_file(bucket, file_name, file_data)

        primitive = self._create_ecg_alive_cor(bucket, file_name)

        return Response(primitive)
