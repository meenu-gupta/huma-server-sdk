import json
import os
import subprocess
from datetime import datetime

import pytz

from extensions.common.s3object import FlatBufferS3Object
from extensions.export_deployment.helpers.convertion_helpers import (
    download_object_to_folder,
)
from sdk.common.utils.path_utils import get_libs_path


def _convert_flatbuffer_to_json(
    file_dir, filename, schema_filename, keep_original_file=False
):
    """Allows to convert FlatBuffer binary file to json file"""
    libs_dir = get_libs_path()

    schema = os.path.join(libs_dir, f"flatbuffer/schemas/{schema_filename}")
    flatc_binary = os.path.join(libs_dir, "flatbuffer/flatc")
    subprocess.run(
        [
            flatc_binary,
            "--json",
            "--raw-binary",
            schema,
            "--",
            filename,
            "--strict-json",
        ],
        capture_output=True,
        cwd=file_dir,
    )
    if not keep_original_file:
        os.remove(f"{file_dir}/{filename}")


def ecg_data_points_to_array(s3object: FlatBufferS3Object):
    s3object_dict = s3object.to_dict()
    schema_file = "ecg.fbs"
    libs_dir = get_libs_path()

    flatbuffer_files_dir = os.path.join(libs_dir, "flatbuffer/files")
    file_dir, file_name = download_object_to_folder(
        s3object_dict[FlatBufferS3Object.BUCKET],
        s3object_dict[FlatBufferS3Object.KEY],
        flatbuffer_files_dir,
    )
    _convert_flatbuffer_to_json(file_dir, file_name, schema_file)
    result = None
    file_path = f"{file_dir}/{file_name}.json"
    with open(file_path, "rb") as json_obj:
        data = json.loads(json_obj.read())
        if "voltages" in data:
            result = [item["mcV"] for item in data["voltages"]]
    os.remove(file_path)
    return result


def process_steps_flatbuffer_file(
    file_dir, filename, from_date: datetime, to_date: datetime
):
    """Processing FlatBuffer file"""
    schema = "steps.fbs"  # todo add multiple schemas if needed in future
    # converting flatbuffer file to json
    _convert_flatbuffer_to_json(file_dir, filename, schema)
    # filtering data inside if date range filtering present
    if from_date or to_date:
        with open(f"{file_dir}/{filename}.json", "rb") as json_obj:
            data = json.loads(json_obj.read())
            results = {"platform": data["platform"], "stepsCounterData": []}
            if "stepCounterData" not in data:
                return

            utc_tz = pytz.timezone("UTC")
            from_date = from_date and from_date.replace(tzinfo=utc_tz)
            to_date = to_date and to_date.replace(tzinfo=utc_tz)

            for record in data["stepCounterData"]:
                try:
                    obj_start = datetime.fromtimestamp(record["startDateTime"])
                    obj_end = datetime.fromtimestamp(record["endDateTime"])
                except ValueError:
                    obj_start = datetime.fromtimestamp(record["startDateTime"] / 1e3)
                    obj_end = datetime.fromtimestamp(record["endDateTime"] / 1e3)

                obj_start = obj_start.replace(tzinfo=utc_tz)
                obj_end = obj_end.replace(tzinfo=utc_tz)

                # appending value if from/till is present and field is in range of from/till
                if (from_date and to_date) and not (
                    from_date <= obj_start and obj_end <= to_date
                ):
                    continue
                # if one of from/till present and value is bigger then from or smaller then end
                if from_date and from_date > obj_start:
                    continue
                if to_date and to_date < obj_end:
                    continue

                record["startDateTime"] = obj_start.isoformat()
                record["endDateTime"] = obj_end.isoformat()
                results["stepsCounterData"].append(record)

        with open(f"{file_dir}/{filename}.json", "w") as res_json:
            json.dump(results, res_json, indent=4)
