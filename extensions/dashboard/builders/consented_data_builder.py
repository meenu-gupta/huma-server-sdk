from collections import defaultdict
from datetime import date
from math import floor
from typing import Union, Optional

from dateutil.relativedelta import relativedelta

from extensions.dashboard.builders.base_data_builder import DataBuilder
from extensions.dashboard.builders.utils import (
    fill_month_data_with_zero_qty,
    fill_missing_data_with_0_and_sort_by_month,
    calculate_average_per_month,
    get_earliest_and_latest_dates,
)
from extensions.dashboard.localization.localization_keys import (
    ConsentedGadgetLocalizationKeys,
)
from extensions.dashboard.models.gadgets.consented import (
    ConsentedGadgetConfig,
    ConsentedData,
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


class ConsentedDataBuilder(DataBuilder):
    config = ConsentedGadgetConfig

    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        econsent_repo: EConsentRepository,
    ):
        self.deployment_repo = deployment_repo
        self.organization_repo = organization_repo
        self.econsent_repo = econsent_repo

    def build_data(self):
        self._populate_gadget_fields()
        organization = self.organization_repo.retrieve_organization(
            organization_id=self.config.organizationId
        )
        deployments = self._get_deployments(organization)
        if not any([deployment.econsent for deployment in deployments]):
            self.gadget.data = []
            self._update_gadget_info_fields(None, None, None)
            return

        total_monthly_target = self._get_total_monthly_consented_target(deployments)
        target_consented = self._get_total_consented_target(deployments)
        total_consented = 0
        sum_avg_consented_per_month = 0
        per_deployment_consented_data = defaultdict(dict)
        for deployment in deployments:
            consented_by_month = self._get_deployment_consented_by_month(deployment)
            per_deployment_consented_data[deployment.id] = consented_by_month
            if not consented_by_month:
                continue

            deployment_consented = sum(consented_by_month.values())
            average_per_month = deployment_consented / len(consented_by_month)
            total_consented += deployment_consented
            sum_avg_consented_per_month += average_per_month

        (
            earliest_date,
            latest_date,
            latest_consented_date,
        ) = get_earliest_and_latest_dates(per_deployment_consented_data)
        total_avg = calculate_average_per_month(
            total_consented,
            earliest_date,
            latest_date,
        )

        expected_completion_date = self._calculate_expected_completion_date(
            target_consented,
            total_consented,
            sum_avg_consented_per_month,
            latest_consented_date,
        )
        self.gadget.data = self._generate_gadget_data(
            per_deployment_consented_data, earliest_date
        )
        self._update_gadget_info_fields(
            total_monthly_target, total_avg, expected_completion_date
        )

    def _get_deployment_consented_by_month(
        self, deployment: Deployment
    ) -> dict[date, int]:
        if not deployment.econsent:
            return {}
        consented = self.econsent_repo.retrieve_consented_users_count(
            econsent_id=deployment.econsent.id
        )
        if not consented:
            return {}

        start_date = list(consented.keys())[0]
        return fill_month_data_with_zero_qty(consented, start_date)

    def _get_deployments(self, organization: Organization) -> list[Deployment]:
        deployment_ids = self.config.deploymentIds or organization.deploymentIds
        return self.deployment_repo.retrieve_deployments_by_ids(deployment_ids)

    @staticmethod
    def _calculate_expected_completion_date(
        target_consented: int,
        total_consented: int,
        total_avg_consented_monthly: int,
        latest_consented_date: date,
    ) -> Union[date, None]:
        required_variables = [
            target_consented,
            total_consented,
            total_avg_consented_monthly,
            latest_consented_date,
        ]
        if any(not variable for variable in required_variables):
            return
        expected_completion_in = (
            target_consented - total_consented
        ) / total_avg_consented_monthly
        months_delta = floor(expected_completion_in)
        return latest_consented_date + relativedelta(months=months_delta)

    def _update_gadget_info_fields(
        self,
        target: Optional[int],
        total_avg_monthly_consented: Optional[int],
        expected_completion_date: Optional[str],
    ):
        self.gadget.infoFields = [
            {
                "name": ConsentedGadgetLocalizationKeys.INFO_MONTHLY_TARGET.key,
                "value": format_text_to_bold(target),
            },
            {
                "name": ConsentedGadgetLocalizationKeys.INFO_AVG_MONTHLY.key,
                "value": format_text_to_bold(total_avg_monthly_consented),
            },
            {
                "name": ConsentedGadgetLocalizationKeys.INFO_EXP_ENROLLMENT.key,
                "value": format_text_to_bold(expected_completion_date),
            },
        ]
        self.gadget.avg = total_avg_monthly_consented

    def _populate_gadget_fields(self):
        self.gadget.metadata = {
            "chart": {
                "avg": {
                    "tooltip": ConsentedGadgetLocalizationKeys.TOOLTIP_AVG_MONTHLY.key
                }
            }
        }
        self.gadget.id = self.gadget.type
        self.gadget.title = ConsentedGadgetLocalizationKeys.TITLE.key
        self.gadget.tooltip = ConsentedGadgetLocalizationKeys.TOOLTIP.key

    @staticmethod
    def _generate_gadget_data(
        per_deployment_consented_data: dict, earliest_date: date
    ) -> list[ConsentedData]:
        sorted_by_date = fill_missing_data_with_0_and_sort_by_month(
            per_deployment_consented_data, earliest_date
        )
        gadget_data = []
        for month, month_data in sorted_by_date.items():
            for deployment, amount in month_data.items():
                gadget_data.append(ConsentedData(x=month, y=amount, d=deployment))
        return gadget_data

    @staticmethod
    def _get_total_monthly_consented_target(deployments: list[Deployment]):
        monthly_targets = [
            deployment.dashboardConfiguration.targetConsentedMonthly or 0
            for deployment in deployments
            if deployment.dashboardConfiguration
        ]
        return sum(monthly_targets)

    @staticmethod
    def _get_total_consented_target(deployments: list[Deployment]):
        targets = [
            deployment.dashboardConfiguration.targetConsented or 0
            for deployment in deployments
            if deployment.dashboardConfiguration
        ]
        return sum(targets)
