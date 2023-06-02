from extensions.module_result.router.custom_module_config_requests import (
    CreateOrUpdateCustomModuleConfigRequestObject,
)

ACCESS_CONTROLLER_ID = "602cfea54dcf4dc1f31c992c"
ADMIN_ID = "5e8f0c74b50aa9656c34789b"
PATIENT_ID = "5e8f0c74b50aa9656c34789c"
PROXY_ID = "5e8f0c74b50aa9656c342220"
MODULE_CONFIG_ID = "5e94b2007773091c9a592660"
SAMPLE_OBJECT_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_USER_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_DEPLOYMENT_ID = "5fe0a9c0d4696db1c7cd759a"
MODULE_ID = "602f641b90517902d644eff2"


def sample_rag_thresholds() -> list[dict]:
    return [
        {
            "color": "green",
            "severity": 1,
            "fieldName": "value",
            "type": "VALUE",
            "thresholdRange": [{"minValue": 110, "maxValue": 119}],
            "enabled": True,
        },
        {
            "color": "amber",
            "severity": 2,
            "fieldName": "value",
            "type": "VALUE",
            "thresholdRange": [{"minValue": 120, "maxValue": 130}],
            "enabled": True,
        },
    ]


def sample_custom_module_config():
    return {
        "moduleId": "Weight",
        "moduleConfigId": SAMPLE_OBJECT_ID,
        "reason": "reason",
        "ragThresholds": sample_rag_thresholds(),
        "schedule": sample_custom_module_schedule(),
        "userId": SAMPLE_USER_ID,
        "id": SAMPLE_OBJECT_ID
    }


def sample_custom_module_schedule():
    return {
        "weeklyRepeatInterval": 2,
        "timesOfReadings": ["PT10H30M"],
        "specificWeekDays": ["MON", "WED"],
    }


def custom_config_req_body(method: str):
    req_body = {
        "create": {
            CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: "Weight",
            CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
            CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds(),
            CreateOrUpdateCustomModuleConfigRequestObject.SCHEDULE: sample_custom_module_schedule(),
            CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
        },
        "update": {
            CreateOrUpdateCustomModuleConfigRequestObject.MODULE_ID: "Weight",
            CreateOrUpdateCustomModuleConfigRequestObject.REASON: "reason",
            CreateOrUpdateCustomModuleConfigRequestObject.RAG_THRESHOLDS: sample_rag_thresholds()[
                :1
            ],
            CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: SAMPLE_USER_ID,
        },
    }
    return req_body[method]
