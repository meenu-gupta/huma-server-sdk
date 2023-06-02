from datetime import datetime, timedelta
from unittest import TestCase

from freezegun import freeze_time

from extensions.authorization.models.user import User
from extensions.deployment.boarding.complete_study_tasks_module import (
    CompleteStudyTasksModule,
)
from extensions.deployment.models.deployment import Deployment
from sdk.common.utils.convertible import ConvertibleClassValidationError


class DeploymentDurationTestCase(TestCase):
    def test_success_create_deployment_no_duration(self):
        deployment_dict = {
            "name": "Test Deployment",
        }
        deployment = Deployment.from_dict(deployment_dict)
        self.assertIsNone(deployment.duration)

    def test_failure_create_deployment(self):
        deployment_dict = {
            "name": "Test Deployment",
            "duration": "P6M",
        }
        deployment = Deployment.from_dict(deployment_dict)
        self.assertEqual(deployment_dict["duration"], deployment.duration)

    def test_failure_create_deployment_wrong_duration(self):
        deployment_dict = {
            "name": "Test Deployment",
            "duration": "P2T1S",
        }
        with self.assertRaises(ConvertibleClassValidationError):
            Deployment.from_dict(deployment_dict)

    def test_success_check_deployment_expired(self):
        now = datetime.utcnow()
        with freeze_time(now):
            user = User(createDateTime=now - timedelta(days=7))
            deployment = Deployment(duration="P1M")
            result = CompleteStudyTasksModule.is_user_expired(user, deployment.duration)
            self.assertFalse(result)

    def test_failure_check_deployment_expired(self):
        now = datetime.utcnow()
        with freeze_time(now):
            user = User(createDateTime=now - timedelta(days=50))
            deployment = Deployment(duration="P1M")
            result = CompleteStudyTasksModule.is_user_expired(user, deployment.duration)
            self.assertTrue(result)
