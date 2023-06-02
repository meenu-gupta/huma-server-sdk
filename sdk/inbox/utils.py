from sdk.common.utils.json_utils import replace_values


def translate_message_text_to_placeholder(text: str, localization: dict):
    reverse_localization = {val: key for key, val in localization.items()}
    return replace_values(text, reverse_localization)
