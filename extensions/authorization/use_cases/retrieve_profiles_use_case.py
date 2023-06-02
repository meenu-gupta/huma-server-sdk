from datetime import datetime
from functools import cached_property
from typing import Union, Optional

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import Role
from extensions.authorization.models.user import User
from extensions.authorization.models.user_fields_converter import UserFieldsConverter
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
    SortParameters,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveProfilesResponseObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.validators import is_common_role
from extensions.deployment.exceptions import PatientIdentifiersPermissionDenied
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.models.module_config import ModuleConfig, RagThreshold
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.modules import rag_enabled_module_ids
from sdk.common.caching.service import CachingService
from sdk.common.usecase.response_object import Response
from .base_authorization_use_case import BaseAuthorizationUseCase
from extensions.common.monitoring import report_exception


class RetrieveProfilesUseCase(BaseAuthorizationUseCase):
    request_object: RetrieveProfilesRequestObject
    cache: CachingService = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = CachingService()

    @cached_property
    def deployment(self):
        return DeploymentService().retrieve_deployment(self.request_object.deploymentId)

    @cached_property
    def module_configs_dict(self) -> dict[str, ModuleConfig]:
        return {config.id: config for config in self.deployment.moduleConfigs or []}

    def process_request(self, request: RetrieveProfilesRequestObject) -> Response:
        if not request.is_for_users() or request.is_complex_sort_request():
            users, users_hash = self._retrieve_all_users()
        else:
            users, users_hash = self._retrieve_users_with_skip()

        if cached_response := self._get_cached_response(users_hash):
            return cached_response

        if not request.clean:
            self.preprocess(users)

        deployment_ids = []

        if request.role == Role.UserType.MANAGER:
            for user in list(users):
                authz_user = AuthorizedUser(user)
                user.deployments = authz_user.deployment_ids()
                # this should not happen so we report it to sentry and exlude this user
                if "*" in user.deployments:
                    error = Exception(
                        f"Unexpected role in search API response {authz_user.get_role()}"
                    )
                    report_exception(error)
                    users.remove(user)
                    continue

                deployment_ids.extend(user.deployments)

            codes = self.deployment_repo.retrieve_deployment_codes(deployment_ids)
            for user in users:
                user.deployments = [codes.get(id_) or id_ for id_ in user.deployments]

        if self.request_object.has_sort_fields():
            if SortParameters.Field.RAG in self.request_object.sort.fields:
                users = self._sort_by_rag(users)

        kwargs = self._get_field_filter_kwargs()
        language = self.deployment.language
        if self.request_object.submitter:
            language = self.request_object.submitter.get_language()
        response = [
            UserFieldsConverter(user, self.deployment, language).to_dict(**kwargs)
            for user in users
        ]
        if self.request_object.hash is not None:
            self.cache.set(key=request.hash, content=response, content_hash=users_hash)
        return self._slice_response(Response(response))

    def preprocess(self, users):
        """
        Inject additional information to each user if needed:
        - Adds seen status
        - Adds threshold data for user's recent module results
        - Adds assigned manager's ids
        - Adds assigned users count
        """
        if self.request_object.role not in Role.UserType.non_managers():
            self._inject_assigned_patients_count_to_managers(users)
        elif self.request_object.role == Role.UserType.USER:
            for user in users:
                self._inject_additional_data(user)
            self._inject_assigned_managers_ids_to_users(users)

    def _get_cached_response(self, users_hash):
        # TODO: remove when beta profiles endpoint removed
        if self.request_object.hash is None:
            return

        cached_result = self.cache.get(key=self.request_object.hash)
        if cached_result and cached_result.contentHash == users_hash:
            return self._slice_response(Response(cached_result.content))

    def _slice_response(self, response: Response):
        if self.request_object.is_complex_sort_request():
            until = self.request_object.skip + self.request_object.limit
            skip = self.request_object.skip
            response.value = response.value[skip:until]

        return response

    @staticmethod
    def _create_sort_params(
        request_object: RetrieveProfilesRequestObject,
    ) -> list[tuple[str, int]]:
        """
        Returns a list of sort keys and their orders.
        If there is status in sort parameters, it has the higher priority over
        the other keys.
        """
        sort = []
        if request_object.has_sort_fields():
            sort_order = request_object.sort.order.value
            sort = [(f.value, sort_order) for f in request_object.sort.fields]
        if request_object.sort and request_object.sort.status:
            sort = [
                (f"tags.{status.value}", -1) for status in request_object.sort.status
            ] + sort

        return sort

    @staticmethod
    def _is_new_data(user: User) -> bool:
        """
        Returns true if the user's last module result is created after the
        latest manager's note
        """
        if not user.recentModuleResults:
            return False
        recent_module_results = [
            next(iter(results[0].values()))
            for results in user.recentModuleResults.values()
        ]
        most_recent = max(
            recent_module_results,
            key=lambda result: (
                result.startDateTime if result.startDateTime else result.createDateTime,
                result.createDateTime,
            ),
        )
        return (
            not isinstance(most_recent, Questionnaire) or not most_recent.isForManager
        )

    @staticmethod
    def _last_module_update_without_note(user: User) -> tuple[bool, Optional[datetime]]:
        """
        Returns the last update time of the user's modules, without
        considering clinician's notes.
        The result for valid dates is in form of the tuple (True, <datetime>),
        which enables sorting None values.
        If there is no last module without note, tuple (False, None) is
        returned.
        """
        if not user.recentModuleResults:
            return False, None
        recent_module_results: list[Primitive] = [
            next(iter(results[0].values()))
            for _, results in user.recentModuleResults.items()
        ]

        results_with_date_and_manager_check = [
            (
                note_module := result is not None
                and not (
                    isinstance(result, Questionnaire) and bool(result.isForManager)
                ),
                result.startDateTime
                if (note_module and result.startDateTime)
                else (result.createDateTime if note_module else None),
            )
            for result in recent_module_results
        ]

        return max(results_with_date_and_manager_check)

    @staticmethod
    def _calculate_rag_count(user: User) -> tuple[int, int, int]:
        """
        returns the number of Red, Amber, and Green severities for the `user`
        """
        if not hasattr(user, ModuleConfig.RAG_THRESHOLDS):
            return 0, 0, 0
        severities: dict[int, int] = {severity: 0 for severity in [1, 2, 3]}
        for module in user.ragThresholds.values():
            for module_id, primitive in module.items():
                if module_id not in rag_enabled_module_ids:
                    continue
                if "severities" in primitive:
                    for severity in primitive["severities"]:
                        severities[severity] += 1
                    continue
                for threshold in primitive.values():
                    if RagThreshold.SEVERITY in threshold:
                        severities[threshold[RagThreshold.SEVERITY]] += 1

        user.ragScore = [severities[3], severities[2], severities[1]]
        return severities[3], severities[2], severities[1]

    def _calculate_status_for_users(self, users: list[User]) -> list[tuple[int, ...]]:
        """
        Returns a list of tuples, each represents the status of user.
        For example, (0, 1, 1) for a user means there where three statuses to
        be sorted based on, and user has the second and the third of them.
        The reason is to have groups of users with same status in one place.
        """
        if self.request_object.sort and self.request_object.sort.status:
            valid_status = [s.value for s in self.request_object.sort.status]
            valid_status.sort()
            return [
                tuple(
                    tag not in (user.tags.keys() if user.tags else {})
                    for tag in valid_status
                )
                for user in users
            ]
        else:
            return [(0,) for _ in users]

    def _calculate_sort_criteria_for_rag(
        self, users: list[User]
    ) -> tuple[
        list[tuple[int, ...]],
        list[bool],
        list[tuple[int, int, int]],
        list[tuple[bool, Union[datetime, None]]],
    ]:
        users_status = self._calculate_status_for_users(users)
        new_data = [RetrieveProfilesUseCase._is_new_data(user) for user in users]
        rag = [RetrieveProfilesUseCase._calculate_rag_count(user) for user in users]
        last_update_wo_note = [
            RetrieveProfilesUseCase._last_module_update_without_note(user)
            for user in users
        ]
        return users_status, new_data, rag, last_update_wo_note

    def _sort_by_rag(self, users: list[User]) -> list[User]:
        reverse = self.request_object.sort.order != SortParameters.Order.ASCENDING
        (
            status,
            new_data,
            rag,
            last_update_wo_note,
        ) = self._calculate_sort_criteria_for_rag(users)
        if reverse:
            status = [tuple(not s for s in status) for status in status]
        users_with_sort_criteria = list(
            zip(users, new_data, status, rag, last_update_wo_note)
        )
        users_with_sort_criteria.sort(
            key=lambda u: (u[1], *u[2], *u[3], u[4]), reverse=reverse
        )
        return [u[0] for u in users_with_sort_criteria]

    def _retrieve_all_users(self) -> tuple[list[User], str]:
        return self.auth_repo.retrieve_user_profiles(
            self.request_object.deploymentId,
            search=self.request_object.search,
            role=self.request_object.role,
            search_ignore_keys=None
            if self.request_object.canViewIdentifierData
            else [User.NHS, User.GIVEN_NAME, User.FAMILY_NAME],
            manager_id=self.request_object.managerId,
            filters=self.request_object.filters,
        )

    def _retrieve_users_with_skip(self) -> tuple[list[User], str]:
        return self.auth_repo.retrieve_user_profiles(
            self.request_object.deploymentId,
            search=self.request_object.search,
            role=self.request_object.role,
            sort=self._create_sort_params(self.request_object),
            skip=self.request_object.skip,
            limit=self.request_object.limit,
            search_ignore_keys=None
            if self.request_object.canViewIdentifierData
            else [User.NHS, User.GIVEN_NAME, User.FAMILY_NAME],
            manager_id=self.request_object.managerId,
            filters=self.request_object.filters,
            enabled_module_ids=self.request_object.enabledModuleIds,
            sort_extra=self.request_object.sort and self.request_object.sort.extra,
        )

    def _get_field_filter_kwargs(self) -> dict:
        kwargs = {}
        if self.request_object.role not in (None, Role.UserType.USER):
            return kwargs

        if self.request_object.patientIdentifiersOnly:
            if not self.request_object.canViewIdentifierData:
                raise PatientIdentifiersPermissionDenied

            kwargs["only_fields"] = User.identifiers_fields()
        elif self.request_object.patientDataOnly:
            kwargs["exclude_fields"] = User.identifiers_fields()
        elif not self.request_object.canViewIdentifierData:
            kwargs["exclude_fields"] = User.identifiable_data_fields()

        return kwargs

    def _inject_additional_data(self, user: User):
        if not user.recentModuleResults:
            return

        self._calculate_and_inject_status(user)
        self._calculate_and_inject_threshold(user)

    @staticmethod
    def _calculate_and_inject_status(user: User):
        # TODO: replace with actual calculation when service is removed
        return AuthorizationService()._append_recent_results_status(user)

    def _calculate_and_inject_threshold(self, user):
        # TODO: replace with actual calculation when service is removed
        return AuthorizationService()._append_rag_threshold(
            user, self.module_configs_dict
        )

    def _inject_assigned_patients_count_to_managers(self, users: list[User]):
        assigned_count_dict = self.auth_repo.retrieve_assigned_patients_count()
        for user in users:
            if not AuthorizedUser(user, self.request_object.deploymentId).is_manager():
                continue
            user.assignedUsersCount = assigned_count_dict.get(user.id, 0)


