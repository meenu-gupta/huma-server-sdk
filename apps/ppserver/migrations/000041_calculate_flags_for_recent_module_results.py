import logging
from contextlib import contextmanager
from typing import Generator

from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.authorization.repository.mongo_auth_repository import (
    MongoAuthorizationRepository,
)
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.height_zscore import HeightZScoreModule
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.modules_manager import ModulesManager
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.mongodb_migrations.progress_bar import ProgressBar
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values

logger = logging.getLogger(__name__)
ModuleResult = list[Primitive]


class Migration(BaseMigration):
    """
    This migration recalculates flags for all unseen primitives across the platform
    and updates parent primitives in primitive collections.
    """

    configs: dict[str, ModuleConfig] = {}
    manager = ModulesManager()
    repo = MongoAuthorizationRepository

    def upgrade(self):
        with self._configure_di():
            self._fetch_module_configs()
            logger.info("Calculating flags for recent module results...")
            total_count = self._total_users_count()
            progress_bar = ProgressBar(total_count)
            logger.info(f"{total_count} users found")
            for index, user in enumerate(self._users(), 1):
                progress_bar.show(index)
                self._calculate_and_save_flags_for_user(user)
                self._save_user(user)

    def downgrade(self):
        pass

    def _fetch_module_configs(self):
        pipeline = [
            {"$match": {"$expr": {"$ne": ["$moduleConfigs", []]}}},
            {"$unwind": "$moduleConfigs"},
            {"$replaceRoot": {"newRoot": "$moduleConfigs"}},
        ]
        configs = self.db.deployment.aggregate(pipeline)
        configs = (
            ModuleConfig.from_dict(c, use_validator_field=False) for c in configs
        )
        self.configs = {config.id: config for config in configs}

    def _users(self) -> Generator[User, None, None]:
        query = {"roles.roleId": "User", "recentModuleResults": {"$ne": None}}
        users = self.db.user.find(query)
        for user in users:
            yield self.repo.build_user_from_dict(remove_none_values(user))

    def _total_users_count(self):
        query = {"roles.roleId": "User", "recentModuleResults": {"$ne": None}}
        return self.db.user.count_documents(query)

    def _calculate_and_save_flags_for_user(self, user: User):
        for config_id, module_results in user.recentModuleResults.items():
            recent_module_result = module_results[0]
            recent_module_result = list(recent_module_result.values())
            self._calculate_flags_for_module_result(recent_module_result)
        self._save_user(user)

    def _calculate_flags_for_module_result(self, module_result: ModuleResult):
        ref_primitive = module_result[0]
        try:
            config = self.configs.get(ref_primitive.moduleConfigId)
            if not config:
                return

            module = self.manager.find_module(
                ref_primitive.moduleId, type(ref_primitive)
            )
            if not module:
                return

            with module.configure(config):
                self._calculate_flags(module, module_result)

        except Exception as e:
            logger.exception(f"Error while migrating {ref_primitive.id}. Details: {e}")

    def _save_user(self, user: User):
        results = self.repo.convert_recent_results_to_dict(user.recentModuleResults)
        results = remove_none_values(results)
        self.db.user.update_one(
            {"_id": ObjectId(user.id)}, {"$set": {User.RECENT_MODULE_RESULTS: results}}
        )

    def _calculate_flags(self, module: Module, module_result: ModuleResult):
        try:
            module.validate_module_result(module_result)
        except Exception as error:
            logger.warning(f"Invalid module result. Error: {error}")
            return

        try:
            for p in module_result:
                threshold, flags = module.calculate_rag_flags(p)
                p.ragThreshold = threshold
                p.flags = flags
            module.apply_overall_flags_logic(module_result)
        except Exception as error:
            msg = f"Error calculating flags for primitives {module_result}. Error: {error}"
            logger.warning(msg)

    @contextmanager
    def _configure_di(self):
        self.manager.add_module(HeightZScoreModule())

        try:
            yield inject.clear_and_configure(
                lambda b: b.bind(ModulesManager, self.manager)
            )
        finally:
            inject.clear()
