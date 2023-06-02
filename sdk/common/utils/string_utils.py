import string
from random import choice


def to_plural(noun: str) -> str:
    last_letter = noun[-1]
    if last_letter == "y":
        result = noun.replace("y", "ies")
    else:
        result = noun + "s"
    return result


def compact_html(html_str: str) -> str:
    html_str = html_str.replace("\t", " ")
    html_str = html_str.replace("\n", " ")
    return " ".join([s for s in html_str.split(" ") if len(s.strip()) != 0])


def generate_random_url_safe_string(length: int):
    return "".join(
        choice(string.ascii_letters + string.digits + "_-") for _ in range(length)
    )
