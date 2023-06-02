import unittest
from pathlib import Path

from jsonschema.validators import validate

from sdk.common.utils.file_utils import load_json_file

CASES = {
    "questionnaire_schema.json": ["questionnaire_example.json"],
    "symptom_schema.json": ["symptom_example.json"],
    "video_questionnaire_schema.json": ["video_questionnaire_example.json"],
    "heart_rate_schema.json": [
        "heart_rate_example.json",
        "heart_rate_without_source_example.json",
    ],
}


class TestSchemaValidation(unittest.TestCase):
    def test_validation_schema(self):
        for schemaFile, examples in CASES.items():
            schema_file = Path(__file__).parent.joinpath(schemaFile)
            schema = load_json_file(schema_file)
            for example in examples:
                example = Path(__file__).parent.joinpath(example)
                with self.subTest():
                    validate(
                        instance=load_json_file(example),
                        schema=schema,
                    )


if __name__ == "__main__":
    unittest.main()
