from datetime import datetime

import pytz

from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveDeploymentKeyActionsRequestObject,
)
from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from extensions.deployment.models.key_action import DeploymentEvent
from extensions.key_action.models.key_action_log import KeyAction
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.models.event_generator import EventGenerator
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveDeploymentKeyActionsUseCase(UseCase):
    request_object: RetrieveDeploymentKeyActionsRequestObject

    @autoparams()
    def __init__(self, repo: DeploymentRepository):
        self.deployment_repo = repo

    def process_request(
        self, request_object: RetrieveDeploymentKeyActionsRequestObject
    ):
        deployment_key_actions = self._get_deployment_key_actions(
            request_object.deploymentId
        )
        events = self._generate_events(deployment_key_actions)
        events = self._make_deployment_events_objects(events)
        return Response(events)

    @staticmethod
    def _make_deployment_events_objects(events: list[dict]) -> list[DeploymentEvent]:
        # we need to pass EXTRA_FIELDS as there we are keeping items like moduleId, moduleConfigId
        # that we need in response payload
        return [
            DeploymentEvent.from_dict({**e, **e[CalendarEvent.EXTRA_FIELDS]})
            for e in events
        ]

    def _get_deployment_key_actions(self, deployment_id: str) -> list[KeyAction]:
        key_actions = self.deployment_repo.retrieve_key_actions(
            deployment_id=deployment_id
        )
        generator = KeyActionGenerator(
            user=None,
            trigger_time=self.request_object.triggerTime,
            deployment_id=deployment_id,
        )
        return [generator.build_key_action_from_config(k) for k in key_actions]

    def _generate_events(self, deployment_key_actions: list[KeyAction]) -> list[dict]:
        event_generator = EventGenerator(
            start=self.request_object.startDate,
            end=self.request_object.endDate,
            timezone=pytz.timezone("UTC"),
        )
        return event_generator.generate(events=deployment_key_actions)
