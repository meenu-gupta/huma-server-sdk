import csv
import os
from pathlib import Path
from typing import Union, Any

import ujson as json
from bson import ObjectId
from jsonpath_ng import parse
from tomlkit._utils import merge_dicts

from extensions.authorization.models.user import User
from extensions.authorization.models.user_fields_converter import UserFieldsConverter
from extensions.common.s3object import S3Object, FlatBufferS3Object
from extensions.deployment.exceptions import DeploymentDoesNotExist
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.export_deployment.models.export_deployment_models import (
    USER_EXCLUDE_FIELDS,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive, QuestionnaireAnswer
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import hash_value, remove_none_values

PrimitiveData = dict
ModuleId = str
ModuleData = list[PrimitiveData]
ExportData = dict[ModuleId, ModuleData]
UserId = str
UserData = dict
UsersData = dict[UserId, UserData]
ConsentsData = dict[UserId, ConsentLog]
EConsentsData = dict[UserId, EConsentLog]
Version = int
ModuleConfigId = str
ModuleConfigVersions: dict[ModuleId, dict[ModuleConfigId, dict[Version, ModuleConfig]]]

DEFAULT_INCLUDED_FIELDS = [
    Primitive.MODULE_ID,
    Primitive.CREATE_DATE_TIME,
    Primitive.USER_ID,
]


@autoparams("file_storage")
def download_object_to_folder(
    bucket: str,
    key: str,
    target_directory: Union[str, Path],
    file_storage: FileStorageAdapter,
):
    """Saves File Object from storage into specified directory"""
    filename = key.split("/")[-1]
    data, length, content_type = file_storage.download_file(bucket, key)
    os.makedirs(target_directory, exist_ok=True)
    with open(f"{target_directory}/{filename}", "wb") as result_file:
        result_file.write(data.read())
    return target_directory, filename


def convert_id_fields_to_string(data):
    if isinstance(data, dict):
        for field in data:
            data[field] = convert_id_fields_to_string(data[field])
    if isinstance(data, list):
        data = [convert_id_fields_to_string(item) for item in data]
    if isinstance(data, ObjectId):
        data = str(data)
    return data


def get_primitive_dict(primitive: Primitive) -> dict:
    """Converts primitive object to dictionary and convert ObjectIds"""
    data = primitive.to_dict(
        ignored_fields=(
            Primitive.USER_ID,
            Primitive.DEPLOYMENT_ID,
            Primitive.SUBMITTER_ID,
        )
    )

    data[Primitive.CLS] = primitive.__class__.__name__
    return convert_id_fields_to_string(data)


def binary_is_none(binary_option):
    return binary_option == ExportRequestObject.BinaryDataOption.NONE


def binary_is_include(binary_option):
    return binary_option == ExportRequestObject.BinaryDataOption.BINARY_INCLUDE


def binary_is_url(binary_option):
    return binary_option == ExportRequestObject.BinaryDataOption.SIGNED_URL


def layer_is_flat(layer):
    return layer == ExportRequestObject.DataLayerOption.FLAT


def layer_is_nested(layer):
    return layer == ExportRequestObject.DataLayerOption.NESTED


def quantity_is_multiple(quantity):
    return quantity == ExportRequestObject.DataQuantityOption.MULTIPLE


def quantity_is_single(quantity):
    return quantity == ExportRequestObject.DataQuantityOption.SINGLE


def view_is_user(view):
    return view == ExportRequestObject.DataViewOption.USER


def view_is_module(view):
    return view == ExportRequestObject.DataViewOption.MODULE_CONFIG


def view_is_day(view):
    return view == ExportRequestObject.DataViewOption.DAY


def view_is_single(view):
    return view == ExportRequestObject.DataViewOption.SINGLE


def export_format_is_json(format_option):
    return format_option == ExportRequestObject.DataFormatOption.JSON


def export_format_requires_json(format_option):
    return data_formats.JSON in EXPORT_FORMATS.get(format_option)


def export_format_requires_csv(format_option):
    return data_formats.CSV in EXPORT_FORMATS.get(format_option)


def translation_format_is_json(format_option):
    return format_option == ExportRequestObject.DataFormatOption.JSON


def export_format_is_csv(format_option):
    return format_option == ExportRequestObject.DataFormatOption.CSV


def export_format_is_json_plus_csv(format_option):
    return format_option == ExportRequestObject.DataFormatOption.JSON_CSV


def fill_index_file(index_file_dir, new_file_name):
    """Adding new filename to index file"""
    with open(f"{index_file_dir}/index.txt", "a") as index_file:
        index_file.write(new_file_name + "\n")


def write_json_data(
    data: Union[dict, list], file_directory: Union[str, Path], file_name: str
):
    os.makedirs(file_directory, exist_ok=True)
    formatted_filename = f"{file_name}.json"
    with open(f"{file_directory}/{formatted_filename}", "w") as resp_f:
        resp_f.write(json.dumps(data, indent=4, escape_forward_slashes=False))
    fill_index_file(file_directory, formatted_filename)


def convert_flat_dict_to_csv_format(
    res_data: Union[list, dict[str, list]]
) -> list[list]:
    if type(res_data) is list:
        res_data = {"data": res_data}

    keys = []
    for key, data in res_data.items():
        # get all keys in json objects
        for i in range(0, len(data)):
            for j in data[i]:
                if j not in keys:
                    keys.append(j)

    # map data in each row to key index
    converted = [keys]
    for key, data in res_data.items():
        for i in range(0, len(data)):
            row = []
            for j in range(0, len(keys)):
                if keys[j] in data[i]:
                    row.append(f"{data[i][keys[j]]}")
                else:
                    row.append(None)
            converted.append(row)

    return converted


def write_csv_data(data: list, file_directory: Union[str, Path], file_name: str):
    os.makedirs(file_directory, exist_ok=True)
    formatted_filename = f"{file_name}.csv"
    with open(f"{file_directory}/{formatted_filename}", "w") as f:
        writer = csv.writer(f)
        converted_data = convert_flat_dict_to_csv_format(data.copy())
        writer.writerows(converted_data)
    fill_index_file(file_directory, formatted_filename)


def merge_csv_file_data(data: dict[str, dict[str, list[dict]]]):
    all_dicts = []
    for view, modules in data.items():
        for module_name, primitives in modules.items():
            all_dicts.extend(primitives)
    return all_dicts


def flat_text_choice_without_question(answer_dict: dict) -> dict:
    result = {}

    choices = answer_dict.get("answerChoices", [])
    answer_text = answer_dict.get("answerText")
    answer_text = answer_text or get_answer_text_from_choices(choices)

    remaining_options = [a for a in answer_text.split(",") if a]
    current_opt = ""
    for i in range(len(remaining_options)):
        opt = remaining_options[i]
        next_opt = None if i >= len(remaining_options) - 1 else remaining_options[i + 1]
        if next_opt and next_opt[0] == " ":
            if current_opt == "":
                current_opt += f"{opt}"
            else:
                current_opt += f",{opt}"
        else:
            if len(current_opt) > 0:
                result[
                    f"{answer_dict['question'].strip()} ({(current_opt + ',' + opt).strip()})"
                ] = "selected"
                current_opt = ""
            else:
                result[
                    f"{answer_dict['question'].strip()} ({opt.strip()})"
                ] = "selected"

    return result


def get_answer_text_from_choices(choices: list[dict]):
    answers = [c["text"] for c in choices if c["selected"]]
    return ",".join(answers)


def flat_text_choice_answer(question_dict: dict, answer_dict: dict) -> dict:
    result = {}

    # guarding wrong format
    first_question = question_dict["items"][0]
    format_is_textchoice = first_question["format"] == "TEXTCHOICE"
    if format_is_textchoice and first_question["selectionCriteria"] == "SINGLE":
        return flat_single_choice_answer(question_dict, answer_dict)
    if not format_is_textchoice or first_question["selectionCriteria"] != "MULTIPLE":
        raise RuntimeError

    question_text = first_question["text"].strip()
    question_options = first_question["options"]

    choices = answer_dict.get("answerChoices", [])
    answer_text = answer_dict.get("answerText")
    answer_text = answer_text or get_answer_text_from_choices(choices)

    for opt in question_options:
        label = opt["label"]
        if answer_text.find(label) != -1:
            result[f"{question_text.strip()} ({label.strip()})"] = "selected"
            answer_text = answer_text.replace(label, "")
        else:
            result[f"{question_text.strip()} ({label.strip()})"] = "not selected"

    merge_dicts(result, flat_text_choice_without_question(answer_dict))
    return result


def flat_single_choice_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    format_not_textchoice = first_question["format"] != "TEXTCHOICE"
    criteria_is_single = first_question["selectionCriteria"] == "SINGLE"
    if format_not_textchoice and criteria_is_single:
        raise RuntimeError

    choices = answer_dict.get("answerChoices", [])
    answer_text = answer_dict.get("answerText")
    answer_text = answer_text or get_answer_text_from_choices(choices)
    return {answer_dict["question"].strip(): answer_text.strip()}


def flat_boolean_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    if first_question["format"] != "BOOLEAN":
        raise RuntimeError

    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_text_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    if first_question["format"] != "TEXT":
        raise RuntimeError

    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_numeric_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    if first_question["format"] != "NUMERIC":
        raise RuntimeError

    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_scale_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    if first_question["format"] != "SCALE":
        raise RuntimeError

    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_date_answer(question_dict: dict, answer_dict: dict) -> dict:
    first_question = question_dict["items"][0]
    if first_question["format"] != "DATE":
        raise RuntimeError

    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_unknown_answer(answer_dict: dict) -> dict:
    return {
        f'{answer_dict["question"].strip()}': f'{answer_dict["answerText"].strip()}'
    }


def flat_questionnaire(
    questionnaire_dict: dict, answers: list, extra_question_ids: dict = None
) -> dict:
    if not answers:
        raise ValueError
    result = {}
    questions_type_func = {
        "DATE": flat_date_answer,
        "SCALE": flat_scale_answer,
        "TEXT": flat_text_answer,
        "BOOLEAN": flat_boolean_answer,
        "TEXTCHOICE": flat_text_choice_answer,
        "NUMERIC": flat_numeric_answer,
        "TEXTCHOICE_MULTIPLE": flat_text_choice_without_question,  # hack around issues with questionnaire history
    }
    questions_func = {}
    questions_dict = {}
    pages = questionnaire_dict["pages"] if "pages" in questionnaire_dict else []
    for page in pages:
        if page["type"] == "QUESTION":
            fmt = page["items"][0]["format"]
            func = questions_type_func[fmt]
            questions_func[page["items"][0]["id"]] = func
            questions_dict[page["items"][0]["id"]] = page

    for answer in answers:
        question_id = answer["questionId"]
        func = questions_func.get(question_id)
        if func is None and extra_question_ids is not None:
            t = extra_question_ids.get(question_id)
            special_flat_question = questions_type_func.get(t)
            if t is not None and special_flat_question is not None:
                merge_dicts(result, special_flat_question(answer))
                continue
        question_dict = questions_dict.get(question_id)

        if func and question_dict:
            merge_dicts(result, func(question_dict, answer))
        else:
            merge_dicts(result, flat_unknown_answer(answer))

    return result


def flat_symptoms(symptoms_dict: dict, symptoms_result: dict) -> dict:
    result = {}

    # guarding wrong format
    symptoms = symptoms_result.pop("complexValues")
    if symptoms is None:
        raise RuntimeError

    missing_symptoms = symptoms_dict.get("complexSymptoms")
    for symptom in symptoms:
        name = symptom["name"]
        severity = str(symptom["severity"])
        result[name] = severity

    if missing_symptoms is not None:
        for missing_symptom in missing_symptoms:
            name = missing_symptom["name"]
            if name not in result:
                result[name] = "not selected"

    return result


data_formats = ExportRequestObject.DataFormatOption
EXPORT_FORMATS = {
    data_formats.JSON: (data_formats.JSON,),
    data_formats.CSV: (data_formats.CSV,),
    data_formats.JSON_CSV: (data_formats.CSV, data_formats.JSON),
}


def get_object_fields(primitive: Primitive):
    return [
        field_name
        for field_name in primitive.__dict__
        if type(primitive.__dict__[field_name]) is S3Object
    ]


def get_flatbuffer_fields(primitive: Primitive):
    return [
        field_name
        for field_name in primitive.__dict__
        if type(primitive.__dict__[field_name]) is FlatBufferS3Object
    ]


def flatten_object(item: Any, parent_field_name=None):
    for key in list(item):
        value = item.pop(key)
        field_name = f"{parent_field_name}.{key}" if parent_field_name else key
        if type(value) is dict:
            flatten_data = flatten_object(value.copy(), field_name)
            merge_dicts(item, flatten_data)
            continue
        item[field_name] = value
    return item


@autoparams("export_repo")
def get_consent_data(deployment: Deployment, export_repo: ExportDeploymentRepository):
    if not deployment.consent:
        return
    consent_logs = export_repo.retrieve_consent_logs(consent_id=deployment.consent.id)
    return {log.userId: log for log in consent_logs}


@autoparams("export_repo")
def get_econsent_data(deployment: Deployment, export_repo: ExportDeploymentRepository):
    if not deployment.econsent:
        return
    econsent_logs = export_repo.retrieve_econsent_logs(
        econsent_id=deployment.econsent.id
    )
    return {log.userId: log for log in econsent_logs}


@autoparams("export_repo", "deployment_repo")
def get_consents_meta_data(
    deployment_id: str,
    export_repo: ExportDeploymentRepository,
    deployment_repo: DeploymentRepository,
):
    try:
        deployment = deployment_repo.retrieve_deployment(deployment_id=deployment_id)
    except DeploymentDoesNotExist:
        return None, None
    consent_meta = get_consent_data(deployment, export_repo)
    econsent_meta = get_econsent_data(deployment, export_repo)
    return consent_meta, econsent_meta


@autoparams("export_repo")
def get_consents_meta_data_with_deployment(
    deployment: Deployment,
    export_repo: ExportDeploymentRepository,
):
    consent_meta = get_consent_data(deployment, export_repo)
    econsent_meta = get_econsent_data(deployment, export_repo)
    return consent_meta, econsent_meta


@autoparams("export_repo")
def retrieve_users_data(
    data: ExportData,
    users_data: UsersData,
    deployment: Deployment,
    consents_data: ConsentsData,
    econsents_data: EConsentsData,
    include_null_fields: bool,
    export_repo: ExportDeploymentRepository,
):
    """Uses already existing "users_data" or fills it with missing users data"""
    user_ids = set()
    for module_name, primitive_dicts in data.items():
        for primitive_dict in primitive_dicts:
            user_ids.add(primitive_dict[Primitive.USER_ID])
    existing_user_ids = users_data.keys()
    new_user_ids = [uid for uid in user_ids if uid not in existing_user_ids]
    if not new_user_ids:
        return
    users = export_repo.retrieve_users(user_ids=new_user_ids)
    for user in users:
        users_data[user.id] = generate_user_metadata(
            user, deployment, consents_data, econsents_data, include_null_fields
        )


def flatten_data(data: ExportData):
    for module_name, primitive_dicts in data.items():
        for primitive_dict in primitive_dicts:
            flatten_object(primitive_dict)


def exclude_fields(data: ExportData, fields_to_exclude: list[str]):
    if not fields_to_exclude:
        return data
    for field in fields_to_exclude:
        mask = f"*.[*].{field}"
        expression = parse(mask)
        matches = expression.find(data)
        for match in matches:
            try:
                del match.context.value[match.path.__str__()]
            except KeyError:  # to avoid exception when deleting already deleted
                continue


def attach_users_data(data: ExportData, users_data: UsersData):
    for module_name, primitive_dicts in data.items():
        for primitive_dict in primitive_dicts:
            user_dict = users_data.get(primitive_dict[Primitive.USER_ID])
            primitive_dict["user"] = user_dict.copy()


def generate_user_metadata(
    user: User,
    deployment: Deployment,
    consents_data: ConsentsData,
    econsents_data: EConsentsData,
    include_null_fields: bool,
):
    # excluding from extra converting unused fields
    [setattr(user, f, None) for f in USER_EXCLUDE_FIELDS]
    user_meta = UserFieldsConverter(user, deployment, deployment.language).to_dict(
        include_none=include_null_fields
    )
    consent_meta_dict = get_user_consent_meta_dict(consents_data, user_meta[User.ID])
    econsent_meta_dict = get_user_econsent_meta_dict(econsents_data, user_meta[User.ID])
    user_meta["consent"] = consent_meta_dict
    user_meta["econsent"] = econsent_meta_dict
    if include_null_fields:
        return user_meta
    return remove_none_values(user_meta)


def deidentify_dict(
    data: dict,
    fields_to_exclude: list[str],
    deidentify: bool,
    deidentify_exclude_fields: list[str],
    deidentify_hash_fields: list[str],
):
    if not type(data) is dict:
        return
    for field in list(data):
        if fields_to_exclude and field in fields_to_exclude:
            del data[field]
            continue
        if not deidentify:
            continue
        if field in deidentify_exclude_fields:
            data[field] = None
            continue
        if type(data[field]) is dict:
            deidentify_dict(
                data[field],
                fields_to_exclude,
                deidentify,
                deidentify_exclude_fields,
                deidentify_hash_fields,
            )
            continue
        if field in deidentify_hash_fields and data[field]:
            data[field] = hash_value(data[field])
            continue
        if type(data[field]) is list:
            for val in data[field]:
                deidentify_dict(
                    val,
                    fields_to_exclude,
                    deidentify,
                    deidentify_exclude_fields,
                    deidentify_hash_fields,
                )


def get_user_consent_meta_dict(consents_meta: dict[str, ConsentLog], user_id: str):
    if consents_meta is None:
        return
    ignored_fields = [ConsentLog.ID, ConsentLog.USER_ID, ConsentLog.CONSENT_ID]
    data = consents_meta.get(user_id)
    if not data:
        return
    consent_meta_dict = consents_meta.get(user_id).to_dict(
        ignored_fields=ignored_fields
    )
    return consent_meta_dict


def get_user_econsent_meta_dict(econsents_meta: dict[str, EConsentLog], user_id: str):
    if not econsents_meta:
        return
    ignored_fields = [EConsentLog.ID, EConsentLog.USER_ID, EConsentLog.ECONSENT_ID]
    data = econsents_meta.get(user_id)
    if not data:
        return
    enconsent_meta_dict = data.to_dict(ignored_fields=ignored_fields)
    return enconsent_meta_dict


def filter_users_based_on_consent(
    users: list[User], consents_meta: dict[str, ConsentLog]
) -> list[User]:
    # meta is None means deployment has no consent
    if consents_meta is None:
        return users
    # skipping user if he haven't signed the deployment's consent
    return [user for user in users if user.id in consents_meta]


def merge_module_results(d1, d2):
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], list):
            d1[k].extend(d2[k])
        else:
            d1[k] = d2[k]
    return d1


