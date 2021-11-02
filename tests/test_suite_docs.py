"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import pytest
import json
import sys
from pprint import pprint

if sys.version_info.minor >= 6:
    from jacobsjsondoc.loader import PrepopulatedLoader
    from jacobsjsondoc.document import create_document

from .context import jacobsjsonschema

from jacobsjsonschema.draft4 import Validator

testsuite_dir = pathlib.Path(__file__).parent / 'JSON-Schema-Test-Suite'

def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    if sys.version_info.minor >= 6:

        testfile_dir = testsuite_dir / "tests" / "draft4"

        for testfile in testfile_dir.glob("*.json"):
            with open(testfile, "r") as test_file:
                test_cases = json.load(test_file)

            for test_case in test_cases:
                ppl = PrepopulatedLoader()
                ppl.prepopulate("A", json.dumps(test_case["schema"]))
                doc = create_document("A", resolver=None, loader=ppl, dollar_id_token=Validator.get_dollar_id_token())
                
                for test in test_case['tests']:
                    testids.append(f"{os.path.splitext(os.path.basename(testfile))[0]} -> {test_case['description']} -> {test['description']}")
                    argvalues.append(pytest.param(doc, test['data'], test['valid']))

    metafunc.parametrize(argnames, argvalues, ids=testids)

def test_draft4_doc(schema, data, valid):
    if sys.version_info.minor < 6:
        pytest.skip()
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(jacobsjsonschema.draft4.JsonSchemaValidationError):
            validator.validate(data)
