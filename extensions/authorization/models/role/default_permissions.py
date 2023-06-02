from enum import Enum

from sdk import meta
from sdk.common.utils.convertible import default_field


class PermissionType(Enum):
    VIEW_OWN_DATA = "VIEW_OWN_DATA"
    MANAGE_OWN_DATA = "MANAGE_OWN_DATA"
    MANAGE_OWN_EVENTS = "MANAGE_OWN_EVENTS"
    INVITE_OWN_PROXY = "INVITE_OWN_PROXY"
    GENERATE_HEALTH_REPORT = "GENERATE_HEALTH_REPORT"

    VIEW_PATIENT_DATA = "VIEW_PATIENT_DATA"
    EDIT_PATIENT_DATA = "EDIT_PATIENT_DATA"
    MANAGE_PATIENT_MODULE_CONFIG = "MANAGE_PATIENT_MODULE_CONFIG"
    OFF_BOARD_PATIENT = "OFF_BOARD_PATIENT"
    MANAGE_PATIENT_DATA = "MANAGE_PATIENT_DATA"
    MANAGE_PATIENT_EVENTS = "MANAGE_PATIENT_EVENTS"
    CONTACT_PATIENT = "CONTACT_PATIENT"
    EXPORT_PATIENT_DATA = "EXPORT_PATIENT_DATA"
    VIEW_PATIENT_IDENTIFIER = "VIEW_PATIENT_IDENTIFIER"
    INVITE_PROXY_FOR_PATIENT = "INVITE_PROXY_FOR_PATIENT"
    MANAGE_LABELS = "MANAGE_LABELS"

    ADD_STAFF_MEMBERS = "ADD_STAFF_MEMBERS"
    ADD_SUPER_STAFF_MEMBERS = "ADD_SUPER_STAFF_MEMBERS"
    ADD_PATIENTS = "ADD_PATIENTS"
    VIEW_STAFF_LIST = "VIEW_STAFF_LIST"
    MANAGE_ADMINS = "MANAGE_ADMINS"
    MANAGE_DEPLOYMENT = "MANAGE_DEPLOYMENT"
    EDIT_DEPLOYMENT = "EDIT_DEPLOYMENT"
    EDIT_ROLE_PERMISSIONS = "EDIT_ROLE_PERMISSIONS"
    CREATE_ORGANIZATION = "CREATE_ORGANIZATION"
    MANAGE_ORGANIZATION = "MANAGE_ORGANIZATION"
    OPERATE_ORGANIZATION = "OPERATE_ORGANIZATION"
    DELETE_ORGANIZATION = "DELETE_ORGANIZATION"
    REMOVE_USER = "REMOVE_USER"
    VIEW_PROXY_PROFILE = "VIEW_PROXY_PROFILE"
    GENERATE_AUTH_TOKEN = "GENERATE_AUTH_TOKEN"
    PUBLISH_PATIENT_DATA = "PUBLISH_PATIENT_DATA"
    VIEW_DEPLOYMENT_KEY_ACTIONS = "VIEW_DEPLOYMENT_KEY_ACTIONS"
    VIEW_OWN_RESOURCES = "VIEW_OWN_RESOURCES"

    MANAGE_DEPLOYMENT_TEMPLATE = "MANAGE_DEPLOYMENT_TEMPLATE"
    RETRIEVE_DEPLOYMENT_TEMPLATE = "RETRIEVE_DEPLOYMENT_TEMPLATE"

    VIEW_DASHBOARD = "VIEW_DASHBOARD"

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    @staticmethod
    def common_permissions() -> list:
        permissions = [
            PermissionType.VIEW_OWN_DATA,
            PermissionType.MANAGE_OWN_DATA,
            PermissionType.VIEW_PROXY_PROFILE,
            PermissionType.GENERATE_AUTH_TOKEN,
        ]
        permissions.sort()
        return permissions


