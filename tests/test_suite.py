"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import json
import unittest
from pprint import pprint

from .context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

class Draft4TestSuite(unittest.TestCase):

    def setUp(self):
        testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'
        test_filepath = os.path.join(testsuite_dir, "tests", "draft4", "enum.json")
        with open(test_filepath, "r") as test_file:
            self.test_data = json.load(test_file)[0]
        self.validator = Validator(self.test_data['schema'])
    
    def test_one(self):
        self.assertTrue(self.validator.validate(self.test_data['tests'][0]))