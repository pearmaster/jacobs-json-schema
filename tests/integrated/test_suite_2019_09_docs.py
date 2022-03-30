"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import pytest
import json
import sys

if sys.version_info.minor >= 7:
    from jacobsjsondoc.document import create_document
    from jacobsjsondoc.options import JsonSchemaParseOptions, RefResolutionMode

from ..context import jacobsjsonschema
from .test_suite_4_docs import UnitTestFileLoader

from jacobsjsonschema.draft2019_09 import Validator, JsonSchemaValidationError

testsuite_dir = pathlib.Path(__file__).parent.parent / 'JSON-Schema-Test-Suite'

def pytest_generate_tests(metafunc):
    argnames = ('schema', 'data', 'valid')
    argvalues = []
    testids = []

    if sys.version_info.minor >= 6:

        testfile_dir = testsuite_dir / "tests" / "draft2019-09"

        for testfile in testfile_dir.glob("unevaluatedProperties.json"):

            with open(testfile, "r") as test_file:
                test_cases = json.load(test_file)
                print(testfile)

            for test_case in test_cases:
                ppl = UnitTestFileLoader()
                ppl.prepopulate(os.path.basename(testfile), json.dumps(test_case["schema"]))
                options = JsonSchemaParseOptions()
                options.dollar_id_token = Validator.get_dollar_id_token()
                options.ref_resolution_mode = RefResolutionMode.RESOLVE_REF_PROPERTIES
                doc = create_document(os.path.basename(testfile), loader=ppl, options=options)
                
                for test in test_case['tests']:
                    testids.append(f"{os.path.splitext(os.path.basename(testfile))[0]} -> {test_case['description']} -> {test['description']}")
                    argvalues.append(pytest.param(doc, test['data'], test['valid']))

    metafunc.parametrize(argnames, argvalues, ids=testids)

def test_d19_9_doc(schema, data, valid):
    if sys.version_info.minor < 7:
        pytest.skip()
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(JsonSchemaValidationError):
            validator.validate(data)
