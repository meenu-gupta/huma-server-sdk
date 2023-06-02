from collections import defaultdict
from operator import itemgetter

from extensions.authorization.boarding.manager import BoardingManager
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.dashboard.builders.base_data_builder import DataBuilder
from extensions.dashboard.localization.localization_keys import (
    OverallViewGadgetLocalization,
)
from extensions.dashboard.models.gadgets.overall_view import (
    OverallViewGadgetConfig,
    OverallViewData,
)
from extensions.deployment.boarding.econsent_module import EConsentModule
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.identity_verification.modules import IdentityVerificationModule
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.utils import format_text_to_bold, remove_trailing_zero_in_decimal
from sdk.common.utils.common_functions_utils import round_half_up
from sdk.common.utils.inject import autoparams

GADGET_ENABLED_MODULE_NAMES = (IdentityVerificationModule.name, EConsentModule.name)
MODULE_ID = "module_id"


class OverallViewDataBuilder(DataBuilder):
    config = OverallViewGadgetConfig

    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        organization_repo: OrganizationRepository,
        auth_repo: AuthorizationRepository,
        econsent_repo: EConsentRepository,
    ):
        self.deployment_repo = deployment_repo
        self.organization_repo = organization_repo
        self.auth_repo = auth_repo
        self.econsent_repo = econsent_repo
        self.overhead_values = {OverallViewGadgetLocalization.SIGNED_UP.key: 0}

    def build_data(self):
        self._populate_initial_gadget_fields()
        organization = self.organization_repo.retrieve_organization(
            organization_id=self.config.organizationId
        )
        deployments = self._get_deployments(organization)
        per_deployment_signed_up = defaultdict(int)
        per_deployment_refused_consent = defaultdict(int)
        per_deployment_failed_id_verification = defaultdict(int)
        completed_count_module = defaultdict(dict)
        per_deployment_withdraw_consent = defaultdict(int)
        per_deployment_manual_off_boarded = defaultdict(int)
        per_deployment_all_tasks_completed_offboarded = defaultdict(int)
        same_configs = True

        enabled_modules_deployments = set()
        for deployment in deployments:
            signed_up_users = self._get_deployment_signed_users_count(deployment.id)
            refused_consented_users = (
                self._get_deployment_refused_consented_users_count(deployment.id)
            )
            failed_id_verification = self._get_failed_identity_verification_user_count(
                deployment.id
            )
            completed_users = self._get_completed_user_count(deployment.id)
            withdraw_consent_users = self._get_withdraw_concent_user_count(
                deployment.id
            )
            manual_off_boarded_users = self._get_manual_off_boarded_user_count(
                deployment.id
            )

            per_deployment_signed_up[deployment.id] = signed_up_users
            per_deployment_refused_consent[deployment.id] = refused_consented_users
            per_deployment_failed_id_verification[
                deployment.id
            ] = failed_id_verification
            per_deployment_all_tasks_completed_offboarded[
                deployment.id
            ] = completed_users
            per_deployment_withdraw_consent[deployment.id] = withdraw_consent_users
            per_deployment_manual_off_boarded[deployment.id] = manual_off_boarded_users

            enabled_modules = self._get_deployment_enabled_modules(deployment)
            users = self._retrieve_users_with_filter(deployment.id, {})
            completed_count_module[deployment.id] = defaultdict(int)
            for module in enabled_modules:
                enabled_modules_deployments.add(module[MODULE_ID])
                if module[MODULE_ID] == EConsentModule.name:
                    # special workaround for econsent in order not to query db for every user
                    completed_count_module[deployment.id][
                        module[MODULE_ID]
                    ] = self._get_deployment_consented_users_count(deployment)
                    continue

                for user in users:
                    authz_user = AuthorizedUser(user=user, deployment_id=deployment.id)
                    is_module_completed = module["module_class"]().is_module_completed(
                        authz_user
                    )
                    if not is_module_completed:
                        continue

                    completed_count_module[deployment.id][
                        module[MODULE_ID]
                    ] += is_module_completed

            if enabled_modules_deployments != {m[MODULE_ID] for m in enabled_modules}:
                same_configs = False

        if not same_configs:
            self.gadget.metadata = {
                "displayOptions": {
                    "blurred": True,
                    "errorMessage": OverallViewGadgetLocalization.DIFFERENT_CONFIGS.key,
                }
            }
            return

        for deployment in deployments:
            enabled_modules = self._get_deployment_enabled_modules(deployment)
            for module_name in GADGET_ENABLED_MODULE_NAMES:
                module_in_deployment = list(
                    filter(lambda x: x[MODULE_ID] == module_name, enabled_modules)
                )
                if module_name not in completed_count_module[deployment.id]:
                    if module_in_deployment:
                        completed_count_module[deployment.id][module_name] = 0
                    else:
                        completed_count_module[deployment.id][module_name] = None

            completed_count_module[deployment.id][
                "total_signed_up"
            ] = per_deployment_signed_up.get(deployment.id)

        self._push_signed_up(sum(per_deployment_signed_up.values()))

        total_sign_ups = sum(per_deployment_signed_up.values())
        if not total_sign_ups:
            return

        if IdentityVerificationModule.name in enabled_modules_deployments:
            self._push_identity_verification_data(
                total_sign_ups,
                sum(per_deployment_failed_id_verification.values()),
                completed_count_module,
            )

        if EConsentModule.name in enabled_modules_deployments:
            self._push_consented_data(
                total_sign_ups,
                sum(per_deployment_refused_consent.values()),
                completed_count_module,
            )

        self._push_completed_data(
            total_sign_ups,
            sum(per_deployment_all_tasks_completed_offboarded.values()),
            sum(per_deployment_manual_off_boarded.values()),
            sum(per_deployment_withdraw_consent.values()),
            completed_count_module,
        )

        self._set_gadget_info_fields(total_sign_ups)

    def _get_deployment_enabled_modules(self, deployment: Deployment) -> list[dict]:
        module_class_mapping = {m.name: m for m in BoardingManager.default_modules}
        if not deployment.onboardingConfigs:
            return []

        modules = [
            {
                MODULE_ID: m.onboardingId,
                "order": m.order,
                "module_class": module_class_mapping.get(m.onboardingId),
            }
            for m in deployment.onboardingConfigs
            if m.is_enabled() and m.onboardingId in GADGET_ENABLED_MODULE_NAMES
        ]
        return sorted(modules, key=itemgetter("order"))

    def _get_deployments(self, organization: Organization) -> list[Deployment]:
        deployment_ids = self.config.deploymentIds or organization.deploymentIds
        return self.deployment_repo.retrieve_deployments_by_ids(deployment_ids)

    def _populate_initial_gadget_fields(self):
        self.gadget.metadata = {
            "chart": {
                "x": {"bars": []},
                "y": {"min": 0, "max": 100},
                "tooltip": {},
            }
        }
        self.gadget.id = self.gadget.type
        self.gadget.title = OverallViewGadgetLocalization.TITLE.key
        self.gadget.tooltip = OverallViewGadgetLocalization.TOOLTIP.key
        self.gadget.data = []

    def _set_gadget_info_fields(
        self,
        total_signed_up: int,
    ):
        drop_off_rate_percentage = (
            sum(self.overhead_values.values()) * 100 / total_signed_up
        )
        drop_off_rate_percentage = self._round_and_format_num(drop_off_rate_percentage)
        prev_value = 0
        prev_module = ""
        module_before_max = ""
        max_module = ""
        for module_name, value in self.overhead_values.items():
            if value > prev_value:
                prev_value = value
                max_module = module_name
                module_before_max = prev_module
            else:
                prev_module = module_name

        self.gadget.infoFields = [
            {
                "name": OverallViewGadgetLocalization.TOTAL_PARTICIPANTS.key,
                "value": format_text_to_bold(total_signed_up),
            },
            {
                "name": OverallViewGadgetLocalization.CURRENT_DROP_OFF.key,
                "value": format_text_to_bold(f"{drop_off_rate_percentage}%"),
            },
            {
                "name": OverallViewGadgetLocalization.LARGEST_DROP_OFF.key,
                "value": f"<strong> {OverallViewGadgetLocalization.BETWEEN.key} {module_before_max} {OverallViewGadgetLocalization.AND.key} {max_module} </strong>",
            },
        ]

        for module_name in self.overhead_values.keys():
            self.gadget.metadata["chart"]["x"]["bars"].append(module_name)

    @staticmethod
    def _round_and_format_num(num):
        return remove_trailing_zero_in_decimal(round_half_up(num, 1))

    def _push_completed_data(
        self,
        total_signed_up: int,
        total_completed: int,
        manual_off_boarded: int,
        withdraw_consent: int,
        completed_modules_data: dict,
    ):
        dropped_out = manual_off_boarded + withdraw_consent
        total_completed_percentage = total_completed * 100 / total_signed_up
        dropped_out_percentage = dropped_out * 100 / total_signed_up
        manual_off_boarded_percentage = manual_off_boarded * 100 / total_signed_up
        withdraw_consent_percentage = withdraw_consent * 100 / total_signed_up

        self.overhead_values[OverallViewGadgetLocalization.COMPLETED.key] = (
            withdraw_consent + manual_off_boarded
        )

        passed_modules_users_count = 0
        for deployment_id in completed_modules_data:
            user_passed = [
                v
                for k, v in completed_modules_data[deployment_id].items()
                if v is not None
            ]
            if user_passed:
                passed_modules_users_count += max(user_passed) - min(user_passed)

        have_not_completed_study = (
            total_signed_up
            - total_completed
            - manual_off_boarded
            - withdraw_consent
            - passed_modules_users_count
        )
        have_not_completed_study_percentage = (
            have_not_completed_study * 100 / total_signed_up
        )

        self.gadget.data.append(
            {
                OverallViewData.X: OverallViewGadgetLocalization.COMPLETED.key,
                OverallViewData.Y: f"{self._round_and_format_num(total_completed_percentage)}%",
                OverallViewData.Y2: total_completed,
                OverallViewData.Y3: f"{self._round_and_format_num(dropped_out_percentage)}%",
                OverallViewData.Y4: dropped_out,
            }
        )
        self.gadget.metadata["chart"]["tooltip"][
            OverallViewGadgetLocalization.COMPLETED.key
        ] = [
            {
                "name": OverallViewGadgetLocalization.COMPLETED.key,
                "value": f"{self._round_and_format_num(total_completed_percentage)}%",
                "header": True,
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_HAVE_NOT_COMPLETED_STUDY.key,
                "value": f"{self._round_and_format_num(have_not_completed_study_percentage)}%",
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_WITHDREW_CONSENT.key,
                "value": f"{self._round_and_format_num(withdraw_consent_percentage)}%",
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_MANUAL_OFF_BOARDED.key,
                "value": f"{self._round_and_format_num(manual_off_boarded_percentage)}%",
            },
        ]

    def _push_identity_verification_data(
        self,
        total_signed_up: int,
        failed_id_verification: int,
        completed_modules_data: dict,
    ):
        if not total_signed_up:
            return

        total_id_verified = sum(
            [
                c.get(IdentityVerificationModule.name, 0)
                for c in completed_modules_data.values()
                if c.get(IdentityVerificationModule.name)
            ]
        )

        id_verified_percentage = total_id_verified * 100 / total_signed_up
        failed_percentage = failed_id_verification * 100 / total_signed_up
        self.overhead_values[
            OverallViewGadgetLocalization.ID_VERIFIED.key
        ] = failed_id_verification

        have_not_completed = (
            total_signed_up - total_id_verified - failed_id_verification
        )
        have_not_completed_percentage = have_not_completed * 100 / total_signed_up
        self.gadget.data.append(
            {
                OverallViewData.X: OverallViewGadgetLocalization.ID_VERIFIED.key,
                OverallViewData.Y: f"{self._round_and_format_num(id_verified_percentage)}%",
                OverallViewData.Y2: total_id_verified,
                OverallViewData.Y3: f"{self._round_and_format_num(failed_percentage)}%",
                OverallViewData.Y4: failed_id_verification,
            }
        )
        self.gadget.metadata["chart"]["tooltip"][
            OverallViewGadgetLocalization.ID_VERIFIED.key
        ] = [
            {
                "name": OverallViewGadgetLocalization.ID_VERIFIED.key,
                "value": f"{self._round_and_format_num(id_verified_percentage)}%",
                "header": True,
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_FAILED_ID_VERIFICATION.key,
                "value": f"{self._round_and_format_num(failed_percentage)}%",
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_NOT_COMPLETED_ID_VERIFICATION.key,
                "value": f"{self._round_and_format_num(have_not_completed_percentage)}%",
            },
        ]

    def _push_signed_up(self, total_signed_up: int):
        self.gadget.metadata["chart"]["tooltip"][
            OverallViewGadgetLocalization.SIGNED_UP.key
        ] = [
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_COMPLETED_SIGN_UP.key,
                "value": "100%",
                "header": True,
            }
        ]
        self.gadget.data.append(
            {
                OverallViewData.X: OverallViewGadgetLocalization.SIGNED_UP.key,
                OverallViewData.Y: 100,  # always 100 -> hardcoded
                OverallViewData.Y2: total_signed_up,
                OverallViewData.Y3: 0,  # always 0 -> hardcoded
                OverallViewData.Y4: 0,  # always 0 -> hardcoded
            }
        )

    def _push_consented_data(
        self,
        total_signed_up: int,
        refused_consented: int,
        completed_modules_data: dict,
    ):
        if not total_signed_up:
            return
        total_consented = sum(
            [
                c.get(EConsentModule.name, 0)
                for c in completed_modules_data.values()
                if c.get(EConsentModule.name)
            ]
        )
        reached_consented_module = 0
        for deployment_id in completed_modules_data:
            for module_name in completed_modules_data[deployment_id]:
                if (
                    module_name == EConsentModule.name
                    and completed_modules_data[deployment_id][module_name] is None
                ):
                    reached_consented_module += completed_modules_data[deployment_id][
                        "total_signed_up"
                    ]
                    break
                elif module_name not in {EConsentModule.name, "total_signed_up"}:
                    reached_consented_module += (
                        completed_modules_data[deployment_id][module_name] or 0
                    )
                elif module_name == EConsentModule.name:
                    break

        consented_percentage = total_consented * 100 / total_signed_up
        refused_percentage = refused_consented * 100 / total_signed_up
        have_not_consented = (
            reached_consented_module - (total_consented + refused_consented)
            if reached_consented_module
            else 0
        )
        have_not_consented_percentage = have_not_consented * 100 / total_signed_up

        self.overhead_values[
            OverallViewGadgetLocalization.CONSENTED.key
        ] = refused_consented

        self.gadget.data.append(
            {
                OverallViewData.X: OverallViewGadgetLocalization.CONSENTED.key,
                OverallViewData.Y: f"{self._round_and_format_num(consented_percentage)}%",
                OverallViewData.Y2: total_consented,
                OverallViewData.Y3: f"{self._round_and_format_num(refused_percentage)}%",
                OverallViewData.Y4: refused_consented,
            }
        )
        self.gadget.metadata["chart"]["tooltip"][
            OverallViewGadgetLocalization.CONSENTED.key
        ] = [
            {
                "name": OverallViewGadgetLocalization.CONSENTED.key,
                "value": f"{self._round_and_format_num(consented_percentage)}%",
                "header": True,
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_REFUSED_CONSENT.key,
                "value": f"{self._round_and_format_num(refused_percentage)}%",
            },
            {
                "name": OverallViewGadgetLocalization.TOOLTIP_HAVE_NOT_CONSENTED.key,
                "value": f"{self._round_and_format_num(have_not_consented_percentage)}%",
            },
        ]

    def _get_deployment_signed_users_count(self, deployment_id) -> int:
        return len(self.auth_repo.retrieve_user_profiles(deployment_id, "")[0])

    def _get_deployment_consented_users_count(self, deployment: Deployment) -> int:
        if not deployment.econsent:
            return 0
        consented = self.econsent_repo.retrieve_consented_users_count(
            econsent_id=deployment.econsent.id
        )
        return sum(consented.values())

    def _retrieve_users_with_filter(self, deployment_id: str, query_filter: dict):
        users = self.auth_repo.retrieve_user_profiles(
            deployment_id, "", filters=query_filter
        )[0]
        return users

    def _get_users_count_with_off_boarding_reason(
        self, deployment_id: str, reason: BoardingStatus.ReasonOffBoarded
    ):
        filters = {
            f"{User.BOARDING_STATUS}.{BoardingStatus.REASON_OFF_BOARDED}": reason
        }
        return self._retrieve_users_with_filter(deployment_id, filters)

    def _get_deployment_refused_consented_users_count(self, deployment_id) -> int:
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_UNSIGNED_EICF
            )
        )

    def _get_failed_pre_screened_user_count(self, deployment_id):
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_FAIL_PRE_SCREENING
            )
        )

    def _get_failed_identity_verification_user_count(self, deployment_id):
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_FAIL_ID_VERIFICATION
            )
        )

    def _get_completed_user_count(self, deployment_id):
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
            )
        )

    def _get_manual_off_boarded_user_count(self, deployment_id):
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED
            )
        )

    def _get_withdraw_concent_user_count(self, deployment_id):
        return len(
            self._get_users_count_with_off_boarding_reason(
                deployment_id, BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF
            )
        )
