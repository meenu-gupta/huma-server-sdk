import requests

from extensions.module_result.config.cvd_integration import CVDIntegrationConfig
from extensions.module_result.modules.cvd_risk_score.ai_cvd_model import (
    CVDRiskScoreRequestObject,
    CVDRiskScoreResponseObject,
)
from sdk.common.utils.inject import autoparams, instance
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.common.requests.request_utils import RequestContext


class CVDRiskScoreServiceException(Exception):
    pass


class AIScoringService:
    @autoparams("config")
    def __init__(self, config: PhoenixServerConfig):
        self.config: CVDIntegrationConfig = config.server.moduleResult.cvd
        self.url = self.config.url

    def get_cvd_risk_score(
        self, data: CVDRiskScoreRequestObject
    ) -> CVDRiskScoreResponseObject:
        """Get scoring for cvd risk from score engine API"""
        request_obj = instance(RequestContext)
        header = {"x-request-id": request_obj.request_id}
        response = requests.post(
            self.url,
            json=data,
            auth=(self.config.username, self.config.password),
            headers=header,
        )
        if response.status_code == 200:
            response_json = response.json()
        else:
            msg = f"Score engine returned error: {response.json()}"
            raise CVDRiskScoreServiceException(msg)

        return self.build_response_object(response_json)

    def build_response_object(self, data: dict):
        return CVDRiskScoreResponseObject.from_dict(data)
