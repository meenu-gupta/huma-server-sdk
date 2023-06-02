from typing import Any

LOWER_CASE_SENSITIVE_KEYS = {"token", "key", "password", "code"}
MASK = "***************"


def _redact_list(data: list):
    for i, d in enumerate(data):
        data[i] = redact_data(d)

    return data


def _redact_dict(data: dict):
    for key, value in data.items():
        # compare key to sensitive keys
        key_lower = key.lower()
        match = any(s in key_lower for s in LOWER_CASE_SENSITIVE_KEYS)

        if match:
            data[key] = MASK
        else:
            data[key] = redact_data(value)

    return data


def redact_data(data: Any):
    if not isinstance(data, (list, dict)):
        return data

    if isinstance(data, list):
        data = _redact_list(data)

    if isinstance(data, dict):
        data = _redact_dict(data)

    return data
