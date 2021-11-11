# jacobs-json-schema

[![CircleCI](https://circleci.com/gh/pearmaster/jacobs-json-schema/tree/main.svg?style=svg)](https://circleci.com/gh/pearmaster/jacobs-json-schema/tree/main) 
[![Coverage Status](https://coveralls.io/repos/github/pearmaster/jacobs-json-schema/badge.svg?branch=main)](https://coveralls.io/github/pearmaster/jacobs-json-schema?branch=main)

This package is yet another JSON Schema validator.  I wrote it because I needed something small to run in Python 3.5. 

Most data validation features are supported without any dependencies (see "Conformance").

## Usage

Before using this library, the schema dna data must already be parsed into a Python data structure.  This can be as simple as using `json.loads()`.

```py
from jacobsjsonschema.draft4 import Validator

schema = { "type": "string" }
validator = Validator(schema)

data = "Hello world"
validator.validate(data)
# Will throw if there are any validation errors
```

Lazy error reporting is also supported.  This means that as much of the data as possible is evaluated, and errors are collected instead of raising an exception.

```py
schema = { "type": "string" }
validator = Validator(schema, _lazy_error_reporting=True)

data = "Hello world"
if validator.validate(data):
    print("Validated")
else:
    for error in validator.get_errors():
        print(error)
```

## Conformance

There are two ways of running the validator: 
1. Passing a JSON-deserialized Python dictionary as the schema.  There are no additional external dependencies needed.  Straightforward `$ref` references (no usage of `$id`) within the same schema are supported.
2. Parse the schema using utility from the `jacobs-json-doc` python package, and pass the wrapped schema to the validator.  Several external dependencies are required.  Full `$id` and `$ref` functionality is supported.

Where "Mostly" is specified, it passes all tests excluding those from `ref.json`, `id.json`, `defintions.json`, `refRemote.json` and `unknownKeyword.json`.  

| Specification | Standalone | using jacobs-json-doc |
|---------------|------------|-----------------------|
| Draft-04      | Mostly     | Passed                |
| Draft-06      | Mostly     | Untested              |
| Draft-07      | Untested   | Untested              |
| Draft-2019-09 | Untested   | Untested              |
| Draft-2020-12 | Untested   | Untested              |

## License

GPLv2.  If you modify the source, please publish your modifications.  