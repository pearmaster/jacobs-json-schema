import unittest
import pytest

from ..context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator, InvalidSchemaError

class TestInvalidMinLength(unittest.TestCase):

    def setUp(self):
        self.data = {
            "aString": "one",
        }
        self.schema = {
            "type": "object",
            "properties": {
                "aString": {
                    "type": "string",
                    "minLength": "1o",
                }
            }
        }
        
    def test_raises_invalid_schema(self):
        validator = Validator(self.schema, lazy_error_reporting=True)
        with pytest.raises(InvalidSchemaError):
            validator.validate(self.data)

class TestInvalidMaxLength(unittest.TestCase):

    def setUp(self):
        self.data = {
            "aString": "one",
        }
        self.schema = {
            "type": "object",
            "properties": {
                "aString": {
                    "type": "string",
                    "maxLength": "1o",
                }
            }
        }
        
    def test_raises_invalid_schema(self):
        validator = Validator(self.schema, lazy_error_reporting=True)
        with pytest.raises(InvalidSchemaError):
            validator.validate(self.data)

class TestInvalidEnum(unittest.TestCase):

    def setUp(self):
        self.data = {
            "aString": "one",
        }
        self.schema = {
            "type": "object",
            "properties": {
                "aString": {
                    "type": "string",
                    "enum": "one"
                }
            }
        }
        
    def test_raises_invalid_schema(self):
        validator = Validator(self.schema, lazy_error_reporting=True)
        with pytest.raises(InvalidSchemaError):
            validator.validate(self.data)