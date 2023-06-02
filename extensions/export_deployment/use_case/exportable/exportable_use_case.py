import os
from collections import defaultdict
from datetime import date
from typing import Optional

from tomlkit._utils import merge_dicts

from extensions.authorization.models.user import User
from extensions.common.s3object import S3Object
from extensions.deployment.models.deployment import (
    Deployment,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.export_deployment.helpers.convertion_helpers import (
    download_object_to_folder,
    view_is_module,
    view_is_day,
    view_is_user,
    layer_is_nested,
    binary_is_url,
    binary_is_include,
    binary_is_none,
    deidentify_dict,
    filter_not_included_fields,
    ExportData,
    flatten_data,
    exclude_fields,
    PrimitiveData,
    build_module_config_versions,
    attach_users,
)
from extensions.export_deployment.helpers.translation_helpers import translate_object
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
    ExportableResponseObject,
)
from extensions.module_result.common.flatbuffer_utils import (
    process_steps_flatbuffer_file,
)
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules import licensed_questionnaire_module
from extensions.module_result.modules.module import Module
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.common_functions_utils import get_all_subclasses
from sdk.common.utils.inject import autoparams
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import remove_none_values

ALL_MODULES_CODE = "__all__"


class ExportableUseCase(UseCase):
    """
    ExportConfig fields proceed here ( only for primitives )
    - deploymentId
    - fromDate
    - toDate
    - moduleNames
    - excludedModuleNames
    - userIds
    - includeNullFields
    - useFlatStructure
    - questionnairePerName
    - excludeFields
    - deIdentifyRemoveFields

    """

    @autoparams()
    def __init__(
        self,
        export_repo: ExportDeploymentRepository,
        deployment_repo: DeploymentRepository,
        file_storage: FileStorageAdapter,
    ):
        self._export_repo = export_repo
        self._deployment_repo = deployment_repo
        self._file_storage = file_storage

    def process_request(
        self, request_object: ExportableRequestObject
    ) -> ExportableResponseObject:

        data = self.get_raw_result()
        self.filter_data_based_on_consent(data)
        if request_object.includeUserMetaData:
            attach_users(
                request_object.consentsData,
                request_object.econsentsData,
                request_object.includeNullFields,
                request_object.usersData,
                data,
                request_object.deployment,
                self._export_repo,
            )
        self.replace_localizable_keys_if_requested(
            request_object, data, request_object.deployment
        )
        self.filter_not_included_fields_if_requested(request_object.includeFields, data)
        exclude_fields(data, request_object.excludeFields)
        self.de_identify_data_if_requested(request_object, data)
        data = self.remove_null_fields_if_requested(request_object, data)
        self.translate_if_requested(request_object, data)
        self.flatten_data_if_requested(request_object, data)
        return self.get_response_object(data)

    def filter_data_based_on_consent(self, data: ExportData):
        if not self.request_object.consentsData:
            return
        for module_name, primitive_dicts in data.items():
            primitive_dicts[:] = [
                p
                for p in primitive_dicts
                if p[Primitive.USER_ID] in self.request_object.consentsData
            ]

    @staticmethod
    def replace_localizable_keys_if_requested(
        request_object: ExportableRequestObject,
        data: ExportData,
        deployment: Deployment,
    ) -> None:
        if not request_object.doTranslate:
            return
        for module in data:
            for index, primitive in enumerate(data[module]):
                if "user" not in primitive or User.LANGUAGE not in primitive["user"]:
                    continue
                user_language = primitive["user"][User.LANGUAGE]
                localizations = deployment.get_localization(user_language)
                if not localizations:
                    continue
                data[module][index] = replace_values(
                    primitive, localizations, False, string_list_translator=True
                )

    def process_binaries(
        self,
        raw_dict: dict,
        request_object: ExportableRequestObject,
        object_fields: list,
        flatbuffer_fields: list,
    ):
        for field_name, value in raw_dict.items():
            if (field_name in flatbuffer_fields) or (field_name in object_fields):
                raw_dict[field_name] = self._process_object_field(
                    request_object,
                    value,
                    raw_dict,
                    request_object.fromDate,
                    request_object.toDate,
                    flatbuffer_field=field_name in flatbuffer_fields,
                )

    @staticmethod
    def build_binary_path(
        request_object: ExportableRequestObject,
        primitive_dict: dict,
    ):

        path = "binaries"
        if not layer_is_nested(request_object.layer):
            return path
        object_dict = primitive_dict.copy()
        deidentify_dict(
            object_dict,
            request_object.excludeFields,
            request_object.deIdentified,
            request_object.deIdentifyRemoveFields,
            request_object.deIdentifyHashFields,
        )
        if view_is_user(request_object.view):
            path = os.path.join(object_dict[Primitive.USER_ID], path)
        elif view_is_day(request_object.view):
            day = object_dict[Primitive.START_DATE_TIME].split("T")[0]
            path = os.path.join(day, path)
        elif view_is_module(request_object.view):
            path = os.path.join(object_dict[Primitive.MODULE_ID], path)
        return path

    def _process_object_field(
        self,
        request_object: ExportableRequestObject,
        file_object_dict: dict,
        primitive_dict: dict,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        flatbuffer_field=False,
    ):
        if binary_is_none(request_object.binaryOption):
            return file_object_dict
        elif binary_is_include(request_object.binaryOption):
            # downloads object from storage and returns filename
            path_for_binary = self.build_binary_path(request_object, primitive_dict)
            file_dir, file_name = download_object_to_folder(
                file_object_dict[S3Object.BUCKET],
                file_object_dict[S3Object.KEY],
                f"{request_object.exportDir}/{path_for_binary}",
                self._file_storage,
            )
            if flatbuffer_field:
                process_steps_flatbuffer_file(file_dir, file_name, from_date, to_date)
            return file_name
        elif binary_is_url(request_object.binaryOption):
            # returns signed url to download file
            return self._file_storage.get_pre_signed_url(
                file_object_dict[S3Object.BUCKET], file_object_dict[S3Object.KEY]
            )
        else:
            raise InvalidRequestException("Invalid binary option provided")

    @classmethod
    def get_response_object(cls, data: ExportData):
        return ExportableResponseObject(items=data)

    def get_raw_result(self) -> ExportData:
        """
        To be implemented by children and provide data.
        It is expected to return a dict, whose keys are module
        names and the values are lists of primitive dictionaries.
        """
        raise NotImplementedError

    @staticmethod
    def get_modules(
        module_names: list[str], excluded_module_names: list[str], parent_module=Module
    ) -> list[Module]:
        results = get_all_subclasses(parent_module)
        if module_names is not None:
            results = filter(lambda m: m.moduleId in module_names, results)

        if excluded_module_names is not None:
            results = filter(lambda m: m.moduleId not in excluded_module_names, results)
        unique_list = list(set(results))
        unique_list.sort(key=lambda m: m.__class__.__name__)
        return unique_list

    def get_module_results(
        self, request_object: ExportableRequestObject, modules: list[Module]
    ) -> dict[str, list[Primitive]]:
        module_results = defaultdict(list)
        for module in modules:
            primitives = self.get_module_result(request_object, module)
            if len(primitives) > 0:
                module_results[module.moduleId].extend(primitives)

        return module_results

    def get_module_result(
        self, request_object: ExportableRequestObject, module: Module
    ) -> list[Primitive]:
        module_results = []
        if module.exportable:
            for primitive_cls in module.primitives:
                primitives = self._export_repo.retrieve_primitives(
                    primitive_class=primitive_cls,
                    module_id=module.moduleId,
                    deployment_id=request_object.deploymentId,
                    start_date=request_object.fromDate,
                    end_date=request_object.toDate,
                    user_ids=request_object.userIds,
                    use_creation_time=request_object.useCreationTime,
                )
                if primitives:
                    for primitive in primitives:
                        module_config = self.get_module_config(
                            primitive, self.request_object.moduleConfigVersions
                        )
                        module.change_primitives_based_on_config(
                            [primitive], [module_config]
                        )
                    module_results.extend(primitives)
        return module_results

    def get_module(
        self, request_object: ExportableRequestObject, module_name: str
    ) -> Optional[Module]:
        modules = list(
            filter(
                lambda m: m.moduleId == module_name,
                self.get_modules(
                    request_object.moduleNames, request_object.excludedModuleNames
                ),
            )
        )
        if not modules:
            return None
        return modules[0]

    def translate_if_requested(
        self,
        request_object: ExportableRequestObject,
        data: ExportData,
    ):
        if not request_object.translatePrimitives:
            return
        for module_name, primitive_dicts in data.items():
            for index, primitive_dict in enumerate(primitive_dicts):
                primitive_dicts[index] = self.translate_primitive(
                    module_name,
                    primitive_dict,
                    request_object.translationModuleCodes,
                    request_object.translationShortCodes,
                )

    @staticmethod
    def translate_primitive(
        module_name: str,
        primitive: PrimitiveData,
        module_codes: dict,
        short_codes: dict,
    ):
        module_code = module_codes.get(module_name, module_name)
        # Preparing list of common and module-specific codes
        total_codes = short_codes.get(ALL_MODULES_CODE, {}).copy()
        module_codes = short_codes.get(module_code, {})
        merge_dicts(total_codes, module_codes)
        if total_codes:
            primitive = translate_object(primitive, total_codes)
        return primitive

    @staticmethod
    def remove_null_fields_if_requested(
        req_object: ExportableRequestObject, data: ExportData
    ) -> ExportData:
        if req_object.includeNullFields:
            return data
        return remove_none_values(data)

    @staticmethod
    def filter_not_included_fields_if_requested(
        fields_to_include: list[str], data: ExportData
    ):
        for module_name, primitive_dicts in data.items():
            for primitive_dict in primitive_dicts:
                filter_not_included_fields(fields_to_include, primitive_dict)

    @staticmethod
    def de_identify_data_if_requested(
        request_object: ExportableRequestObject, data: ExportData
    ):
        """De-identifying, excluding unneeded fields, etc."""
        for module_name, primitive_dicts in data.items():
            for primitive_dict in primitive_dicts:
                deidentify_dict(
                    primitive_dict,
                    request_object.excludeFields,
                    request_object.deIdentified,
                    request_object.deIdentifyRemoveFields,
                    request_object.deIdentifyHashFields,
                )

    @staticmethod
    def flatten_data_if_requested(
        request_object: ExportableRequestObject,
        data: ExportData,
    ):
        if not request_object.useFlatStructure:
            return
        flatten_data(data)

    def get_module_config(self, primitive: Primitive, module_configs_versions: dict):
        module_config = self._get_module_config(module_configs_versions, primitive)
        if module_config:
            return module_config
        return self.get_module_config_from_revision(primitive)

    def get_module_config_from_revision(self, primitive: Primitive):
        revision = (
            self._deployment_repo.retrieve_deployment_revision_by_module_config_version(
                deployment_id=primitive.deploymentId,
                module_id=primitive.moduleId,
                module_config_id=primitive.moduleConfigId,
                module_config_version=primitive.version,
            )
        )
        if not revision:
            return
        build_module_config_versions(
            self.request_object.moduleConfigVersions, revision.snap.moduleConfigs
        )
        return self._get_module_config(
            self.request_object.moduleConfigVersions, primitive
        )

    def _get_module_config(self, module_configs_versions: dict, primitive: Primitive):
        versions = module_configs_versions.get(primitive.moduleId, {})
        config_versions = versions.get(primitive.moduleConfigId, {})
        module_config = config_versions.get(primitive.version)
        if primitive.version == 0 and not module_config:
            module_config = config_versions.get(None)
        return module_config
