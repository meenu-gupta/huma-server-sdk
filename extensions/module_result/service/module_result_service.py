import logging
from datetime import datetime

import pytz
from pymongo.client_session import ClientSession

from extensions.authorization.events.update_stats_event import UpdateUserStatsEvent
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.services.authorization import AuthorizationService
from extensions.common.monitoring import report_exception
from extensions.common.sort import SortField
from extensions.deployment.models.user_note import UserNote
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.module_result.event_bus.post_create_primitive import (
    PostCreatePrimitiveEvent,
)
from extensions.module_result.event_bus.pre_create_primitive import (
    PreCreatePrimitiveEvent,
)
from extensions.module_result.exceptions import PrimitiveNotFoundException
from extensions.module_result.models.primitives import (
    Primitive,
    Questionnaire,
    AZFurtherPregnancyKeyActionTrigger,
    AZGroupKeyActionTrigger,
    CurrentGroupCategory,
)
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode
from extensions.module_result.modules.key_action_trigger import KeyActionTriggerModule
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.router.module_result_requests import (
    CreateModuleResultRequestObject,
    RetrieveUnseenModuleResultRequestObject,
)
from extensions.module_result.router.module_result_response import UnseenModulesResponse
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.constants import VALUE_IN
from sdk.common.exceptions.exceptions import (
    DuplicatePrimitiveException,
    ObjectDoesNotExist,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values

log = logging.getLogger(__name__)


class ModuleResultService:
    """Service to work  with modules repo."""

    @autoparams()
    def __init__(self, repo: ModuleResultRepository):
        self.repo = repo
        self.deployment_service = DeploymentService()

    def create_module_result(self, req_obj: CreateModuleResultRequestObject):
        def report_error(error, primitive):
            error_message = f"Error creating primitive {primitive.class_name}"
            log_message = f"{error_message}: {error}"
            log.warning(log_message)
            return log_message

        discard = set()
        is_unseen = dict()
        ids = []
        errors = []

        req_obj.module.preprocess(req_obj.primitives, req_obj.user)
        user = AuthorizationService().retrieve_user_profile(req_obj.user.id)
        recent_results = (
            user.recentModuleResults.get(req_obj.moduleConfigId, [])
            if user.recentModuleResults
            else []
        )

        is_manager_note = False
        for pid, primitive in enumerate(req_obj.primitives):
            try:
                is_manager_note = (
                    isinstance(primitive, Questionnaire) and primitive.isForManager
                )
                is_unseen[pid] = not is_manager_note

                if is_manager_note:
                    self.repo.flush_unseen_results(
                        user_id=primitive.userId,
                        start_date_time=primitive.startDateTime,
                    )

                latest_value = next(iter(recent_results), {})
                primitives = [
                    old_primitive
                    for pr_name, old_primitive in latest_value.items()
                    if pr_name == primitive.class_name
                ]
                self._calculate_primitive_with_flags(
                    req_obj.module, primitive, not is_manager_note, primitives
                )

            except Exception as error:
                errors.append(report_error(error, primitive))
                discard.add(pid)

        if not is_manager_note:
            req_obj.module.validate_module_result(req_obj.primitives)
            if len(req_obj.primitives) > len(req_obj.module.primitives):
                for primitive in req_obj.primitives:
                    req_obj.module.apply_overall_flags_logic([primitive])
            else:
                req_obj.module.apply_overall_flags_logic(req_obj.primitives)

        success_primitives = list()
        for pid, primitive in enumerate(req_obj.primitives):
            if pid in discard:
                continue
            try:
                inserted_id = self.create_primitive(
                    primitive, req_obj.module, save_unseen=is_unseen[pid]
                )
                ids.append(inserted_id)
                success_primitives.append(primitive)
            except Exception as error:
                errors.append(report_error(error, primitive))

        if ids:
            self._post_batch_create_event(success_primitives)
            self.update_unseen_flags(req_obj.user.id)

        return remove_none_values({"ids": ids or None, "errors": errors or None})

    def create_primitive(
        self, primitive: Primitive, module: Module, save_unseen: bool = False
    ) -> str:
        self._pre_create(primitive)

        is_trigger_required = False
        if issubclass(module.__class__, KeyActionTriggerModule):
            is_trigger_required = not self._check_existing_trigger_primitive(primitive)

        inserted_id = self._create_primitive(primitive, save_unseen=save_unseen)
        if is_trigger_required:
            self._trigger_key_actions(primitive, module, module.config.configBody)
        return inserted_id

    @staticmethod
    def _calculate_primitive_with_flags(
        module, primitive, save_unseen: bool = False, primitives: list[Primitive] = None
    ):
        module.calculate(primitive)
        if save_unseen:
            threshold, flags = module.calculate_rag_flags(primitive, primitives)
            primitive.ragThreshold = threshold
            primitive.flags = flags

    def _check_existing_trigger_primitive(self, primitive: Primitive) -> bool:
        filter_options = {}
        further_pregnancy = AZFurtherPregnancyKeyActionTrigger
        if primitive.moduleId == further_pregnancy.__name__:
            filter_options.update(
                {
                    further_pregnancy.CURRENT_GROUP_CATEGORY: CurrentGroupCategory.PREGNANT.value
                }
            )

        try:
            self.repo.retrieve_primitive_by_name(
                user_id=primitive.userId,
                primitive_name=primitive.moduleId,
                **filter_options,
            )
            report_exception(DuplicatePrimitiveException(name=primitive.moduleId))
            return True
        except ObjectDoesNotExist:
            return False

    def _create_primitive(self, primitive: Primitive, save_unseen: bool = False):
        inserted_id = self.repo.create_primitive(primitive, save_unseen)
        self._post_create(primitive)
        return inserted_id

    def retrieve_module_results(
        self,
        user_id: str,
        module_id: str,
        skip: int,
        limit: int,
        direction: SortField.Direction,
        from_date_time: datetime,
        to_date_time: datetime,
        filters: dict,
        deployment_id: str,
        role: str,
        excluded_fields: list[str] = None,
        module_config_id: str = None,
        exclude_module_ids: list[str] = None,
        only_unseen_results: bool = None,
    ) -> dict[str, list[Primitive]]:
        module = self.deployment_service.retrieve_module(module_id)
        deployment = self.deployment_service.retrieve_deployment(deployment_id)
        deployment.prepare_module_configs_for_role(role)
        module_configs = deployment.moduleConfigs

        if module_config_id:
            module_config = module.extract_module_config(
                module_configs, None, module_config_id=module_config_id
            )
            module_configs = [module_config]

        results = {}
        options = {
            "user_id": user_id,
            "module_id": module_id,
            "skip": skip,
            "limit": limit,
            "direction": direction,
            "from_date_time": from_date_time,
            "to_date_time": to_date_time,
            "field_filter": filters,
            "excluded_fields": excluded_fields,
            "module_config_id": module_config_id,
            "exclude_module_ids": exclude_module_ids,
            "only_unseen_results": only_unseen_results,
        }
        for module_primitive in module.primitives:
            options["primitive_name"] = module_primitive.__name__
            module_results = self.repo.retrieve_primitives(**options)
            module_results = module.filter_results(
                primitives=module_results,
                module_configs=module_configs,
                is_for_user=role == RoleName.USER,
            )
            module.change_primitives_based_on_config(module_results, module_configs)
            results[module_primitive.__name__] = module_results

        return results

    def retrieve_aggregated_results(
        self,
        primitive_name: str,
        aggregation_function: AggregateFunc,
        mode: AggregateMode,
        start_date: datetime = None,
        end_date: datetime = None,
        skip: int = None,
        limit: int = None,
        user_id: str = None,
        timezone: str = None,
        module_config_id: str = None,
    ):
        if timezone:
            start_date = pytz.timezone(timezone).localize(start_date)
            end_date = pytz.timezone(timezone).localize(end_date)
        return self.repo.retrieve_aggregated_results(
            primitive_name,
            aggregation_function,
            mode,
            start_date,
            end_date,
            skip,
            limit,
            user_id,
            module_config_id,
        )

    @staticmethod
    def _post_batch_create_event(primitives: list[Primitive]):
        ref_primitive: Primitive = primitives[0]
        _dict = {
            "primitives": {primitive.class_name: primitive for primitive in primitives},
            Primitive.USER_ID: ref_primitive.userId,
            Primitive.MODULE_ID: ref_primitive.moduleId,
            Primitive.MODULE_RESULT_ID: ref_primitive.moduleResultId,
            Primitive.DEPLOYMENT_ID: ref_primitive.deploymentId,
            Primitive.DEVICE_NAME: ref_primitive.deviceName,
            Primitive.MODULE_CONFIG_ID: ref_primitive.moduleConfigId,
            Primitive.START_DATE_TIME: ref_primitive.startDateTime,
        }

        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(PostCreateModuleResultBatchEvent.from_dict(_dict))
        event = UpdateUserStatsEvent(user_id=ref_primitive.userId)
        event_bus.emit(event)

    def _trigger_key_actions(
        self, primitive: Primitive, module: Module, config_body: dict = None
    ):

        user = AuthorizationService().retrieve_user_profile(user_id=primitive.userId)
        authz_user = AuthorizedUser(user)
        deployment = self.deployment_service.retrieve_deployment_config(authz_user)
        group_primitive = None
        if primitive.moduleId == AZFurtherPregnancyKeyActionTrigger.__name__:
            try:
                group_primitive = self.repo.retrieve_primitive_by_name(
                    user_id=user.id, primitive_name=AZGroupKeyActionTrigger.__name__
                )
            except ObjectDoesNotExist:
                error = PrimitiveNotFoundException(
                    f"Group information primitive not found for this user: {user.email}"
                )
                report_exception(error)
                raise error

        if authz_user.is_user():
            module.trigger_key_actions(
                user=user,
                key_actions=deployment.keyActions or [],
                primitive=primitive,
                config_body=config_body,
                deployment_id=deployment.id,
                start_date=group_primitive and group_primitive.firstVaccineDate,
                group_category=group_primitive and group_primitive.groupCategory,
            )

    def _post_create(self, primitive: Primitive):
        event_bus = inject.instance(EventBusAdapter)
        event = PostCreatePrimitiveEvent.from_primitive(primitive)
        event_bus.emit(event)

    def _pre_create(self, primitive: Primitive):
        event_bus = inject.instance(EventBusAdapter)
        event = PreCreatePrimitiveEvent.from_primitive(primitive)
        event_bus.emit(event, raise_error=True)

    def retrieve_observation_notes(
        self, module_configs: list, user_id: str, skip: int, limit: int
    ) -> list[dict]:
        results = []

        module_results_list = []
        field_filter = {
            Primitive.MODULE_CONFIG_ID: {VALUE_IN: [mc.id for mc in module_configs]}
        }
        module_results = self.repo.retrieve_primitives(
            user_id,
            QuestionnaireModule.moduleId,
            Questionnaire.__name__,
            skip,
            limit,
            SortField.Direction.ASC,
            field_filter=field_filter,
        )
        module_results_list.extend(module_results)

        service = AuthorizationService()
        user_ids = {mr.submitterId for mr in module_results_list}
        manager_profiles = service.retrieve_user_profiles_by_ids(user_ids)
        manager_names = {
            manager.id: manager.get_full_name() for manager in manager_profiles
        }

        for module_result in module_results_list:
            user_note = {
                **module_result.to_dict(include_none=False),
                UserNote.TYPE: UserNote.UserNoteType.OBSERVATION_NOTES.value,
            }
            manager_name = manager_names.get(module_result.submitterId)
            if manager_name:
                user_note[UserNote.SUBMITTER_NAME] = manager_name

            results.append(UserNote.from_dict(user_note))

        return results

    def delete_user_primitive(self, user_id: str, session: ClientSession = None):
        primitive_names = []

        for module in self.deployment_service.retrieve_modules():
            for primitive in module.primitives:
                primitive_names.append(primitive.__name__.lower())

        self.repo.delete_user_primitive(
            session=session, user_id=user_id, primitive_names=primitive_names
        )

    def retrieve_unseen_module_results(
        self, req_obj: RetrieveUnseenModuleResultRequestObject
    ) -> UnseenModulesResponse:
        results = self.repo.retrieve_unseen_results(
            deployment_id=req_obj.deploymentId,
            user_id=req_obj.userId,
            module_ids=req_obj.hybridQuestionnaireModuleIds,
            enabled_module_ids=req_obj.enabledModuleIds,
        )
        results = [p for p in results if any(p.get(Primitive.FLAGS).values())]
        response = {
            UnseenModulesResponse.FLAGS: results,
            UnseenModulesResponse.LAST_MANAGER_NOTE: self.repo.retrieve_first_unseen_result(
                deployment_id=req_obj.deploymentId, user_id=req_obj.userId
            ),
        }
        return UnseenModulesResponse.from_dict(response)

    def update_unseen_flags(self, user_id: str):
        excluded_modules_ids = [
            "CVDRiskScore",
            "HighFrequencyStep",
            "BodyMeasurement",
            "SurgeryDetails",
        ]
        user = AuthorizationService().retrieve_simple_user_profile(user_id=user_id)
        authz_user = AuthorizedUser(user)
        deployment_module_config_ids = [
            mc.id for mc in authz_user.deployment.moduleConfigs
        ]
        unseen_flags = self.repo.calculate_unseen_flags(
            user_id=user_id,
            module_config_ids=deployment_module_config_ids,
            excluded_modules_ids=excluded_modules_ids,
        )
        AuthorizationService().update_unseen_flags(user_id, unseen_flags)
