import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, Union

from bson import ObjectId
from bson.errors import InvalidId
from flask_limiter.util import get_ipaddr
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import OperationFailure
from pymongo import MongoClient, WriteConcern
from pymongo import UpdateOne, InsertOne
from extensions.authorization.exceptions import MaxLabelsAssigned

from extensions.authorization.models.admin_ip import AdminIP
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.invitation import Invitation
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.manager_assigment import ManagerAssignment
from extensions.authorization.models.mongo_label_log import MongoLabelLog
from extensions.authorization.models.mongo_manager_assigment import (
    MongoManagerAssignment,
)
from extensions.authorization.models.mongo_tag_log import MongoTagLog
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import (
    RecentFlags,
    UnseenFlags,
    User,
    RoleAssignment,
    PersonalDocument,
    BoardingStatus,
    UserLabel,
    UserStats,
    TaskCompliance,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import SortParameters
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
)
from extensions.deployment.models.deployment import Label
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.exceptions import UserDoesNotExist
from extensions.module_result.models.primitives import Primitive
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.utils import build_date
from sdk.common.adapter.mongodb.mongodb_utils import convert_kwargs, kwargs_to_obj_id
from sdk.common.adapter.redis.redis_utils import calculate_hashed_value
from sdk.common.exceptions.exceptions import (
    InternalServerErrorException,
    InvalidRequestException,
)
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import escape
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import MongoPhoenixDocument, convert_date_to_datetime
from sdk.common.utils.validators import remove_none_values, id_as_obj_id
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


