
import unittest

from ..context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

class TestReferences(unittest.TestCase):

    def test_validate_from_reference(self):
        schema = {
            "definitions": {
                "myint": {
                    "type": "integer"
                }
            },
            "type": "array",
            "items": {
                "$ref": "#/definitions/myint"
            }
        }
        data = [1,2,3,4]
        validator = Validator(schema, lazy_error_reporting=False)
        self.assertTrue(validator.validate_from_reference(12, "#/definitions/myint"))