from dataclasses import dataclass


@dataclass
class CalendarViewUsersData:
    additional_fields: dict
    users_data: list[dict]
