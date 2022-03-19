# Standalone Mode

"Standalone mode" means using `jacobs-json-schema` in a way that doesn't require dependencies to provide the most common JSON Schema functionality.

## Dependencies

In standalone mode, there aren't any dependencies.  Everything is implemented in pure Python3.

It requires Python 3.5 or later.

## Conformance

Standalone mode doesn't _fully_ conform with any of the JSON Schema drafts.  It fails conformance with schemas that use `$id` and has some conformance issues with complicated `$ref` usage.  

With those exceptions, standalone mode implements: Draft-04, Draft-06, and Draft-07 versions of the JSON Schema specification.

## Usage

In stand alone mode, the caller does all JSON parsing and passes Python structures (representing the JSON) to the validator.  

The example, doesn't use any JSON at all.  It only uses Python structures.

```py
from jacobsjsonschema.draft4 import Validator

schema = { "type": "string" }
validator = Validator(schema, lazy_error_reporting=True)

data = "Hello world"
if validator.validate(data):
    print("Validated")
else:
    print("Not Valid")
```

But we could do something similar that includes JSON parsing.

```py
from jacobsjsonschema.draft6 import Validator
import json

json_schema_text = '{ "type": "string" }'
schema = json.loads(json_schema_text)
validator = Validator(schema, lazy_error_reporting=True)

json_data_text = "Hello world"
data = json.loads(json_data_text)
if validator.validate(data):
    print("Validated")
else:
    print("Not Valid")
```

### `$ref` File Loading

Standalone usage does not, by itself, conform to the JSON Schema rules of loading files providing in `$ref` references.  However, the caller can provide a function that performs the file loading.  The function would have this structure:

```py
def load_file(uri: str) -> dict:
    """ The URI from the `$ref` reference is provided as an argument.  The URI is everything before the `#` in the `#ref` reference.

    The function loads the file, parses it, then returns a Python dictionary representation of the file contents.

    We assume that we are loading a JSON Schema file, which is a JSON object (thus we return a Python dictionary.)
    """
    pass
```

A super simple implementation would look like this, (as long as the URI is just referencing a local JSON file):

```py
import json

def load_file(uri: str) -> dict:
    with open(uri, "r") as fp:
        return json.load(fp)
```

The file loading function needs to be provided to the validator.  That can be accomplished by calling the `set_file_loader(Callable[[str],dict]):` method on the validator like this:

```py
from jacobsjsonschema.draft7 import Validator
import json

def load_file(uri: str) -> dict:
    with open(uri, "r") as fp:
        return json.load(fp)

# Using `load_file()` to load the base schema is convenient, but not required.
schema = load_file("base_schema.json")
validator = Validator(schema)
validator.set_file_loader(load_file)
```
