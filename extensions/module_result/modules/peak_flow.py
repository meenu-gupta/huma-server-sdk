from extensions.authorization.services.authorization import AuthorizationService
from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Primitive, PeakFlow
from sdk.common.exceptions.exceptions import InvalidRequestException


class PeakFlowModule(Module):
    moduleId = "PeakFlow"
    primitives = [PeakFlow]
    ragEnabled = True

    def calculate(self, primitive: Primitive):
        user = AuthorizationService().retrieve_user_profile(user_id=primitive.userId)
        if not isinstance(primitive, PeakFlow):
            return

        if not user.gender:
            raise InvalidRequestException('Field "gender" is not set in user profile')

        if not user.height:
            raise InvalidRequestException('Field "height" is not set in user profile')

        primitive.valuePercent = primitive.calculate_percent(
            user.gender, user.get_age(), user.height
        )
