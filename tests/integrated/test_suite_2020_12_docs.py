"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import pytest
import json
import sys

if sys.version_info.minor >= 7:
    from jacobsjsondoc.document import create_document  # type: ignore[import-untyped]
    from jacobsjsondoc.options import JsonSchemaParseOptions  # type: ignore[import-untyped]

from .test_suite_4_docs import UnitTestFileFetcher

from jacobsjsonschema.draft2020_12 import Validator
from jacobsjsonschema import draft4

testsuite_dir = pathlib.Path(__file__).parent.parent / "JSON-Schema-Test-Suite"


def pytest_generate_tests(metafunc):
    argnames = ("schema", "data", "valid")
    argvalues = []
    testids = []

    if sys.version_info.minor >= 6:

        testfile_dir = testsuite_dir / "tests" / "draft2020-12"

        for testfile in testfile_dir.glob("*.json"):
            stem = os.path.splitext(os.path.basename(testfile))[0]

            with open(testfile, "r") as test_file:
                test_cases = json.load(test_file)

            for test_case in test_cases:
                ppl = UnitTestFileFetcher()
                ppl.prepopulate(
                    os.path.basename(testfile), json.dumps(test_case["schema"])
                )
                options = JsonSchemaParseOptions(dialect="2020-12")
                doc = create_document(
                    os.path.basename(testfile), fetcher=ppl, options=options
                )

                for test in test_case["tests"]:
                    testids.append(
                        f"{stem} -> {test_case['description']} -> {test['description']}"
                    )
                    argvalues.append(pytest.param(doc, test["data"], test["valid"]))

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_d2020_12_doc(schema, data, valid):
    if sys.version_info.minor < 7:
        pytest.skip()
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(draft4.JsonSchemaValidationError):
            validator.validate(data)
