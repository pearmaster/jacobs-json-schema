"""
Uses a bunch of JSON Schema test data to validate a bunch of stuff"""

import pathlib
import os.path
import json
import pytest

from jacobsjsonschema.draft2019_09 import Validator
from jacobsjsonschema import draft4

testsuite_dir = pathlib.Path(__file__).parent.parent / "JSON-Schema-Test-Suite"

# Test files that exercise cross-document/$ref resolution or vocabulary features
# which the standalone (no jacobs-json-doc) validator does not support.
SPECIAL_TESTS = [
    "ref.json",
    "anchor.json",
    "defs.json",
    "recursiveRef.json",
    "refRemote.json",
]

# Individual cases that rely on annotation collection (unevaluatedItems /
# unevaluatedProperties), which the validator does not implement yet.
SKIP_TESTS = {
    (
        "unevaluatedProperties.json",
        "unevaluatedProperties with $recursiveRef",
        "with no unevaluated properties",
    ),
    (
        "unevaluatedProperties.json",
        "unevaluatedProperties with $recursiveRef",
        "with unevaluated properties",
    ),
    (
        "unevaluatedItems.json",
        "unevaluatedItems with $recursiveRef",
        "with no unevaluated items",
    ),
    (
        "unevaluatedItems.json",
        "unevaluatedItems with $recursiveRef",
        "with unevaluated items",
    ),
    (
        "vocabulary.json",
        "schema that uses custom metaschema with with no validation vocabulary",
        "no validation: invalid number, but it still validates",
    ),
}


def pytest_generate_tests(metafunc):
    argnames = ("schema", "data", "valid")
    argvalues = []
    testids = []

    testfile_dir = testsuite_dir / "tests" / "draft2019-09"

    for testfile in testfile_dir.glob("*.json"):
        if testfile.name in SPECIAL_TESTS:
            continue
        with testfile.open() as test_file:
            test_cases = json.load(test_file)

        for test_case in test_cases:

            for test in test_case["tests"]:
                testids.append(
                    "{} -> {} -> {}".format(
                        os.path.splitext(testfile.name)[0],
                        test_case["description"],
                        test["description"],
                    )
                )
                marks = ()
                if (
                    testfile.name,
                    test_case["description"],
                    test["description"],
                ) in SKIP_TESTS:
                    marks = (
                        pytest.mark.skip(reason="annotation collection not supported"),
                    )
                argvalues.append(
                    pytest.param(
                        test_case["schema"],
                        test["data"],
                        test["valid"],
                        marks=marks,
                    )
                )

    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_draft2019_09(schema, data, valid):
    validator = Validator(schema)
    if valid:
        assert validator.validate(data) == valid
    else:
        with pytest.raises(draft4.JsonSchemaValidationError):
            validator.validate(data)
