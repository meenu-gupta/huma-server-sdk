from collections import defaultdict
from datetime import date

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.dashboard.builders.base_data_builder import DataBuilder
from extensions.dashboard.builders.utils import (
    fill_month_data_with_zero_qty,
    fill_missing_data_with_0_and_sort_by_month,
    calculate_average_per_month,
    get_earliest_and_latest_dates,
)
from extensions.dashboard.localization.localization_keys import (
    SignedUpGadgetLocalizationKeys,
)
from extensions.dashboard.models.gadgets.signed_up import (
    SignUpGadgetConfig,
    SignedUpData,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.utils import format_text_to_bold
from sdk.common.utils.inject import autoparams


class SignedUpDataBuilder(DataBuilder):
    config = SignUpGadgetConfig

    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        auth_repo: AuthorizationRepository,
    ):
        self.deployment_repo = deployment_repo
        self.organization_repo = organization_repo
        self.auth_repo = auth_repo

    def build_data(self):
        organization = self.organization_repo.retrieve_organization(
            organization_id=self.config.organizationId
        )
        deployments = self._get_deployments(organization)
        total_signed_up = 0
        per_deployment_signed_up_data = defaultdict(dict)
        for deployment in deployments:
            signed_up_by_month = self._get_deployment_signed_up_by_month(deployment)
            per_deployment_signed_up_data[deployment.id] = signed_up_by_month
            if not signed_up_by_month:
                continue
            total_signed_up += sum(signed_up_by_month.values())

        earliest_date, latest_consented_date, _ = get_earliest_and_latest_dates(
            per_deployment_signed_up_data
        )

        total_avg = calculate_average_per_month(
            total_signed_up, earliest_date, latest_consented_date
        )

        self._update_gadget_info_fields(total_avg)
        self._populate_gadget_fields()
        self.gadget.data = self._generate_gadget_data(
            per_deployment_signed_up_data, earliest_date
        )

    def _get_deployment_signed_up_by_month(
        self, deployment: Deployment
    ) -> dict[date, int]:
        signed_up = self.auth_repo.retrieve_grouped_signed_up_user_count_by_month(
            deployment_id=deployment.id
        )
        if not signed_up:
            return {}

        start_date = list(signed_up.keys())[0]
        return fill_month_data_with_zero_qty(signed_up, start_date)

    def _get_deployments(self, organization: Organization) -> list[Deployment]:
        deployment_ids = self.config.deploymentIds or organization.deploymentIds
        return self.deployment_repo.retrieve_deployments_by_ids(deployment_ids)

    def _update_gadget_info_fields(
        self,
        total_avg_monthly_signed_up: int,
    ):
        self.gadget.infoFields = [
            {
                "name": SignedUpGadgetLocalizationKeys.INFO_AVG_MONTHLY.key,
                "value": format_text_to_bold(total_avg_monthly_signed_up),
            },
        ]
        self.gadget.avg = total_avg_monthly_signed_up

    def _populate_gadget_fields(self):
        self.gadget.metadata = {
            "chart": {
                "avg": {"tooltip": SignedUpGadgetLocalizationKeys.CHART_TOOLTIP.key}
            }
        }
        self.gadget.id = self.gadget.type
        self.gadget.title = SignedUpGadgetLocalizationKeys.TITLE.key
        self.gadget.tooltip = SignedUpGadgetLocalizationKeys.TOOLTIP.key

    @staticmethod
    def _generate_gadget_data(
        per_deployment_signed_up_data: dict, earliest_date: date
    ) -> list[SignedUpData]:
        sorted_by_date = fill_missing_data_with_0_and_sort_by_month(
            per_deployment_signed_up_data, earliest_date
        )
        gadget_data = []
        for month, month_data in sorted_by_date.items():
            for deployment, amount in month_data.items():
                gadget_data.append(SignedUpData(x=month, y=amount, d=deployment))
        return gadget_data
