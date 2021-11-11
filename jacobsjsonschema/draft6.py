
from typing import Union, Optional, List, Dict
from math import modf

from .draft4 import Validator as Draft4Validator, JsonTypes, JsonSchemaValidationError, InvalidSchemaError

class Validator(Draft4Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        self.generic_validators["const"] = self._validate_const
        self.array_validators["contains"] = self._validate_contains
        self.object_validators["propertyNames"] = self._validate_propertynames
        self.value_validators["maximum"] = self._validate_maximum
        self.value_validators["minimum"] = self._validate_minimum
        self.value_validators["exclusiveMaximum"] = lambda d,s : self._validate_maximum(d, s, True)
        self.value_validators["exclusiveMinimum"] = lambda d,s : self._validate_minimum(d, s, True)

    @staticmethod
    def get_dollar_id_token() -> str:
        return "$id"

    def _validate_type_integer(self, data:Union[int, float], schema_type) -> bool:
        if isinstance(data, bool) or ((not isinstance(data, float)) and (not isinstance(data, int))):
            return self._report_validation_error("The data type of '{}' is not an integer".format(data), data, schema_type)
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

    def _validate_propertynames(self, data:dict, schema:dict) -> bool:
        if not isinstance(data, dict):
            return True
        if not isinstance(schema, dict) and not isinstance(schema, bool):
            raise InvalidSchemaError("propertyNames must be a valid schema object")
        all_names_valid = True
        for name in data.keys():
            try:
                all_names_valid = self._validate(name, schema) and all_names_valid
            except JsonSchemaValidationError as e:
                return self._report_validation_error("Property name '{}' didn't conform to the propertyNames schema: {}".format(name, e))
        if not all_names_valid:
            return self._report_validation_error("Property names didn't conform to the propertyNames schema")
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

    def _value_validate(self, data:Union[int,float,str,None], schema:dict) -> bool:
        retval = True
        for k, validator_func in self.value_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval
        return retval

    def _validate_dependency(self, data:dict, required:Dict[str,Union[list,dict]]) -> bool:
        retval = True
        for requirement, consequence in required.items():
            if requirement in data:
                if isinstance(consequence, bool):
                    if not consequence:
                        retval = self._report_validation_error("For the {} property, false schema invalidates data", requirement)
                elif isinstance(consequence, list):
                    retval = self._validate_required(data, consequence) and retval
                elif isinstance(consequence, dict):
                    retval = self.validate(data, consequence) and retval
                else:
                    return InvalidSchemaError("Dependency must be either a list or a schema")
        return retval

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