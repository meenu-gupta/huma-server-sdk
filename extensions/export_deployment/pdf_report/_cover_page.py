from dataclasses import dataclass
from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.modules.visualizer import HTMLVisualizer


@dataclass
class Field:
    title: str
    value: Optional[str]


class CoverPage(HTMLVisualizer):
    template_name = "cover-letter-page.html"
    date_format = "%d %b %Y"
    full_height = True

    def get_context(self) -> dict:
        user = self.user
        gender = user and user.gender
        dob = self.user.dateOfBirth
        return {
            "title": "Summary Health Report",
            "fields": [
                Field("Patient", user.get_full_name()),
                Field("Deployment", self.deployment.name),
                Field("Date Period", self._get_date_period()),
                Field("Email", user.email),
                Field("Gender", gender and user.gender.value.capitalize()),
                Field("DOB", dob and dob.strftime(self.date_format)),
                Field("Height", self.get_height(user)),
            ],
        }

    def _get_date_period(self):
        return (
            f"{self.start_date_time.strftime(self.date_format)} - "
            f"{self.end_date_time.strftime(self.date_format)}"
        )

    @staticmethod
    def get_height(user: User):
        return f"{user.height} cm" if user.height else None
