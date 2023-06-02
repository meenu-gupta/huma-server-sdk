import re

from sdk import convertibleclass

from sdk.common.exceptions.exceptions import InvalidUserAgentHeaderException
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.json_utils import decamelize
from sdk.common.utils.validators import default_version_meta
from sdk.phoenix.config.server_config import Client
from sdk.versioning.models.version_field import VersionField


@convertibleclass
class UserAgent:
    header_pattern = re.compile(r"(.+\/.+?)\s\((.*)\)")

    PRODUCT = "product"
    VERSION = "version"
    SOFTWARE_NAME = "software_name"
    SOFTWARE_VERSION = "software_version"
    BUNDLE_ID = "bundle_id"
    BUILD = "build"
    HARDWARE = "hardware"
    COMPONENT = "component"
    LANGUAGE = "language"
    CLIENT_TYPE = "client_type"
    MOBILE_OS_NAMES = {
        "iOS": Client.ClientType.USER_IOS,
        "Android": Client.ClientType.USER_ANDROID,
    }

    product: str = required_field()
    version: VersionField = required_field(metadata=default_version_meta())
    software_name: str = required_field()
    software_version: str = required_field()
    bundle_id: str = default_field()
    build: str = default_field()
    hardware: str = default_field()
    component: str = default_field()
    language: str = default_field()
    client_type: Client.ClientType = default_field()

    def __str__(self):
        main_part = f"{self.product}/{str(self.version)}"
        comment_pattern = (
            "(bundleId: %s; build: %s; software: %s; hardware: %s; component: %s)"
        )
        software = f"{self.software_name} {self.software_version}"
        comment = comment_pattern % (
            self.bundle_id,
            self.build,
            software,
            self.hardware,
            self.component,
        )
        return f"{main_part} {comment}"

    @classmethod
    def parse(cls, value: str):
        try:
            header = UserAgent.header_pattern.search(value)
            main = header.group(1).split("/")
            comment = header.group(2)
            return cls(
                main[0], VersionField(main[1]), **UserAgent.parse_comment(comment)
            )
        except Exception:
            raise InvalidUserAgentHeaderException

    @staticmethod
    def parse_comment(comment: str) -> dict:
        parts = comment.split(";")
        comment_dict = {}
        for part in parts:
            part = part.strip()

            try:
                key, value = part.split(":")
                if key == "software":
                    software_val = UserAgent.parse_software(value)
                    comment_dict.update(
                        {
                            **software_val,
                            UserAgent.CLIENT_TYPE: UserAgent.MOBILE_OS_NAMES.get(
                                software_val.get(UserAgent.SOFTWARE_NAME)
                            ),
                        }
                    )
                elif key == "version":
                    comment_dict[key.strip()] = VersionField(value.strip())
                else:
                    comment_dict[key.strip()] = value.strip()
            except (TypeError, ValueError):
                continue

        return decamelize(comment_dict)

    @staticmethod
    def parse_software(value) -> dict:
        software_name, software_version = value.split(maxsplit=1)
        return {
            UserAgent.SOFTWARE_NAME: software_name.strip(),
            UserAgent.SOFTWARE_VERSION: software_version.strip(),
        }
