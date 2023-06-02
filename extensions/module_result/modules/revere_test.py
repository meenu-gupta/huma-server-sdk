from extensions.module_result.modules.module import Module
from extensions.revere.models.revere import RevereTest


class RevereTestModule(Module):
    moduleId = "RevereTest"
    primitives = [RevereTest]
