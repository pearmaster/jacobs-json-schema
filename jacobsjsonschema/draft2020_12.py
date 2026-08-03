from .draft4 import InvalidSchemaError, JsonSchemaValidationError
from .draft2019_09 import Validator as Draft201909Validator
from .vocabularies import DRAFT2020_12_VOCABULARIES


class Validator(Draft201909Validator):

    def __init__(self, schema: dict, lazy_error_reporting: bool = False):
        super().__init__(schema, lazy_error_reporting)
        # 2020-12 uses $dynamicRef instead of $recursiveRef.
        self._ref_keywords = {"$ref", "$dynamicRef"}

    def _vocabularies_map(self) -> dict:
        """Return the 2020-12 vocabulary-URI → keyword-set mapping."""
        return DRAFT2020_12_VOCABULARIES

    def _array_validate(self, data: list, schema: dict) -> bool:  # type: ignore[override]
        # 2020-12 array semantics differ enough from 2019-09/draft4 that we
        # implement them directly here rather than delegating to super():
        #   prefixItems -> items -> contains -> maxItems/minItems/uniqueItems.
        # (draft4._array_validate handles the removed `additionalItems` keyword
        # and array-form `items`, neither of which applies in 2020-12.)
        retval = True
        prefix_len = 0
        # prefixItems — positional tuple validation (was array `items` pre-2020).
        if "prefixItems" in schema and self._keyword_active("prefixItems"):
            prefix = schema["prefixItems"]
            if not isinstance(prefix, list):
                raise InvalidSchemaError("prefixItems must be an array of schemas")
            prefix_len = len(prefix)
            for idx in range(min(len(data), prefix_len)):
                retval = self.validate(data[idx], prefix[idx]) and retval
                self._record_evaluated_item(idx)
        # items — a single subschema applied to every index at or after
        # prefixItems (an array here is a pre-2020 construct and is invalid).
        if "items" in schema and self._keyword_active("items"):
            items_schema = schema["items"]
            if isinstance(items_schema, list):
                raise InvalidSchemaError(
                    "In draft 2020_12, 'items' can no longer be an array. "
                    "Use 'prefixItems' instead"
                )
            for idx in range(prefix_len, len(data)):
                retval = self.validate(data[idx], items_schema) and retval
                self._record_evaluated_item(idx)
        # contains / minContains / maxContains
        if "contains" in schema and self._keyword_active("contains"):
            contains_schema = schema["contains"]
            # Every item matching `contains` is an evaluated item (2020-12
            # annotation behaviour), so unevaluatedItems can see them.
            for idx, item in enumerate(data):
                self._temp_ignore_errors = True
                try:
                    if self.validate(item, contains_schema):
                        self._record_evaluated_item(idx)
                except JsonSchemaValidationError:
                    pass
                finally:
                    self._temp_ignore_errors = False
            max_contains = schema["maxContains"] if "maxContains" in schema else None
            min_contains = schema["minContains"] if "minContains" in schema else 1
            retval = (
                self._validate_contains(
                    data, contains_schema, min_contains, max_contains
                )
                and retval
            )
        # maxItems / minItems / uniqueItems
        for k, validator_func in self.array_validators.items():
            if k in schema:
                retval = validator_func(data, schema[k]) and retval  # type: ignore[operator]
        return retval
