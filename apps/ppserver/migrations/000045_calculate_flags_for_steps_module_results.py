import logging
from contextlib import contextmanager

from bson import ObjectId
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive

from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.authorization.models.user import UnseenFlags
from extensions.module_result.modules.step import StepModule
from extensions.module_result.models.primitives import Step
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils import inject

logger = logging.getLogger(__name__)
bulk_size = 10000


class Migration(BaseMigration):
    """
    This migration recalculates flags for all steps module results
    and updates corresponding entries in unseenrecentresult collection.
    """

    configs: dict[str, ModuleConfig] = {}
    manager = ModulesManager()

    def upgrade(self):
        logger.info("Clearing flags for steps module results...")
        self._reset_steps_flags()
        with self._configure_di():
            self._fetch_module_configs()
            logger.info("Calculating flags for steps module results...")
            self._calculate_flags_for_steps_module_results()

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

    def _get_aggregated_steps_data(self):
        pipeline = [
            {"$match": {"moduleId": {"$eq": "Step"}, "moduleConfigId": {"$ne": None}}},
            {"$sort": {"startDateTime": 1}},
            {
                "$group": {
                    "_id": {
                        "userID": "$userId",
                        "moduleConfigId": "$moduleConfigId",
                        "deploymentId": "$deploymentId",
                        "year": {"$year": "$startDateTime"},
                        "week": {"$week": "$startDateTime"},
                    },
                    "weeklyTotal": {"$sum": "$value"},
                    "lastPrimitiveId": {"$last": "$_id"},
                    "deviceName": {"$last": "$deviceName"},
                },
            },
            {"$sort": {"_id.moduleConfigId": 1}},
        ]
        results = self.db[Step.__name__.lower()].aggregate(pipeline, allowDiskUse=True)
        return results

    def _calculate_flags_for_steps_module_results(self):
        steps = self._get_aggregated_steps_data()

        module_config_id = None
        primitives: list[Primitive] = []
        for index, step_data in enumerate(steps):
            primitive = self._create_step_primitive(step_data)
            if not module_config_id:
                module_config_id = primitive.moduleConfigId
            if module_config_id != primitive.moduleConfigId or (
                index > 0 and index % bulk_size == 0
            ):
                module_config_id = primitive.moduleConfigId
                self._update_flags(primitives=primitives)
                primitives = []
            primitives.append(primitive)

        if primitives:
            self._update_flags(primitives=primitives)

    def _update_flags(self, primitives: list[Primitive]):
        self._calculate_flags(primitives=primitives)
        self._save_flags(primitives=primitives)

    def _calculate_flags(self, primitives: list[Primitive]):
        primitive = primitives[0]
        try:
            config = self.configs.get(primitive.moduleConfigId)
            if not config:
                return

            module = self.manager.find_module(primitive.moduleId, type(primitive))
            if not module:
                return

            with module.configure(config):
                for p in primitives:
                    p.ragThreshold, p.flags = module.calculate_rag_flags(p)

        except Exception as e:
            logger.exception(f"Error while migrating {primitive.id}. Details: {e}")

    def _save_flags(self, primitives: list[Primitive]):
        step_update_ops = []
        for p in primitives:
            filter_query = {"_id": ObjectId(p.id)}
            update_query = {
                "$set": {
                    Step.FLAGS: p.flags,
                    Step.RAG_THRESHOLD: p.ragThreshold,
                    Step.WEEKLY_TOTAL: p.weeklyTotal,
                }
            }
            step_update_ops.append(UpdateOne(filter_query, update_query))
        try:
            self.db[Step.__name__.lower()].bulk_write(step_update_ops, ordered=False)
            self.db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].bulk_write(
                step_update_ops, ordered=False
            )
        except BulkWriteError as bwe:
            logger.exception(f"Error while updating steps flags. Details: {bwe}")

    @staticmethod
    def _create_step_primitive(step_data: dict):
        step_primitive_data = {
            Step.ID: step_data["lastPrimitiveId"],
            Step.MODULE_ID: StepModule.moduleId,
            Step.USER_ID: step_data["_id"]["userID"],
            Step.MODULE_CONFIG_ID: step_data["_id"]["moduleConfigId"],
            Step.DEPLOYMENT_ID: step_data["_id"]["deploymentId"],
            Step.DEVICE_NAME: step_data["deviceName"],
            Step.VALUE: step_data["weeklyTotal"],
            Step.WEEKLY_TOTAL: step_data["weeklyTotal"],
        }
        return Step.create_from_dict(step_primitive_data, name="Step")

    def _reset_steps_flags(self):
        query = {
            Primitive.MODULE_ID: StepModule.moduleId,
        }
        update = {
            "$set": {
                Primitive.FLAGS: {
                    UnseenFlags.RED: 0,
                    UnseenFlags.GRAY: 0,
                    UnseenFlags.AMBER: 0,
                }
            }
        }
        self.db[Primitive.UNSEEN_PRIMITIVES_COLLECTION].update_many(query, [update])
        self.db[Step.__name__.lower()].update_many(query, [update])

    @contextmanager
    def _configure_di(self):
        def bind(binder):
            binder.bind(ModulesManager, self.manager)

        try:
            yield inject.clear_and_configure(bind)
        finally:
            inject.clear()
