
from typing import Union, List, Dict, Optional, Callable

import re

from .bool_compare_util import replace_bools_for_comparison

class JsonSchemaValidationError(Exception):
    pass

class InvalidSchemaError(Exception):
    pass

JsonTypes = Union[str,dict,list,int,float,None]

class Validator(object):

    def __init__(self, schema:dict, lazy_error_reporting=False):
        self.generic_validators = {
            "type": self._validate_type,
            "anyOf": self._validate_anyof,
            "allOf": self._validate_allof,
            "oneOf": self._validate_oneof,
            "not": self._validate_not,
            "enum": self._validate_enum,
        }
        self.value_validators = {
            "minLength": self._validate_minlength,
            "maxLength": self._validate_maxlength,
            "pattern": self._validate_pattern,
            "format": self._validate_format,
            "multipleOf": self._validate_multipleof,
        }
        self.array_validators = {
            "maxItems": self._validate_maxitems,
            "minItems": self._validate_minitems,
            "uniqueItems": self._validate_uniqueitems,
        }
        self.object_validators = {
            "properties": self._validate_properties,
            "patternProperties": self._validate_pattern_properties,
            "required": self._validate_required,
            "minProperties": self._validate_minproperties,
            "maxProperties": self._validate_maxproperties,
            "dependencies": self._validate_dependency,
        }
        self._format_validators = {
            'date-time': self._is_format_datetime
        }
        self._root_schema = schema
        self._file_loader = None
        self._temp_ignore_errors = False
        self._lazy_error_reporting = lazy_error_reporting
        self._errors = []

    @staticmethod
    def get_dollar_id_token() -> str:
        return "id"

    def get_errors(self) -> List[str]:
        return self._errors

    def add_format(self, name:str, validator_func:Callable[[Union[str, int, float]],bool]):
        self._format_validators[name] = validator_func

    def set_file_loader(self, file_loader_func:Callable[[str],dict]):
        self._file_loader = file_loader_func

    def walk_schema_from_root(self, path:str) -> dict:
        parts = path.split('/')
        node = self._root_schema
        for part in parts[1:]:
            node = node[part]
        return node

    def validate_from_reference(self, data, dollar_ref):
        uri, path = dollar_ref.split('#')
        if len(uri) > 0:
            try:
                loader = self._root_schema._loader
                remote_schema_root = loader.load(uri)
            except:
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
        if hasattr(data, "line") and data.line is not None:
            message = "Input line {}: {}".format(data.line, message)
        if hasattr(schema, "line") and schema.line is not None:
            message = "{} (schema line {})".format(message, schema.line)
        if not self._lazy_error_reporting:
            raise JsonSchemaValidationError(message)
        if not self._temp_ignore_errors:
            self._errors.append(message)
        return False

    def _validate_type_integer(self, data:int, schema_type) -> bool:
        if isinstance(data, bool) or not isinstance(data, int):
            return self._report_validation_error("The value '{}' is not an integer", data, schema_type)
        return True

    def _validate_type(self, data:JsonTypes, schema_type:Union[str,list]) -> bool:
        if isinstance(schema_type, list):
            for st in schema_type:
                try:
                    if self._validate_type(data, st):
                        return True
                except JsonSchemaValidationError:
                    pass
            return self._report_validation_error("Data was not a {}".format(" or ".join(schema_type)), data, schema_type)
        mapping = {
            "string": str,
            "array": list,
            "object": dict,
            "boolean": bool,
        }
        if schema_type == 'integer':
            return self._validate_type_integer(data, schema_type)
        elif schema_type == 'null':
            if data is not None:
                return self._report_validation_error("Data type was not null", data, schema_type)
        elif schema_type == 'number':
            if isinstance(data, bool) or (not isinstance(data, int) and not isinstance(data, float)):
                return self._report_validation_error("Data was not a number", data, schema_type)
            else:
                return True
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
        retval = True
        for k, v in data.items():
            if k in schema:
                retval = self.validate(v, schema[k]) and retval
        return retval

    def _validate_pattern_properties(self, data:Dict[str,JsonTypes], schema:Dict[str,dict]) -> bool:
        if not isinstance(data, dict):
            return self._report_validation_error("patternProperties will only validate against an object", data, schema)
        if not isinstance(schema, dict):
            raise InvalidSchemaError("patternProperties must be an object")
        retval = True
        for regex_expression, subschema in schema.items():
            pattern = re.compile(regex_expression)
            for k, v in data.items():
                if pattern.search(k):
                    retval = retval and self.validate(v, subschema)
        return retval

    def _validate_additional_properties(self, data:dict, additional:Union[bool,dict], property_keys:Optional[List[str]]=None, property_patterns:Optional[List[str]]=None) -> bool:
        if not isinstance(data, dict):
            return self._report_validation_error("additionalProperties will only validate against an object", data, additional)
        retval = True
        if additional or additional is not True:
            for propname in data.keys():
                found_somewhere = False
                if property_keys is not None and propname in property_keys:
                    found_somewhere = True
                if property_patterns is not None:
                    for regex_expression in property_patterns:
                        if re.search(regex_expression, propname):
                            found_somewhere = True
                if not found_somewhere:
                    if additional is not False and self.validate(data[propname], additional):
                        continue
                    retval = self._report_validation_error("The property '{}' is an additional property which is not allowed".format(propname), data, additional) and retval
        return retval

    def _validate_maxproperties(self, data:dict, schema:int) -> bool:
        num_props = len(data)
        if num_props > schema:
            return self._report_validation_error("There are too many properties {} on the object".format(num_props), data, schema)
        return True

    def _validate_minproperties(self, data:dict, schema:int) -> bool:
        num_props = len(data)
        if num_props < schema:
            return self._report_validation_error("There are too few properties {} on the object".format(num_props), data, schema)
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

    def _validate_dependency(self, data:dict, required:Dict[str,Union[list,dict]]) -> bool:
        retval = True
        for requirement, consequence in required.items():
            if requirement in data:
                if isinstance(consequence, list):
                    retval = self._validate_required(data, consequence) and retval
                elif isinstance(consequence, dict):
                    retval = self.validate(data, consequence) and retval
                else:
                    return InvalidSchemaError("Dependency must be either a list or a schema")
        return retval

    def _validate_anyof(self, data:JsonTypes, schemas:list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        for schema in schemas:
            try:
                self._temp_ignore_errors = True
                if self.validate(data, schema):
                    self._temp_ignore_errors = False
                    return True
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        return self._report_validation_error("The JSON data did not match any of the provided anyOf schemas", data, schemas)

    def _validate_oneof(self, data:JsonTypes, schemas:list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        valid_count = 0
        for schema in schemas:
            try:
                self._temp_ignore_errors = True
                if self.validate(data, schema):
                    valid_count += 1
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        if valid_count != 1:
            return self._report_validation_error("The data matched against {} schemas but was required to match exactly 1".format(valid_count), data, schemas)
        return True

    def _validate_allof(self, data:JsonTypes, schemas:List[dict]) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("AnyOf schema was not a list")
        retval = True
        for schema in schemas:
            retval = self.validate(data, schema) and retval
        return retval

    def _validate_not(self, data:JsonTypes, schema:dict) -> bool:
        try:
            self._temp_ignore_errors = True
            if not self.validate(data, schema):
                self._temp_ignore_errors = False
                return True
        except InvalidSchemaError:
            raise
        except JsonSchemaValidationError:
            self._temp_ignore_errors = False
            return True
        except Exception:
            raise
        else:
            self._temp_ignore_errors = False
            return self._report_validation_error("The data matched against the schema when it was not supposed to", data, schema)

    def _validate_enum(self, data:JsonTypes, schema:List[JsonTypes]) -> bool:
        if not isinstance(schema, list):
            raise InvalidSchemaError("The enum restriction must be a list of values")
        if isinstance(data, bool):
            if data:
                for x in schema:
                    if x is True:
                        return True
            else:
                for x in schema:
                    if x is False:
                        return True
        elif isinstance(data, float):
            for x in schema:
                if ((isinstance(x, int) or isinstance(x, float)) and not isinstance(x, bool)) and data == float(x):
                    return True
        elif isinstance(data, int):
            for x in schema:
                if (isinstance(x, float) or isinstance(x, int) and not isinstance(x, bool)) and data == int(x):
                    return True
        elif data in schema:
            return True

        return self._report_validation_error("The value '{}' was not in the enumerated list of allowed values".format(data), data, schema)


    def _validate_minlength(self, data:str, length:int) -> bool:
        if not isinstance(length, int):
            raise InvalidSchemaError("The minLength value must be an integer")
        if not isinstance(data, str):
            #minLength ignores non-strings per spec
            return True
        if len(data) < length:
            return self._report_validation_error("The data length {} was less than the minimum {}".format(len(data), length), data, length)
        return True

    def _validate_maxlength(self, data:str, length:int) -> bool:
        if not isinstance(length, int):
            raise InvalidSchemaError("The maxLength value must be an integer")
        if not isinstance(data, str):
            # MaxLength ignores non-strings per spec
            return True
        if len(data) > length:
            return self._report_validation_error("Length of '{}' is more than maximum {}".format(len(data), length), data, length)
        return True

    def _validate_pattern(self, data:str, pattern:str) -> bool:
        if not isinstance(data, str):
            return True
        if not re.search(pattern, data):
            return self._report_validation_error("The string '{}' did not match the pattern '{}'".format(data, pattern), data, pattern)
        return True

    def _validate_format(self, data:str, format:str) -> bool:
        if format in self._format_validators:
            return self._format_validators[format](data)
        return True

    def _is_format_datetime(self, data:str) -> bool:
        return True

    def _validate_maximum(self, data:Union[float,int], value:int, exclusive=False) -> bool:
        if not isinstance(data, float) and not isinstance(data, int):
            # Per spec, ignore non-numbers
            return True
        if (data > value) or (data == value and exclusive is True):
            return self._report_validation_error("The value {} is greater than the maximum {}".format(data, value), data, value)
        return True

    def _validate_minimum(self, data:Union[float,int], value:int, exclusive=False) -> bool:
        if not isinstance(data, float) and not isinstance(data, int):
            # Per spec, ignore non-numbers
            return True
        if (data < value) or (data == value and exclusive is True):
            return self._report_validation_error("The value {} is less than the minimum {}".format(data, value), data, value)
        return True

    def _validate_multipleof(self, data:Union[float,int], value:Union[float,int]) -> bool:
        if not isinstance(data, float) and not isinstance(data, int):
            return True
        remainder = (data % value)
        if remainder != 0:
            # Handle float imprecision
            if isinstance(value, float) and value < 1.0:
                multiplier = int(1.0/value)
                if ((multiplier*data) % (multiplier*value)) == 0:
                    return True
            return self._report_validation_error("The value {} is not a multiple of {}".format(data, value), data, value)
        return True

    def _validate_prefixitems(self, data:list, schema:list) -> bool:
        retval = True
        for idx, item in enumerate(data):
            retval = self.validate(item, schema[idx]) and retval
        return retval

    def _validate_items(self, data:list, schema:Union[list, dict], additionalItems=True) -> bool:
        retval = True
        if isinstance(schema, list):
            data_len = len(data)
            schema_len = len(schema)
            if data_len <= schema_len:
                return self._validate_prefixitems(data[:schema_len], schema)
            else:
                if additionalItems:
                    retval = self._validate_prefixitems(data[:schema_len], schema)
                    for item in data[schema_len:]:
                        retval = ((additionalItems is True) or self.validate(item, additionalItems)) and retval
                    return retval
                else:
                    return self._report_validation_error("There are too many items when additional items is false", data, schema)
        for item in data:
            retval = self.validate(item, schema) and retval
        return retval

    def _validate_maxitems(self, data:list, maximum:int) -> bool:
        if len(data) > maximum:
            return self._report_validation_error("There were more items {} than the maximum {}".format(len(data), maximum), data, maximum)
        return True

    def _validate_minitems(self, data:list, minimum:int) -> bool:
        if len(data) < minimum:
            return self._report_validation_error("There were fewer items {} than the minimum {}".format(len(data), minimum), data, minimum)
        return True

    def _validate_uniqueitems(self, data:list, uniqueness:bool) -> bool:
        def is_unique(data:list) -> bool:
            found = []
            for item in data:
                fixed_item = replace_bools_for_comparison(item)
                if fixed_item in found:
                    return False
                found.append(fixed_item)
            return True

        if uniqueness is False:
            return True
        num_items = len(data)

        try:
            # Easy way
            unique_items = len(set(data))
            if num_items == unique_items:
                return True
        except TypeError:
            pass

        if not is_unique(data):
            return self._report_validation_error("There were items which were not unique", data, uniqueness)

        return True

    def _array_validate(self, data:list, schema:dict) -> bool:
        retval = True
        additionalItems = schema['additionalItems'] if 'additionalItems' in schema else True
        if 'items' in schema:
            retval = self._validate_items(data, schema['items'], additionalItems)
        for k, validator_func in self.array_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
        return retval

    def _object_validate(self, data:dict, schema:dict) -> bool:
        retval = True
        for k, validator_func in self.object_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
        if 'additionalProperties' in schema:
            if isinstance(data, dict):
                property_keys = schema['properties'].keys() if 'properties' in schema else None
                property_patterns = schema['patternProperties'].keys() if 'patternProperties' in schema else None
                retval = self._validate_additional_properties(data, schema['additionalProperties'], property_keys, property_patterns) and retval
            else:
                retval = self._report_validation_error("Use of additionalProperties to validate a non-object", data, schema['additionalProperties'])
        return retval

    def _value_validate(self, data:Union[int,float,str,None], schema:dict) -> bool:
        retval = True
        if 'maximum' in schema:
            exclusive = schema['exclusiveMaximum'] if 'exclusiveMaximum' in schema else False
            retval = self._validate_maximum(data, schema['maximum'], exclusive=exclusive) and retval
        if 'minimum' in schema:
            exclusive = schema['exclusiveMinimum'] if 'exclusiveMinimum' in schema else False
            retval = self._validate_minimum(data, schema['minimum'], exclusive=exclusive) and retval
        for k, validator_func in self.value_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
        return retval

    def _validate(self, data:JsonTypes, schema:dict) -> bool:
        retval = True
        if hasattr(schema, "_reference"):
            resolved_schema = schema.resolve()
            return self.validate(data, resolved_schema) and retval
        elif '$ref' in schema:
            return self.validate_from_reference(data, schema['$ref']) and retval
        for k, validator_func in self.generic_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
        if isinstance(data, list):
            retval = self._array_validate(data, schema) and retval
        elif isinstance(data, dict):
            retval = self._object_validate(data, schema) and retval
        else:
            retval = self._value_validate(data, schema) and retval
        return retval

    def validate(self, data:JsonTypes, schema:Optional[dict]=None) -> bool:
        if schema is None:
            schema = self._root_schema
        return self._validate(data, schema)



if __name__ == '__main__':
    test_validate()
    