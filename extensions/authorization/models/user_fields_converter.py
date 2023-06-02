from typing import Optional

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, BoardingStatus, UserLabel
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.primitives import Primitive
from sdk.common.utils.json_utils import replace_key_values
from sdk.common.utils.validators import remove_none_values


def generate_enrollment_number(deployment_code: str, enrollment_id: int):
    return f"{deployment_code}-{str(enrollment_id).zfill(4)}"


class UserFieldsConverter:
    IGNORED_PRIMITIVE_FIELDS = (
        Primitive.DEPLOYMENT_ID,
        Primitive.SUBMITTER_ID,
        Primitive.USER_ID,
        Primitive.ID,
    )
    IGNORED_USER_FIELDS = (
        User.TAGS_AUTHOR_ID,
        f"{User.BOARDING_STATUS}.{BoardingStatus.SUBMITTER_ID}",
    )

    def __init__(
        self,
        user: User,
        deployment: Optional[Deployment] = None,
        language: Optional[str] = None,
    ):
        self.user = user
        self.deployment = deployment
        self.language = language
        self.user_dict = self.user.to_dict(ignored_fields=self.IGNORED_USER_FIELDS)
        self.generate_enrollment_number()
        self.convert_complex_fields()

    def get_localization(self):
        authz_user = AuthorizedUser(self.user)
        deployment = self.deployment or (
            authz_user.deployment_id()
            and authz_user.deployment_id() != "*"
            and authz_user.deployment
        )
        localization = deployment and deployment.get_localization(self.language)
        return localization or {}

    def generate_enrollment_number(self):
        if self.deployment and self.deployment.code and self.user.enrollmentId:
            enrollment_number = generate_enrollment_number(
                self.deployment.code, self.user.enrollmentId
            )
            self.user_dict.update({self.user.ENROLLMENT_NUMBER: enrollment_number})

    def convert_complex_fields(self):
        self.recent_results_to_dict()

    def recent_results_to_dict(self):
        results = self._recent_results_to_dict()
        if (
            self.deployment
            and self.deployment.localizations
            and self.language in self.deployment.localizations
        ):
            results = replace_key_values(
                results,
                self.deployment.localizations[self.language],
                check_hashable=False,
                string_list_translator=True,
            )
        self.user_dict.update({self.user.RECENT_MODULE_RESULTS: results})

    def to_dict(
        self,
        include_none: bool = False,
        only_fields: set = None,
        exclude_fields: set = None,
    ) -> dict:
        if include_none:
            return self._to_dict(only_fields=only_fields, exclude_fields=exclude_fields)

        return self._to_dict_remove_none(
            only_fields=only_fields, exclude_fields=exclude_fields
        )

    def _recent_results_to_dict(self):
        if not self.user.recentModuleResults:
            return
        return {
            key: [
                {
                    p_type: val.to_dict(False, self.IGNORED_PRIMITIVE_FIELDS)
                    for p_type, val in primitive.items()
                }
                for primitive in value
            ]
            for key, value in self.user.recentModuleResults.items()
        }

    def _to_dict(self, only_fields: set = None, exclude_fields: set = None) -> dict:
        self.user_dict = replace_key_values(
            self.user_dict,
            self.get_localization(),
            string_list_translator=True,
        )

        if only_fields:
            return {
                user_field: value
                for user_field, value in self.user_dict.items()
                if user_field in only_fields
            }

        private_fields = self.user.private_fields()
        if not exclude_fields:
            exclude_fields = {}
        return {
            user_field: value
            for user_field, value in self.user_dict.items()
            if user_field not in private_fields and user_field not in exclude_fields
        }

    def _to_dict_remove_none(
        self, only_fields: set = None, exclude_fields: set = None
    ) -> dict:
        user_dict = self._to_dict(
            only_fields=only_fields, exclude_fields=exclude_fields
        )
        return remove_none_values(user_dict)
