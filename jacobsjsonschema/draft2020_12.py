from .draft4 import InvalidSchemaError
from .draft2019_09 import Validator as Draft201909Validator


class Validator(Draft201909Validator):

    def __init__(self, schema: dict, lazy_error_reporting: bool = False):
        super().__init__(schema, lazy_error_reporting)
        self.array_validators["prefixItems"] = self._validate_prefixitems  # type: ignore[assignment]

    def _validate_items(self, data: list, schema: dict) -> bool:  # type: ignore[override]
        retval = True
        if isinstance(schema, list):
            raise InvalidSchemaError(
                "In draft 2020_12, 'items' can no longer be an array.  Use 'prefixItems' instead"
            )
        for item in data:
            retval = self.validate(item, schema) and retval
        return retval
