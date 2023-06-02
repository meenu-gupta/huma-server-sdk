import logging
from contextlib import contextmanager
from typing import Generator

import pymongo
from bson import ObjectId

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
unseen_primitive_collection = "unseenrecentresult"
ModuleResult = list[Primitive]


class Migration(BaseMigration):
    """
    This migration recalculates flags for all unseen primitives across the platform
    and updates parent primitives in primitive collections.
    """

    configs: dict[str, ModuleConfig] = {}
    manager = ModulesManager()

    def upgrade(self):
        with self._configure_di():
            self._fetch_module_configs()
            logger.info("Calculating flags for unseen module results...")
            self._calculate_flags_for_unseen_results()

    def downgrade(self):
        self.db[unseen_primitive_collection].update_many(
            {}, {"$unset": ["ragThreshold", "flags"]}
        )

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

    def _calculate_flags_for_unseen_results(self):
        module_result: ModuleResult = []
        progress = ProgressBar(total=self._total_primitives_count())
        for index, primitive in enumerate(self._primitives(), 1):
            progress.show(current=index)
            if not module_result:
                module_result.append(primitive)
                continue

            module = self.manager.find_module(primitive.moduleId)
            if is_part_of_module_result(primitive, module_result, module):
                if module and len(module.primitives) > 1:
                    module_result.append(primitive)
                    continue

            self._calculate_flags_for_unseen_primitives(module_result)
            # initiate a new module result block
            module_result = [primitive]

        if module_result:
            self._calculate_flags_for_unseen_primitives(module_result)

    def _calculate_flags_for_unseen_primitives(self, primitives: ModuleResult):
        primitive = primitives[0]
        try:
            config = self.configs.get(primitive.moduleConfigId)
            if not config:
                return

            module = self.manager.find_module(primitive.moduleId, type(primitive))
            if not module:
                return

            with module.configure(config):
                self._calculate_and_save_flags(module, primitives)

        except Exception as e:
            logger.exception(f"Error while migrating {primitive.id}. Details: {e}")

    @staticmethod
    def _calculate_flags(module: Module, primitives: ModuleResult):
        for p in primitives:
            threshold, flags = module.calculate_rag_flags(p)
            p.ragThreshold = threshold
            p.flags = flags
        module.apply_overall_flags_logic(primitives)

    def _calculate_and_save_flags(self, module: Module, module_result: ModuleResult):
        try:
            module.validate_module_result(module_result)
        except Exception as error:
            print(f"Invalid module result. Error: {error}")
            return

        try:
            self._calculate_flags(module, module_result)
            for primitive in module_result:
                self._save_primitive(primitive)
        except Exception as error:
            logger.warning(
                f"Error calculating flags for primitives {module_result}. Error: {error}"
            )

    def _save_primitive(self, primitive: Primitive):
        filter_query = {"_id": ObjectId(primitive.id)}
        new_fields = {"flags": primitive.flags, "ragThreshold": primitive.ragThreshold}
        update = {"$set": remove_none_values(new_fields)}
        self.db[unseen_primitive_collection].update_one(filter_query, update)

    def _primitives(self) -> Generator[Primitive, None, None]:
        sort = [
            ("userId", pymongo.ASCENDING),
            ("startDateTime", pymongo.ASCENDING),
            ("createDateTime", pymongo.ASCENDING),
        ]

        self.db[unseen_primitive_collection].create_index(sort)
        results = self.db[unseen_primitive_collection].find(
            {"primitiveName": {"$ne": None}}, sort=sort
        )
        for result in results:
            result.update({"id": result.pop("_id")})
            yield Primitive.create_from_dict(
                result, result.get("primitiveName"), validate=False
            )

    def _total_primitives_count(self):
        return self.db[unseen_primitive_collection].count_documents(
            {"primitiveName": {"$ne": None}}
        )

    @contextmanager
    def _configure_di(self):
        self.manager.add_module(HeightZScoreModule())

        def bind(binder):
            binder.bind(ModulesManager, self.manager)

        try:
            yield inject.clear_and_configure(bind)
        finally:
            inject.clear()


def is_part_of_module_result(
    primitive: Primitive,
    module_result: ModuleResult,
    module: Module,
):
    ref = module_result[-1]
    conditions = [
        primitive.userId == ref.userId,
        primitive.moduleConfigId == ref.moduleConfigId,
        primitive.startDateTime == ref.startDateTime,
        primitive.moduleId == ref.moduleId,
    ]

    if not all(conditions):
        return False

    if len(module.primitives) > 1:  # if module is complex
        allowed_primitives = set(module.primitives.copy())
        existing_primitives = {type(cls) for cls in module_result}
        missing_primitives = allowed_primitives - existing_primitives
        if type(primitive) not in missing_primitives:
            return False

    return True
