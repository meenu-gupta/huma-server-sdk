from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import FeverAndPainDrugs


class FeverAndPainDrugsModule(AzModuleMixin, Module):
    moduleId = "FeverAndPainDrugs"
    primitives = [FeverAndPainDrugs]
