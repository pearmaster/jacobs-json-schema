
from typing import Union, List, Dict, Optional, Callable

class JsonSchemaValidationError(Exception):
    pass

class InvalidSchemaError(Exception):
    pass

JsonTypes = Union[str,dict,list,int,float,None]

class Validator(object):

    def __init__(self, schema:dict, _lazy_error_reporting=False):
        self.validators = {
            "type": self._validate_type,
            "properties": self._validate_properties,
            "patternProperties": self._validate_pattern_properties,
            "required": self._validate_required,
            "anyOf": self._validate_anyof,
            "allOf": self._validate_allof,
            "oneOf": self._validate_oneof,
            "not": self._validate_not,
            "enum": self._validate_enum,
            "minLength": self._validate_minlength,
            "maxLength": self._validate_maxlength,
            "pattern": self._validate_pattern,
            "minimum": self._validate_minimum,
            "maximum": self._validate_maximum,
            "items": self._validate_items,
            "maxItems": self._validate_maxitems,
            "format": self._validate_format,
        }
        self._format_validators = {
            'date-time': self._is_format_datetime
        }
        self._root_schema = schema
        self._file_loader = None
        self._lazy_error_reporting = _lazy_error_reporting
        self._errors = []

    def get_errors(self) -> List[str]:
        return self._errors

    def add_format(self, name:str, validator_func:Callable[[Union[str, int, float]],bool]):
        self._format_validators[name] = validator_func

    def set_file_loader(self, file_loader_func:Callable[[str],dict]):
        self._file_loader = file_loader_func

    def walk_schema_from_root(self, path:str) -> dict:
        parts = path.split('/')
        if parts[0] != '#':
            raise InvalidSchemaError("$ref '{}' could not be handled because it didn't start with '#'".format(path))
        node = self._root_schema
        for part in parts[1:]:
            node = self._root_schema[part]
        return node

    def validate_from_reference(self, data, dollar_ref):
        uri, path = dollar_ref.split('#')
        if len(uri) > 0:
            if self._file_loader is None:
                raise Exception("Unable to load '{}' because file loader was not set".format(uri))
            remote_schema_root = self._file_loader(uri)
            remote_schema_validator = Validator(remote_schema_root)
            remote_schema = remote_schema_validator.walk_schema_from_root(path)
            return remote_schema_validator.validate(data, remote_schema)
        else:
            schema = self.walk_schema_from_root(path)
            return self.validate(data, schema)

    def _report_validation_error(self, message:str, data=None, schema=None) -> bool:
        if hasattr(data, "line"):
            message = "Input line {}: {}".format(data.line, message)
        if hasattr(schema, "line"):
            message = "{} (schema line {})".format(message, schema.line)
        if not self._lazy_error_reporting:
            raise JsonSchemaValidationError(message)
        self._errors.append(message)
        return False

    def _validate_type_integer(self, data:int, schema_type) -> bool:
        if not isinstance(data, int):
            return self._report_validation_error("The value '{}' is not an integer", data, schema_type)
        return True

    def _validate_type(self, data:JsonTypes, schema_type:str) -> bool:
        mapping = {
            "string": str,
            "array": list,
            "object": dict
        }
        if schema_type == 'integer':
            return self._validate_type_integer(data, schema_type)
        elif schema_type == 'null' and data is not None:
            return self._report_validation_error("Data type was not null", data, schema_type)
        elif schema_type == 'number' and (not isinstance(data, int) and not isinstance(data, float)):
            return self._report_validation_error("Data was not a number", data, schema_type)
        elif schema_type in mapping:
            if not isinstance(data, mapping[schema_type]):
                return self._report_validation_error("Data was not a {}".format(schema_type), data, schema_type)
        else:
            raise InvalidSchemaError("Unknown type '{}'".format(schema_type))
        return True

    def _validate_properties(self, data:dict, schema:Dict[str,dict]) -> bool:
        if not isinstance(schema, dict):
            raise InvalidSchemaError("Properties schema must be an object")
        if not isinstance(data, dict):
            return self._report_validation_error("Cannot validate properties on a non-object", data, schema)
        for k, v in data.items():
            if k in schema:
                self.validate(v, schema[k])
        return True

    def _validate_pattern_properties(self, data:dict, schema:Dict[str,dict]) -> bool:
        return True

    def _validate_additional_properties(self, data:dict, additional:bool, property_keys:Optional[List[str]]=None, property_patterns:Optional[List[str]]=None) -> bool:
        return True

    def _validate_required(self, data:dict, schema:List[str]) -> bool:
        if not isinstance(data, dict):
            return self._report_validation_error("Required schema requires an object", data, schema)
        if not isinstance(schema, list):
            raise InvalidSchemaError("Required must be a list of property names")
        for item in schema:
            if not isinstance(item, str):
                raise InvalidSchemaError("Required property name must be a string")
            if item not in data:
                return self._report_validation_error("The '{}' property is required but was missing".format(item), data, schema)
        return True

    def _validate_anyof(self, data:JsonTypes, schemas:list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        for schema in schemas:
            try:
                self.validate(data, schema)
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            else:
                return True
        return self._report_validation_error("The JSON data did not match any of the provided anyOf schemas", data, schemas)

    def _validate_oneof(self, data:JsonTypes, schemas:list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        valid_count = 0
        for schema in schemas:
            try:
                self.validate(data, schema)
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            else:
                valid_count += 1
        if valid_count != 1:
            return self._report_validation_error("The data matched against {} schemas but was required to match exactly 1".format(valid_count), data, schemas)
        return True

    def _validate_allof(self, data:JsonTypes, schemas:List[dict]) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        for schema in schemas:
            self.validate(data, schema)
        return True

    def _validate_not(self, data:JsonTypes, schema:dict) -> bool:
        try:
            self.validate(data, schema)
        except InvalidSchemaError:
            raise
        except JsonSchemaValidationError:
            return True
        except Exception:
            raise
        else:
            return self._report_validation_error("The data matched against the schema when it was not supposed to", data, schema)

    def _validate_enum(self, data:JsonTypes, schema:List[JsonTypes]) -> bool:
        if not isinstance(schema, list):
            raise InvalidSchemaError("The enum restriction must be a list of values")
        if data not in schema:
            return self._report_validation_error("The value '{}' was not in the enumerated list of allowed values".format(data), data, schema)
        return True

    def _validate_minlength(self, data:str, length:int) -> bool:
        if not isinstance(length, int):
            raise InvalidSchemaError("The minLength value must be an integer")
        if not isinstance(data, str):
            return self._report_validation_error("The data for minLength was not a string", data, length)
        if len(data) < length:
            return self._report_validation_error("The data length {} was less than the minimum {}".format(len(data), length), data, length)
        return True

    def _validate_maxlength(self, data:str, length:int) -> bool:
        if not isinstance(length, int):
            raise InvalidSchemaError("The maxLength value must be an integer")
        if not isinstance(data, str):
            return self._report_validation_error("Cannot determine length of non-string '{}'".format(data), data, length)
        if len(data) > length:
            return self._report_validation_error("Length of '{}' is more than maximum {}".format(len(data), length), data, length)
        return True

    @staticmethod
    def _validate_pattern(data:str, pattern:str) -> bool:
        return True

    def _validate_format(self, data:str, format:str) -> bool:
        if format in self._format_validators:
            return self._format_validators[format](data)
        return True

    def _is_format_datetime(self, data:str) -> bool:
        return True

    @staticmethod
    def _validate_maximum(data:Union[float,int], value:int) -> bool:
        return True

    @staticmethod
    def _validate_minimum(data:Union[float,int], value:int) -> bool:
        return True

    def _validate_items(self, data:list, schema:dict) -> bool:
        return True

    def _validate_maxitems(self, data:list, maximum:int) -> bool:
        return True

    def _validate_minitems(self, data:list, minimum:int) -> bool:
        return True

    def validate(self, data:JsonTypes, schema:Optional[dict]=None) -> bool:
        if schema is None:
            schema = self._root_schema
        if '$ref' in schema:
            return self.validate_from_reference(data, schema['$ref'])
        for k, validator_func in self.validators.items():
            if k in schema:
                validator_func(data, schema[k])
        if 'additionalProperties' in schema:
            if isinstance(data, dict):
                property_keys = schema['properties'].keys() if 'properties' in schema else None
                property_patterns = schema['patternProperties'].keys() if 'patternProperties' in schema else None
                self._validate_additional_properties(data, schema['additionalProperties'], property_keys, property_patterns)
            else:
                self._report_validation_error("Use of additionalProperties to validate a non-object", data, schema['additionalProperties'])

        return True

def test_validate():
    data = {
        "foo": "bar"
    }
    schema = {
        "type": "object",
        "properties": {
            "foo": {
                "type": "string",
                "enum": [
                    "bar",
                    "fred",
                ]
            }
        },
        "required": ["foo"],
        "anyOf": [
            {"type": "object"}
        ],
        "allOf": [
            {"type": "object"}
        ],
        "oneOf": [
            {"type": "string"},
            {"type": "object"},
        ]
    }
    validator = Validator(schema)
    assert(validator.validate(data))

if __name__ == '__main__':
    test_validate()
    