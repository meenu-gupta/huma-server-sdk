from dataclasses import dataclass


@dataclass
class PrimitiveData:
    NAME = "name"
    USER_ID = "user_id"
    ID = "id"

    id: str
    name: str
    user_id: str
