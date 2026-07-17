import unittest


from jacobsjsonschema.draft4 import Validator


class TestReferences(unittest.TestCase):

    def test_validate_from_reference(self):
        schema = {
            "definitions": {"myint": {"type": "integer"}},
            "type": "array",
            "items": {"$ref": "#/definitions/myint"},
        }
        validator = Validator(schema, lazy_error_reporting=False)
        self.assertTrue(validator.validate_from_reference(12, "#/definitions/myint"))
