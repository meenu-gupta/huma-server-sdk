import re
from dataclasses import field

from sdk.common.utils.convertible import convertibleclass


@convertibleclass
class Localizable:
    LOCALIZABLE_FIELDS = "_localizableFields"

    _localizableFields: tuple[str, ...] = field(default_factory=tuple)

    def get_localized_path(self, path: str = None, result: set = None) -> list[str]:
        if result is None:
            result = set()

        if not hasattr(self, Localizable.LOCALIZABLE_FIELDS):
            return []

        for field_name in self._localizableFields:
            field_data = getattr(self, field_name)
            if field_data is None:
                continue

            if isinstance(field_data, str):
                result.add(f"{path}.{field_name}")

            elif isinstance(field_data, list):
                for item in field_data:
                    if hasattr(item, self.get_localized_path.__name__):
                        item.get_localized_path(
                            path=f"{path}.{field_name}", result=result
                        )
                    elif isinstance(item, str):
                        result.add(f"{path}.{field_name}")

            elif hasattr(field_data, self.get_localized_path.__name__):
                field_data.get_localized_path(
                    path=f"{path}.{field_name}", result=result
                )

        return list(result)

    def _set_translation_to_field_and_add_to_localization_dict(
        self, field_name: str, path: str, translation_dict: dict
    ):
        field_data = getattr(self, field_name) or ""
        if field_data.startswith("hu_"):
            if field_data not in translation_dict:
                translation_dict[field_data] = ""
        else:
            translation_placeholder = self.sanitize_placeholder(f"{path}_{field_name}")
            translation_dict[translation_placeholder] = field_data
            self.set_field_value(field=field_name, field_value=translation_placeholder)

    @staticmethod
    def sanitize_placeholder(placeholder: str) -> str:
        return re.sub(r"\W+", "_", placeholder)

    def collect_localization_dict_and_replace_original_values(
        self, path: str = "", translation_dict: dict = None
    ) -> dict:
        if translation_dict is None:
            translation_dict = dict()

        if not hasattr(self, Localizable.LOCALIZABLE_FIELDS):
            return {}

        for field_name in self._localizableFields:
            field_data = getattr(self, field_name)

            if isinstance(field_data, str) and field_data:
                self._set_translation_to_field_and_add_to_localization_dict(
                    field_name, path, translation_dict
                )

            elif isinstance(field_data, list):
                self._process_list_type(field_data, field_name, path, translation_dict)

            elif isinstance(field_data, dict):
                for key, value in field_data.items():
                    value.collect_localization_dict_and_replace_original_values(
                        path=f"{path}_{field_name}_{key}",
                        translation_dict=translation_dict,
                    )

            elif isinstance(field_data, Localizable):
                field_data.collect_localization_dict_and_replace_original_values(
                    path=f"{path}_{field_name}",
                    translation_dict=translation_dict,
                )

        return translation_dict

    def _process_list_type(
        self, list_data: list, field_name: str, path: str, translation_dict: dict
    ):
        index = 0
        str_items = []
        for item in list_data:
            if isinstance(item, str):
                # If the item is localization key, then no need to replace.
                if item.startswith("hu_"):
                    # If item is localization key but doesn't have value in translation dictionary, add it to dictionary
                    if item not in translation_dict:
                        translation_dict[item] = ""
                    str_items.append(item)
                # Generate a localization key and add it to dictionary
                else:
                    translation_placeholder = self.sanitize_placeholder(
                        f"{path}_{field_name}_{index}"
                    )
                    translation_dict[translation_placeholder] = item
                    str_items.append(translation_placeholder)

            elif isinstance(item, Localizable):
                item.collect_localization_dict_and_replace_original_values(
                    path=f"{path}_{field_name}_{index}",
                    translation_dict=translation_dict,
                )

            index += 1

        if str_items:
            self.set_field_value(field=field_name, field_value=str_items)
