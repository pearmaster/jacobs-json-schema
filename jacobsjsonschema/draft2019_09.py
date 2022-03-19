
from typing import Optional, List, Dict
import re

from .json_types import JsonTypes
from .draft7 import Validator as Draft7Validator, InvalidSchemaError as imported_ise, JsonSchemaValidationError as imported_jsve

InvalidSchemaError = imported_ise
JsonSchemaValidationError = imported_jsve

class PropName(str):
    def __new__(cls, *args, **kwargs):
        obj = str.__new__(cls, *args, **kwargs)
        obj._evaluated = False
        return obj

    @property
    def evaluated(self):
        return self._evaluated

    @evaluated.setter
    def evaluated(self, value):
        self._evaluated = value

class Validator(Draft7Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        del self.array_validators['contains']

        del self.object_validators['dependencies']
        self.object_validators.update({
            "dependentRequired": self._validate_dependency,
            "dependentSchemas": self._validate_dependency,
            "properties": self._validate_properties,
            "patternProperties": self._validate_pattern_properties,
        })
        self._warnings = []
    
    def get_warnings(self):
        return self._warnings

    def _report_format_warning(self, data, format):
        message = "String '{}' didn't conform to format {}".format(data, format)
        if hasattr(data, "line"):
            message = "Line {}: {}".format(data.line, message)
        self._warnings.append(message)
    
    def _validate_format(self, data:str, format:str) -> bool:
        """
        According to https://json-schema.org/draft/2019-09/release-notes.html#incompatible-changes
        format is no longer an assertation.
        """
        if format in self._format_validators:
            if not self._format_validators[format](data):
                self._report_format_warning(data, format)
        return True
    
    def _validate_contains(self, data:List[JsonTypes], schema:dict, min_contains:int=1, max_contains:Optional[int]=None) -> bool:
        occurances = self._contains_count(data, schema)
        if max_contains is None:
            max_contains = occurances + 1
        retval = True
        if occurances < min_contains:
            retval = self._report_validation_error("There were too few occurances {} in array that matched schema".format(occurances), data, min_contains) and retval
        if occurances > max_contains:
            retval = self._report_validation_error("There were too many occurances {} in array that matched schema".format(occurances), data, max_contains) and retval
        return retval

    def _array_validate(self, data:list, schema:dict) -> bool:
        retval = super()._array_validate(data, schema)
        if 'contains' in schema:
            if not isinstance(data, list):
                self._report_validation_error("Cannot evaluate a 'contains' against a non-array", data, schema)
            else:
                max_contains = schema['maxContains'] if 'maxContains' in schema else None
                min_contains = schema['minContains'] if 'minContains' in schema else 1
                retval = self._validate_contains(data, schema['contains'], min_contains, max_contains) and retval
        return retval

    def _validate_properties(self, data:dict, schema:Dict[str,dict]) -> bool:
        if not isinstance(schema, dict):
            raise InvalidSchemaError("Properties schema must be an object")
        if not isinstance(data, dict):
            return self._report_validation_error("Cannot validate properties on a non-object", data, schema)
        retval = True
        for k, v in data.items():
            if k in schema:
                retval = self.validate(v, schema[k]) and retval
                k.evaluated = True
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
                    k.evaluated = True
        return retval

    def _object_validate(self, data:dict, schema:dict) -> bool:

        new_data = dict()
        for propname, propval in data.items():
            new_data[PropName(propname)] = propval
        data = new_data

        retval = True

        for k, validator_func in self.object_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
    
        if 'additionalProperties' in schema:
            for propname in data.keys():
                propname.evaluated = True
            if isinstance(data, dict):
                property_keys = schema['properties'].keys() if 'properties' in schema else None
                property_patterns = schema['patternProperties'].keys() if 'patternProperties' in schema else None
                retval = self._validate_additional_properties(data, schema['additionalProperties'], property_keys, property_patterns) and retval
            else:
                retval = self._report_validation_error("Use of additionalProperties to validate a non-object", data, schema['additionalProperties'])

        if 'unevaluatedProperties' in schema:
            for propname, propvalue in data.items():
                if not propname.evaluated:
                    retval = retval and self.validate(propvalue, schema['unevaluatedProperties'])

        return retval