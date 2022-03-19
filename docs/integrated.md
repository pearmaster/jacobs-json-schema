# Integrated Mode

"Integrated mode" means using `jacobs-json-schema` in a way that requires the `jacobs-json-doc` library to do post-parsing of the JSON Schema structure.  When doing so, it fulfils the full JSON Schema specification.

## Dependencies

 * [jacobs-json-doc](https://pypi.org/project/jacobs-json-doc/)
 * `jacobs-json-doc` requires Python 3.7 or later.

## Conformance

Integrated mode passes the [JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite) tests for: 

 * Draft-04
 * Draft-06
 * Draft-07

Other versions are untested.

## Usage

In integrated mode, the `jacobs-json-doc` library is used to parse the JSON text into a `jacobsjsondoc.document.Document` object.  

But we could do something similar that includes JSON parsing.

```py
import jacobsjsondoc

json_schema_text = '{ "type": "string" }'
schema = jacobsjsondoc.parse(json_schema_text)
validator = Validator(schema, lazy_error_reporting=True)

json_data_text = "Hello world"
data = json.loads(json_data_text)
if validator.validate(data):
    print("Validated")
else:
    print("Not Valid")
```

### File Loading

A JSON Schema `$ref` property can contain a URI to a file.  The `jacobs-json-doc` library provides a file loader mechanism.  

```py
from jacobsjsonschema.draft4 import Validator, JsonSchemaValidationError
from jacobsjsondoc.loader import FilesystemLoader
from jacobsjsondoc.document import Document

schema = Document(uri="/path/to/schema.json", loader=FilesystemLoader())

validator = Validator(schema)
try:
    validator.validate({"key": "value"})
except JsonSchemaValidationError as e:
    print("Did not validate")
else:
    print("Validated")

```

Note, that when using file loading, the initial schema document must be loaded through its URI.

