import unittest

from ..context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

class TestLazyReporting(unittest.TestCase):

    def setUp(self):
        self.data = {
            "foo": "one",
            "bar": 2
        }
        self.schema = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "number",
                },
                "bar": {
                    "type": "string",
                }
            }
        }
        
    def test_does_not_validate(self):
        validator = Validator(self.schema, _lazy_error_reporting=True)
        self.assertFalse(validator.validate(self.data))

    def test_number_of_errors(self):
        validator = Validator(self.schema, _lazy_error_reporting=True)
        validator.validate(self.data)
        self.assertEqual(len(validator.get_errors()), 2)