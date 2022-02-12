# Documentation for `jacobs-json-docs`

JSON Schema is a way of validating that a JSON structure has a particular form. 

This project is a JSON Schema validator.  Given a schema and a structure, it validates that the structure conforms to the contraints of the schema.

### Alternatives

There are other python libraries that do JSON Schema validation.  This project aims to be slightly different from alternatives in these aspects:
 * More memory efficient (perhaps at the expense of speed).
 * Minimize external dependencies.