from typing import Optional

from extensions.authorization.router.user_profile_request import (
    RetrieveDeploymentConfigRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveDeploymentConfigResponseObject,
    translate_deployment,
)
from extensions.deployment.models.deployment import Deployment
from extensions.authorization.boarding.manager import BoardingManager
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.exceptions import OffBoardingRequiredError
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.flask_request_utils import (
    get_current_path_or_empty,
    get_current_url_rule_or_empty,
)


class RetrieveDeploymentConfigUseCase(UseCase):
    request_object: RetrieveDeploymentConfigRequestObject = None

    def execute(self, request_object: RetrieveDeploymentConfigRequestObject):
        self.request_object = request_object
        return super(RetrieveDeploymentConfigUseCase, self).execute(request_object)

    def process_request(self, request_object):
        # for now leaving this as service
        service = DeploymentService()
        deployment = service.retrieve_deployment_config(request_object.user)
        deployment.filter_static_event_module_configs(request_object.user.user)
        service.apply_default_disclaimer_configs(deployment)
        localization = deployment.get_localization(request_object.user.get_language())
        deployment.localizations = None
        deployment.preprocess_for_configuration()
        deployment_dict = deployment.to_dict(include_none=False)

        if request_object.user.is_user():
            deployment_dict.pop(Deployment.CARE_PLAN_GROUP, None)

        args = request_object.user.id, deployment
        consent_needed = not service.is_consent_signed(*args)
        econsent_needed = not service.is_econsent_signed(*args)
        next_onboarding_task = self._retrieve_next_onboarding_task()

        response_data = {
            **deployment_dict,
            RetrieveDeploymentConfigResponseObject.CONSENT_NEEDED: consent_needed,
            RetrieveDeploymentConfigResponseObject.ECONSENT_NEEDED: econsent_needed,
            RetrieveDeploymentConfigResponseObject.NEXT_ONBOARDING_TASK_ID: next_onboarding_task,
            RetrieveDeploymentConfigResponseObject.IS_OFF_BOARDED: self._is_user_off_boarded(),
        }

        result = translate_deployment(response_data, localization)
        return RetrieveDeploymentConfigResponseObject(result)

    def _retrieve_next_onboarding_task(self) -> Optional[str]:
        path = get_current_path_or_empty()
        url_rule = get_current_url_rule_or_empty()
        onboarding_manager = BoardingManager(self.request_object.user, path, url_rule)
        return onboarding_manager.get_next_onboarding_task()

    def _is_user_off_boarded(self):
        manager = BoardingManager(self.request_object.user, "", "")
        try:
            manager.check_off_boarding_and_raise_error()
        except OffBoardingRequiredError:
            return True
        return False
