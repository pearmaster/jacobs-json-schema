
from typing import Optional, List

from .draft4 import InvalidSchemaError, JsonSchemaValidationError, JsonTypes
from .draft7 import Validator as Draft7Validator

class Validator(Draft7Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        del self.array_validators['contains']

        del self.object_validators['dependencies']
        self.object_validators.extend({
            "dependentRequired": self._validate_dependency,
            "dependentSchemas": self._validate_dependency,
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