from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.dashboard.builders.base_data_builder import DataBuilder
from extensions.dashboard.localization.localization_keys import (
    KeyMetricsGadgetLocalization,
)
from extensions.dashboard.models.gadgets.key_metrics import (
    KeyMetricsGadgetConfig,
    KeyMetricsData,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.utils import format_text_to_bold
from sdk.common.utils.inject import autoparams


class KeyMetricsDataBuilder(DataBuilder):
    config = KeyMetricsGadgetConfig
    per_deployment_consented_data = {}
    per_deployment_completed_data = {}

    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        econsent_repo: EConsentRepository,
        auth_repo: AuthorizationRepository,
    ):
        self.deployment_repo = deployment_repo
        self.organization_repo = organization_repo
        self.econsent_repo = econsent_repo
        self.auth_repo = auth_repo

    def build_data(self):
        self._set_initial_values()
        organization = self.organization_repo.retrieve_organization(
            organization_id=self.config.organizationId
        )
        target_consented = 0
        study_completion_target = 0
        deployments = self._get_deployments(organization)
        for deployment in deployments:
            consented = self._get_deployment_consented(deployment)
            completed = self._get_deployment_completed_users(deployment.id)
            self.per_deployment_consented_data[deployment.id] = sum(consented.values())
            self.per_deployment_completed_data[deployment.id] = len(completed)
            if deployment.dashboardConfiguration:
                target_consented += (
                    deployment.dashboardConfiguration.targetConsented or 0
                )
                study_completion_target += (
                    deployment.dashboardConfiguration.targetCompleted or 0
                )

        is_consent_enabled = any([deployment.econsent for deployment in deployments])
        if is_consent_enabled:
            self._fill_consented_gadget_with_data(target_consented)

        self._fill_completed_gadget_with_data(study_completion_target)
        self._set_tooltip_and_bars(is_consent_enabled)

    def _set_initial_values(self):
        self.per_deployment_consented_data = {}
        self.per_deployment_completed_data = {}
        self.gadget.id = self.gadget.type
        self.gadget.title = KeyMetricsGadgetLocalization.TITLE.key
        self.gadget.metadata = {"chart": {"bars": []}}
        self.gadget.data = []
        self.gadget.infoFields = []

    def _fill_completed_gadget_with_data(self, study_completion_target: int):
        self._fill_gadget_fields_with_data(
            self.per_deployment_completed_data,
            study_completion_target,
            KeyMetricsGadgetLocalization.COMPLETED.key,
        )

    def _fill_consented_gadget_with_data(self, target_consented: int):
        self._fill_gadget_fields_with_data(
            self.per_deployment_consented_data,
            target_consented,
            KeyMetricsGadgetLocalization.CONSENTED.key,
        )

    def _fill_gadget_fields_with_data(self, data: dict, target: int, name: str):
        for key, value in data.items():
            self.gadget.data.append(
                {
                    KeyMetricsData.D: key,
                    KeyMetricsData.Y: value,
                    KeyMetricsData.X: name,
                }
            )
        self.gadget.metadata["chart"][name] = {
            "max": target,
            "min": 0,
        }
        value = None
        if data_values := sum(data.values()):
            value = f"{format_text_to_bold(data_values)}/{target}"
        self.gadget.infoFields.append(
            {
                "name": name,
                "value": value,
            }
        )

    def _set_tooltip_and_bars(self, is_consent_enabled: bool):
        tooltip_mapping = {
            True: f"{KeyMetricsGadgetLocalization.TOOLTIP_CONSENTED.key} {KeyMetricsGadgetLocalization.TOOLTIP_COMPLETED.key}",
            False: KeyMetricsGadgetLocalization.TOOLTIP_COMPLETED.key,
        }
        self.gadget.tooltip = tooltip_mapping.get(is_consent_enabled)

        bars_ordering_mapping = {
            True: [
                KeyMetricsGadgetLocalization.CONSENTED.key,
                KeyMetricsGadgetLocalization.COMPLETED.key,
            ],
            False: [
                KeyMetricsGadgetLocalization.COMPLETED.key,
            ],
        }
        self.gadget.metadata["chart"]["bars"] = bars_ordering_mapping.get(
            is_consent_enabled
        )

    def _get_deployment_consented(self, deployment: Deployment):
        if not deployment.econsent:
            return {}
        consented = self.econsent_repo.retrieve_consented_users_count(
            econsent_id=deployment.econsent.id
        )
        return consented if consented else {}

    def _get_deployment_completed_users(self, deployment_id):
        filters = {
            f"{User.BOARDING_STATUS}.{BoardingStatus.REASON_OFF_BOARDED}": BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        }
        return self.auth_repo.retrieve_user_profiles(
            deployment_id, "", filters=filters
        )[0]

    def _get_deployments(self, organization: Organization) -> list[Deployment]:
        deployment_ids = self.config.deploymentIds or organization.deploymentIds
        return self.deployment_repo.retrieve_deployments_by_ids(deployment_ids)