class PolicyType(Enum):
    # Common
    VIEW_OWN_DATA = 1
    EDIT_OWN_DATA = 2
    VIEW_OWN_PROFILE = 3
    EDIT_OWN_PROFILE = 4
    VIEW_OWN_DEPLOYMENT = 5
    VIEW_OWN_EVENTS = 6
    EDIT_OWN_EVENTS = 7
    VIEW_PROXY_PROFILE = 8
    VIEW_OWN_MESSAGES = 9
    INVITE_OWN_PROXY = 10

    # User
    GENERATE_HEALTH_REPORT = 15

    # Contributor
    VIEW_PATIENT_DATA = 21
    EDIT_PATIENT_DATA = 22
    VIEW_PATIENT_PROFILE = 23
    EDIT_PATIENT_PROFILE = 24
    EDIT_PATIENT_NOTE = 25
    CHANGE_PATIENT_STATUS = 26
    ASSIGN_PATIENT_TO_STAFF = 27
    MOVE_PATIENT_TO_OTHER_GROUP = 28
    INVITE_PROXY_FOR_PATIENT = 29
    SCHEDULE_AND_CALL_PATIENT = 30
    RESCHEDULE_CALL = 31
    EXPORT_PATIENT_DATA = 32
    VIEW_PATIENT_IDENTIFIER = 33
    ADD_REMOVE_PATIENT = 34

    INVITE_PATIENTS = 35
    INVITE_STAFFS = 36
    INVITE_ADMINS = 37
    REMOVE_STAFF = 38
    ASSIGN_ROLES_TO_STAFF = 39
    VIEW_CUSTOM_ROLES = 40
    EDIT_CUSTOM_ROLES = 41
    VIEW_STAFF_LIST = 42
    OFF_BOARD_PATIENT = 43

    SEND_PATIENT_MESSAGE = 44
    VIEW_PATIENT_MESSAGE = 45

    VIEW_PATIENT_EVENTS = 46
    EDIT_PATIENT_EVENTS = 47

    MANAGE_PATIENT_MODULE_CONFIG = 48

    CREATE_PATIENT_LABELS = 49
    EDIT_PATIENT_LABELS = 50
    ASSIGN_PATIENT_LABELS = 51
    DELETE_PATIENT_LABELS = 52

    # Super Admin
    VIEW_DEPLOYMENT = 80
    EDIT_DEPLOYMENT = 81
    CREATE_DEPLOYMENT = 82
    EDIT_EXPORT_DEPLOYMENT_CONFIG = 83
    REMOVE_USER = 84
    VIEW_ORGANIZATION = 85
    CREATE_ORGANIZATION = 86
    EDIT_ORGANIZATION = 87
    DELETE_ORGANIZATION = 88
    GENERATE_AUTH_TOKEN = 89
    PUBLISH_PATIENT_DATA = 90
    INVITE_SUPER_STAFF = 91
    VIEW_OWN_RESOURCES = 92
    CREATE_DEPLOYMENT_TEMPLATE = 93
    RETRIEVE_DEPLOYMENT_TEMPLATE = 94
    DELETE_DEPLOYMENT_TEMPLATE = 95
    UPDATE_DEPLOYMENT_TEMPLATE = 96
    VIEW_DASHBOARD = 97
    CREATE_DASHBOARD = 98

    # Huma Support
    VIEW_DEPLOYMENT_KEY_ACTIONS = 100


class PermissionPolicy:
    permission_type: PermissionType = default_field()
    policies: tuple[PolicyType] = default_field(metadata=meta(required=False))

    def __init__(self, permission_type: PermissionType, policies: tuple):
        self.permission_type = permission_type
        self.policies = policies


MANAGE_DEPLOYMENT_TEMPLATE = PermissionPolicy(
    permission_type=PermissionType.MANAGE_DEPLOYMENT_TEMPLATE,
    policies=(
        PolicyType.CREATE_DEPLOYMENT_TEMPLATE,
        PolicyType.DELETE_DEPLOYMENT_TEMPLATE,
        PolicyType.UPDATE_DEPLOYMENT_TEMPLATE,
        PolicyType.RETRIEVE_DEPLOYMENT_TEMPLATE,
    ),
)
RETRIEVE_DEPLOYMENT_TEMPLATE = PermissionPolicy(
    permission_type=PermissionType.RETRIEVE_DEPLOYMENT_TEMPLATE,
    policies=(PolicyType.RETRIEVE_DEPLOYMENT_TEMPLATE,),
)

