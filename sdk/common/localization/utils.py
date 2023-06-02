from os import listdir
from os.path import basename
from pathlib import Path
from typing import Set

import i18n

from sdk.common.utils.file_utils import load_json_file


def setup_i18n(path: str):
    i18n.set("file_format", "json")
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.load_path.append(path)


class Language:
    EN = "en"
    EN_GB = "en-GB"
    EN_US = "en-US"
    DE = "de"
    DE_AT = "de-AT"
    DE_CH = "de-CH"
    DE_DE = "de-DE"
    FR = "fr"
    ES = "es"
    SV = "sv"
    CA = "ca"
    AR = "ar"
    NL = "nl"
    IT = "it"

    @staticmethod
    def get_valid_languages():
        languages = []
        for attr in Language.__dict__:
            value = getattr(Language, attr)
            if not callable(value) and not attr.startswith("__"):
                languages.append(value)
        return languages

    @staticmethod
    def get_rtl_languages() -> Set:
        return {Language.AR}


def validate_localizations(localizations):
    valid_languages = Language.get_valid_languages()
    msg = f"Language \"%s\" is not supported. Available languages [{', '.join(valid_languages)}]"
    for lang, keys in localizations.items():
        if lang not in valid_languages:
            raise KeyError(msg % lang)
        for key, word in keys.items():
            if not isinstance(word, str):
                raise ValueError(f"{key}.{word} value should be str not [{type(word)}]")
    return True


class Localization:
    def __init__(self, localization_path: str):
        self.localization_path = localization_path
        self._localizations = self._load_localizations()

    def get(self, locale: str = Language.EN):
        localization = self._localizations.get(locale, {})
        if locale == Language.EN:
            return localization
        default_en_localization = self._localizations.get(Language.EN)
        return {**default_en_localization, **localization}

    def _load_localizations(self):
        localizations = {Language.EN: {}}
        if not (
            loc_dir_path := self.localization_path and Path(self.localization_path)
        ):
            return localizations
        for loc_file_name in listdir(loc_dir_path):
            locale = basename(loc_file_name).split(".")[0]
            localizations[locale] = load_json_file(loc_dir_path.joinpath(loc_file_name))
        return localizations
