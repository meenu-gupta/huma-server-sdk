import onfido

from sdk.common.adapter.identity_verification_adapter import (
    IdentityVerificationAdapter,
    IdentityVerificationApplicant,
    IdentityVerificationCheck,
)
from sdk.common.exceptions.exceptions import (
    OnfidoSdkTokenGenerationException,
    OnfidoCreateApplicantException,
    OnfidoCreateCheckException,
)
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig


class OnfidoAdapter(IdentityVerificationAdapter):
    @autoparams()
    def __init__(self, config: PhoenixServerConfig):
        self._config = config.server.adapters.onfido
        self.api = onfido.Api(self._config.apiToken, base_url=self._config.region)

    @property
    def webhook_token(self):
        return self._config.webhookToken

    def create_applicant(self, applicant: IdentityVerificationApplicant) -> str:
        try:
            return self.api.applicant.create(applicant.to_dict(include_none=False)).get(
                "id"
            )
        except Exception as e:
            raise OnfidoCreateApplicantException(
                f"Onfido Creating Applicant Failed with error [{e}]"
            )

    def generate_sdk_token(self, applicant_id: str, application_id: str) -> str:
        try:
            return self.api.sdk_token.generate(
                {
                    "applicant_id": applicant_id,
                    "application_id": application_id,
                }
            ).get("token")
        except Exception as e:
            raise OnfidoSdkTokenGenerationException(
                f"Onfido SDK Token Generation failed with error [{e}]"
            )

    def create_check(self, check: IdentityVerificationCheck):
        try:
            return self.api.check.create(check.to_dict(include_none=False))
        except Exception as e:
            raise OnfidoCreateCheckException(
                f"Onfido Creating Check failed with error [{e}]"
            )

    def retrieve_verification_check(self, check_id: str) -> dict:
        try:
            return self.api.check.find(check_id)
        except Exception as e:
            raise OnfidoCreateApplicantException(
                f"Onfido Retrieve User Verification Failed with error [{e}]"
            )
