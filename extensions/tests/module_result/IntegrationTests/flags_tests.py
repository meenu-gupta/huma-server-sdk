from datetime import datetime
from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import Step
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.test_samples import sample_steps
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent
from sdk.common.utils.validators import utc_str_field_to_val

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"


class FlagsCalculationLogicTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        ModuleResultComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Step"
    route_result = (
        f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Step/search"
    )

    def get_sample_steps_data(self, value: int, start_date: datetime = None):
        steps_data = sample_steps(value)
        steps_data[Step.START_DATE_TIME] = utc_str_field_to_val(
            start_date or datetime.utcnow()
        )
        return steps_data

    def send_multiple_steps(
        self,
        step_config_id="a844f828a543393adbba0559",
        results=[
            (6000, datetime(2022, 3, 2)),
            (7000, datetime(2022, 3, 4)),
            (33000, datetime(2022, 3, 6)),
            (2000, datetime(2022, 3, 9)),
            (3000, datetime(2022, 3, 10)),
        ],
    ):
        """
        The results are aggregated (weekly) in the Step module. The result of of this
        aggregation with the default result values will be:
        - First week:
          - 6000  --> red, then
          - 13000 --> amber, then
          - 46000 --> gray.
        - Second week:
          - 2000  --> red, then
          - 3000 --> still red
        Therefore, the final result will be gray for the first week and red for the seocnd week
        """
        steps = [
            self.get_sample_steps_data(value=result[0], start_date=result[1])
            for result in results
        ]
        return self.flask_client.post(
            self.route,
            json=steps,
            query_string={"moduleConfigId": step_config_id},
            headers=self.get_headers_for_token(VALID_USER_ID),
        )

    def assertFlags(self, color, primitive, value=1):
        self.assertIn("flags", primitive)
        self.assertEqual(value, primitive["flags"][color])
        self.assertFalse(any([v for k, v in primitive["flags"].items() if k != color]))

    def get_steps(self, count=6, step_config_id="a844f828a543393adbba0559"):
        body = {"direction": "DESC", "limit": count, "moduleConfigId": step_config_id}
        return self.flask_client.post(
            self.route_result,
            json=body,
            query_string={"moduleConfigId": step_config_id},
            headers=self.get_headers_for_token(VALID_USER_ID),
        )

    def test_success_flag_calculation_for_all_steps(self):
        step_config_id = "a844f828a543393adbba0559"
        rsp = self.send_multiple_steps(step_config_id)
        self.assertEqual(201, rsp.status_code)

        steps = self.mongo_database.step.find(
            {Step.USER_ID: ObjectId(VALID_USER_ID)},
            sort=[
                ("flags.red", -1),
                ("flags.amber", -1),
                ("flags.gray", -1),
            ],
        )
        steps = list(steps)

        self.assertEqual(5, len(steps))

        self.assertFlags("red", steps[0])
        self.assertFlags("gray", steps[1])
        for step in steps[2:]:
            self.assertFalse("flags" in step and any(step["flags"].values()))

    def test_success_loading_module_result_with_flags(self):
        step_config_id = "a844f828a543393adbba0559"
        rsp = self.send_multiple_steps(step_config_id)
        self.assertEqual(201, rsp.status_code)

        self.mongo_database.step.update({}, {"$unset": {"flags": ""}})

        rsp = self.get_steps(count=6, step_config_id=step_config_id)
        self.assertEqual(200, rsp.status_code)
        steps = rsp.json["Step"]

        self.assertEqual(5, len(steps))

        self.assertFlags("red", steps[0])
        self.assertFlags("gray", steps[2])
        for step in steps[1:2] + steps[3:]:
            self.assertFalse("flags" in step and any(step["flags"].values()))

    def test_success_adding_steps(self):
        step_config_id = "a844f828a543393adbba0559"
        step_counts = [6000, 7000, 33000]
        flags = ["red", "amber", "gray"]
        for steps, color in zip(step_counts, flags):
            rsp = self.send_multiple_steps(step_config_id, [(steps, datetime.utcnow())])
            self.assertEqual(201, rsp.status_code)

            rsp = self.get_steps(count=6, step_config_id=step_config_id)
            self.assertFlags(color, rsp.json["Step"][0])
            for step in rsp.json["Step"][1:]:
                self.assertFalse("flags" in step and any(step["flags"].values()))