MANAGE_PATIENT_DATA = PermissionPolicy(
    permission_type=PermissionType.MANAGE_PATIENT_DATA,
    policies=(
        PolicyType.ADD_REMOVE_PATIENT,
        PolicyType.CHANGE_PATIENT_STATUS,
        PolicyType.EDIT_PATIENT_NOTE,
        PolicyType.EDIT_PATIENT_PROFILE,
        PolicyType.EDIT_PATIENT_DATA,
        PolicyType.ASSIGN_PATIENT_TO_STAFF,
        PolicyType.MOVE_PATIENT_TO_OTHER_GROUP,
        PolicyType.OFF_BOARD_PATIENT,
        PolicyType.INVITE_PATIENTS,
        PolicyType.INVITE_PROXY_FOR_PATIENT,
        PolicyType.ASSIGN_PATIENT_LABELS,
    ),
)
MANAGE_PATIENT_EVENTS = PermissionPolicy(
    permission_type=PermissionType.MANAGE_PATIENT_EVENTS,
    policies=(
        PolicyType.VIEW_PATIENT_EVENTS,
        PolicyType.EDIT_PATIENT_EVENTS,
    ),
)
OFF_BOARD_PATIENT = PermissionPolicy(
    permission_type=PermissionType.OFF_BOARD_PATIENT,
    policies=(PolicyType.OFF_BOARD_PATIENT,),
)
EDIT_PATIENT_DATA = PermissionPolicy(
    permission_type=PermissionType.EDIT_PATIENT_DATA,
    policies=(PolicyType.EDIT_PATIENT_PROFILE, PolicyType.EDIT_PATIENT_DATA),
)

MANAGE_LABELS = PermissionPolicy(
    permission_type=PermissionType.MANAGE_LABELS,
    policies=(
        PolicyType.CREATE_PATIENT_LABELS,
        PolicyType.EDIT_PATIENT_LABELS,
        PolicyType.DELETE_PATIENT_LABELS,
    ),
)

