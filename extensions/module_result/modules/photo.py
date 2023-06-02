from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Photo


class PhotoModule(Module):
    moduleId = "Photo"
    primitives = [Photo]
