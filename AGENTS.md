# jacobs-json-schema

This is a pure python JSON Schema validator.  The code must run on a Python 3.7 interpreter, though code verification tools are allowed to run in later version of Python. 

Do not remove Python 3.7 from the list of supported Python versions.

The project is managed with Astral's `uv`.  This means instead of running `pytest` or `python -m pytest` the correct command is `uv pytest`.

## Verification

Tasks can be run to perform certain common verifcation actions:

* all:         Run all checks and tests
* black:       Run black formatter
* mypy:        Run mypy type checker
* ruff:        Run ruff linter
* test:        Run all tests

### Test Suite

A Git Submodule is used to bring in a standardized test of JSON Schema tests: `tests/JSON-Schema-Test-Suite`.  Certain unit tests are skipped when the git submodule is not initialized.  The AI Agent should ensure initialization of the submodule when it detects skipped unit tests.

Specific test suites can be run by running these commands:

* `task test:draft4`
* `task test:draft6`
* `task test:draft7`
* `task test:draft2019-09`
* `task test:draft2020-12`

In order to assert that changes do not create regressions, always make sure that the draft4, draft6, and draft7 test suites pass with no failures.

## JSON Document Parsing

The schema validator can take python structures as both the data and schema.  However, for full checking across multiple documents using `$ref`, `$id`, `$recursiveRef`, `$anchor`, `$dynamicRef`, `$dynamicAnchor` and other `$`-prefixed constructs, the `jacobs-json-doc` package should be used.  Full JSON Schema conformance requires use of `jacobs-json-doc` although small use cases which don't need full conformance can skip it.

The `jacobs-json-doc` project is meant to handle document references that are used in non-schema JSON/YAML specifications like OpenAPI or AsyncAPI.  It provides a base document representation that the `jacobs-json-schema` project builds on.

### Development

The author of `jacobs-json-schema` is also the author of `jacobs-json-doc`, and the two projects can be updated and released simultaneously.  When AI agents attempt to fix a bug, implement a feature, or solve a problem, they should see if both projects are in the workspace or otherwise ask the user to be able to modify both projects in order to create the best design.

## Code development between projects

The `jacobs-json-schema` project deals directly with *validation* of JSON-compatible data structures.  It's job is to evaluate the conformance of a data structure to a specific schema. 

The `jacobs-json-doc` project deals with inter- and intra- document references in order to provide an arranged data structure that is ready for evaluation.  It deals with 

When an AI agent is tasked with fixing a bug, implementing a feature, or solving a problem, it should consider both projects and provide code changes in the appropriate project.  For work dealing with `$ref`, `$id`, `$recursiveRef`, `$anchor`, `$dynamicRef`, `$dynamicAnchor` and other `$`-prefixed constructs, the changes probably should happen in the `jacobs-json-doc` project.   For work dealing with `type` constraints, value constraints, `properties`, data dependencies, `allOf`, `anyOf`, `oneOf`, `not`, if/then/else, `unevaluatedProperties`, `unevaluatedItems`, or other specific data checks or contraints, the changes should probably happen in the `jacobs-json-schema` project.