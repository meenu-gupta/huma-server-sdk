import ast
import codecs
import csv
import json
from collections import defaultdict
from copy import copy
from typing import Any, Union, Iterator

from extensions.common.s3object import S3Object
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils import inject


def translate_object(translation_object: Any, short_codes: dict[str, str]):
    if type(translation_object) is str and translation_object.strip() in short_codes:
        return short_codes.get(translation_object.strip())
    if type(translation_object) is list:
        return [translate_object(obj, short_codes) for obj in translation_object]
    if type(translation_object) is dict:
        object_copy = copy(translation_object)
        for key, value in object_copy.items():
            translated_key = translate_object(key, short_codes)
            translated_value = translate_object(value, short_codes)
            if key != translated_key:
                del translation_object[key]
            translation_object[translated_key] = translated_value
    return translation_object


def prepare_short_codes(
    translation_short_codes_object: S3Object, is_json: bool = True, is_csv: bool = False
) -> tuple[dict, dict]:
    """
    Return:
        - [module name -> module id]
        - [module id -> text,keyword]
    Used to download and generate dictionary with translation short codes"""
    if not translation_short_codes_object:
        return {}, {}
    file_storage = inject.instance(FileStorageAdapter)
    object_data, object_length, object_content_type = file_storage.download_file(
        translation_short_codes_object.bucket, translation_short_codes_object.key
    )

    module_codes = {}
    short_codes = defaultdict(dict)

    if is_csv:
        data = csv.DictReader(codecs.iterdecode(object_data, "utf-8"))
    elif is_json:
        data = json.loads(object_data.read())["dictionary"]
    prefill_short_codes(data, module_codes, short_codes)
    return module_codes, short_codes


def prefill_short_codes(
    data: Union[list[dict], Iterator[dict]], module_codes: dict, short_codes: dict
):
    for row in data:
        module_ids = row.get("moduleId")
        if isinstance(module_ids, str) and module_ids:
            if module_ids.startswith("[") and module_ids.endswith("]"):
                module_ids = ast.literal_eval(module_ids)
            else:
                module_ids = [module_ids]
        if module_ids:
            for module_id in module_ids:
                code = row["keyword"]
                raw_value = row["text"].strip()
                short_codes[module_id][raw_value] = code
        else:
            module_code = row["text"].strip()
            module_name = row["keyword"]
            module_codes[module_code] = module_name
