from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.deployment.validators import validate_vaccination_batch_number
from extensions.module_result.models.primitives import PostVaccination, Primitive
from sdk.common.utils.validators import must_not_be_present


class PostVaccinationModule(AzModuleMixin, Module):
    moduleId = "PostVaccination"
    primitives = [PostVaccination]
    ragEnabled = True

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        super().preprocess(primitives, user)
        for primitive in primitives:
            if type(primitive) == PostVaccination:
                must_not_be_present(isBatchNumberValid=primitive.isBatchNumberValid)
                if primitive.batchNumberVaccine:
                    primitive.isBatchNumberValid = validate_vaccination_batch_number(
                        primitive.batchNumberVaccine
                    )
