from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import BackgroundInformation


class BackgroundInformationModule(AzModuleMixin, Module):
    moduleId = "BackgroundInformation"
    primitives = [BackgroundInformation]
