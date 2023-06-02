import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.models.user import User
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.module_result.models.primitives import Primitive
from extensions.publisher.adapters.fhir.fhir_converter_util import (
    get_fhir_templates,
    convert_to_fhir_observation_v4,
    convert_to_fhir_patient_v4,
)
from extensions.publisher.adapters.gcp_fhir_adapter import (
    GCPFHIRAdapter,
    OBSERVATION_DATA,
    PATIENT_DATA,
)
from extensions.tests.publisher.UnitTests.UnitTests.publisher_callback_tests import (
    get_deployment,
    attach_users,
)
from extensions.tests.publisher.UnitTests.UnitTests.sample_data import (
    patient_template_sample,
    sample_blood_pressure,
    sample_blood_glucose_dict,
    sample_weight_dict,
    sample_heart_rate_dict,
    sample_body_temperature_dict,
    sample_user_dict,
    sample_event_dicts,
    sample_gcp_fhir_publisher,
)
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values, utc_date_to_str


class PublisherFHIRTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind(DeploymentRepository, self.deployment_repo)

        inject.clear_and_configure(bind)

    def test_get_fhir_templates_not_exists(self):
        res = get_fhir_templates("xxx")

        self.assertEqual(res, {})

    def test_get_fhir_templates_exists(self):
        res = get_fhir_templates("patient")

        self.assertEqual(res, patient_template_sample)

    def test_convert_to_observation_v4_blood_pressure(self):
        data = convert_to_fhir_observation_v4(sample_blood_pressure)
        self.assertEqual(
            data["component"][0]["valueQuantity"]["value"],
            sample_blood_pressure.systolicValue,
        )
        self.assertEqual(
            data["component"][0]["valueQuantity"]["unit"],
            sample_blood_pressure.systolicValueUnit,
        )
        self.assertEqual(
            data["component"][1]["valueQuantity"]["value"],
            sample_blood_pressure.diastolicValue,
        )
        self.assertEqual(
            data["component"][1]["valueQuantity"]["unit"],
            sample_blood_pressure.diastolicValueUnit,
        )

    def test_convert_to_observation_v4_blood_glucose(self):
        ref_primitive = Primitive.create_from_dict(
            remove_none_values(sample_blood_glucose_dict),
            name="BloodGlucose",
            validate=False,
        )

        data = convert_to_fhir_observation_v4(ref_primitive)
        self.assertEqual(data["valueQuantity"]["value"], ref_primitive.value)
        self.assertEqual(data["valueQuantity"]["unit"], ref_primitive.valueUnit)

    def test_convert_to_observation_v4_weight(self):
        ref_primitive = Primitive.create_from_dict(
            remove_none_values(sample_weight_dict), name="Weight", validate=False
        )

        data = convert_to_fhir_observation_v4(ref_primitive)
        self.assertEqual(data["valueQuantity"]["value"], ref_primitive.value)
        self.assertEqual(data["valueQuantity"]["unit"], ref_primitive.valueUnit)

    def test_convert_to_observation_v4_heart_rate(self):
        ref_primitive = Primitive.create_from_dict(
            remove_none_values(sample_heart_rate_dict), name="HeartRate", validate=False
        )

        data = convert_to_fhir_observation_v4(ref_primitive)
        self.assertEqual(data["valueQuantity"]["value"], ref_primitive.value)
        self.assertEqual(data["valueQuantity"]["unit"], ref_primitive.valueUnit)

    def test_convert_to_observation_v4_body_temperature(self):
        ref_primitive = Primitive.create_from_dict(
            remove_none_values(sample_body_temperature_dict),
            name="Temperature",
            validate=False,
        )

        data = convert_to_fhir_observation_v4(ref_primitive)
        self.assertEqual(data["valueQuantity"]["value"], ref_primitive.value)
        self.assertEqual(data["valueQuantity"]["unit"], ref_primitive.valueUnit)

    def test_convert_to_observation_v4_patient(self):
        user = User.from_dict(sample_user_dict, use_validator_field=False)
        patient_data = convert_to_fhir_patient_v4(user, {})

        self.assertEqual(patient_data["identifier"][0]["value"], user.id)
        self.assertEqual(patient_data["name"][0]["family"], user.familyName)
        self.assertEqual(patient_data["name"][0]["given"][0], user.givenName)
        self.assertEqual(patient_data["gender"], user.gender.value)
        self.assertEqual(patient_data["birthDate"], utc_date_to_str(user.dateOfBirth))

    @patch("extensions.publisher.adapters.utils.get_consents_meta_data_with_deployment")
    @patch(
        "extensions.publisher.adapters.utils.attach_users",
        side_effect=attach_users,
    )
    def test_transform_publisher_data_gcp_fhir(
        self, mocked_attach_users, mocked_get_consents_meta_data
    ):
        mocked_get_consents_meta_data.return_value = None, None

        event = sample_event_dicts[2]
        publisher = sample_gcp_fhir_publisher
        adapter = GCPFHIRAdapter(publisher=publisher)
        adapter.transform_publisher_data(event)

        self.assertEqual(PATIENT_DATA in adapter._message, True)
        self.assertEqual(OBSERVATION_DATA in adapter._message, True)
        self.assertEqual(
            adapter._message[OBSERVATION_DATA]["component"][1]["valueQuantity"][
                "value"
            ],
            event["primitives"][0]["diastolicValue"],
        )


if __name__ == "__main__":
    unittest.main()
