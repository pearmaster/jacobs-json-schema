import unittest

from ..context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

class TestValidate(unittest.TestCase):

    def test_draft4(self):
        data = {
            "foo": "bar",
            "bar": 10,
        }
        schema = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "string",
                    "enum": [
                        "bar",
                        "fred",
                    ],
                    "maxLength": 10,
                    "minLength": 1,
                },
                "bar": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["foo"],
            "anyOf": [
                {"type": "object"}
            ],
            "allOf": [
                {"type": "object"}
            ],
            "oneOf": [
                {"type": "string"},
                {"type": "object"},
            ],
            "not": {"type": "integer"},
        }
        validator = Validator(schema, lazy_error_reporting=False)
        self.assertTrue(validator.validate(data))