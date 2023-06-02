from pathlib import Path

from extensions.authorization.callbacks import setup_storage_auth
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.medication.component import MedicationComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.revere.component import RevereComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    BUCKET_NAME,
)
from extensions.tests.test_case import ExtensionTestCase
from extensions.twilio_video.component import TwilioVideoComponent
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter
from sdk.common.utils import inject
from sdk.notification.component import NotificationComponent
from sdk.storage.callbacks.binder import PostStorageSetupEvent
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

CONFIG_PATH = Path(__file__).with_name("config.test.yaml")


class AbstractPermissionTestCase(ExtensionTestCase):
    DEPLOYMENT_KEY = "deploymentId"
    config_file_path = CONFIG_PATH
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        StorageComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        MedicationComponent(),
        RevereComponent(),
        TwilioVideoComponent(),
        ExportDeploymentComponent(),
        NotificationComponent(),
        CalendarComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/users_dump.json"),
        Path(__file__).parent.joinpath("fixtures/organization_dump.json"),
        Path(__file__).parent.joinpath("fixtures/invitation_dump.json"),
    ]

    def setUp(self):
        super().setUp()

        # preparing bucket
        m: MinioFileStorageAdapter = inject.instance(FileStorageAdapter)
        try:
            m._client.remove_bucket(BUCKET_NAME)
        except Exception:
            pass

        try:
            m._client.make_bucket(BUCKET_NAME)
        except Exception:
            pass

        self.test_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)

        self.auth_route = "/api/auth/v1beta"
        self.deployment_route = "/api/extensions/v1beta/deployment"
