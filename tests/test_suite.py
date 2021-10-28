"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import json
import pytest
from pprint import pprint

from .context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'
        

def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    testfile_dir = testsuite_dir / "tests" / "draft4"

    for testfile in testfile_dir.glob("*.json"):
        test_filepath = os.path.join(testfile_dir, testfile)
        with open(test_filepath, "r") as test_file:
            test_cases = json.load(test_file)

        for test_case in test_cases:
            
            for test in test_case['tests']:
                testids.append(f"draft4 -> {os.path.basename(testfile)} -> {test_case['description']} -> {test['description']}")
                argvalues.append(pytest.param(test_case['schema'], test['data'], test['valid']))

    metafunc.parametrize(argnames, argvalues, ids=testids)

def test_draft4(schema, data, valid):
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(jacobsjsonschema.draft4.JsonSchemaValidationError):
            validator.validate(data)