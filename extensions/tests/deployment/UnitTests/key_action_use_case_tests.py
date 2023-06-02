import unittest
from unittest.mock import MagicMock, patch

import pytz
from freezegun import freeze_time
from freezegun.api import FakeDatetime

from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveDeploymentKeyActionsRequestObject,
)
from extensions.deployment.use_case.retrieve_deployment_key_actions_use_case import (
    RetrieveDeploymentKeyActionsUseCase,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder

VALID_OBJECT_ID = "60019625090d076320280736"
USE_CASE_PATH = (
    "extensions.deployment.use_case.retrieve_deployment_key_actions_use_case"
)


class RetrieveDeploymentKeyActionsUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MagicMock()
        self.deployment_repo = MagicMock()

        def configure_with_binder(binder: Binder):
            binder.bind(DeploymentRepository, self.deployment_repo)

        inject.clear_and_configure(config=configure_with_binder)

    @staticmethod
    def _sample_obj():
        sample_dt = "2019-10-13T00:00:26.255616Z"
        return {
            RetrieveDeploymentKeyActionsRequestObject.DEPLOYMENT_ID: VALID_OBJECT_ID,
            RetrieveDeploymentKeyActionsRequestObject.START_DATE: sample_dt,
            RetrieveDeploymentKeyActionsRequestObject.END_DATE: sample_dt,
        }

    @freeze_time("2012-01-01")
    @patch(f"{USE_CASE_PATH}.EventGenerator")
    @patch(f"{USE_CASE_PATH}.KeyActionGenerator")
    def test_success_execute_retrieve_deployment_key_actions(
        self, key_action_generator, event_generator
    ):
        req_obj = RetrieveDeploymentKeyActionsRequestObject.from_dict(
            self._sample_obj()
        )
        RetrieveDeploymentKeyActionsUseCase().execute(req_obj)
        self.deployment_repo.retrieve_key_actions.assert_called_with(
            deployment_id=VALID_OBJECT_ID
        )
        key_action_generator.assert_called_with(
            user=None,
            trigger_time=FakeDatetime(2012, 1, 1, 0, 0),
            deployment_id=VALID_OBJECT_ID,
        )
        event_generator.assert_called_with(
            start=FakeDatetime(2019, 10, 13, 0, 0, 26, 255616),
            end=FakeDatetime(2019, 10, 13, 0, 0, 26, 255616),
            timezone=pytz.timezone("UTC"),
        )


if __name__ == "__main__":
    unittest.main()
