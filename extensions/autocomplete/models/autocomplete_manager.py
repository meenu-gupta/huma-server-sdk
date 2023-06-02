from typing import Union, Iterable

from extensions.autocomplete.models.autocomplete_module import AutocompleteModule
from extensions.autocomplete.models.modules.az_vaccine_batch_number_autocomplete import (
    AZVaccineBatchNumberModule,
)
from extensions.autocomplete.models.modules.medications_autocomplete import (
    MedicationsAutocompleteModule,
)
from extensions.autocomplete.models.modules.symptoms_autocomplete import (
    SymptomsAutocompleteModule,
)


class AutocompleteModulesManager:
    def __init__(self):
        self._modules = []
        self.add_modules(self.default_modules)

    def __add__(self, module: AutocompleteModule):
        self.add_module(module)
        return self

    def __sub__(self, module: AutocompleteModule):
        self.remove_module(module)
        return self

    @property
    def modules(self):
        return self._modules

    def has(self, module: Union[str, AutocompleteModule]) -> bool:
        if isinstance(module, str):
            return module in [m.moduleId for m in self._modules]

        return module in self._modules

    def add_module(self, module: AutocompleteModule):
        if not isinstance(module, AutocompleteModule):
            raise Exception(
                f"Expected type AutocompleteModule, got {type(module)} instead."
            )
        if self.has(module):
            raise Exception(f"Module {module.moduleId} already registered.")
        self._modules.append(module)

    def remove_module(self, module: AutocompleteModule):
        if not isinstance(module, AutocompleteModule):
            raise Exception(
                f"Expected type AutocompleteModule, got {type(module)} instead."
            )
        if not self.has(module):
            raise Exception(f"Module {module.moduleId} not registered.")
        self._modules.remove(module)

    def add_modules(self, modules: Iterable[AutocompleteModule]):
        for module in modules:
            self.add_module(module)

    def retrieve_module(self, module_id: str) -> AutocompleteModule:
        return next(filter(lambda m: m.moduleId == module_id, self._modules), None)

    @property
    def default_modules(self):
        return (
            AZVaccineBatchNumberModule(),
            MedicationsAutocompleteModule(),
            SymptomsAutocompleteModule(),
        )
