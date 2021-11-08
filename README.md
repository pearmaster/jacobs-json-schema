# jacobs-json-schema

## Conformance

There are two ways of running the validator: 
1. Passing a JSON-deserialized Python dictionary as the schema.  There are no additional external dependencies needed.  Straightforward `$ref` references (no usage of `$id`) within the same schema are supported.
2. Parse the schema using utility from the `jacobs-json-doc` python package, and pass the wrapped schema to the validator.  Several external dependencies are required.  Full `$id` and `$ref` functionality is supported.

Where "Mostly" is specified, it passes all tests excluding those from `ref.json`, `id.json`, `defintions.json` and `refRemote.json`.  

| Specification | Standalone | using jacobs-json-doc |
|---------------|------------|-----------------------|
| Draft-04      | Mostly     |                       |
| Draft-06      |            |                       |
| Draft-07      | Untested   | Untested              |
| Draft-2019-09 | Untested   | Untested              |
| Draft-2020-12 | Untested   | Untested              |
