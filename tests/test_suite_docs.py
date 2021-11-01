"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import pytest
from pprint import pprint

from jacobsjsondoc.loader import PrepopulatedLoader
from jacobsjsondoc.document import create_document

from .context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'
        
SPECIAL_TESTS = ["ref.json", "id.json", "definitions.json", "refRemote.json"]

def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    testfile_dir = testsuite_dir / "tests" / "draft4"

    for testfile in testfile_dir.glob("*.json"):
        if os.path.basename(testfile) in SPECIAL_TESTS:
            continue
        with open(testfile, "r") as test_file:
            print(f"Starting with {testfile}")
            ppl = PrepopulatedLoader()
            ppl.prepopulate(os.path.basename(testfile), test_file.read())
            test_cases = create_document(uri=os.path.basename(testfile), resolver=None, loader=ppl)

        for test_case in test_cases:
            
            for test in test_case['tests']:
                testids.append(f"draft4 -> {os.path.basename(testfile)} -> {test_case['description']} -> {test['description']}")
                argvalues.append(pytest.param(test_case['schema'], test['data'], test['valid']))

    metafunc.parametrize(argnames, argvalues, ids=testids)

def test_draft4_doc(schema, data, valid):
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(jacobsjsonschema.draft4.JsonSchemaValidationError):
            validator.validate(data)
