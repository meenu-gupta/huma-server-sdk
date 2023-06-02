from typing import Iterable, Union

from extensions.common.exceptions import InvalidModuleException
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules import default_modules
from extensions.module_result.modules.module import Module
from sdk.common.exceptions.exceptions import InvalidRequestException


class ModulesManager:
    """
    Manager for adding new modules to deployment.
    How to use:
    class NewModule(Module)
        moduleId = "NewModule"
        primitive = [Weight]
    > module = NewModule()
    >
    > manager = inject.instance(ModulesManager)
    > or
    > manager = DeploymentComponent().module_manager
    >
    > manager.add_module(module)

    """

    def __init__(self):
        self._modules = []
        self.add_modules(self.default_modules)

    def __add__(self, module: Module):
        self.add_module(module)
        return self

    def __sub__(self, module: Module):
        self.remove_module(module)
        return self

    @property
    def modules(self):
        return self._modules

    def has(self, module: Union[Module, str], raise_error=False) -> bool:
        module_exist = False
        if isinstance(module, Module):
            module_exist = module in self._modules
        elif isinstance(module, str):
            module_exist = any(True for m in self._modules if m.moduleId == module)

        if not module_exist and raise_error:
            module_name = module if isinstance(module, str) else module.moduleId
            raise InvalidModuleException(module_name)

        return module_exist

    def add_module(self, module: Module):
        if not isinstance(module, Module):
            raise Exception(f"Expected type Module, got {type(module)} instead.")
        if self.has(module):
            raise Exception(f"Module {module.moduleId} already registered.")
        self._modules.append(module)

    def remove_module(self, module: Module):
        if not isinstance(module, Module):
            raise Exception(f"Expected type Module, got {type(module)} instead.")
        if not self.has(module):
            raise Exception(f"Module {module.moduleId} not registered.")
        self._modules.remove(module)

    def add_modules(self, modules: Iterable[Module]):
        for module in modules:
            self.add_module(module)

    def get_preferred_unit_enabled_module_ids(self):
        return [m.moduleId for m in self.modules if m.preferredUnitEnabled]

    def find_module(
        self, module_id: str, primitive: Union[type, set[type]] = None
    ) -> Module:
        if primitive and not isinstance(primitive, set):
            primitive = {primitive}

        def filter_modules(item: Module) -> bool:
            if item.moduleId == module_id:
                return not primitive or all(p in item.primitives for p in primitive)  #
            return False

        return next(filter(filter_modules, self.modules), None)

    def validate_module_config(self, module_config: ModuleConfig):
        module = self.find_module(module_config.moduleId)
        if not module:
            msg = f"Wrong module id {module_config.moduleId}"
            raise InvalidRequestException(msg)

        module.validate_module_config(module_config)

    @property
    def default_modules(self):
        return (module() for module in default_modules)
