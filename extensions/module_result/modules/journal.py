from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Journal


class JournalModule(Module):
    moduleId = "Journal"
    primitives = [Journal]
