"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import json
import pytest
from pprint import pprint

from ..context import jacobsjsonschema

from jacobsjsonschema.draft7 import Validator

testsuite_dir = pathlib.Path(__file__).parent.parent / 'JSON-Schema-Test-Suite'
        
SPECIAL_TESTS = ["ref.json", "id.json", "definitions.json", "refRemote.json", "unknownKeyword.json"]

def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    testfile_dir = testsuite_dir / "tests" / "draft7"

    for testfile in testfile_dir.glob("*.json"):
        if testfile.name in SPECIAL_TESTS:
            continue
        with testfile.open() as test_file:
            test_cases = json.load(test_file)

        for test_case in test_cases:
            
            for test in test_case['tests']:
                testids.append("{} -> {} -> {}".format(os.path.splitext(testfile.name)[0], test_case['description'], test['description']))
                argvalues.append(pytest.param(test_case['schema'], test['data'], test['valid']))

    metafunc.parametrize(argnames, argvalues, ids=testids)

def test_draft7(schema, data, valid):
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(jacobsjsonschema.draft4.JsonSchemaValidationError):
            validator.validate(data)