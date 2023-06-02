import json
import logging
import string
import random

import requests
from flask import g

from extensions.kardia.models.kardia_integration_config import KardiaIntegrationConfig

log = logging.getLogger(__name__)


class KardiaIntegrationClient:
    def __init__(self, config: KardiaIntegrationConfig):
        self._config = config

    def create_kardia_patient(self, email: str, dob: str):
        create_patient_url = self._config.baseUrl + "/v1/patients"
        create_mobile_user_url = self._config.baseUrl + "/v1/users"

        # Create patient
        create_patient_data = {
            "mrn": g.user.id,
            "email": email,
            "firstName": g.user.givenName,
            "lastName": g.user.familyName,
            "dob": dob
        }
        create_patient_response = requests.post(
            create_patient_url, auth=(self._config.apiKey, ""), data=create_patient_data
        )

        if create_patient_response.status_code != 200:
            log.error(f"Create Kardia patient failed with error: {create_patient_response.text}")

        patient_dict = json.loads(create_patient_response.text)

        # Create Kardia mobile user
        password_characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(password_characters) for i in range(12))

        create_mobile_user_data = {
            "email": email,
            "password": password,
            "countryCode": "us",
            "patientId": patient_dict.get("id")
        }
        create_mobile_user_response = requests.post(
            create_mobile_user_url, auth=(self._config.apiKey, ""), data=create_mobile_user_data
        )

        if create_mobile_user_response.status_code != 201:
            log.error(f"Create Kardia mobile user failed with error: {create_mobile_user_response.text}")

        patient_dict["password"] = password

        return patient_dict

    def retrieve_patient_recordings(self, patient_id: str) -> dict:
        url = self._config.baseUrl + "/v1/patients/" + patient_id + "/recordings"

        response = requests.get(
            url, auth=(self._config.apiKey, "")
        )

        if response.status_code != 200:
            log.error(f"Retrieve patient recordings failed with error: {response.text}")

        return json.loads(response.text)

    def retrieve_single_ecg(self, record_id: str) -> dict:
        url = self._config.baseUrl + "/v1/recordings/" + record_id

        response = requests.get(
            url, auth=(self._config.apiKey, "")
        )

        if response.status_code != 200:
            log.error(f"Retrieve single ecg failed with error: {response.text}")

        return json.loads(response.text)

    def retrieve_single_ecg_pdf(self, record_id: str):
        url = self._config.baseUrl + "/v1/recordings/" + record_id + ".pdf"

        response = requests.get(
            url, auth=(self._config.apiKey, "")
        )

        if response.status_code != 200:
            log.error(f"Retrieve single ecg pdf failed with error: {response.text}")

        return response.content
