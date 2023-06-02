from datetime import datetime
from typing import Optional

import isodate

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.stats import DeploymentStats as Stats, Stat
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.key_action.models.key_action_log import KeyAction
from extensions.organization.models.organization import ViewType
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.service.calendar_service import CalendarService
from sdk.calendar.utils import get_dt_from_str
from sdk.common.utils.inject import autoparams


class DeploymentStatsCalculator:
    @autoparams()
    def __init__(
        self,
        deployment: Deployment,
        repo: AuthorizationRepository,
        consent_repo: ConsentRepository,
        econsent_repo: EConsentRepository,
        organisation_repo: OrganizationRepository,
    ):
        self.deployment = deployment
        self.now = datetime.utcnow()
        self._user_repo = repo
        self._consent_repo = consent_repo
        self._econsent_repo = econsent_repo
        self._organisation_repo = organisation_repo
        self._service = DeploymentService()

    def run(self) -> Stats:
        task_compliance = {
            Stat.VALUE: self.retrieve_task_compliance_rate(),
            Stat.UNIT: "%",
        }

        view_type = self.retrieve_organisation_view_type()
        if view_type and view_type == ViewType.RPM:
            data = {Stats.PATIENT_COUNT: {Stat.VALUE: self.retrieve_patient_count()}}
            return Stats.from_dict(data)

        data = {
            Stats.COMPLETED_TASK: task_compliance,
            Stats.COMPLETED_COUNT: {Stat.VALUE: self.retrieve_completed_users_count()},
            Stats.ENROLLED_COUNT: {Stat.VALUE: self.retrieve_enrolled_users_count()},
        }
        if (consented_count := self.retrieve_consented_users_count()) is not None:
            data[Stats.CONSENTED_COUNT] = {Stat.VALUE: consented_count}
        return Stats.from_dict(data)

    def retrieve_patient_count(self) -> int:
        return self._user_repo.retrieve_users_count(
            deployment_id=self.deployment.id, role=RoleName.USER
        )

    def retrieve_enrolled_users_count(self) -> int:
        filter_options = {User.FINISHED_ONBOARDING: True}
        return self._user_repo.retrieve_users_count(
            deployment_id=self.deployment.id,
            role=RoleName.USER,
            **filter_options,
        )

    def retrieve_completed_users_count(self):
        if not self.deployment.is_off_boarding_enabled():
            return 0
        duration = isodate.parse_duration(self.deployment.duration)
        to = datetime.utcnow() - duration
        role = RoleName.USER
        return self._user_repo.retrieve_users_count(None, to, self.deployment.id, role)

    def retrieve_consented_users_count(self):
        e_consented = self._retrieve_e_consented_users()

        if e_consented is None:
            return e_consented
        return len(e_consented)

    def _retrieve_consented_users(self) -> Optional[set]:
        if not self.deployment.consent:
            return None

        return self._consent_repo.retrieve_consented_users(
            consent_id=self.deployment.consent.id
        )

    def _retrieve_e_consented_users(self) -> Optional[set]:
        if not self.deployment.econsent:
            return None

        return self._econsent_repo.retrieve_consented_users(
            econsent_id=self.deployment.econsent.id
        )

    def retrieve_task_compliance_rate(self) -> float:
        def is_expired(event):
            return get_dt_from_str(event[CalendarEvent.END_DATE_TIME]) <= self.now

        users = self._retrieve_user_timezones()
        service = CalendarService()
        total_completed = 0
        total_expired = 0
        for user_id, timezone in users.items():
            kwargs = {
                CalendarEvent.USER_ID: user_id,
                CalendarEvent.MODEL: KeyAction.__name__,
                "to_model": False,
            }
            events = service.retrieve_calendar_events_between_two_dates(
                start=self.deployment.createDateTime,
                end=self.now,
                timezone=timezone,
                **kwargs,
            )

            key = CalendarEvent.ENABLED
            completed = tuple(event for event in events if not event.get(key, True))
            expired_events = sum(
                1 for event in events if is_expired(event) or event in completed
            )
            total_completed += len(completed)
            total_expired += expired_events

        return total_completed / total_expired * 100 if total_expired else 0

    def _retrieve_user_timezones(self) -> dict[str, str]:
        role_name = RoleName.USER
        role: RoleAssignment = RoleAssignment.create_role(role_name, self.deployment.id)
        filter_options = {f"{User.ROLES}.resource": role.resource}
        return self._user_repo.retrieve_users_timezones(**filter_options)

    def retrieve_organisation_view_type(self):
        organisation = self._organisation_repo.retrieve_organization_by_deployment_id(
            deployment_id=self.deployment.id
        )
        return organisation.viewType if organisation else organisation