def filter_not_included_fields(fields_to_include: list[str], primitive_dict: dict):
    if not fields_to_include:
        return
    # at least these fields should be present in export
    # to successfully export each view
    fields_to_include.extend(DEFAULT_INCLUDED_FIELDS)
    excluded_dict = primitive_dict.copy()
    for field in set(fields_to_include):
        expression = parse(field)
        matches = expression.find(excluded_dict)
        for match in matches:
            del match.context.value[match.path.__str__()]

    retrieve_difference_between_two_objects(primitive_dict, excluded_dict)


def retrieve_difference_between_two_objects(original_object, object_to_filter_out):
    if type(original_object) is dict:
        for field, value in list(original_object.items()):
            if field in object_to_filter_out:
                # do not support nested filtering for now
                del original_object[field]

    elif type(original_object) is list:
        for item in original_object:
            if item in object_to_filter_out:
                original_object.remove(item)


@autoparams("export_repo")
def attach_users(
    consents_data: ConsentsData,
    econsents_data: EConsentsData,
    include_null_fields: bool,
    users_data: UsersData,
    data: ExportData,
    deployment: Deployment,
    export_repo: ExportDeploymentRepository,
):
    if not data:
        return
    retrieve_users_data(
        data,
        users_data,
        deployment,
        consents_data,
        econsents_data,
        include_null_fields,
        export_repo,
    )
    attach_users_data(data, users_data)


def build_module_config_versions(
    module_configs_versions: dict, configs: list[ModuleConfig]
):
    if not configs:
        return
    for config in configs:
        module_configs_versions[config.moduleId][config.id][config.version] = config
        if questionnaire_id := (config.configBody or {}).get("id"):
            module_configs_versions[config.moduleId][questionnaire_id][
                config.version
            ] = config


def replace_answer_text_with_short_codes(
    answers: list[dict], module_config: ModuleConfig
):
    if not module_config or not answers:
        return
    questions = module_config.configBody.get("pages", [])
    short_codes = {
        q["items"][0]["id"]: q["items"][0].get("exportShortCode")
        for q in questions
        if q.get("items")
    }
    if not short_codes:
        return
    for answer in answers:
        short_code = short_codes.get(answer[QuestionnaireAnswer.QUESTION_ID])
        if not short_code:
            continue
        answer[QuestionnaireAnswer.QUESTION] = short_code
