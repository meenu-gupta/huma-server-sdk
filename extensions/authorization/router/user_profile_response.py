from dataclasses import dataclass
from enum import IntEnum

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.organization.models.organization import Organization
from sdk import convertibleclass, meta
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import (
    default_field,
    positive_integer_field,
    required_field,
)
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import validate_object_id


def translate_deployment(deployment: dict, localization: dict) -> dict:
    ignored_keys = {
        Deployment.ID,
        Deployment.DEPLOYMENT_ID,
        Deployment.STATUS,
        Deployment.COLOR,
        Deployment.MANAGER_ACTIVATION_CODE,
        Deployment.USER_ACTIVATION_CODE,
        Deployment.PROXY_ACTIVATION_CODE,
        Deployment.LOCALIZATIONS,
        Deployment.STATS,
        Deployment.CODE,
        Deployment.ROLES,
        Deployment.ICON,
        Deployment.UPDATE_DATE_TIME,
        Deployment.CREATE_DATE_TIME,
    }
    return replace_values(deployment, localization, ignored_keys=ignored_keys)


class RetrieveFullConfigurationResponseObject(Response):
    ORGANIZATIONS = "organizations"
    DEPLOYMENTS = "deployments"

    @dataclass
    class Response:
        ORGANIZATIONS = "organizations"
        DEPLOYMENTS = "deployments"

        organizations: list[Organization] = required_field()
        deployments: list[Deployment] = required_field()
        language: str = default_field()

        def to_dict(self, translate=True) -> dict[str, list]:
            organizations = [o.to_dict(include_none=False) for o in self.organizations]
            deployments = []
            for deployment in self.deployments:
                deployment_dict = deployment.to_dict(include_none=False)
                if translate:
                    language = self.language or deployment.language
                    vocabulary = deployment.get_localization(language)
                    deployment_dict = translate_deployment(deployment_dict, vocabulary)

                deployment_dict["deploymentId"] = deployment_dict.pop("id")
                deployment_dict.pop(Deployment.LOCALIZATIONS, None)
                deployments.append(deployment_dict)

            return {self.ORGANIZATIONS: organizations, self.DEPLOYMENTS: deployments}

    def __init__(self, organizations, deployments, language=None):
        response = self.Response(
            organizations=organizations,
            deployments=deployments,
            language=language,
        )
        super().__init__(value=response)


class RetrieveDeploymentConfigResponseObject(Response):
    DEPLOYMENT_ID = "deploymentId"
    CONSENT_NEEDED = "consentNeeded"
    ECONSENT_NEEDED = "eConsentNeeded"
    NEXT_ONBOARDING_TASK_ID = "nextOnboardingTaskId"
    IS_OFF_BOARDED = "isOffBoarded"

    @convertibleclass
    class Response(Deployment):
        deploymentId: str = required_field()
        consentNeeded: bool = required_field()
        eConsentNeeded: bool = required_field()
        nextOnboardingTaskId: str = default_field()
        isOffBoarded: bool = required_field()

    def __init__(self, deployment_dict: dict):
        deployment_dict[self.DEPLOYMENT_ID] = deployment_dict.pop(Deployment.ID)
        resp = self.Response.from_dict(deployment_dict)
        super().__init__(value=resp)


class RetrieveProfileResponseObject(Response):
    ASSIGNED_PROXIES = "assignedProxies"
    ASSIGNED_PARTICIPANTS = "assignedParticipants"


class LinkProxyUserResponseObject(Response):
    PROXY_ID = "proxyId"

    @convertibleclass
    class Response:
        proxyId: str = required_field()

    def __init__(self, proxy_id: str):
        super().__init__(value=self.Response(proxyId=proxy_id))


class RetrieveProxyInvitationsResponseObject(Response):
    @convertibleclass
    class Response:
        STATUS = "status"
        PROXY = "proxy"
        INVITATION_ID = "invitationId"

        class ProxyStatus(IntEnum):
            PENDING_SIGNUP = 1
            PENDING_ONBOARDING = 2
            ACTIVE = 3

        @convertibleclass
        class ProxyData:
            EMAIL = "email"
            PHONE_NUMBER = "phoneNumber"
            GIVEN_NAME = "givenName"
            FAMILY_NAME = "familyName"

            givenName: str = default_field()
            familyName: str = default_field()
            phoneNumber: str = default_field()
            email: str = default_field()

        status: ProxyStatus = required_field()
        proxy: ProxyData = default_field()
        invitationId: str = default_field(metadata=meta(validate_object_id))

    def __init__(self, status, proxy=None, invitation_id=None):
        super().__init__(
            value=self.Response(proxy=proxy, status=status, invitationId=invitation_id)
        )


class RetrieveUserResourcesResponseObject(Response):
    @convertibleclass
    class Response:
        ORGANIZATIONS = "organizations"
        DEPLOYMENTS = "deployments"

        organizations: list[Organization] = default_field()
        deployments: list[Deployment] = default_field()

    def __init__(
        self, organizations: list[Organization], deployments: list[Deployment]
    ):
        super().__init__(
            value=self.Response(organizations=organizations, deployments=deployments)
        )


class RetrieveProfilesResponseObject(Response):
    @convertibleclass
    class Response:
        USERS = "users"
        FILTERED = "filtered"
        TOTAL = "total"

        users: list[User] = default_field()
        filtered: int = positive_integer_field(default=None)
        total: int = positive_integer_field(default=None)

    def __init__(self, users: list[User], filtered: int, total: int):
        super().__init__(
            value=self.Response(users=users, filtered=filtered, total=total)
        )
