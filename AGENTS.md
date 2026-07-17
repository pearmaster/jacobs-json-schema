# jacobs-json-schema

This is a pure python JSON Schema validator.  The code must run on a Python 3.7 interpreter, though code verification tools are allowed to run in later version of Python. 

Do not remove Python 3.7 from the list of supported Python versions.

The project is managed with Astral's `uv`.

## Verification

Tasks can be run to perform certain common verifcation actions:

* all:         Run all checks and tests
* black:       Run black formatter
* mypy:        Run mypy type checker
* ruff:        Run ruff linter
* test:        Run all tests

### Test Suite

A Git Submodule is used to bring in a standardized test of JSON Schema tests: `tests/JSON-Schema-Test-Suite`.  Certain unit tests are skipped when the git submodule is not initialized.  The AI Agent should ensure initialization of the submodule when it detects skipped unit tests.

## JSON Document Parsing

The schema validator can take python structures as both the data and schema.  However, for full checking across multiple documents using `$ref`, `$id`, and other reference identifiers, the `jacobs-json-doc` package should be used.  Full JSON Schema conformance requires use of `jacobs-json-doc` although small use cases which don't need full conformance can skip it.
