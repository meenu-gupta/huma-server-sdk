import csv
import io
import logging
import os
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import reduce
from typing import Union

import ujson as json
from tomlkit._utils import merge_dicts

from extensions.authorization.callbacks import extract_user, AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.s3object import S3Object
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.export_deployment.helpers.convertion_helpers import (
    view_is_day,
    write_json_data,
    view_is_user,
    translation_format_is_json,
    export_format_requires_json,
    export_format_requires_csv,
    convert_flat_dict_to_csv_format,
    write_csv_data,
    layer_is_nested,
    layer_is_flat,
    quantity_is_single,
    merge_module_results,
    merge_csv_file_data,
    get_consents_meta_data,
    build_module_config_versions,
)
from extensions.export_deployment.helpers.translation_helpers import (
    prepare_short_codes,
)
from extensions.export_deployment.models.export_deployment_models import (
    ExportProcess,
    ExportParameters,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.tasks import run_export
from extensions.export_deployment.use_case.export_profile_use_cases import (
    get_default_export_profile,
)
from extensions.export_deployment.use_case.export_request_objects import (
    RunExportTaskRequestObject,
    CheckExportDeploymentTaskStatusRequestObject,
    RetrieveExportDeploymentProcessesRequestObject,
    ExportRequestObject,
    ExportUserDataRequestObject,
    ExportUsersRequestObject,
    RunAsyncUserExportRequestObject,
    RetrieveUserExportProcessesRequestObject,
    ConfirmExportBadgesRequestObject,
)
from extensions.export_deployment.use_case.export_response_objects import (
    ExportDeploymentResponseObject,
    RunExportDeploymentTaskResponseObject,
    CheckExportDeploymentTaskStatusResponseObject,
    RetrieveExportProcessesResponseObject,
    ConfirmExportBadgesResponseObject,
)
from extensions.export_deployment.use_case.exportable.consent_exportable_use_case import (
    ConsentExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
    ExportableResponseObject,
)
from extensions.export_deployment.use_case.exportable.medication_tracker_exportable_use_case import (
    MedicationTrackerModuleExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.medications_exportable_use_case import (
    MedicationsModuleExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.module_exportable_use_case import (
    ModuleExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.questionnaire_exportable_use_case import (
    QuestionnaireModuleExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.revere_exportable_use_case import (
    RevereExportableUseCase,
)
from extensions.export_deployment.use_case.exportable.symptom_exportable_use_case import (
    SymptomModuleExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values

logger = logging.getLogger(__name__)


class FileType(Enum):
    JSON = "JSON"
    CSV = "CSV"


class File:
    name: str
    content_primitives: list[Primitive]
    content_module_results: dict[str, dict[str, list[Primitive]]]
    type: FileType


class Folder:
    name: str
    files: list[File]


def fill_flat_layer_folders(results: dict, folders: list, file_type: FileType):
    folder = Folder()
    folder.files = []
    folder.name = ""
    for view_key, module_results in results.items():
        file = File()
        file.type = file_type
        file.name = view_key
        file.content_primitives = module_results
        folder.files.append(file)
    folders.append(folder)


def fill_nested_layer_folders(
    results: dict,
    folders: list,
    request_object: ExportRequestObject,
    file_type: FileType,
):
    for view_key, module_results in results.items():
        folder = Folder()
        folder.name = view_key
        folder.files = []
        if quantity_is_single(request_object.quantity):
            file = File()
            file.type = file_type
            file.content_primitives = module_results
            file.name = view_key
            folder.files.append(file)
        else:
            for module_name, primitives in module_results.items():
                file = File()
                file.type = file_type
                file.name = module_name
                file.content_primitives = primitives
                folder.files.append(file)
        folders.append(folder)


def merge_export_params(
    request_object: ExportRequestObject,
    export_repo: ExportDeploymentRepository,
):
    request_data = request_object.to_dict(include_none=False)
    if not request_object.useExportProfile:
        return ExportRequestObject.from_dict(request_data)

    if not request_object.baseProfile:
        profile = get_default_export_profile(
            export_repo, request_object.deploymentId, request_object.organizationId
        )
        if not profile:
            return ExportRequestObject.from_dict(request_data)
    else:
        profile = export_repo.retrieve_export_profile(
            deployment_id=request_object.deploymentId,
            organization_id=request_object.organizationId,
            profile_name=request_object.baseProfile,
        )
    profile_data = profile.content.to_dict(include_none=False)
    merge_dicts(profile_data, request_data)
    return ExportRequestObject.from_dict(profile_data)


class ExportDeploymentUseCase(UseCase):
    request_object = None
    EXPORT_DIR = "export"
    """
    ExportConfig proceed here
    - includeUserMetaData
    - removeFields
    - hashFields
    - deIdentified
    - view
    - format
    - binaryOption
    - layer
    - quantity
    - translatePrimitives
    """

    def execute(self, request_object: ExportRequestObject):
        updated_request_object = merge_export_params(request_object, self._export_repo)
        self.request_object = updated_request_object
        self.request_object.userIds = self.retrieve_users() or None
        return super(ExportDeploymentUseCase, self).execute(updated_request_object)

    @autoparams()
    def __init__(
        self,
        export_repo: ExportDeploymentRepository,
        deployment_repo: DeploymentRepository,
        file_storage: FileStorageAdapter,
        organization_repo: OrganizationRepository,
        auth_repo: AuthorizationRepository,
    ):
        self._organization_repo = organization_repo
        self._export_repo = export_repo
        self._deployment_repo = deployment_repo
        self._auth_repo = auth_repo
        self._temp_directory_object = self._create_temp_dir([self.EXPORT_DIR])
        self._temp_export_directory = os.path.join(
            self._temp_directory_object.name, self.EXPORT_DIR
        )
        self._file_storage = file_storage

        self._exportable_use_cases = []
        self._exportable_use_cases.append(QuestionnaireModuleExportableUseCase)
        self._exportable_use_cases.append(ModuleExportableUseCase)
        self._exportable_use_cases.append(SymptomModuleExportableUseCase)
        self._exportable_use_cases.append(MedicationTrackerModuleExportableUseCase)
        self._exportable_use_cases.append(RevereExportableUseCase)
        self._exportable_use_cases.append(ConsentExportableUseCase)
        self._exportable_use_cases.append(MedicationsModuleExportableUseCase)
        self._module_codes = {}
        self._users_meta = {}

    def process_request(
        self, request_object: ExportRequestObject
    ) -> ExportDeploymentResponseObject:
        deployment_results = {}
        responses = []
        module_codes, short_codes = self.get_translation_codes(
            request_object.translationShortCodesObject,
            request_object.translationShortCodesObjectFormat,
        )
        for deployment_id in self.retrieve_deployments():
            deployment = self._deployment_repo.retrieve_deployment(
                deployment_id=deployment_id
            )
            module_config_versions = defaultdict(
                lambda: defaultdict(lambda: defaultdict(dict))
            )
            build_module_config_versions(
                module_config_versions, deployment.moduleConfigs
            )
            identifier = self.get_deployment_identifier(deployment_id)
            deployment_responses = []
            self._module_codes[deployment_id] = module_codes
            consents_meta, econsents_meta = get_consents_meta_data(
                deployment_id, self._export_repo, self._deployment_repo
            )
            deployment_export_dir = self.get_deployment_export_root_dir(identifier)
            req_data = {
                **request_object.to_dict(include_none=False),
                ExportableRequestObject.CONSENTS_DATA: consents_meta,
                ExportableRequestObject.ECONSENTS_DATA: econsents_meta,
                ExportableRequestObject.TRANSLATION_MODULE_CODES: module_codes,
                ExportableRequestObject.TRANSLATION_SHORT_CODES: short_codes,
                ExportableRequestObject.EXPORT_DIR: deployment_export_dir,
                ExportableRequestObject.DEPLOYMENT_ID: deployment_id,
                ExportableRequestObject.DEPLOYMENT: deployment,
            }
            req = ExportableRequestObject.from_dict(remove_none_values(req_data))
            req.usersData = self._users_meta
            req.moduleConfigVersions = module_config_versions
            for exportable_uc in self._exportable_use_cases:
                use_case = exportable_uc(
                    self._export_repo, self._deployment_repo, self._file_storage
                )
                rsp = use_case.execute(req)
                deployment_responses.append(rsp)
            folder_or_files = self.breakdown_deployment_results(deployment_responses)
            deployment_results[identifier] = folder_or_files
            responses.extend(deployment_responses)
        total_results = self.breakdown_total_results(responses)
        return self.create_response_object(
            total_results, deployment_results, request_object
        )

    def breakdown_total_results(self, responses: list):
        # this is to not breakdown "total" results when they are not needed
        if self.request_object.singleFileResponse or layer_is_flat(
            self.request_object.layer
        ):
            return self.breakdown_data(responses, self.request_object)

    def breakdown_deployment_results(self, responses: list):
        # this is to not breakdown "deployment" results when they are not needed
        if self.request_object.singleFileResponse or layer_is_flat(
            self.request_object.layer
        ):
            return
        return self.breakdown_data(responses, self.request_object)

    def get_deployment_identifier(self, deployment_id):
        deployment = self._deployment_repo.retrieve_deployment(
            deployment_id=deployment_id
        )
        return deployment.code or deployment_id

    def get_deployment_export_root_dir(self, deployment_identifier):
        not_old_implementation = self.request_object.deploymentId is None
        if (
            self.request_object.layer == self.request_object.DataLayerOption.NESTED
            and not_old_implementation
        ):
            return os.path.join(self._temp_export_directory, deployment_identifier)
        return self._temp_export_directory

    @staticmethod
    def get_translation_codes(
        translation_s3object: S3Object,
        translation_format: ExportParameters.DataFormatOption,
    ):
        if translation_format_is_json(translation_format):
            module_codes, short_codes = prepare_short_codes(
                translation_s3object, is_json=True
            )
        else:
            module_codes, short_codes = prepare_short_codes(
                translation_s3object, is_csv=True
            )
        return module_codes, short_codes

    @staticmethod
    def _create_temp_dir(extra_directories: list[str] = ()):
        """Creates temporary directory, which will be removed after destruction of Service object"""
        temp_dir = tempfile.TemporaryDirectory()
        for directory in extra_directories:
            os.mkdir(os.path.join(temp_dir.name, directory))
        return temp_dir

    def breakdown_data(
        self,
        use_case_results: list[ExportableResponseObject],
        request_object: ExportRequestObject,
    ):
        results = []
        if export_format_requires_json(request_object.format):
            # merging json results
            json_results = [r.to_json() for r in use_case_results]
            data = reduce(merge_module_results, json_results, {})
            result = self.fill_folders_and_files(data, request_object, FileType.JSON)
            results.append(result)

        if export_format_requires_csv(request_object.format):
            # merging csv results
            csv_results = [r.to_csv() for r in use_case_results]
            data = reduce(merge_module_results, csv_results, {})
            result = self.fill_folders_and_files(data, request_object, FileType.CSV)
            results.append(result)
        return results

    def fill_folders_and_files(
        self,
        data: dict[str, list],
        request_object: ExportRequestObject,
        file_type: FileType,
    ):
        results = defaultdict(lambda: defaultdict(list))
        for module_name, primitive_dicts in data.items():
            for primitive_dict in primitive_dicts:
                deployment_id = primitive_dict.get(Primitive.DEPLOYMENT_ID)
                primitive_module_codes = self._module_codes.get(deployment_id, {})
                mod_code = primitive_module_codes.get(module_name, module_name)
                view_key = ExportDeploymentUseCase.get_view_key(
                    request_object.view, primitive_dict
                )
                results[view_key][mod_code].append(primitive_dict)

        if request_object.singleFileResponse:
            file = File()
            file.content_module_results = results
            file.type = file_type
            return file

        folders = []

        if layer_is_nested(request_object.layer):
            fill_nested_layer_folders(results, folders, request_object, file_type)
        if layer_is_flat(request_object.layer):
            if quantity_is_single(request_object.quantity):
                file = File()
                file.type = file_type
                file.content_module_results = results
                return file
            fill_flat_layer_folders(results, folders, file_type)
        return folders

    @staticmethod
    def get_view_key(view, primitive_dict):
        view_key = primitive_dict[Primitive.MODULE_ID]  # default one
        if view_is_user(view):
            view_key = primitive_dict[Primitive.USER_ID]
        elif view_is_day(view):
            view_key = primitive_dict[Primitive.START_DATE_TIME].split("T")[0]
        return view_key

    def create_response_object(
        self,
        total_results: Union[list[list[Folder]], list[File]],
        deployment_results: dict[str, Union[list[list[Folder]], list[File]]],
        req_object: ExportRequestObject,
    ) -> ExportDeploymentResponseObject:
        if self.request_object.singleFileResponse:
            if len(total_results) > 1:
                raise InvalidRequestException("Multiple single file results")
            return self.generate_single_file_response(total_results[0])
        root_dir = self._temp_export_directory
        if req_object.layer == req_object.DataLayerOption.FLAT:
            self.write_format_results(root_dir, total_results)
        else:
            self.write_nested(root_dir, deployment_results)
        return self.generate_archive_response()

    def write_nested(
        self,
        directory: os.path,
        results: dict[str, Union[list[list[Folder]], list[File]]],
    ):
        for deployment_id in results:
            deployment_dir = f"{directory}/{deployment_id}"
            # fallback to single deployment implementation
            if self.request_object.deploymentId:
                deployment_dir = directory
            self.write_format_results(deployment_dir, results[deployment_id])

    def write_format_results(
        self, root_dir: str, results: Union[list[list[Folder]], list[File]]
    ):
        for format_results in results:
            if isinstance(format_results, File):
                if format_results.type == FileType.JSON:
                    write_json_data(
                        format_results.content_module_results,
                        root_dir,
                        "data",
                    )
                elif format_results.type == FileType.CSV:
                    data = merge_csv_file_data(format_results.content_module_results)
                    write_csv_data(data, root_dir, "data")
            else:
                for folder in format_results:
                    for f in folder.files:
                        if f.type == FileType.JSON:
                            write_json_data(
                                f.content_primitives,
                                f"{root_dir}/{folder.name}",
                                f.name,
                            )
                        if f.type == FileType.CSV:
                            write_csv_data(
                                f.content_primitives,
                                f"{root_dir}/{folder.name}",
                                f.name,
                            )

    def generate_archive_response(self):
        archive_name = shutil.make_archive(
            f"{self._temp_directory_object.name}/export_{datetime.utcnow().isoformat()}",
            "zip",
            self._temp_export_directory,
        )
        with open(archive_name, "rb") as archive:
            return ExportDeploymentResponseObject(
                content=archive.read(),
                filename=archive_name,
                content_type="application/zip",
            )

    def generate_single_file_response(self, result: File):
        if result.type == FileType.JSON:
            return ExportDeploymentResponseObject(
                content=str.encode(
                    json.dumps(
                        result.content_module_results,
                        indent=4,
                        escape_forward_slashes=False,
                    )
                ),
                filename="single",
                content_type="application/json",
            )
        elif result.type == FileType.CSV:
            data = merge_csv_file_data(result.content_module_results)
            csv_data = convert_flat_dict_to_csv_format(data)
            output = io.StringIO()
            writer = csv.writer(output, lineterminator="\n")
            writer.writerows(csv_data)
            return ExportDeploymentResponseObject(
                content=str.encode(output.getvalue()),
                filename="single",
                content_type="text/csv",
            )
        else:
            raise NotImplementedError

    def upload_result_to_bucket(
        self, filename: str, file_data: bytes, file_type: str, bucket: str
    ):
        self._file_storage.upload_file(
            bucket, filename, io.BytesIO(file_data), len(file_data), file_type
        )

    def retrieve_deployments(self):
        """Based on request prepares list of deployments for export"""
        if self.request_object.deploymentIds:
            return self.request_object.deploymentIds
        elif self.request_object.organizationId:
            organization = self._organization_repo.retrieve_organization(
                organization_id=self.request_object.organizationId
            )
            return organization.deploymentIds
        # fallback to old implementation
        return [self.request_object.deploymentId]

    def retrieve_users(self):
        """Based on request prepares list of users for export"""
        if self.request_object.managerId:
            return list(
                self._auth_repo.retrieve_user_ids_with_assigned_manager(
                    self.request_object.managerId
                )
            )
        return self.request_object.userIds


class RunExportTaskUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ExportDeploymentRepository):
        self._repo = repo

    def process_request(
        self, request_object: RunExportTaskRequestObject
    ) -> RunExportDeploymentTaskResponseObject:
        if self._repo.check_export_process_already_running_for_user(
            request_object.requesterId
        ):
            raise InvalidRequestException("Export process is already running")
        export_params = ExportParameters.from_dict(
            request_object.to_dict(include_none=False)
        )
        export_process = ExportProcess(
            status=ExportProcess.ExportStatus.CREATED,
            exportParams=export_params,
            requesterId=request_object.requesterId,
            deploymentId=request_object.deploymentId,
            deploymentIds=request_object.deploymentIds,
            organizationId=request_object.organizationId,
            exportType=request_object.exportType,
            seen=True,
        )
        export_process_id = self._repo.create_export_process(export_process)
        run_export.apply_async(kwargs={"export_process_id": export_process_id})
        return RunExportDeploymentTaskResponseObject(export_process_id)


class CheckExportTaskStatusUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ExportDeploymentRepository):
        self._repo = repo

    def process_request(
        self, request_object: CheckExportDeploymentTaskStatusRequestObject
    ) -> CheckExportDeploymentTaskStatusResponseObject:
        export_process = self._repo.retrieve_export_process(
            request_object.exportProcessId
        )
        response = {ExportProcess.STATUS: export_process.status}
        if export_process.status == ExportProcess.ExportStatus.DONE:
            response["export_data_object"] = export_process.resultObject
        return CheckExportDeploymentTaskStatusResponseObject(**response)


class RetrieveExportDeploymentProcessesUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ExportDeploymentRepository):
        self._repo = repo

    def process_request(
        self, request_object: RetrieveExportDeploymentProcessesRequestObject
    ) -> RetrieveExportProcessesResponseObject:
        export_processes = self._repo.retrieve_export_processes(
            deployment_id=request_object.deploymentId,
            export_type=[ExportProcess.ExportType.DEFAULT],
        )
        return RetrieveExportProcessesResponseObject(export_processes)


class RetrieveUserExportProcessesUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ExportDeploymentRepository):
        self._repo = repo

    def process_request(
        self, request_object: RetrieveUserExportProcessesRequestObject
    ) -> RetrieveExportProcessesResponseObject:
        export_processes = self._repo.retrieve_export_processes(
            user_id=request_object.userId,
            export_type=[
                ExportProcess.ExportType.USER,
                ExportProcess.ExportType.SUMMARY_REPORT,
            ],
        )
        return RetrieveExportProcessesResponseObject(export_processes)


class ExportUserDataUseCase(UseCase):
    def process_request(
        self, request_object: ExportUserDataRequestObject
    ) -> RetrieveExportProcessesResponseObject:
        user = extract_user(request_object.userId)
        authz_user = AuthorizedUser(user)
        deployment_ids = authz_user.deployment_ids()

        export_data = request_object.to_dict(include_none=False)
        export_data[ExportUsersRequestObject.USER_IDS] = [request_object.userId]
        export_data[ExportUsersRequestObject.DEPLOYMENT_IDS] = deployment_ids
        export_request_object = ExportUsersRequestObject.from_dict(export_data)
        return ExportDeploymentUseCase().execute(export_request_object)


class AsyncExportUserDataUseCase(UseCase):
    def process_request(
        self, request_object: RunAsyncUserExportRequestObject
    ) -> RunExportDeploymentTaskResponseObject:
        user = extract_user(request_object.userId)
        authz_user = AuthorizedUser(user)
        deployment_ids = authz_user.deployment_ids()

        export_data = request_object.to_dict(include_none=False)
        export_data[RunExportTaskRequestObject.USER_IDS] = [request_object.userId]
        export_data[RunExportTaskRequestObject.DEPLOYMENT_IDS] = deployment_ids
        export_data[
            RunExportTaskRequestObject.EXPORT_TYPE
        ] = ExportProcess.ExportType.USER.value
        export_request_object = RunExportTaskRequestObject.from_dict(export_data)

        return RunExportTaskUseCase().execute(export_request_object)


class ConfirmExportBadgesUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ExportDeploymentRepository):
        self._repo = repo

    def process_request(self, request_object: ConfirmExportBadgesRequestObject):
        updated = self._repo.mark_export_processes_seen(
            export_process_ids=request_object.exportProcessIds,
            requester_id=request_object.requesterId,
        )
        return ConfirmExportBadgesResponseObject(updated)
