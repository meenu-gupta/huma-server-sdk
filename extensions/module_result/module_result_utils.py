from enum import Enum, IntEnum
from typing import Optional, Union

from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.primitives.primitive_questionnaire import (
    PageType,
    QuestionAnswerFormat,
    Questionnaire,
    QuestionnaireAnswer,
)


class AggregateFunc(Enum):
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX"
    MIN = "MIN"


class AggregateMode(Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class AlwaysToNever(IntEnum):
    ALWAYS = 1
    OFTEN = 2
    SOMETIMES = 3
    RARELY = 4
    NEVER = 5


class NotToCompletely(IntEnum):
    NOT_AT_ALL = 1
    A_LITTLE = 2
    MODERATELY = 3
    MOSTLY = 4
    COMPLETELY = 5


class PoorToExcellent(IntEnum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


class VerySevereToNone(IntEnum):
    VERY_SEVERE = 1
    SEVERE = 2
    MODERATE = 3
    MILD = 4
    NONE = 5


def config_body_to_question_map(config_body: dict) -> dict[str, dict]:
    question_map = {}

    for page in config_body.get("pages", []):
        if page["type"] != PageType.QUESTION.value:
            continue

        for item in page["items"]:
            question_map[item["id"]] = item

    return question_map


def check_answered_required_questions(primitive: Questionnaire, config_body: dict):
    question_map = config_body_to_question_map(config_body)
    required_questions = [
        question for question in question_map.values() if question.get("required")
    ]

    if len(primitive.answers) < len(required_questions):
        raise NotAllRequiredQuestionsAnsweredException


def get_maximum_possible_score(config_body: dict, scoreable_question_ids: set[str]):
    def get_weight(option):
        return option.get("weight")

    max_score = 0
    for page in config_body.get("pages", []):
        if page["type"] != PageType.QUESTION.value:
            continue

        for item in page["items"]:

            if item["id"] not in scoreable_question_ids:
                continue
            if item["format"] == QuestionAnswerFormat.TEXTCHOICE.value:
                options: list = item["options"]
                options.sort(key=get_weight, reverse=True)
                max_score += options[0]["weight"]

            elif item["format"] == QuestionAnswerFormat.SCALE.value:
                max_score += item["upperBound"]

            elif item["format"] == QuestionAnswerFormat.BOOLEAN.value:
                max_score += 1
    return max_score
