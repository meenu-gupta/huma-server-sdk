import logging
from extensions.deployment.models.status import EnableStatus

from pymongo import UpdateOne
from bson import ObjectId

from extensions.authorization.models.user import UnseenFlags, User
from extensions.authorization.repository.mongo_auth_repository import (
    MongoAuthorizationRepository,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.module_result.models.primitives import Primitive
from sdk.common.mongodb_migrations.progress_bar import ProgressBar

logger = logging.getLogger(__name__)
bulk_size = 1000

excluded_modules_ids = [
    "CVDRiskScore",
    "HighFrequencyStep",
    "BodyMeasurement",
    "SurgeryDetails",
]


class UserFlagsStats:
    def __init__(self, db) -> None:
        self.db = db

    def calculate(self):
        logger.info("Loading module configs for all deployments...")
        self.deployment_module_configs = self.get_deployments_module_configs()
        logger.info(
            f"Loaded module configs for {len(self.deployment_module_configs)} deployments"
        )
        logger.info("Calculating unseen flags for all users...")
        self.calculate_unseen_flags_for_all_users()
        logger.info(f"\nCalculated unseen flags for {len(self.unseen_flags)} users")
        logger.info("Updating unseen and recent flags for all users...")
        users_count = self.set_user_flags()
        logger.info(f"\nFinished updating flags for {users_count} users")

    def get_deployments_module_configs(self):
        deployments_modules = {}
        deployments = self.db[MongoDeploymentRepository.DEPLOYMENT_COLLECTION].find({})
        for deployment in deployments:
            module_configs = deployment.get("moduleConfigs") or []
            deployments_modules[deployment.get("_id")] = [
                m.get("id") for m in module_configs if self.is_module_valid(m)
            ]
        return deployments_modules

    @staticmethod
    def is_module_valid(module_config: dict):
        is_enabled = module_config.get("status") == EnableStatus.ENABLED.value
        is_for_manager = module_config.get("configBody", {}).get("isForManager", False)
        return is_enabled and not is_for_manager

    def calculate_unseen_flags_for_all_users(self):
        self.unseen_flags = {}
        progress = ProgressBar(total=len(self.deployment_module_configs))
        for index, data in enumerate(self.deployment_module_configs.items()):
            self.calculate_unseen_flags_for_deployment_users(*data)
            progress.show(current=index + 1)

    def calculate_unseen_flags_for_deployment_users(
        self, deployment_id: ObjectId, module_configs: list[ObjectId]
    ):
        pipeline = [
            {
                "$match": {
                    "deploymentId": deployment_id,
                    "moduleConfigId": {"$in": module_configs},
                    "moduleId": {"$nin": excluded_modules_ids},
                }
            },
            {
                "$group": {
                    "_id": "$userId",
                    "reds": {"$sum": "$flags.red"},
                    "ambers": {"$sum": "$flags.amber"},
                    "grays": {"$sum": "$flags.gray"},
                    "greens": {"$sum": "$flags.green"},
                },
            },
        ]
        results = self.db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].aggregate(
            pipeline, allowDiskUse=True
        )
        for result in results:
            user_id = result.get("_id")
            self.unseen_flags[user_id] = {
                UnseenFlags.RED: result.get("reds"),
                UnseenFlags.AMBER: result.get("ambers"),
                UnseenFlags.GRAY: result.get("grays") + result.get("greens"),
            }

    def set_user_flags(self):
        filter_query = {"roles.roleId": "User"}
        users = self.db[MongoAuthorizationRepository.USER_COLLECTION].find(
            {},
            {
                User.ROLES: 1,
                User.RECENT_MODULE_RESULTS: 1,
                User.UNSEEN_FLAGS: 1,
                User.RECENT_FLAGS: 1,
            },
        )
        users_count = users.count()
        progress = ProgressBar(total=users_count)
        update_ops = []
        empty_flags = {UnseenFlags.RED: 0, UnseenFlags.AMBER: 0, UnseenFlags.GRAY: 0}
        for index, user in enumerate(users):
            progress.show(current=index + 1)
            user_id = user.get("_id")
            deployment_id = self.get_user_deployment_id(user)
            if deployment_id not in self.deployment_module_configs:
                continue
            module_configs = self.deployment_module_configs[deployment_id] or []

            recent_flags = self.calculate_recent_flags(user, module_configs)
            unseen_flags = self.unseen_flags.get(user_id, empty_flags)
            flags_changed = unseen_flags != user.get(
                User.UNSEEN_FLAGS
            ) or recent_flags != user.get(User.RECENT_FLAGS)
            if flags_changed:
                filter_query = {"_id": user_id}
                update_query = {
                    "$set": {
                        User.UNSEEN_FLAGS: unseen_flags,
                        User.RECENT_FLAGS: recent_flags,
                    }
                }
                update_ops += [UpdateOne(filter_query, update_query)]
            if update_ops and index % bulk_size == 0 and index:
                self.db[MongoAuthorizationRepository.USER_COLLECTION].bulk_write(
                    update_ops, ordered=False
                )
                update_ops = []
        if update_ops:
            self.db[MongoAuthorizationRepository.USER_COLLECTION].bulk_write(
                update_ops, ordered=False
            )
        return users_count

    def get_user_deployment_id(self, user: dict):
        user_roles = user.get("roles", {})
        for role in user_roles:
            if role.get("roleId") == "User":
                resource = role.get("resource")
                if resource.startswith("deployment/"):
                    deployment_id = resource[len("deployment/") :]
                    return ObjectId(deployment_id)

    def calculate_recent_flags(self, user: dict, module_configs: list[ObjectId]):
        recent_modules = user.get("recentModuleResults") or {}
        reds, ambers, grays = 0, 0, 0
        for module_config_id, primitives in recent_modules.items():
            if not primitives or ObjectId(module_config_id) not in module_configs:
                continue
            primitive_data = list(primitives[0].values())[0]
            module_id = primitive_data.get("moduleId")
            if module_id not in excluded_modules_ids:
                flags = primitive_data.get("flags", {})
                reds += flags.get("red", 0)
                ambers += flags.get("amber", 0)
                grays += flags.get("gray", 0)
        recent_flags = {
            UnseenFlags.RED: reds,
            UnseenFlags.AMBER: ambers,
            UnseenFlags.GRAY: grays,
        }
        return recent_flags
