import unittest

from ..context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

class LazyMixin:

    def test_does_not_validate(self):
        validator = Validator(self.schema, lazy_error_reporting=True)
        self.assertFalse(validator.validate(self.data))


class TestLazyReporting(unittest.TestCase, LazyMixin):

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
        
    def test_number_of_errors(self):
        validator = Validator(self.schema, lazy_error_reporting=True)
        validator.validate(self.data)
        self.assertEqual(len(validator.get_errors()), 2)


class TestLazyReportingOfAdditionalItems(unittest.TestCase, LazyMixin):

    def setUp(self):
        self.schema = {'additionalItems': {'type': 'integer'}, 'items': [{}]}
        self.data = [None, 2, 3, 'foo']


class TestLazyReportingOfAllOf(unittest.TestCase, LazyMixin):

    def setUp(self):
        self.schema = {'allOf': [{'maximum': 30}, {'minimum': 20}]}
        self.data = 35