MANAGE_PATIENT_MODULE_CONFIG = PermissionPolicy(
    permission_type=PermissionType.MANAGE_PATIENT_MODULE_CONFIG,
    policies=(PolicyType.MANAGE_PATIENT_MODULE_CONFIG,),
)
MANAGE_OWN_DATA = PermissionPolicy(
    permission_type=PermissionType.MANAGE_OWN_DATA,
    policies=(PolicyType.EDIT_OWN_PROFILE, PolicyType.EDIT_OWN_DATA),
)
CONTACT_PATIENT = PermissionPolicy(
    permission_type=PermissionType.CONTACT_PATIENT,
    policies=(
        PolicyType.SCHEDULE_AND_CALL_PATIENT,
        PolicyType.RESCHEDULE_CALL,
        PolicyType.SEND_PATIENT_MESSAGE,
        PolicyType.VIEW_PATIENT_MESSAGE,
    ),
)
ADD_PATIENTS = PermissionPolicy(
    permission_type=PermissionType.ADD_PATIENTS,
    policies=(PolicyType.INVITE_PATIENTS,),
)
EXPORT_PATIENT_DATA = PermissionPolicy(
    permission_type=PermissionType.EXPORT_PATIENT_DATA,
    policies=(PolicyType.EXPORT_PATIENT_DATA,),
)
PUBLISH_PATIENT_DATA = PermissionPolicy(
    permission_type=PermissionType.PUBLISH_PATIENT_DATA,
    policies=(PolicyType.PUBLISH_PATIENT_DATA,),
)
VIEW_PATIENT_DATA = PermissionPolicy(
    permission_type=PermissionType.VIEW_PATIENT_DATA,
    policies=(PolicyType.VIEW_PATIENT_PROFILE, PolicyType.VIEW_PATIENT_DATA),
)
VIEW_OWN_DATA = PermissionPolicy(
    permission_type=PermissionType.VIEW_OWN_DATA,
    policies=(
        PolicyType.VIEW_OWN_PROFILE,
        PolicyType.VIEW_OWN_DATA,
        PolicyType.VIEW_OWN_DEPLOYMENT,
        PolicyType.VIEW_OWN_EVENTS,
        PolicyType.VIEW_OWN_MESSAGES,
    ),
)
MANAGE_OWN_EVENTS = PermissionPolicy(
    permission_type=PermissionType.MANAGE_OWN_EVENTS,
    policies=(PolicyType.EDIT_OWN_EVENTS,),
)
ADD_STAFF_MEMBERS = PermissionPolicy(
    permission_type=PermissionType.ADD_STAFF_MEMBERS,
    policies=(
        PolicyType.INVITE_STAFFS,
        PolicyType.ASSIGN_ROLES_TO_STAFF,
    ),
)
ADD_SUPER_STAFF_MEMBERS = PermissionPolicy(
    permission_type=PermissionType.ADD_SUPER_STAFF_MEMBERS,
    policies=(PolicyType.INVITE_SUPER_STAFF,),
)
VIEW_PATIENT_IDENTIFIER = PermissionPolicy(
    permission_type=PermissionType.VIEW_PATIENT_IDENTIFIER,
    policies=(PolicyType.VIEW_PATIENT_IDENTIFIER,),
)
MANAGE_ADMINS = PermissionPolicy(
    permission_type=PermissionType.MANAGE_ADMINS,
    policies=(
        PolicyType.INVITE_ADMINS,
        PolicyType.REMOVE_STAFF,
    ),
)
EDIT_ROLE_PERMISSIONS = PermissionPolicy(
    permission_type=PermissionType.EDIT_ROLE_PERMISSIONS,
    policies=(
        PolicyType.EDIT_CUSTOM_ROLES,
        PolicyType.VIEW_CUSTOM_ROLES,
    ),
)
VIEW_STAFF_LIST = PermissionPolicy(
    permission_type=PermissionType.VIEW_STAFF_LIST,
    policies=(PolicyType.VIEW_STAFF_LIST,),
)
MANAGE_DEPLOYMENT = PermissionPolicy(
    permission_type=PermissionType.MANAGE_DEPLOYMENT,
    policies=(
        PolicyType.CREATE_DEPLOYMENT,
        PolicyType.VIEW_DEPLOYMENT,
        PolicyType.EDIT_DEPLOYMENT,
    ),
)
EDIT_DEPLOYMENT = PermissionPolicy(
    permission_type=PermissionType.EDIT_DEPLOYMENT,
    policies=(
        PolicyType.VIEW_DEPLOYMENT,
        PolicyType.EDIT_DEPLOYMENT,
    ),
)
CREATE_ORGANIZATION = PermissionPolicy(
    permission_type=PermissionType.CREATE_ORGANIZATION,
    policies=(PolicyType.CREATE_ORGANIZATION,),
)
MANAGE_ORGANIZATION = PermissionPolicy(
    permission_type=PermissionType.MANAGE_ORGANIZATION,
    policies=(
        PolicyType.VIEW_ORGANIZATION,
        PolicyType.CREATE_ORGANIZATION,
        PolicyType.EDIT_ORGANIZATION,
    ),
)
VIEW_DASHBOARD = PermissionPolicy(
    permission_type=PermissionType.VIEW_DASHBOARD,
    policies=(PolicyType.VIEW_DASHBOARD,),
)
OPERATE_ORGANIZATION = PermissionPolicy(
    permission_type=PermissionType.OPERATE_ORGANIZATION,
    policies=(
        PolicyType.VIEW_ORGANIZATION,
        PolicyType.EDIT_ORGANIZATION,
    ),
)
DELETE_ORGANIZATION = PermissionPolicy(
    permission_type=PermissionType.DELETE_ORGANIZATION,
    policies=(PolicyType.DELETE_ORGANIZATION,),
)
REMOVE_USER = PermissionPolicy(
    permission_type=PermissionType.REMOVE_USER, policies=(PolicyType.REMOVE_USER,)
)
VIEW_PROXY_PROFILE = PermissionPolicy(
    permission_type=PermissionType.VIEW_PROXY_PROFILE,
    policies=(PolicyType.VIEW_PROXY_PROFILE,),
)
GENERATE_AUTH_TOKEN = PermissionPolicy(
    permission_type=PermissionType.GENERATE_AUTH_TOKEN,
    policies=(PolicyType.GENERATE_AUTH_TOKEN,),
)
INVITE_OWN_PROXY = PermissionPolicy(
    permission_type=PermissionType.INVITE_OWN_PROXY,
    policies=(PolicyType.INVITE_OWN_PROXY,),
)

INVITE_PROXY_FOR_PATIENT = PermissionPolicy(
    permission_type=PermissionType.INVITE_PROXY_FOR_PATIENT,
    policies=(PolicyType.INVITE_PROXY_FOR_PATIENT,),
)
VIEW_DEPLOYMENT_KEY_ACTIONS = PermissionPolicy(
    permission_type=PermissionType.VIEW_DEPLOYMENT_KEY_ACTIONS,
    policies=(PolicyType.VIEW_DEPLOYMENT_KEY_ACTIONS,),
)
VIEW_OWN_RESOURCES = PermissionPolicy(
    permission_type=PermissionType.VIEW_OWN_RESOURCES,
    policies=(PolicyType.VIEW_OWN_RESOURCES,),
)
GENERATE_HEALTH_REPORT = PermissionPolicy(
    permission_type=PermissionType.GENERATE_HEALTH_REPORT,
    policies=(PolicyType.GENERATE_HEALTH_REPORT,),
)

