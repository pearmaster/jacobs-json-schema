from .draft4 import InvalidSchemaError
from .draft2019_09 import Validator as Draft201909Validator
from .vocabularies import (
    DRAFT2019_09_VOCABULARIES,
    DRAFT2020_12_VOCABULARIES,
    compute_active_keywords,
)


class Validator(Draft201909Validator):

    def __init__(self, schema: dict, lazy_error_reporting: bool = False):
        super().__init__(schema, lazy_error_reporting)
        self.array_validators["prefixItems"] = self._validate_prefixitems  # type: ignore[assignment]
        # 2020-12 uses $dynamicRef instead of $recursiveRef.
        self._ref_keywords = {"$ref", "$dynamicRef"}

    def _vocabularies_map(self) -> dict:
        """Return the 2020-12 vocabulary-URI → keyword-set mapping."""
        return DRAFT2020_12_VOCABULARIES

    def _validate_items(self, data: list, schema: dict) -> bool:  # type: ignore[override]
        retval = True
        if isinstance(schema, list):
            raise InvalidSchemaError(
                "In draft 2020_12, 'items' can no longer be an array.  Use 'prefixItems' instead"
            )
        for item in data:
            retval = self.validate(item, schema) and retval
        return retval
