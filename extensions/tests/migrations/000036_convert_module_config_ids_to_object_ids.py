from functools import cached_property

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.modules_manager import ModulesManager
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.common_functions_utils import find


class Migration(BaseMigration):
    """
    This migration recalculates flags for all unseen primitives across the platform
    and updates parent primitives in primitive collections.
    """

    configs: dict[str, ModuleConfig] = {}
    manager = ModulesManager()

    def upgrade(self):
        query = {"moduleConfigId": {"$type": "string", "$regex": "^[0-9a-fA-F]{24}$"}}
        update = {
            "$set": {
                "moduleConfigId": {"$convert": {"input": "$moduleConfigId", "to": 7}}
            }
        }
        collections = self.primitive_collections + ["unseenrecentresult"]
        for collection in collections:
            self.db[collection.lower()].update_many(query, [update])

    def downgrade(self):
        pass

    @cached_property
    def primitive_collections(self):
        if not (collections := self.existing_collections):
            return []

        return [
            cls.__name__
            for cls in Primitive.__subclasses__()
            if find(lambda c: c == cls.__name__.lower(), collections)
        ]

    @cached_property
    def existing_collections(self):
        collections = self.db.list_collection_names()
        return [col for col in collections if not col.startswith("_")]
