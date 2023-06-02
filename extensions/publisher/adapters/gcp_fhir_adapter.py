import logging
import json

from google.auth.transport import requests
from google.oauth2 import service_account

from extensions.authorization.models.user import User
from extensions.common.monitoring import report_exception
from extensions.module_result.models.primitives import Primitive
from extensions.publisher.adapters.fhir.fhir_converter_util import (
    convert_to_fhir_observation_v4,
    convert_to_fhir_patient_v4,
)
from extensions.publisher.adapters.publisher_adapter import (
    PublisherAdapter,
)
from extensions.publisher.adapters.utils import transform_publisher_data
from extensions.publisher.models.publisher import Publisher
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values


logger = logging.getLogger(__name__)

OBSERVATION_DATA = "observationData"
PATIENT_DATA = "patientData"


class GCPFHIRAdapter(PublisherAdapter):
    headers = ""
    session = ""
    fhir_store_path = ""

    @autoparams()
    def __init__(self, publisher: Publisher):
        self._publisher = publisher

    def transform_publisher_data(self, event: dict):
        """transform huma data to fhir v4.0.1 compatible format"""

        # TODO we may need to fix some transformation parameters for fhirstore because either we don't need them or
        #  changing them could break something
        self._publisher.transform.includeNullFields = False
        self._publisher.transform.includeUserMetaData = True
        self._publisher.transform.deIdentified = False

        transform_publisher_data(self._publisher, event)

        observation_data = self.convert_to_fhir_observation_json(event)

        patient_data = self.convert_to_fhir_patient_json(
            event, self._publisher.target.gcp_fhir.config
        )

        self._message = {
            OBSERVATION_DATA: observation_data,
            PATIENT_DATA: patient_data,
        }

    def prepare_publisher_data(self, event: dict) -> bool:
        # Gets credentials from the config
        credentials_data = self._publisher.target.gcp_fhir.serviceAccountData
        info = json.loads(credentials_data)

        try:
            credentials = service_account.Credentials.from_service_account_info(info)
        except ValueError as e:
            report_exception(
                error=Exception(e),
                context_name="Publisher",
                context_content={
                    "publisherName": self._publisher.name,
                    "publisherType": self._publisher.target.publisherType,
                },
            )
            return False

        scoped_credentials = credentials.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.session = requests.AuthorizedSession(scoped_credentials)

        self.fhir_store_path = self._publisher.target.gcp_fhir.url

        self.headers = {"Content-Type": "application/fhir+json;charset=utf-8"}

        return True

    def send_publisher_data(self):
        if not self._message:
            return
        # first search if patient exists right now, if not add it
        patient_id = self.search_resource_by_identifier(
            "Patient", self._message[PATIENT_DATA]["identifier"][0]["value"]
        )

        if not patient_id:
            patient_id = self.create_resource("Patient", self._message[PATIENT_DATA])

        subject = {"subject": {"reference": "Patient/" + patient_id}}
        # add it to the subject
        self._message[OBSERVATION_DATA].update(subject)
        self.create_resource("Observation", self._message[OBSERVATION_DATA])

    def send_ping(self):
        pass

    def create_resource(self, resource_name: str, data: dict):
        """
        Creates a new resource_name resource in the Google FHIR store
        """
        response = self.session.post(
            self.fhir_store_path + "/" + resource_name,
            headers=self.headers,
            json=data,
        )
        if response.status_code == 201:
            resource = response.json()
            logger.debug(
                f"Successfully created {resource_name} on Google fhir store with publisher name: {self._publisher.name}"
                f" - with ID: {resource['id']}'"
            )

            return resource["id"]
        else:
            logger.error(
                f"Failed to create {resource_name} on Google fhir store with publisher name: {self._publisher.name}"
                f" with Status: {response.status_code} - Error: {response.text}"
            )
        #     TODO send exception also

        return None

    def search_resource_by_identifier(self, resource_name: str, identifier: str) -> str:
        """
        Search for a resource_name resource by identifier in the Google FHIR store
        return True if it exists or return False if it does not
        """
        response = self.session.get(
            self.fhir_store_path + "/" + resource_name + "?identifier=" + identifier,
            headers=self.headers,
        )
        if response.status_code == 200:
            resource = response.json()
            if resource["total"] == 0:
                return None
            elif resource["total"] == 1:
                return resource["entry"][0]["resource"]["id"]
            else:
                logger.error(
                    f"There should not be multiple resource for {resource_name}"
                    f" with identifier: {identifier} on Google fhir store"
                )
                return resource["entry"][0]["resource"]["id"]
        else:
            logger.error(
                f"Failed to search for {resource_name} on Google fhir store"
                f" with Status: {response.status_code} - Error: {response.text}"
            )
            return None

    @staticmethod
    def convert_to_fhir_observation_json(event: dict):
        primitive_name = event["moduleId"]
        primitive_dict = event["primitives"][0]

        ref_primitive = Primitive.create_from_dict(
            remove_none_values(primitive_dict), name=primitive_name, validate=False
        )
        return convert_to_fhir_observation_v4(ref_primitive)

    @staticmethod
    def convert_to_fhir_patient_json(event: dict, config: dict):
        user_raw = event["primitives"][0]["user"]
        user = User.from_dict(user_raw, use_validator_field=False)
        return convert_to_fhir_patient_v4(user, config)
