import copy

from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.helpers.convertion_helpers import ExportData
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from sdk import convertibleclass
from sdk.common.usecase.request_object import RequestObject
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import default_field


@convertibleclass
class ExportableRequestObject(RequestObject, ExportRequestObject):
    TRANSLATION_MODULE_CODES = "translationModuleCodes"
    TRANSLATION_SHORT_CODES = "translationShortCodes"
    USERS_DATA = "usersData"
    EXPORT_DIR = "exportDir"
    CONSENTS_DATA = "consentsData"
    ECONSENTS_DATA = "econsentsData"
    DEPLOYMENT = "deployment"

    """
    This request will contain information how to extract data from export manager
    """

    translationModuleCodes: dict = default_field()
    translationShortCodes: dict = default_field()
    usersData: dict = default_field()
    consentsData: dict = default_field()
    econsentsData: dict = default_field()
    exportDir: str = default_field()
    deployment: Deployment = default_field()
    moduleConfigVersions: dict = default_field()

    @classmethod
    def validate(cls, request):
        pass


class ExportableResponseObject(Response):
    """
    This class will take information
    """

    @convertibleclass
    class Response:
        items: ExportData = default_field()

    def __init__(self, items: dict):
        super().__init__(value=self.Response(items))

    def to_csv(self):
        items = copy.deepcopy(self.value.items)
        self.preprocess_csv_data(items)
        return items

    def to_json(self):
        return self.value.items

    def preprocess_csv_data(self, items):
        from extensions.export_deployment.helpers.convertion_helpers import (
            flatten_object,
        )

        for module, primitives in items.items():
            for item in primitives:
                flatten_object(item)