PERMISSIONS = {
    # User
    PermissionType.VIEW_OWN_DATA.value: VIEW_OWN_DATA,
    PermissionType.MANAGE_OWN_DATA.value: MANAGE_OWN_DATA,
    PermissionType.MANAGE_OWN_EVENTS.value: MANAGE_OWN_EVENTS,
    PermissionType.VIEW_PROXY_PROFILE.value: VIEW_PROXY_PROFILE,
    PermissionType.INVITE_OWN_PROXY.value: INVITE_OWN_PROXY,
    PermissionType.GENERATE_HEALTH_REPORT.value: GENERATE_HEALTH_REPORT,
    # Manager
    PermissionType.VIEW_PATIENT_DATA.value: VIEW_PATIENT_DATA,
    PermissionType.MANAGE_PATIENT_DATA.value: MANAGE_PATIENT_DATA,
    PermissionType.EDIT_PATIENT_DATA.value: EDIT_PATIENT_DATA,
    PermissionType.MANAGE_PATIENT_MODULE_CONFIG.value: MANAGE_PATIENT_MODULE_CONFIG,
    PermissionType.VIEW_PATIENT_IDENTIFIER.value: VIEW_PATIENT_IDENTIFIER,
    PermissionType.CONTACT_PATIENT.value: CONTACT_PATIENT,
    PermissionType.EXPORT_PATIENT_DATA.value: EXPORT_PATIENT_DATA,
    PermissionType.ADD_STAFF_MEMBERS.value: ADD_STAFF_MEMBERS,
    PermissionType.ADD_PATIENTS.value: ADD_PATIENTS,
    PermissionType.VIEW_STAFF_LIST.value: VIEW_STAFF_LIST,
    PermissionType.OFF_BOARD_PATIENT.value: OFF_BOARD_PATIENT,
    PermissionType.MANAGE_PATIENT_EVENTS.value: MANAGE_PATIENT_EVENTS,
    PermissionType.INVITE_PROXY_FOR_PATIENT.value: INVITE_PROXY_FOR_PATIENT,
    PermissionType.MANAGE_LABELS.value: MANAGE_LABELS,
    # Super Admin
    PermissionType.EDIT_ROLE_PERMISSIONS.value: EDIT_ROLE_PERMISSIONS,
    PermissionType.MANAGE_ADMINS.value: MANAGE_ADMINS,
    PermissionType.MANAGE_DEPLOYMENT.value: MANAGE_DEPLOYMENT,
    PermissionType.EDIT_DEPLOYMENT.value: EDIT_DEPLOYMENT,
    PermissionType.CREATE_ORGANIZATION.value: CREATE_ORGANIZATION,
    PermissionType.MANAGE_ORGANIZATION.value: MANAGE_ORGANIZATION,
    PermissionType.OPERATE_ORGANIZATION.value: OPERATE_ORGANIZATION,
    PermissionType.DELETE_ORGANIZATION.value: DELETE_ORGANIZATION,
    PermissionType.REMOVE_USER.value: REMOVE_USER,
    PermissionType.GENERATE_AUTH_TOKEN.value: GENERATE_AUTH_TOKEN,
    PermissionType.PUBLISH_PATIENT_DATA.value: PUBLISH_PATIENT_DATA,
    PermissionType.ADD_SUPER_STAFF_MEMBERS.value: ADD_SUPER_STAFF_MEMBERS,
    PermissionType.MANAGE_DEPLOYMENT_TEMPLATE.value: MANAGE_DEPLOYMENT_TEMPLATE,
    PermissionType.RETRIEVE_DEPLOYMENT_TEMPLATE.value: RETRIEVE_DEPLOYMENT_TEMPLATE,
    PermissionType.VIEW_DASHBOARD.value: VIEW_DASHBOARD,
    # Huma Support
    PermissionType.VIEW_DEPLOYMENT_KEY_ACTIONS.value: VIEW_DEPLOYMENT_KEY_ACTIONS,
    # Other
    PermissionType.VIEW_OWN_RESOURCES.value: VIEW_OWN_RESOURCES,
}