class MongoAuthorizationRepository(AuthorizationRepository):
    USER_COLLECTION = "user"
    ADMIN_IP_COLLECTION = "adminip"
    CARE_PLAN_GROUP_LOG_COLLECTION = "careplangrouplog"
    HELPER_AGREEMENT_LOG_COLLECTION = "helperagreementlog"
    INVITATION_COLLECTION = "invitation"
    IGNORED_USER_FIELDS = (
        User.DATE_OF_BIRTH,
        User.CREATE_DATE_TIME,
        User.SURGERY_DATE_TIME,
        User.UPDATE_DATE_TIME,
        User.LAST_SUBMIT_DATE_TIME,
        f"{User.BOARDING_STATUS}.{BoardingStatus.UPDATE_DATE_TIME}",
        f"{User.STATS}.{UserStats.TASK_COMPLIANCE}.{TaskCompliance.UPDATE_DATE_TIME}",
    )

    GIVEN_NAME_LOWER_CASE = "givenN"
    FAMILY_NAME_LOWER_CASE = "familyN"
    DATE_OF_BIRTH_NULL_CONSIDERED = "DOB"
    ID_STR = "idStr"
    FULL_NAME_LOWER_CASE = "fullName"
    HAS_GIVEN_NAME = "hasGivenName"
    HAS_FAMILY_NAME = "hasFamilyName"
    SURGERY_DATE_REARRANGED = "surgeryDateRearranged"
    ENROLMENT_STR = "enrolmentStr"
    DETAILS_OFF_BOARDED_NULL = (
        f"{User.BOARDING_STATUS}.{BoardingStatus.DETAILS_OFF_BOARDED}_NULL"
    )

    DEPLOYMENT_FILTERS = "deploymentFilters"
    SEARCH_FILTERS = "searchFilters"

    ACTIVE_USERS_VALUE = 3
    NOT_ONBOARDED_USERS_VALUE = 2
    OFFBOARDED_USERS_VALUE = 1

    SUM_PRIMITIVE_RED = "sumRed"
    SUM_PRIMITIVE_AMBER = "sumAmber"
    SUM_PRIMITIVE_GRAY = "sumGray"

    FLAGS_SORT_KEYS = [
        f"{User.UNSEEN_FLAGS}.{UnseenFlags.RED}",
        f"{User.UNSEEN_FLAGS}.{UnseenFlags.AMBER}",
        f"{User.UNSEEN_FLAGS}.{UnseenFlags.GRAY}",
        f"{User.RECENT_FLAGS}.{RecentFlags.RED}",
        f"{User.RECENT_FLAGS}.{RecentFlags.AMBER}",
        f"{User.RECENT_FLAGS}.{RecentFlags.GRAY}",
    ]

    @autoparams()
    def __init__(
        self, database: Database, config: PhoenixServerConfig, client: MongoClient
    ):
        self._config = config
        self._db = database
        self._client = client
        self.masterKey = config.server.project.masterKey

    def create_user(self, user: User, **kwargs) -> str:
        user.createDateTime = user.updateDateTime = datetime.utcnow()
        user_dict = user.to_dict(ignored_fields=self.IGNORED_USER_FIELDS)
        user_dict[User.ID_] = ObjectId(user_dict.pop(User.ID))
        user_dict = remove_none_values(user_dict)
        convert_date_to_datetime(user_dict, User)
        result = self._db[self.USER_COLLECTION].insert_one(
            user_dict, session=kwargs.pop("session", None)
        )
        return str(result.inserted_id)

    def update_user_unseen_flags(self, user_id: str, unseen_flags: dict):
        filter_query = {User.ID_: ObjectId(user_id)}
        update_query = {"$set": {User.UNSEEN_FLAGS: unseen_flags}}
        self._db[self.USER_COLLECTION].update_one(filter_query, update_query)

    @id_as_obj_id
    def delete_invitation_with_session(
        self, invitation_id: str, session: ClientSession
    ):
        self._db[self.INVITATION_COLLECTION].delete_one(
            {Invitation.ID_: invitation_id}, session=session
        )

    def retrieve_users_count(
        self,
        from_: datetime = None,
        to: datetime = None,
        deployment_id: str = None,
        role: str = None,
        **options,
    ) -> int:
        filter_options = self._build_filter_options(deployment_id, "", role)
        date_filter = remove_none_values({"$gte": from_, "$lt": to})
        if date_filter:
            filter_options[User.CREATE_DATE_TIME] = date_filter
        filter_options.update(options)
        return self._db[self.USER_COLLECTION].count_documents(filter_options)

    def retrieve_users_with_user_role_including_only_fields(
        self, fields: tuple, to_model=True
    ) -> list[User]:
        fields_to_include = {key: 1 for key in fields if key in User.__dict__}

        result = self._db[self.USER_COLLECTION].find(
            {User.ROLES: {"$elemMatch": {RoleAssignment.ROLE_ID: RoleName.USER}}},
            fields_to_include,
        )

        if to_model:
            return [self.build_user_from_dict(user) for user in result]

        return result

    def create_tag(self, user_id: str, tags: dict, tags_author_id: str) -> str:
        user = User.from_dict(
            {User.ID: user_id, User.TAGS: tags, User.TAGS_AUTHOR_ID: tags_author_id}
        )
        return self.update_user_profile(user)

    def assign_labels_to_user(
        self, user_id: str, labels: list[Label], assignee_id: str
    ) -> str:
        self._check_user_labels_exceeds_maximum_number(labels)
        user_labels = self._build_user_labels_dict(
            labels=labels, assignee_id=assignee_id
        )
        user_dict = {User.LABELS: user_labels, User.UPDATE_DATE_TIME: datetime.utcnow()}
        result = self._db[self.USER_COLLECTION].update_one(
            {User.ID_: ObjectId(user_id)}, {"$set": user_dict}
        )
        if not result.matched_count:
            raise UserDoesNotExist
        return str(user_id)

    def bulk_assign_labels_to_users(
        self, user_ids_str: list[str], labels: list[Label], assignee_id: str
    ) -> list[str]:
        user_ids = [ObjectId(user_id) for user_id in user_ids_str]
        user_labels_dict = self._build_user_labels_dict(
            labels=labels, assignee_id=assignee_id
        )
        update_ops = []
        for user_id in user_ids:
            user = self.retrieve_user(user_id=user_id)
            new_user_labels_dict = self._update_user_labels(
                user.labels, user_labels_dict
            )
            self._check_user_labels_exceeds_maximum_number(new_user_labels_dict)
            filter_query = {User.ID_: user_id}
            update_query = {
                "$set": {
                    User.LABELS: new_user_labels_dict,
                },
            }
            update_ops.append(UpdateOne(filter_query, update_query))

        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[self.USER_COLLECTION].bulk_write(
                    update_ops, ordered=False, session=session
                )
                number_of_updated_records = result.matched_count
                if number_of_updated_records != len(user_ids):
                    raise InternalServerErrorException

        return user_ids_str

    @id_as_obj_id
    def unassign_label_from_users(self, label_id: str):
        query = {f"{User.LABELS}.{UserLabel.LABEL_ID}": label_id}
        update_query = {"$pull": {User.LABELS: {UserLabel.LABEL_ID: label_id}}}

        self._db[self.USER_COLLECTION].update_many(filter=query, update=update_query)

    def get_users_per_label_count(self, deployment_id: str) -> dict[str, Any]:
        pipeline = [
            {
                "$match": {
                    User.LABELS: {"$ne": None},
                    f"{User.ROLES}.{RoleAssignment.ROLE_ID}": "User",
                    f"{User.ROLES}.{RoleAssignment.RESOURCE}": f"deployment/{deployment_id}",
                }
            },
            {
                "$project": {
                    User.LABELS: {
                        "$map": {
                            "input": f"${User.LABELS}",
                            "as": "label",
                            "in": f"$$label.{UserLabel.LABEL_ID}",
                        }
                    }
                }
            },
            {"$unwind": f"${User.LABELS}"},
            {"$group": {"_id": f"${User.LABELS}", "count": {"$sum": 1}}},
            {
                "$group": {
                    "_id": None,
                    "data": {"$push": {"k": {"$toString": "$_id"}, "v": "$count"}},
                }
            },
            {"$replaceRoot": {"newRoot": {"$arrayToObject": "$data"}}},
        ]

        users_per_label_count_cur = self._db[self.USER_COLLECTION].aggregate(
            pipeline=pipeline
        )
        return next(users_per_label_count_cur, {})

    def create_label_logs(self, label_logs: list[LabelLog]) -> list[str]:
        new_label_logs = [
            MongoLabelLog(**label_log.to_dict(include_none=False))
            for label_log in label_logs
        ]
        label_logs_ids = MongoLabelLog.objects.insert(new_label_logs, load_bulk=False)
        return [str(label_log_id) for label_log_id in label_logs_ids]

    def create_tag_log(self, tag_log: TagLog):
        new_event: MongoPhoenixDocument = MongoTagLog(
            **tag_log.to_dict(include_none=False)
        )
        return str(new_event.save().id)

    def assign_managers_to_users(
        self, manager_ids: list[str], user_ids: list[str], submitter_id: str
    ):
        user_ids = [ObjectId(user_id) for user_id in user_ids]
        manager_ids = [ObjectId(manager_id) for manager_id in manager_ids]
        submitter_id = ObjectId(submitter_id)

        update_ops = []
        insert_ops = []
        now = datetime.utcnow()
        for user_id in user_ids:
            filter_query = {MongoManagerAssignment.ID_: user_id}
            update_query = {
                "$set": {
                    MongoManagerAssignment.USER_ID: user_id,
                    MongoManagerAssignment.MANAGERS_ID: manager_ids,
                    MongoManagerAssignment.SUBMITTER_ID: submitter_id,
                    MongoManagerAssignment.UPDATE_DATE_TIME: now,
                },
                "$setOnInsert": {
                    MongoManagerAssignment.ID_: user_id,
                    # adding _cls to be compatible with mongoengine
                    "_cls": MongoManagerAssignment.__name__,
                },
            }
            update_ops.append(UpdateOne(filter_query, update_query, upsert=True))
            insert_query = {
                MongoManagerAssignment.USER_ID: user_id,
                MongoManagerAssignment.MANAGERS_ID: manager_ids,
                MongoManagerAssignment.SUBMITTER_ID: submitter_id,
                MongoManagerAssignment.CREATE_DATE_TIME: now,
                MongoManagerAssignment.UPDATE_DATE_TIME: now,
            }
            insert_ops.append(InsertOne(insert_query))

        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[
                    MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
                ].bulk_write(update_ops, ordered=False, session=session)
                number_of_updated_records = result.upserted_count + result.matched_count
                if number_of_updated_records != len(user_ids):
                    raise InternalServerErrorException
                result = self._db[
                    MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_LOG_COLLECTION
                ].bulk_write(insert_ops, ordered=False, session=session)
                if result.inserted_count != len(user_ids):
                    raise InternalServerErrorException

    def assign_managers_and_create_log(self, manager_assigment: ManagerAssignment):
        new_object: MongoManagerAssignment = self.assign_managers(manager_assigment)
        self.create_assignment_log(new_object)
        return str(new_object.userId)

    def assign_managers(self, manager_assigment: ManagerAssignment):
        pk = ObjectId(manager_assigment.userId)
        manager_assigment.updateDateTime = datetime.utcnow()

        record: MongoManagerAssignment = MongoManagerAssignment.objects(pk=pk).first()
        try:
            record.update(**manager_assigment.to_dict(include_none=False))
            return record
        except AttributeError:
            return self._assign_managers(manager_assigment)

    def _assign_managers(self, manager_assignment: ManagerAssignment):
        record: MongoManagerAssignment = MongoManagerAssignment(
            **manager_assignment.to_dict(include_none=False),
        )
        record.id = record.userId
        return record.save()

    def create_assignment_log(self, managers_assignment_log: MongoManagerAssignment):
        log_collection = (
            MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_LOG_COLLECTION
        )
        managers_assignment_log.switch_collection(log_collection)
        managers_assignment_log.id = None
        managers_assignment_log.updateDateTime = None
        return managers_assignment_log.save()

    def retrieve_assigned_managers_ids(self, user_id: str):
        record = MongoManagerAssignment.objects(userId=user_id).first()
        return list(map(lambda _id: str(_id), record.managerIds)) if record else []

    def retrieve_assigned_managers_ids_for_multiple_users(
        self, user_ids: list[str]
    ) -> dict:
        assigment_records = MongoManagerAssignment.objects(userId__in=user_ids)
        result_dict = {}
        for record in assigment_records:
            manager_str_ids = [str(manager_id) for manager_id in record.managerIds]
            result_dict[str(record.userId)] = manager_str_ids

        return result_dict

    def _fix_sort_params(
        self, sort: list[tuple[str, int]], extra: SortParameters.Extra
    ):
        if not sort:
            return sort

        sort_keys = [item[0] for item in sort]
        is_module_sort = SortParameters.Field.MODULE.value in sort_keys
        if is_module_sort:
            index = sort_keys.index(SortParameters.Field.MODULE.value)
            key = f"{User.RECENT_MODULE_RESULTS}.{extra.moduleConfigId}.0.{extra.moduleId}.value"
            sort[index] = (key, sort[index][-1])

        def update_sort_keys(
            sort, field_name, new_field_name, extra_field=None, extra_field_order=-1
        ):
            """
            If `field_name` is in the `sort`, it is replaced by the
            `new_field_name`.
            If `extra_field` is there, it will be added before the `field_name`
            but the order comes from `extra_field_order`.
            """
            keys = [t[0] for t in sort]
            if field_name in keys:
                index = keys.index(field_name)
                order = sort[index][1]
                if extra_field:
                    changed_order = order * extra_field_order
                    new_keys = [(extra_field, changed_order), (new_field_name, order)]
                else:
                    new_keys = [(new_field_name, order)]
                sort = sort[:index] + new_keys + sort[index + 1 :]
            return sort

        sort = update_sort_keys(
            sort, User.GIVEN_NAME, self.GIVEN_NAME_LOWER_CASE, self.HAS_GIVEN_NAME
        )
        sort = update_sort_keys(
            sort, User.FAMILY_NAME, self.FAMILY_NAME_LOWER_CASE, self.HAS_FAMILY_NAME
        )
        sort = update_sort_keys(
            sort, User.DATE_OF_BIRTH, self.DATE_OF_BIRTH_NULL_CONSIDERED
        )
        sort = update_sort_keys(
            sort, User.SURGERY_DATE_TIME, self.SURGERY_DATE_REARRANGED
        )
        sort = update_sort_keys(
            sort,
            SortParameters.Field.BOARDING_DETAILS_OFF_BOARDED.value,
            self.DETAILS_OFF_BOARDED_NULL,
        )

        flags = SortParameters.Field.FLAGS.value
        # Replace `flags` with flags_sort_keys to sort
        for (index, key) in enumerate(reversed(self.FLAGS_SORT_KEYS)):
            if index == len(self.FLAGS_SORT_KEYS) - 1:
                sort = update_sort_keys(sort, flags, key)
            else:
                sort = update_sort_keys(sort, flags, key, flags, extra_field_order=1)

        return sort

    def retrieve_user_profiles(
        self,
        deployment_id: str,
        search: str,
        role: str = RoleName.USER,
        sort: list[tuple[str, int]] = None,
        skip: int = None,
        limit: int = None,
        search_ignore_keys: str = None,
        manager_id: str = None,
        filters: dict = None,
        enabled_module_ids: list[str] = None,
        return_count: bool = False,
        manager_deployment_ids: list[str] = None,
        sort_extra: SortParameters.Extra = None,
        is_common_role: bool = False,
    ) -> Union[
        tuple[list[User], Union[str, None]],
        tuple[list[User], Union[str, None], tuple[int, int]],
    ]:
        query = self._build_filter_options(
            deployment_id,
            search,
            role,
            search_ignore_keys,
            build_separate_filters=return_count,
            manager_deployment_ids=manager_deployment_ids,
            is_common_role=is_common_role,
        )

        # also search for organization staff if role is manager
        org_query = self._build_org_filter_options(deployment_id, role, is_common_role)

        if org_query:
            if not return_count:
                query = {"$or": [query, org_query]}
            else:
                query[self.DEPLOYMENT_FILTERS] = {
                    "$or": [query[self.DEPLOYMENT_FILTERS], org_query]
                }

        # supporting lists and `lte`, `gte` for filters
        if filters:
            filters = deepcopy(filters)
            filter_empty_labels = dict()
            tags_filter = dict()
            if User.TAGS in filters:
                keys = filters.pop(User.TAGS)
                if keys:
                    tags_conditions = [{f"{User.TAGS}.{key}": "true"} for key in keys]
                else:
                    tags_conditions = [{User.TAGS: None}, {User.TAGS: dict()}]
                tags_filter = {"$or": tags_conditions}

            if User.LABELS in filters:
                labels = filters.pop(User.LABELS)
                label_id_key = f"{User.LABELS}.{UserLabel.LABEL_ID}"
                if labels:
                    labels = [ObjectId(label_id) for label_id in labels]
                    filters[label_id_key] = labels
                else:
                    filter_empty_labels["$or"] = [
                        {User.LABELS: None},
                        {User.LABELS: list()},
                    ]

            for key, value in filters.items():
                if isinstance(value, list):
                    filters[key] = {"$in": value} if value else None
                elif isinstance(value, dict):
                    converter = (
                        datetime.fromisoformat if "date" in key.lower() else None
                    )
                    for operator in ["gte", "lte"]:
                        if operator in value:
                            if converter:
                                try:
                                    value[f"${operator}"] = converter(
                                        value.pop(operator)
                                    )
                                except ValueError as e:
                                    raise InvalidRequestException(e.args)
                            else:
                                value[f"${operator}"] = value.pop(operator)

            filters.update(tags_filter)
            if filter_empty_labels:
                filters.update(filter_empty_labels)

            if not return_count:
                query.update(filters)
            else:
                query[self.SEARCH_FILTERS] = {
                    "$and": [query[self.SEARCH_FILTERS], filters]
                }

        return self._retrieve_users_by_query(
            query,
            skip=skip,
            limit=limit,
            sort=self._fix_sort_params(sort, sort_extra),
            calculate_hash=True,
            manager_id=manager_id,
            enabled_module_ids=enabled_module_ids,
            return_count=return_count,
        )

    def retrieve_staff(
        self, organization_id: str, search: str = None, is_common_role: bool = False
    ) -> list[User]:
        resource = f"organization/{organization_id}"
        org_repo = inject.instance(OrganizationRepository)
        organization = org_repo.retrieve_organization(organization_id=organization_id)
        organization.deploymentIds = organization.deploymentIds or []
        org_resources = [
            f"deployment/{dep_id}" for dep_id in organization.deploymentIds
        ]
        organization_role_ids = [
            role.id
            for role in (organization.roles or [])
            if role.userType == Role.UserType.MANAGER
        ]
        default_roles = inject.instance(DefaultRoles)
        if is_common_role:
            organization_role_ids.extend(list(RoleName.common_roles()))
        else:
            organization_role_ids.extend(
                list(
                    set(default_roles.organization_managers.keys())
                    - set(RoleName.common_roles())
                )
            )

        resource_filter = {
            f"{User.ROLES}.{RoleAssignment.RESOURCE}": {"$in": org_resources}
        }
        role_id_filter = {
            f"{User.ROLES}.{RoleAssignment.ROLE_ID}": {"$in": organization_role_ids}
        }
        resource_options = {f"{User.ROLES}.{RoleAssignment.RESOURCE}": resource}
        if not is_common_role:
            filter_options = {
                "$and": [
                    {
                        "$or": [
                            {**resource_options, **role_id_filter},
                            {"$and": [resource_filter, role_id_filter]},
                        ]
                    }
                ]
            }
        else:
            filter_options = {**resource_options, **role_id_filter}
        if search:
            query: dict[str, list] = {
                "$or": [
                    {User.GIVEN_NAME: {"$regex": escape(search), "$options": "i"}},
                    {User.FAMILY_NAME: {"$regex": escape(search), "$options": "i"}},
                ]
            }
            filter_options["$and"].append(query)

        result, _ = self._retrieve_users_by_query(filter_options)
        return result

    def retrieve_assigned_patients_count(self):
        """Aggregate assigned patients count"""
        aggregation_key = "details"
        count_options = {"_id": "$managerIds", "count": {"$sum": 1}}
        group_options = {
            "_id": None,
            aggregation_key: {"$push": {"managerId": "$_id", "count": "$count"}},
        }
        # aggregate count of patients and group by managerId
        collection = self._db.get_collection(
            MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
        )
        results = collection.aggregate(
            [
                {"$unwind": "$managerIds"},
                {"$group": count_options},
                {"$group": group_options},
                {"$project": {"_id": 0, aggregation_key: 1}},
            ]
        )
        return {
            str(result["managerId"]): result["count"]
            for result in next(results, {}).get(aggregation_key, [])
        }

    def retrieve_assigned_to_user_proxies(self, user_id: str) -> list[User]:
        role_match = {
            RoleAssignment.ROLE_ID: RoleName.PROXY,
            RoleAssignment.RESOURCE: f"user/{user_id}",
        }
        query = {User.ROLES: {"$elemMatch": role_match}}
        result = self._db[self.USER_COLLECTION].find(query)
        users = []
        for user_data in result:
            user_data[User.ID] = str(user_data.pop(User.ID_))
            user = User.from_dict(user_data)
            users.append(user)
        return users

    @staticmethod
    def retrieve_user_ids_with_assigned_manager(manager_id: str) -> set[str]:
        assigned_record = MongoManagerAssignment.objects(managerIds=manager_id)
        if not assigned_record:
            return set()
        return {str(record.userId) for record in assigned_record}

    def retrieve_profiles_with_assigned_manager(self, manager_id: str) -> list[User]:
        user_ids = self.retrieve_user_ids_with_assigned_manager(manager_id)
        return self.retrieve_user_profiles_by_ids(user_ids)

    def retrieve_user_profiles_by_ids(
        self, ids: set[str], role: str = None
    ) -> list[User]:
        try:
            query = {User.ID_: {"$in": [ObjectId(x) for x in ids]}}
        except InvalidId:
            raise InvalidRequestException(message="Invalid User Id")
        if role:
            query.update(self._build_filter_options("", "", role))
        result, result_hash = self._retrieve_users_by_query(query)
        return result

    def retrieve_all_user_profiles(self, role: str = None):
        query = {}
        if role:
            query.update(self._build_filter_options("", "", role))
        result, result_hash = self._retrieve_users_by_query(query)
        return result

    def retrieve_user_ids_in_deployment(
        self, deployment_id: str, user_type: str = Role.UserType.USER
    ) -> list[str]:
        query = {
            f"{User.ROLES}.{RoleAssignment.RESOURCE}": f"deployment/{deployment_id}",
            f"{User.ROLES}.{RoleAssignment.USER_TYPE}": user_type,
        }
        users = self._db[self.USER_COLLECTION].find(query, {User.ID_: 1})
        return [str(user.get(User.ID_)) for user in users]

    @id_as_obj_id
    def retrieve_user(
        self, phone_number: str = None, email: str = None, user_id: str = None, **kwargs
    ) -> User:
        query = {**kwargs}
        if phone_number is not None:
            query[User.PHONE_NUMBER] = phone_number
        if email is not None:
            query[User.EMAIL] = {"$regex": f"^{escape(email)}$", "$options": "i"}
        if user_id is not None:
            query[User.ID_] = user_id
        result, result_hash = self._retrieve_user_by_query(query)
        return result

    @id_as_obj_id
    def retrieve_users_by_id_list(
        self, user_id_list: list[str] = None, **kwargs
    ) -> list[User]:
        query = {**kwargs}
        if user_id_list is not None:
            query[User.ID_] = {"$in": list(map(ObjectId, user_id_list))}
            result = list(
                map(
                    self.build_user_from_dict,
                    self._db[self.USER_COLLECTION].find(query),
                )
            )
            return result

    def _additional_user_fields(self):
        impossible_future_date = datetime(5000, 12, 30)
        empty_string = ""
        return {
            self.ID_STR: {"$toString": "$_id"},
            self.ENROLMENT_STR: {"$toString": f"${User.ENROLLMENT_ID}"},
            self.GIVEN_NAME_LOWER_CASE: {"$toLower": f"${User.GIVEN_NAME}"},
            self.HAS_GIVEN_NAME: {
                "$cond": [
                    {"$ne": [{"$ifNull": [f"${User.GIVEN_NAME}", None]}, None]},
                    2,
                    1,
                ]
            },
            self.FAMILY_NAME_LOWER_CASE: {"$toLower": f"${User.FAMILY_NAME}"},
            self.HAS_FAMILY_NAME: {
                "$cond": [
                    {"$ne": [{"$ifNull": [f"${User.FAMILY_NAME}", None]}, None]},
                    2,
                    1,
                ]
            },
            self.DATE_OF_BIRTH_NULL_CONSIDERED: {
                "$ifNull": [f"${User.DATE_OF_BIRTH}", impossible_future_date]
            },
            self.DETAILS_OFF_BOARDED_NULL: {
                "$ifNull": [
                    f"${User.BOARDING_STATUS}.{BoardingStatus.DETAILS_OFF_BOARDED}",
                    empty_string,
                ]
            },
            self.SURGERY_DATE_REARRANGED: {
                "$ifNull": [f"${User.SURGERY_DATE_TIME}", impossible_future_date]
            },
            self.FULL_NAME_LOWER_CASE: {
                "$concat": [
                    {"$toLower": f"${User.GIVEN_NAME}"},
                    " ",
                    {"$toLower": f"${User.FAMILY_NAME}"},
                ]
            },
            **self._onboarding_stage(),
        }

    def _onboarding_stage(self):
        """
        This applies double conditions to assign boarding status of the user.
        conditions are:
        if user.boardingStatus.status == offboarded (i.e. 1):
            user is OFFBOARDED
        elif user.finishedOnboarding is true:
            user is ACTIVE
        else:
            user is NOT_ONBOARDED
        """
        return {
            SortParameters.Field.BOARDING_STATUS.value: {
                "$cond": [
                    {
                        "$eq": [
                            f"${User.BOARDING_STATUS}.{BoardingStatus.STATUS}",
                            BoardingStatus.Status.OFF_BOARDED.value,
                        ]
                    },
                    self.OFFBOARDED_USERS_VALUE,
                    {
                        "$cond": [
                            {"$eq": [f"${User.FINISHED_ONBOARDING}", True]},
                            self.ACTIVE_USERS_VALUE,
                            self.NOT_ONBOARDED_USERS_VALUE,
                        ]
                    },
                ]
            }
        }

    def _clean_aggregate_query(self, aggregate_kwargs: list[dict]):
        query = []
        for pipeline in aggregate_kwargs:
            if pipeline := remove_none_values(pipeline):
                query.append(pipeline)
        return query

    def _manage_pipeline(self, manager_id: Optional[str]) -> list[dict[str, dict]]:
        if not manager_id:
            return []

        collection = MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
        records = self._db[collection].find({"managerIds": ObjectId(manager_id)})
        return [
            {
                "$match": {
                    "_id": {"$in": list({r["userId"] for r in records})},
                }
            }
        ]

    def _retrieve_users_by_query(
        self,
        query,
        fields=None,
        skip=None,
        limit=None,
        sort=None,
        calculate_hash=False,
        manager_id=None,
        enabled_module_ids=None,
        return_count=False,
    ) -> Union[
        tuple[list[User], Union[str, None]],
        tuple[list[User], Union[str, None], tuple[int, int]],
    ]:
        if return_count:
            count_pipeline, whole_query = self._get_count_pipeline(query, manager_id)
        else:
            count_pipeline = None
            whole_query = query

        pipeline = self._build_retrieve_profiles_pipeline(
            whole_query, fields, skip, limit, sort, manager_id, enabled_module_ids
        )
        counts = (0, 0)
        try:
            result = list(
                self._db[self.USER_COLLECTION].aggregate(pipeline, allowDiskUse=True)
            )
            if return_count:
                count_result = list(
                    self._db[self.USER_COLLECTION].aggregate(
                        count_pipeline, allowDiskUse=True
                    )
                )
                if count_result:
                    counts = (
                        count_result[0]["searched"][0]["c1"]
                        if count_result[0]["searched"]
                        else 0,
                        count_result[0]["total"][0]["c2"]
                        if count_result[0]["total"]
                        else 0,
                    )
        except OperationFailure:
            result = []
        result_hash = None
        if calculate_hash:
            result_hash = calculate_hashed_value(result)
        profiles = []
        for profile in result:
            self.set_user_flags(profile)
            profiles.append(self.build_user_from_dict(profile))
        if return_count:
            return (
                profiles,
                result_hash,
                counts,
            )
        return profiles, result_hash

    def _get_count_pipeline(self, query, manager_id):
        """
        returns two queries, one used for counting "whole" users, and
        other used to retrieve/count the users with the search filters.
        """
        whole_query = {**query[self.DEPLOYMENT_FILTERS], **query[self.SEARCH_FILTERS]}
        pipeline = []
        if query[self.SEARCH_FILTERS]:
            pipeline.append({"$addFields": self._additional_user_fields()})
        pipeline.append(
            {
                "$facet": {
                    "searched": self._manage_pipeline(manager_id)
                    + [{"$match": whole_query}, {"$count": "c1"}],
                    "total": [
                        {"$match": query[self.DEPLOYMENT_FILTERS]},
                        {"$count": "c2"},
                    ],
                }
            },
        )
        return pipeline, whole_query

    def _build_retrieve_profiles_pipeline(
        self,
        query,
        fields=None,
        skip=None,
        limit=None,
        sort=None,
        manager_id=None,
        enabled_module_ids=None,
    ):
        aggregate_first_part = [
            {"$addFields": self._additional_user_fields()},
            {"$match": query},
        ]
        pipeline = self._manage_pipeline(manager_id)

        if sort:
            sort_pipeline = [{"$sort": {k: v for (k, v) in sort}}]
            pipeline.extend(sort_pipeline)

        aggregate_last_part: list[dict[str, Any]] = [
            {"$project": fields},
            {"$skip": skip},
            {"$limit": limit},
        ]
        pipeline.extend(aggregate_last_part)
        clean_pipeline = self._clean_aggregate_query(pipeline)
        return aggregate_first_part + clean_pipeline

    def _retrieve_user_by_query(self, query, fields=None, calculate_hash=False):
        find_kwargs = remove_none_values({"filter": query, "projection": fields})
        result = self._db[self.USER_COLLECTION].find_one(**find_kwargs)
        if result is None:
            raise UserDoesNotExist

        result_hash = None
        if calculate_hash:
            result_hash = calculate_hashed_value(dict(result))
        return self.build_user_from_dict(result), result_hash

    @id_as_obj_id
    def retrieve_simple_user_profile(
        self, user_id: str = None, email: str = None
    ) -> User:
        fields = {
            User.TAGS: 0,
            User.TAGS_AUTHOR_ID: 0,
            User.RECENT_MODULE_RESULTS: 0,
        }
        query = {}
        if user_id:
            query = {User.ID_: user_id}
        if email:
            query[User.EMAIL] = {"$regex": f"^{escape(email)}$", "$options": "i"}
        if not query:
            raise InvalidRequestException("Either userId or email should be provided")

        result = self._db[self.USER_COLLECTION].find_one(
            remove_none_values(query), fields
        )
        if result is None:
            raise UserDoesNotExist
        result[User.ID] = str(result.pop(User.ID_))
        return User.from_dict(result, use_validator_field=False)

    def retrieve_simple_user_profiles_by_ids(self, ids: set[str]) -> list[User]:
        try:
            query = {User.ID_: {"$in": [ObjectId(x) for x in ids]}}
        except InvalidId:
            raise InvalidRequestException(message="Invalid User Id")
        fields = {
            User.TAGS: 0,
            User.TAGS_AUTHOR_ID: 0,
            User.RECENT_MODULE_RESULTS: 0,
        }
        results = self._db[self.USER_COLLECTION].find(remove_none_values(query), fields)
        users = [
            User.from_dict(
                {**result, User.ID: str(result.pop(User.ID_))},
                use_validator_field=False,
            )
            for result in results
        ]
        if len(users) != len(ids):
            raise UserDoesNotExist
        return users

    def update_user_profile(self, user: User) -> str:
        user.updateDateTime = datetime.utcnow()
        user.recentModuleResults = (
            self.convert_recent_results_to_dict(user.recentModuleResults or {}) or None
        )
        user_dict = user.to_dict(ignored_fields=self.IGNORED_USER_FIELDS)
        user_id = user_dict.pop(User.ID)

        user_dict = remove_none_values(user_dict)
        convert_date_to_datetime(user_dict, User)
        result = self._db[self.USER_COLLECTION].update_one(
            {User.ID_: ObjectId(user_id)}, {"$set": user_dict}
        )
        if not result.matched_count:
            raise UserDoesNotExist
        return str(user_id)

    def update_user_profiles(self, users: list[User]):
        updateDateTime = datetime.utcnow()
        update_ops = []
        for user in users:
            user.updateDateTime = updateDateTime
            user.recentModuleResults = (
                self.convert_recent_results_to_dict(user.recentModuleResults or {})
                or None
            )
            user_dict = user.to_dict(ignored_fields=self.IGNORED_USER_FIELDS)
            user_id = user_dict.pop(User.ID)
            user_dict = remove_none_values(user_dict)
            convert_date_to_datetime(user_dict, User)
            update_ops.append(
                UpdateOne({User.ID_: ObjectId(user_id)}, {"$set": user_dict})
            )

        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[self.USER_COLLECTION].bulk_write(
                    update_ops, ordered=False, session=session
                )
                number_of_updated_records = result.matched_count
                if number_of_updated_records != len(users):
                    raise InternalServerErrorException

    def update_user_onfido_verification_status(
        self, applicant_id: str, verification_status: int
    ) -> str:

        result = self._db[self.USER_COLLECTION].update_one(
            {User.ONFIDO_APPLICANT_ID: applicant_id},
            {"$set": {User.VERIFICATION_STATUS: verification_status}},
        )
        if not result.matched_count:
            raise UserDoesNotExist

        return applicant_id

    def delete_tag(self, user_id: str, tags_author_id: str) -> str:
        user = self.retrieve_user(user_id=user_id)
        user.tags = {}
        user.tagsAuthorId = ObjectId(tags_author_id)
        return self.update_user_profile(user)

    def check_ip_allowed_create_super_admin(self, master_key: str) -> bool:
        if master_key == self.masterKey:
            ip = get_ipaddr()
            log.info(f"sign up admin: connection accepted from [{ip}]")

            if ip == "127.0.0.1":
                return True

            admin_ip = self._db[self.ADMIN_IP_COLLECTION].find_one({"ip": ip})
            if not admin_ip:
                log.info(f"sign up admin: IP {ip} was blocked.")
                return False

            admin_ip: AdminIP = AdminIP.from_dict(admin_ip)
            if admin_ip.mode == AdminIP.Mode.WHITELIST:
                return True
            else:
                log.info(f"sign up admin: IP {ip} was blocked.")

        return False

    @staticmethod
    def build_user_from_dict(user_dict: dict) -> User:
        user_dict.pop(User.RECENT_FLAGS, None)
        user_dict.pop(User.UNSEEN_FLAGS, None)
        user = User.from_dict(user_dict, use_validator_field=False)
        user.id = str(user_dict[User.ID_])
        cls = MongoAuthorizationRepository
        user.recentModuleResults = (
            cls._convert_recent_results_from_dict(user.recentModuleResults or {})
            or None
        )
        user.tagsAuthorId = str(user.tagsAuthorId) if user.tagsAuthorId else None
        return user

    @staticmethod
    def set_user_flags(user_dict: dict):
        user_flags = user_dict.get(User.UNSEEN_FLAGS)
        if user_flags and sum(user_flags.values()):
            user_dict[User.FLAGS] = user_flags

    @staticmethod
    def _convert_recent_results_from_dict(recent_results: dict):
        results = {}
        for key, value in recent_results.items():
            res = []
            for primitive in value:
                item = {}
                for p_type, val in primitive.items():
                    if Primitive.ID in val:
                        val[Primitive.ID] = str(val[Primitive.ID])
                    item[p_type] = Primitive.create_from_dict(
                        val, p_type, validate=False
                    )
                res.append(item)
            results[key] = res
        return results

    @staticmethod
    def convert_recent_results_to_dict(recent_results: dict):
        results = {}
        for key, value in recent_results.items():
            res = []
            for primitive in value:
                item = {}
                for p_type, val in primitive.items():
                    item[p_type] = val.to_dict(
                        ignored_fields=(
                            Primitive.CREATE_DATE_TIME,
                            Primitive.START_DATE_TIME,
                            Primitive.END_DATE_TIME,
                        )
                    )
                    if Primitive.MODULE_CONFIG_ID in item[p_type]:
                        item[p_type][Primitive.MODULE_CONFIG_ID] = ObjectId(
                            item[p_type][Primitive.MODULE_CONFIG_ID]
                        )
                res.append(item)
            results[key] = res
        return results

    def _build_filter_options(
        self,
        deployment_id: str,
        search: str,
        role: str,
        search_ignore_keys: str = None,
        build_separate_filters: bool = False,
        manager_deployment_ids: list[str] = None,
        is_common_role: bool = False,
    ):
        """
        In profiles, two new optional counts are added. We need to return the
        number of total users in the deployment (needs a condition) and the
        number of users included in current search (needs a more specific
        condition). Therefore, the conditions are separated into two parts.
        """
        resource_options = {}
        if deployment_id:
            resource_options = {
                f"{User.ROLES}.{RoleAssignment.RESOURCE}": f"deployment/{deployment_id}"
            }
        elif manager_deployment_ids:
            resource_ids = [f"deployment/{d_id}" for d_id in manager_deployment_ids]
            resource_options = {
                f"{User.ROLES}.{RoleAssignment.RESOURCE}": {"$in": resource_ids}
            }
        user_type_options = {
            f"{User.ROLES}.{RoleAssignment.USER_TYPE}": {
                "$nin": [Role.UserType.SERVICE_ACCOUNT, Role.UserType.SUPER_ADMIN]
            }
        }
        if role == Role.UserType.MANAGER:
            non_managers = [
                RoleName.SUPER_ADMIN,
                RoleName.HUMA_SUPPORT,
                RoleName.USER,
                RoleName.PROXY,
                "",
            ]

            if is_common_role:
                non_managers.extend(
                    list(
                        set(RoleName.org_roles()).union(RoleName.deployment_roles())
                        - set(RoleName.common_roles())
                    )
                )
            else:
                non_managers.extend(RoleName.common_roles())

            role_options = {
                f"{User.ROLES}.{RoleAssignment.ROLE_ID}": {"$nin": non_managers}
            }
        else:
            role_options = {
                f"{User.ROLES}.{RoleAssignment.ROLE_ID}": {
                    "$nin": [RoleName.SUPER_ADMIN, RoleName.HUMA_SUPPORT]
                }
            }
            if role:
                role_options = {f"{User.ROLES}.{RoleAssignment.ROLE_ID}": role}

        search_options = {}
        if search:
            search_conditions = self._build_search_conditions(
                search, search_ignore_keys or []
            )
            if deployment_id:
                regex_search = {"$regex": escape(search), "$options": "i"}
                custom_fields_condition = [
                    {f"{User.EXTRA_CUSTOM_FIELDS}.{f}": regex_search}
                    for f in _get_extra_fields_from_deployment(deployment_id)
                ]
                search_conditions.extend(custom_fields_condition)

            search_options = {"$or": [c for c in search_conditions if c]}

        filter_options = {
            **resource_options,
            **search_options,
            **role_options,
            **user_type_options,
        }
        if build_separate_filters:
            filter_options = {
                self.DEPLOYMENT_FILTERS: {
                    **resource_options,
                    **role_options,
                    **user_type_options,
                },
                self.SEARCH_FILTERS: {**search_options},
            }
        return remove_none_values(filter_options)

    def _build_org_filter_options(
        self, deployment_id: str, role: str, is_common_role: bool = False
    ):
        org_filter_option = {}

        excluded_roles = [
            RoleName.SUPER_ADMIN,
            RoleName.HUMA_SUPPORT,
            RoleName.USER,
            RoleName.PROXY,
            "",
        ]

        if role == Role.UserType.MANAGER and deployment_id:
            org_repo = inject.instance(OrganizationRepository)
            organization = org_repo.retrieve_organization_by_deployment_id(
                deployment_id=deployment_id
            )

            user_type_options = {
                f"{User.ROLES}.{RoleAssignment.USER_TYPE}": {
                    "$nin": [Role.UserType.SERVICE_ACCOUNT, Role.UserType.SUPER_ADMIN]
                }
            }

            if is_common_role:
                excluded_roles.extend(
                    list(
                        set(RoleName.org_roles()).union(RoleName.deployment_roles())
                        - set(RoleName.common_roles())
                    )
                )
            else:
                excluded_roles.extend(RoleName.common_roles())

            role_options = {
                f"{User.ROLES}.{RoleAssignment.ROLE_ID}": {"$nin": excluded_roles}
            }

            if organization:
                organization_id = organization.id
                resource = f"organization/{organization_id}"
                resource_options = {f"{User.ROLES}.{RoleAssignment.RESOURCE}": resource}

                org_filter_option = {
                    **resource_options,
                    **user_type_options,
                    **role_options,
                }

        return org_filter_option

    def create_care_plan_group_log(self, log: CarePlanGroupLog):
        log_dict = remove_none_values(log.to_dict(include_none=False))
        log_dict = kwargs_to_obj_id(log_dict)
        self._db[self.CARE_PLAN_GROUP_LOG_COLLECTION].insert_one(log_dict)

    def _retrieve_users_timezone_dict_by_query(self, query, fields=None):
        result = self._db[self.USER_COLLECTION].find(query, fields)
        if result is None:
            raise UserDoesNotExist
        return {str(item[User.ID_]): item[User.TIMEZONE] for item in result}

    @convert_kwargs
    def retrieve_users_timezones(self, user_ids: list[str] = None, **options) -> dict:
        fields = {User.ID_: 1, User.TIMEZONE: 1}
        query = {**options}
        if user_ids:
            query[User.ID_] = {"$in": [ObjectId(id_) for id_ in user_ids]}
        query.update(self._build_filter_options("", "", RoleName.USER))
        return self._retrieve_users_timezone_dict_by_query(query, fields=fields)

    @id_as_obj_id
    def delete_user(self, user_id: str, session: ClientSession = None):
        self._db[self.USER_COLLECTION].delete_one({User.ID_: user_id}, session=session)

    @id_as_obj_id
    def delete_user_from_care_plan_log(
        self, user_id: str, session: ClientSession = None
    ):
        self._db[self.CARE_PLAN_GROUP_LOG_COLLECTION].delete_many(
            {CarePlanGroupLog.USER_ID: user_id}, session=session
        )

    @id_as_obj_id
    def delete_user_from_patient(self, user_id: str, session: ClientSession = None):
        patient_collection = (
            MongoManagerAssignment.PATIENT_MANAGER_ASSIGNMENT_COLLECTION
        )
        self._db[patient_collection].delete_many(
            {MongoManagerAssignment.USER_ID: user_id}, session=session
        )

        self._db[patient_collection].update_many(
            {MongoManagerAssignment.MANAGERS_ID: user_id},
            {"$pull": {MongoManagerAssignment.MANAGERS_ID: user_id}},
            session=session,
        )

    @id_as_obj_id
    def create_personal_document(self, user_id: str, personal_doc: PersonalDocument):
        personal_doc.createDateTime = personal_doc.updateDateTime = datetime.utcnow()
        personal_document_dict = personal_doc.to_dict(
            ignored_fields=(
                f"{User.personalDocuments}.{PersonalDocument.CREATE_DATE_TIME}",
                f"{User.personalDocuments}.{PersonalDocument.UPDATE_DATE_TIME}",
            )
        )
        self._db[self.USER_COLLECTION].update(
            {User.ID_: user_id},
            {
                "$push": {
                    User.PERSONAL_DOCUMENTS: remove_none_values(personal_document_dict)
                }
            },
            upsert=True,
        )

        return str(user_id)

    @id_as_obj_id
    def retrieve_personal_documents(self, user_id: str):
        user: User = self._db[self.USER_COLLECTION].find_one({User.ID_: user_id})
        try:
            return user[User.PERSONAL_DOCUMENTS]
        except KeyError:
            return []

    def create_helper_agreement_log(
        self, helper_agreement_log: HelperAgreementLog
    ) -> str:
        collection = self.HELPER_AGREEMENT_LOG_COLLECTION
        helper_agreement_log_dict = helper_agreement_log.to_dict(include_none=False)
        result = self._db[collection].insert_one(helper_agreement_log_dict)
        return str(result.inserted_id)

    @id_as_obj_id
    def retrieve_helper_agreement_log(
        self, user_id: str, deployment_id: str
    ) -> Optional[HelperAgreementLog]:
        search_query = {
            HelperAgreementLog.USER_ID: user_id,
            HelperAgreementLog.DEPLOYMENT_ID: deployment_id,
        }
        return self._db[self.HELPER_AGREEMENT_LOG_COLLECTION].find_one(search_query)

    def _build_search_conditions(self, search: str, ignored_keys: list[str]) -> list:
        search_given_name = User.GIVEN_NAME not in ignored_keys
        search_family_name = User.FAMILY_NAME not in ignored_keys

        regex_search = {"$regex": escape(search), "$options": "i"}
        search_conditions = [
            {self.ID_STR: regex_search},
            {self.ENROLMENT_STR: regex_search},
        ]

        if search_given_name:
            search_conditions.append({self.GIVEN_NAME_LOWER_CASE: regex_search})
        if search_family_name:
            search_conditions.append({self.FAMILY_NAME_LOWER_CASE: regex_search})
        if search_given_name and search_family_name:
            search_conditions.append({self.FULL_NAME_LOWER_CASE: regex_search})
        if User.NHS not in ignored_keys:
            search_conditions.append({User.NHS: regex_search})

        return search_conditions

    @staticmethod
    def _build_user_labels_dict(
        labels: list[Label], assignee_id: str
    ) -> list[dict[str, Any]]:
        user_labels = []
        for label in labels:
            user_label = {
                UserLabel.LABEL_ID: ObjectId(label.id),
                UserLabel.ASSIGNED_BY: ObjectId(assignee_id),
                UserLabel.ASSIGN_DATE_TIME: datetime.now(),
            }
            user_labels.append(user_label)
        return user_labels

    @staticmethod
    def _update_user_labels(
        existing_user_label: list[UserLabel], new_user_labels: list[dict]
    ) -> list[dict[str, Any]]:
        if not existing_user_label:
            return new_user_labels

        updated_label = []
        existing_user_label_ids = []

        for label in existing_user_label:
            existing_user_label_ids.append(ObjectId(label.labelId))
            label_dict = {
                UserLabel.LABEL_ID: ObjectId(label.labelId),
                UserLabel.ASSIGNED_BY: ObjectId(label.assignedBy),
                UserLabel.ASSIGN_DATE_TIME: label.assignDateTime,
            }
            updated_label.append(label_dict)
        for new_label in new_user_labels:
            if new_label[UserLabel.LABEL_ID] not in existing_user_label_ids:
                updated_label.append(new_label)

        return updated_label

    @staticmethod
    def _check_user_labels_exceeds_maximum_number(new_labels: list):
        label_diff = len(new_labels) - 20
        if label_diff > 0:
            raise MaxLabelsAssigned(f"User Labels would exceed max by {label_diff}")

    def retrieve_grouped_signed_up_user_count_by_month(self, deployment_id: str):
        aggregate_options = [
            {
                "$match": {
                    f"{User.ROLES}.{RoleAssignment.RESOURCE}": f"deployment/{deployment_id}",
                    f"{User.ROLES}.{RoleAssignment.USER_TYPE}": Role.UserType.USER,
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$createDateTime"},
                        "month": {"$month": "$createDateTime"},
                    },
                    "usersCount": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        result = self._db[self.USER_COLLECTION].aggregate(aggregate_options)

        return {build_date(item): item["usersCount"] for item in result}

    def create_indexes(self):
        self._db[self.USER_COLLECTION].ensure_index(f"{User.ROLES}.$**")


@autoparams("repo")
def _get_extra_fields_from_deployment(id: str, repo: DeploymentRepository):
    deployment = repo.retrieve_deployment(deployment_id=id)
    fields = deployment.extraCustomFields or {}
    return list(fields.keys())
