
from typing import Optional, Union

from .draft4 import InvalidSchemaError, JsonSchemaValidationError, JsonTypes
from .draft6 import Validator as Draft6Validator

class Validator(Draft6Validator):

    def __init__(self, schema:dict, lazy_error_reporting:bool=False):
        super().__init__(schema, lazy_error_reporting)

    def _validate_if_then_else(self, data, if_schema:dict, then_schema:Optional[dict]=None, else_schema:Optional[dict]=None) -> bool:
        try:
            self.validate(data, if_schema)
        except InvalidSchemaError:
            raise
        except JsonSchemaValidationError:
            if else_schema:
                return self.validate(data, else_schema)
            return True
        except Exception:
            raise
        else:
            if then_schema:
                return self.validate(data, then_schema)
            return True

    def _validate(self, data:JsonTypes, schema:Union[dict,bool]) -> bool:
        retval = super()._validate(data, schema)
        if isinstance(schema, dict) and 'if' in schema:
            then_schema = schema['then'] if 'then' in schema else None
            else_schema = schema['else'] if 'else' in schema else None
            retval = retval and self._validate_if_then_else(data, schema['if'], then_schema, else_schema)
        return retval