from typing import Optional

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import ModuleConfig
from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Weight, BMI, Primitive
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.validators import remove_none_values


class BMI2Module(Module):
    moduleId = "BMI2"
    primitives = [BMI, Weight]

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        if not primitives:
            return
        # raise error if BMI primitive present in the list
        for primitive in primitives:
            if primitive.class_name == BMI.__name__:
                raise InvalidRequestException("BMI primitive can not be created.")

        primitive = primitives[0]
        if not primitive.class_name == Weight.__name__:
            return

        if not (user and user.height):
            raise InvalidRequestException('Field "height" is not set in user profile')

        height = user.height / 100
        weight = primitive.value
        bmi = round(weight / (height * height), 2)

        primitives.append(
            BMI.from_dict({**remove_none_values(primitive.to_dict()), BMI.VALUE: bmi})
        )

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        if not isinstance(target_primitive, BMI):
            return {}

        return super(BMI2Module, self).get_threshold_data(
            target_primitive, module_config, primitives
        )
