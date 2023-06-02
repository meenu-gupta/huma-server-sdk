from unittest import TestCase

from sdk.common.utils.json_utils import replace_values, SPLITTER


class ReplaceValuesTestCase(TestCase):
    def test_replace_values(self):
        data = {
            "field1": "Value1",
            "field2": "Value2",
        }
        localization = {
            "Value1": "Translated1",
            "Value2": "Translated2",
        }
        translated = replace_values(data, localization)
        self.assertEqual(translated["field1"], "Translated1")
        self.assertEqual(translated["field2"], "Translated2")

    def test_replace_values__translate_keys(self):
        data = {
            "hu_some_placeholder": "some value",
        }
        localization = {
            "hu_some_placeholder": "Translated1",
        }
        translated = replace_values(data, localization, key_translation=True)
        self.assertEqual({"Translated1": "some value"}, translated)

    def test_replace_values__in_text_translation(self):
        data = {
            "field1": "hu_some_placeholder I am continuation after placeholder",
        }
        localization = {
            "hu_some_placeholder": "Translated1",
        }
        translated = replace_values(data, localization, in_text_translation=True)
        self.assertEqual(
            "Translated1 I am continuation after placeholder", translated["field1"]
        )

    def test_replace_values_ignored_fields(self):
        data = {
            "field1": "Value1",
            "field2": "Value2",
            "field3": "Value3",
            "field4": "Value4",
        }
        localization = {
            "Value1": "Translated1",
            "Value2": "Translated2",
            "Value3": "Translated3",
            "Value4": "Translated4",
        }
        ignored_keys = {"field1", "field3"}
        translated = replace_values(data, localization, ignored_keys=ignored_keys)
        for key, value in data.items():
            if key in ignored_keys:
                self.assertEqual(translated[key], value)
            else:
                self.assertEqual(translated[key], localization[value])

    def test_replace_values_string_list(self):
        data = {
            "field1": "Value1,Value2,Value3",
            "field2": "Value2",
        }
        localization = {
            "Value1": "Translated1",
            "Value2": "Translated2",
            "Value3": "Translated3",
        }

        translated = replace_values(data, localization, string_list_translator=True)
        expected_value_1 = SPLITTER.join(["Translated1", "Translated2", "Translated3"])

        self.assertEqual(translated["field1"], expected_value_1)
        self.assertEqual(translated["field2"], "Translated2")
