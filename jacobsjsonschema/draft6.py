
from typing import Union, Optional
from math import modf

from .draft4 import Validator as Draft4Validator, JsonTypes

class Validator(Draft4Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)
        self.validators["const"] = self._validate_const
    
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

    def validate(self, data:JsonTypes, schema:Optional[dict]=None) -> bool:
        if schema is None:
            schema = self._root_schema
        if schema is True:
            return True
        if schema is False:
            return self._report_validation_error("False schema always fails validation", data, schema)
        return super().validate(data, schema)