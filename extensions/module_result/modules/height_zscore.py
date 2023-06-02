from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Height


class HeightZScoreModule(Module):  # pragma: no cover
    moduleId = "HeightZScore"
    primitives = [Height]
    ragEnabled = True
