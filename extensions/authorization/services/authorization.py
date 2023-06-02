from datetime import datetime
import logging
from functools import reduce
from typing import Optional, Union

from pymongo.client_session import ClientSession

from extensions.authorization.di.components import PostCreateUserEvent
from extensions.authorization.events import (
    PostCreateAuthorizationBatchEvent,
    PostUserProfileUpdateEvent,
)
from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.authorization.events.pre_user_update_event import (
    PreUserProfileUpdateEvent,
)
from extensions.authorization.events.post_create_tag_event import PostCreateTagEvent
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import (
    RecentFlags,
    User,
    RoleAssignment,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.validators import check_role_id_valid_for_resource
from extensions.common.exceptions import InvalidModuleForPreferredUnitException
from extensions.common.validators import validate_custom_unit
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive, Questionnaire
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


class AuthorizationService:
    @autoparams()
    def __init__(self, repo: AuthorizationRepository, event_bus: EventBusAdapter):
        self._repo = repo
        from extensions.deployment.service.deployment_service import DeploymentService

        self._deployment_service = DeploymentService()
        self._event_bus = event_bus

    def _assign_enrollment_id(self, user: User, session=None) -> None:
        authz_user = AuthorizedUser(user)
        if not authz_user.is_user():
            return

        deployment_id = authz_user.deployment_id()
        deployment = self._deployment_service.update_enrollment_counter(
            deployment_id=deployment_id, session=session
        )
        user.enrollmentId = deployment.enrollmentCounter

    def create_user(self, user: User, session=None) -> str:
        self._assign_enrollment_id(user, session=session)
        user.id = self._repo.create_user(user, session=session)
        self._post_create_user(user)
        return user.id

    def _post_create_user(self, user: User):
        event = PostCreateUserEvent(user)
        self._event_bus.emit(event)

    def _post_create_tags(self, **kwargs):
        self._event_bus.emit(PostCreateTagEvent(**kwargs))

    def create_tag(self, user_id, tags: dict, tags_author_id: str):
        user_id = self._repo.create_tag(user_id, tags, tags_author_id)
        self._post_create_tags(user_id=user_id, tags=tags, author_id=tags_author_id)
        return user_id

    def create_assign_label_logs(self, label_logs: list[LabelLog]):
        return self._repo.create_label_logs(label_logs=label_logs)

    def create_tag_log(self, tag_log: TagLog):
        return self._repo.create_tag_log(tag_log=tag_log)

    def retrieve_users_with_user_role_including_only_fields(
        self, required_fields: tuple, to_model=True
    ) -> list[Union[dict, User]]:
        return self._repo.retrieve_users_with_user_role_including_only_fields(
            required_fields, to_model
        )

    def retrieve_user_profile(
        self, user_id: str, is_manager_request: bool = False
    ) -> User:
        user = self._repo.retrieve_user(user_id=user_id)
        self._append_assigned_managers(user)
        if not is_manager_request:
            self._add_badges(user)

        if not user.recentModuleResults:
            return user

        self._append_recent_results_status(user)

        if not is_manager_request:
            return user

        authz_user = AuthorizedUser(user)
        deployment = self._deployment_service.retrieve_deployment_config(authz_user)
        module_configs_dict = {config.id: config for config in deployment.moduleConfigs}

        self._append_rag_threshold(user, module_configs_dict)
        return user

    def retrieve_simple_user_profile(self, user_id: str) -> User:
        return self._repo.retrieve_simple_user_profile(user_id=user_id)

    @staticmethod
    def update_covid_risk_score(user: User, deployment_id: str):
        user_attributes = remove_none_values(
            {
                "height": user.height,
                "biologicalSex": user.biologicalSex,
                "dateOfBirth": user.dateOfBirth,
            }
        )

        if not user_attributes:
            return

        event = PostCreateAuthorizationBatchEvent(
            primitives=user_attributes,
            user_id=user.id,
            module_id="UpdateProfile",
            module_config_id=None,
            deployment_id=deployment_id,
            device_name=user.deviceName or "iOS",
            start_date_time=None,
        )

        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(event, raise_error=True)

    def retrieve_user_profiles_by_ids(self, ids: set[str]) -> list[User]:
        return self._repo.retrieve_user_profiles_by_ids(ids)

    def retrieve_simple_user_profiles_by_ids(self, ids: set[str]) -> list[User]:
        return self._repo.retrieve_simple_user_profiles_by_ids(ids)

    def update_user_profile(self, user: UpdateUserProfileRequestObject) -> str:
        self._pre_update_profile(user, user.previousState)
        previous_state = user.previousState
        user.previousState = None
        user_id = self._repo.update_user_profile(user)
        self._post_update_profile_event(user, previous_state)
        return user_id

    def _post_update_profile_event(self, user: User, previous_state: User = None):
        self._event_bus.emit(PostUserProfileUpdateEvent(user, previous_state))

    def update_recent_results(self, primitives: list[Primitive]):
        def sort_results(results_dict: dict):
            """Sorts primitives by startDateTime and createDateTime"""
            primitive = next(iter(results_dict.values()))
            return (
                primitive.startDateTime.timestamp(),
                primitive.createDateTime.timestamp(),
            )

        if not primitives:
            return

        ref_primitive: Primitive = primitives[0]
        user = self._repo.retrieve_user(user_id=ref_primitive.userId)
        module_id = ref_primitive.moduleId
        module_config_id = ref_primitive.moduleConfigId

        primitive_dict = {primitive.class_name: primitive for primitive in primitives}
        user.recentModuleResults = user.recentModuleResults or {}
        module = self._deployment_service.retrieve_module(
            module_id, type(ref_primitive)
        )
        primitive_array = user.recentModuleResults.get(module_config_id, None)
        if primitive_array:
            primitive_array.append(primitive_dict)
            primitive_array.sort(key=sort_results, reverse=True)
            max_records = module.recent_results_number
            user.recentModuleResults[module_config_id] = primitive_array[:max_records]
        else:
            user.recentModuleResults[module_config_id] = [primitive_dict]

        last_result_dict: dict = user.recentModuleResults[module_config_id][0]
        last_result: Primitive = last_result_dict[ref_primitive.class_name]
        if not isinstance(last_result, Questionnaire) or not last_result.isForManager:
            user.lastSubmitDateTime = last_result.createDateTime
        self.update_recent_flags(user)
        return self._repo.update_user_profile(user)

    def update_recent_flags(self, user: User):
        excluded_modules_ids = [
            "CVDRiskScore",
            "HighFrequencyStep",
            "BodyMeasurement",
            "SurgeryDetails",
        ]
        authz_user = AuthorizedUser(user)
        deployment_module_config_ids = [
            mc.id for mc in authz_user.deployment.moduleConfigs
        ]
        reds, ambers, grays = 0, 0, 0
        for module_config_id, primitives in user.recentModuleResults.items():
            if not primitives or module_config_id not in deployment_module_config_ids:
                continue
            primitive_data = list(primitives[0].values())[0]
            module_id = primitive_data.moduleId
            if module_id not in excluded_modules_ids:
                flags = primitive_data.flags or {}
                reds += flags.get("red", 0)
                ambers += flags.get("amber", 0)
                grays += flags.get("gray", 0)
        user.recentFlags = {
            RecentFlags.RED: reds,
            RecentFlags.AMBER: ambers,
            RecentFlags.GRAY: grays,
        }

    def update_unseen_flags(self, user_id: str, unseen_flags: dict):
        self._repo.update_user_unseen_flags(user_id, unseen_flags)

    def delete_tag(self, user_id: str, tags_author_id: str) -> str:
        return self._repo.delete_tag(user_id, tags_author_id)

    def check_ip_allowed_create_super_admin(self, master_key: str) -> bool:
        return self._repo.check_ip_allowed_create_super_admin(master_key)

    def _append_rag_threshold(self, user: User, module_configs_dict: dict):
        """
        @param user: user object
        @param module_configs_dict: {moduleConfigId: ModuleConfig}
        @return: None
        """
        user.ragThresholds = {}
        for module_config_id, modules in user.recentModuleResults.items():
            module_config: ModuleConfig = module_configs_dict.get(
                module_config_id, None
            )

            if not (module_config and module_config.ragThresholds):
                continue

            threshold_dict = {module_config_id: {}}
            for primitive_name, new_primitive in modules[0].items():
                primitives = []

                if len(modules) > 1:
                    primitives.extend(
                        [
                            old_primitive
                            for item in modules[1:]
                            for pr_name, old_primitive in item.items()
                            if pr_name == primitive_name
                        ]
                    )
                module = self._deployment_service.retrieve_module(
                    module_id=module_config.moduleId, primitive=type(new_primitive)
                )
                threshold_dict[module_config_id].update(
                    {
                        primitive_name: module.get_threshold_data(
                            new_primitive, module_config, primitives
                        )
                        or None
                    }
                )

            # remove empty dict
            threshold_dict = remove_none_values(
                {module_config_id: threshold_dict.pop(module_config_id, {}) or None}
            )
            user.ragThresholds.update(threshold_dict or None)

    def _append_recent_results_status(self, user: User):
        """
        Adds status field to user profile.
        Structure:
          "status": {
            <module_config_id>: {
              <primitive>: {
                "seen": True | False
              }
            }
          }
        If Observation Note is present in recentModuleResults, make all module results seen, if they were
        submitted before Observation Note.
        """
        ref_start_date_time = self._get_latest_observation_note_datetime(user)
        user.status = {}

        for module_config_id, module_results in user.recentModuleResults.items():
            module_result = module_results[0]
            status_data = {}
            for name, primitive in module_result.items():
                module_seen = False
                if (
                    ref_start_date_time
                    and primitive.startDateTime
                    and primitive.startDateTime <= ref_start_date_time
                ):
                    module_seen = True
                status_data.update({name: {"seen": module_seen}})

            user.status.update({module_config_id: status_data})

    def _append_assigned_managers(self, user: User):
        user.assignedManagers = self._repo.retrieve_assigned_managers_ids(user.id)

    def _get_latest_observation_note_datetime(self, user: User) -> Optional[datetime]:
        latest_observation_note_datetime: Optional[datetime] = None
        authz_user = AuthorizedUser(user)
        user_notes, _ = self._deployment_service.retrieve_user_observation_notes(
            deployment_id=authz_user.deployment_id(),
            user_id=authz_user.id,
            skip=0,
            limit=1,
        )
        if user_notes:
            latest_observation_note_datetime = user_notes[0].createDateTime

        for module_results in user.recentModuleResults.values():
            for module_result in module_results:
                for primitive in module_result.values():
                    if not isinstance(primitive, Questionnaire):
                        continue
                    if not primitive.isForManager:
                        continue
                    if not latest_observation_note_datetime and primitive.startDateTime:
                        latest_observation_note_datetime = primitive.startDateTime
                        continue
                    if (
                        primitive.startDateTime
                        and primitive.startDateTime > latest_observation_note_datetime
                    ):
                        latest_observation_note_datetime = primitive.startDateTime

        return latest_observation_note_datetime

    def _pre_update_profile(self, user: User, previous_state: User):
        event = PreUserProfileUpdateEvent(user, previous_state)
        self._event_bus.emit(event, raise_error=True)

    @autoparams("event_bus")
    def _add_badges(self, user: User, event_bus: EventBusAdapter):
        event = GetUserBadgesEvent(user.id)
        badges_results = event_bus.emit(event)
        if badges_results:
            badges = reduce(lambda a, b: {**a, **b}, badges_results)
            user.set_field_value(User.BADGES, badges)

    def update_user_roles(self, user_id: str, roles: list[RoleAssignment]) -> str:
        roles = [
            role
            for role in roles
            if check_role_id_valid_for_resource(role.roleId, role.resource_id())
        ]

        update_fields = UpdateUserProfileRequestObject(id=user_id, roles=roles)
        return self._repo.update_user_profile(update_fields)

    def retrieve_users_timezones(self, user_ids: list[str] = None) -> dict:
        return self._repo.retrieve_users_timezones(user_ids)

    @staticmethod
    def validate_user_preferred_units(preferred_units: dict):
        from extensions.module_result.modules.modules_manager import ModulesManager

        preferred_units_enabled_modules = (
            ModulesManager().get_preferred_unit_enabled_module_ids()
        )
        for preferred_unit in preferred_units.items():
            if preferred_unit[0] not in preferred_units_enabled_modules:
                raise InvalidModuleForPreferredUnitException(preferred_unit[0])
            else:
                validate_custom_unit(preferred_unit[1])

    def delete_user(self, user_id: str, session: ClientSession = None):
        self._repo.delete_user(session=session, user_id=user_id)
        self._repo.delete_user_from_care_plan_log(session=session, user_id=user_id)
        self._repo.delete_user_from_patient(session=session, user_id=user_id)

        try:
            file_storage = inject.instance(FileStorageAdapter)
            config = inject.instance(PhoenixServerConfig)

            all_blob, deleted_blob = file_storage.delete_folder(
                config.server.storage.defaultBucket, f"user/{user_id}"
            )
            log.info(
                f"# of user blobs is {all_blob} and # of deleted blob successfully is {deleted_blob}"
            )
        except Exception as e:
            log.warning(str(e))
