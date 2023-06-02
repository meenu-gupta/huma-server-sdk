import abc
from abc import ABC
from pathlib import PosixPath, Path
from string import Template

from sdk import convertibleclass
from sdk.common.utils.string_utils import compact_html


@convertibleclass
class TemplateParameters:
    textDirection: str = ""
    title: str = ""
    boldTitle: str = ""
    subtitle: str = ""
    body: str = ""
    buttonText: str = ""
    buttonLink: str = ""
    alternativeButtonText: str = ""
    alternativeButtonLink: str = ""
    rectangleBody: str = ""
    iosAppLink: str = ""
    androidAppLink: str = ""
    firstBlockText: str = ""
    secondBlockText: str = ""


class PercentageTemplate(Template):
    delimiter = "%"


class EmailAdapter(ABC):
    """
    Example:
    with open("f.html", "w") as f:
        f.write(TestTemplate().generate_html_with_button(
            TemplateParameters(title="Hey", subtitle="bosh", buttonText="click here", buttonLink="https://google.com",
                           rectangleBody="Here")))
    """

    _template_path: PosixPath = Path(__file__).parent.joinpath("./email_templates")

    @abc.abstractmethod
    def send_html_email(self, from_: str, to: str, subject: str, html: str):
        raise NotImplementedError

    @abc.abstractmethod
    def default_from_email(self):
        raise NotImplementedError

    def generate_html_with_button(self, template_params: TemplateParameters) -> str:
        return self._generate_html(
            template_params, self.get_generic_template_with_button
        )

    def generate_html_with_rectangle_body(
        self, template_params: TemplateParameters
    ) -> str:
        return self._generate_html(
            template_params, self.get_generic_template_with_rectangle_body
        )

    def generate_support_html_with_button(
        self, template_params: TemplateParameters
    ) -> str:
        return self._generate_html(
            template_params, self.get_support_template_with_button
        )

    def generate_email_with_app_downloading(
        self, template_params: TemplateParameters
    ) -> str:
        return self._generate_html(
            template_params, self.get_template_with_app_downloading
        )

    def generate_info_html(self, template_params: TemplateParameters) -> str:
        return self._generate_html(template_params, self.get_info_template)

    @staticmethod
    def _generate_html(template_params: TemplateParameters, get_template_method) -> str:
        return compact_html(
            PercentageTemplate(get_template_method()).safe_substitute(
                template_params.to_dict()
            )
        )

    def _get_template(self, template_path: str) -> str:
        p = Path(self._template_path.absolute()).joinpath(template_path)
        return p.read_text()

    def get_generic_template_with_button(self) -> str:
        return self._get_template("generic_template_with_button.html")

    def get_generic_template_with_rectangle_body(self) -> str:
        return self._get_template("generic_template_with_rectangle_body.html")

    def get_support_template_with_button(self) -> str:
        return self._get_template("generic_support_template_with_button.html")

    def get_template_with_app_downloading(self) -> str:
        return self._get_template("email_template_with_app_download.html")

    def get_info_template(self) -> str:
        return self._get_template("generic_template_without_button.html")
