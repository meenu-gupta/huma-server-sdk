import json
import os
from pathlib import Path

from extensions.authorization.models.user import User
from extensions.module_result.models.primitives import (
    Primitive,
    BloodPressure,
    BloodGlucose,
    Weight,
    BMI,
    HeartRate,
    Height,
    Temperature,
)

from sdk.common.utils.validators import utc_str_field_to_val, utc_date_to_str

FHIR_TEMPLATE_PATH = "fhir-templates/"


def convert_to_fhir_observation_v4(primitive: Primitive):
    """convert primitive data to fhir v4.0.1 observation format"""

    data = get_fhir_templates(primitive.class_name.lower())
    data["effectiveDateTime"] = utc_str_field_to_val(primitive.startDateTime)

    # finally in the end replace all placeholders in the templates by object values
    replace_all_placeholders(data, primitive)

    return data


def convert_to_fhir_patient_v4(user: User, config: dict):
    """convert user data to fhir v4.0.1 Patient format"""

    patient_data = get_fhir_templates("patient")
    patient_data["gender"] = user.gender.value
    patient_data["birthDate"] = utc_date_to_str(user.dateOfBirth)

    # replace all placeholders
    replace_all_placeholders(patient_data, user)

    # replace identifier from config
    if "identifier" in config:
        for identifier in config["identifier"]:
            replace_all_placeholders(identifier, user)
        patient_data["identifier"] = config["identifier"]

    return patient_data


def replace_all_placeholders(config: dict, obj):
    for key, value in config.items():
        if isinstance(value, dict):
            replace_all_placeholders(value, obj)
        elif isinstance(value, list):
            for i, value2 in enumerate(value):
                if isinstance(value2, dict):
                    replace_all_placeholders(value2, obj)
                else:
                    config[key][i] = format_value(obj, config[key][i])
        else:
            config[key] = format_value(obj, config[key])


def format_value(obj, value: str):
    res = value.format(obj=obj)
    return float(res) if isfloat(res) else res


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def get_fhir_templates(name: str):
    cur_dir = os.path.dirname(__file__)
    file_path = os.path.join(cur_dir, FHIR_TEMPLATE_PATH + name + ".json")
    try:
        with open(file_path) as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {}
