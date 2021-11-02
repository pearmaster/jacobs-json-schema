
from typing import Union, Optional, List
from math import modf

from .draft4 import Validator as Draft4Validator, JsonTypes, JsonSchemaValidationError

class Validator(Draft4Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        self.generic_validators["const"] = self._validate_const
        self.array_validators["contains"] = self._validate_contains
    
    @staticmethod
    def get_dollar_id_token() -> str:
        return "$id"

    def _validate_type_integer(self, data:Union[int, float], schema_type) -> bool:
        if isinstance(data, float):
            fractional_part, _ = modf(data)
            if fractional_part != 0:
                self._report_validation_error("The data value '{}' is not an integer".format(data), data, schema_type)
        elif not isinstance(data, int):
            self._report_validation_error("The data value '{}' is not an integer".format(data), data, schema_type)
        return True

    def _validate_const(self, data:JsonTypes, const_value:JsonTypes) -> bool:
        if isinstance(data, int) and isinstance(const_value, float) and (not isinstance(data, bool)) and data == int(const_value):
            return True
        elif isinstance(data, float) and isinstance(const_value, int) and (not isinstance(const_value, bool)) and int(data) == const_value:
            return True
        elif isinstance(const_value, list) and isinstance(data, list) and len(const_value) == len(data):
            all_elements_matched = True
            for i, x in enumerate(const_value):
                all_elements_matched = self._validate_const(data[i], x) and all_elements_matched
            if all_elements_matched:
                return True
        elif isinstance(const_value, dict) and isinstance(data, dict) and len(const_value) == len(data):
            all_elements_matched = True
            for k, v in const_value.items():
                if k not in data:
                    all_elements_matched = self._report_validation_error("The property '{}' in the const value was not found in the data".format(k), data, const_value)
                else:
                    all_elements_matched = self._validate_const(data[k], v) and all_elements_matched
                if all_elements_matched:
                    return True
        elif (isinstance(data, bool) and not isinstance(const_value, bool)) or (not isinstance(data, bool) and isinstance(const_value, bool)):
            return self._report_validation_error("The data value '{}' was not the const value '{}'".format(data, const_value), data, const_value)
        elif data == const_value:
            return True
        return self._report_validation_error("The data value '{}' was not the const value '{}'".format(data, const_value), data, const_value)

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