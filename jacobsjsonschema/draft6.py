
from typing import Union, Optional, List
from math import modf

from .draft4 import Validator as Draft4Validator, JsonTypes, JsonSchemaValidationError

class Validator(Draft4Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        self.value_validators["const"] = self._validate_const
        self.array_validators["contains"] = self._validate_contains
    
    def _validate_type_integer(self, data:Union[int, float], schema_type) -> bool:
        if isinstance(data, float):
            fractional_part, _ = modf(data)
            if fractional_part != 0:
                self._report_validation_error("The data value '{}' is not an integer".format(data), data, schema_type)
        elif not isinstance(data, int):
            self._report_validation_error("The data value '{}' is not an integer".format(data), data, schema_type)
        return True

    def _validate_const(self, data:JsonTypes, const_value:dict) -> bool:
        if data != const_value:
            self._report_validation_error("The data value '{}' was not the const value '{}'".format(data, const_value), data, const_value)
        return True

    def _contains_count(self, data:List[JsonTypes], schema:dict) -> int:
        occurances = 0
        for item in data:
            self._temp_ignore_errors = True
            try:
                if self.validate(item, schema):
                    occurances += 1
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        return occurances

    def _validate_contains(self, data:List[JsonTypes], schema:dict) -> bool:
        occurances = self._contains_count(data, schema)
        if occurances < 1:
            return self._report_validation_error("There weren't any occurances in the array", data, schema)
        return True

    def _validate(self, data:JsonTypes, schema:Union[dict,bool]) -> bool:
        if schema is True:
            return True
        if schema is False:
            return self._report_validation_error("False schema always fails validation", data, schema)
        return super()._validate(data, schema)

    def validate(self, data:JsonTypes, schema:Union[dict,bool,None]=None) -> bool:
        if schema is None:
            schema = self._root_schema
        return self._validate(data, schema)