class RetrieveProfilesV1UseCase(BaseAuthorizationUseCase):
    request_object: RetrieveProfilesRequestObject
    cache: CachingService = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = CachingService()

    @cached_property
    def deployment(self):
        if self.request_object.deploymentId:
            return DeploymentService().retrieve_deployment(
                self.request_object.deploymentId
            )

    @cached_property
    def module_configs_dict(self) -> dict[str, ModuleConfig]:
        if not self.deployment:
            return {}
        return {config.id: config for config in self.deployment.moduleConfigs or []}

    def process_request(self, request: RetrieveProfilesRequestObject) -> Response:
        users, users_hash, count = self._retrieve_users_with_skip()

        if not request.clean:
            self.preprocess(users)

        kwargs = self._get_field_filter_kwargs()
        language = self.request_object.submitter.get_language()
        response = [
            UserFieldsConverter(user, self.deployment, language).to_dict(**kwargs)
            for user in users
        ]
        if self.request_object.hash is not None:
            self.cache.set(key=request.hash, content=response, content_hash=users_hash)

        sliced_response = self._slice_response(Response(response))
        return RetrieveProfilesResponseObject(
            users=sliced_response.value, filtered=count[0], total=count[1]
        )

    def preprocess(self, users):
        """
        Inject additional information to each user if needed:
        - Adds seen status
        - Adds threshold data for user's recent module results
        - Adds assigned manager's ids
        - Adds assigned users count
        """
        if self.request_object.role not in Role.UserType.non_managers():
            self._inject_assigned_patients_count_to_managers(users)
        elif self.request_object.role == Role.UserType.USER:
            for user in users:
                self._inject_additional_data(user)
            self._inject_assigned_managers_ids_to_users(users)

    def _slice_response(self, response: Response):
        if self.request_object.is_complex_sort_request():
            until = self.request_object.skip + self.request_object.limit
            skip = self.request_object.skip
            response.value = response.value[skip:until]

        return response

    @staticmethod
    def _create_sort_params(
        request_object: RetrieveProfilesRequestObject,
    ) -> list[tuple[str, int]]:
        """
        Returns a list of sort keys and their orders.
        If there is status in sort parameters, it has the higher priority over
        the other keys.
        By default, reverse order is applied to the boarding status, which
        forces this order to the users:
          * Active users on the top of the list
          * Not Unboarded users next
          * Offboarded users at the bottom of the list.
        For flags sort we also have a condition, on which when two or more
        users have the same flags, they are sorted by their names.
        """
        sort = []
        sort_header = []
        if request_object.has_sort_fields():
            sort_order = request_object.sort.order.value
            sort = [
                (f.value, sort_order)
                for f in request_object.sort.fields
                if f != SortParameters.Field.BOARDING_STATUS
            ]

            if SortParameters.Field.FLAGS in request_object.sort.fields:
                sort += [
                    (SortParameters.Field.FAMILY_NAME.value, -sort_order),
                    (SortParameters.Field.GIVEN_NAME.value, -sort_order),
                ]

            sort_header = [(SortParameters.Field.BOARDING_STATUS.value, -1)]

        if request_object.sort and request_object.sort.status:
            sort = [
                (f"tags.{status.value}", -1) for status in request_object.sort.status
            ] + sort

        return sort_header + sort

    def _retrieve_users_with_skip(self) -> tuple[list[User], str, tuple[int, int]]:
        submitter_deployments = None
        if self.request_object.managerId:
            submitter_deployments = self.request_object.submitter.deployment_ids()
        common_role = is_common_role(self.request_object.submitter.get_role().id)
        ignore_keys = [User.NHS, User.GIVEN_NAME, User.FAMILY_NAME]
        return self.auth_repo.retrieve_user_profiles(
            self.request_object.deploymentId,
            search=self.request_object.search,
            role=self.request_object.role,
            sort=self._create_sort_params(self.request_object),
            skip=self.request_object.skip,
            limit=self.request_object.limit,
            search_ignore_keys=None
            if self.request_object.canViewIdentifierData
            else ignore_keys,
            manager_id=self.request_object.managerId,
            filters=self.request_object.filters,
            enabled_module_ids=self.request_object.enabledModuleIds,
            return_count=True,
            manager_deployment_ids=submitter_deployments,
            sort_extra=self.request_object.sort and self.request_object.sort.extra,
            is_common_role=common_role,
        )

    def _get_field_filter_kwargs(self) -> dict:
        kwargs = {}
        if self.request_object.role not in (None, Role.UserType.USER):
            return kwargs

        if self.request_object.patientIdentifiersOnly:
            if not self.request_object.canViewIdentifierData:
                raise PatientIdentifiersPermissionDenied

            kwargs["only_fields"] = User.identifiers_fields()
        elif self.request_object.patientDataOnly:
            kwargs["exclude_fields"] = User.identifiers_fields()
        elif not self.request_object.canViewIdentifierData:
            kwargs["exclude_fields"] = User.identifiable_data_fields()

        return kwargs

    def _inject_additional_data(self, user: User):
        if not user.recentModuleResults:
            return

        self._calculate_and_inject_status(user)
        self._calculate_and_inject_threshold(user)

    @staticmethod
    def _calculate_and_inject_status(user: User):
        # TODO: replace with actual calculation when service is removed
        return AuthorizationService()._append_recent_results_status(user)

    def _calculate_and_inject_threshold(self, user):
        # TODO: replace with actual calculation when service is removed
        return AuthorizationService()._append_rag_threshold(
            user, self.module_configs_dict
        )

    def _inject_assigned_patients_count_to_managers(self, users: list[User]):
        assigned_count_dict = self.auth_repo.retrieve_assigned_patients_count()
        for user in users:
            if not AuthorizedUser(user, self.request_object.deploymentId).is_manager():
                continue
            user.assignedUsersCount = assigned_count_dict.get(user.id, 0)
