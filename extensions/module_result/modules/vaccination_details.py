from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.deployment.validators import validate_vaccination_batch_number
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives import (
    VaccinationDetails,
)
from sdk.common.utils.validators import must_not_be_present


class VaccinationDetailsModule(AzModuleMixin, Module):
    moduleId = "VaccinationDetails"
    primitives = [VaccinationDetails]
    ragEnabled = True

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        super().preprocess(primitives, user)
        for primitive in primitives:
            if type(primitive) == VaccinationDetails:
                must_not_be_present(isBatchNumberValid=primitive.isBatchNumberValid)
                if primitive.batchNumber:
                    primitive.isBatchNumberValid = validate_vaccination_batch_number(
                        primitive.batchNumber
                    )
