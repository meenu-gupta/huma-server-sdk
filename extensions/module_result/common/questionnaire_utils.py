from typing import Optional

START_DATE_IN_2019 = "2019-01-01"
START_DATE_IN_2020 = "2020-01-01"
START_DATE_IN_2021 = "2021-01-01"

ANSWERS = "answers"
ANSWER_TEXT = "answerText"
QUESTION_ID = "questionId"
QUESTION = "question"
LABEL = "label"
SPLITTER = ","


def build_question_map(questionnaire_dict: dict) -> dict[str, dict]:
    """Iterate through questionnaire and return map of questionIds to question properties."""
    question_map = {}

    if not questionnaire_dict:
        return question_map

    for page in questionnaire_dict.get("pages", []):
        if page["type"] == "QUESTION":
            for item in page["items"]:
                question_map[item["id"]] = item
    return question_map


def find_questionnaire_raw_data(raw_data: list[dict]) -> Optional[tuple[int, dict]]:
    for index, primitive in enumerate(raw_data):
        if primitive.get(ANSWERS):
            return index, primitive
    return


def manual_translation(raw_data: list[dict], question_map: dict, localization: dict):
    # Check if the raw data being handled is for a questionnaire primitive
    questionnaire_raw_data = find_questionnaire_raw_data(raw_data)
    if not questionnaire_raw_data:
        return raw_data

    index, questionnaire_data = questionnaire_raw_data
    for answer in questionnaire_data[ANSWERS]:
        answer_text = answer.get(ANSWER_TEXT, "")
        question_id = answer.get(QUESTION_ID)
        question = question_map.get(question_id)

        # To support previous questionnaires whose question_id do
        # not necessarily need to match what is in the config
        if not question:
            return raw_data

        matching_keys = []
        for key, value in localization.items():
            if value == answer_text or value in answer_text.split(SPLITTER):
                matching_keys.append(key)

        result = []
        options = question.get("options", [])
        for option in options:
            if option[LABEL] in matching_keys:
                result.append(option[LABEL])

        if result:
            answer[ANSWER_TEXT] = (
                SPLITTER.join(result) if len(result) > 1 else result[0]
            )
    raw_data[index] = questionnaire_data
    return raw_data
