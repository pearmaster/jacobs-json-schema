from typing import Optional, List, Union

from .json_types import JsonTypes, AnnotationFrame
from .draft4 import InvalidSchemaError, JsonSchemaValidationError
from .draft7 import Validator as Draft7Validator


class Validator(Draft7Validator):

    def __init__(self, schema: dict, lazy_error_reporting: bool = False):
        super().__init__(schema, lazy_error_reporting)
        del self.array_validators["contains"]

        del self.object_validators["dependencies"]
        self.object_validators.update(
            {
                "dependentRequired": self._validate_dependency,
                "dependentSchemas": self._validate_dependency,
            }
        )

        self._warnings: List[str] = []

    def get_warnings(self):
        return self._warnings

    def _report_format_warning(self, data, format):
        message = "String '{}' didn't conform to format {}".format(data, format)
        if hasattr(data, "line"):
            message = "Line {}: {}".format(data.line, message)
        self._warnings.append(message)

    def _validate_format(self, data: str, format: str) -> bool:
        """
        According to https://json-schema.org/draft/2019-09/release-notes.html#incompatible-changes
        format is no longer an assertation.
        """
        if format in self._format_validators:
            if not self._format_validators[format](data):
                self._report_format_warning(data, format)
        return True

    def _validate_contains(
        self,
        data: List[JsonTypes],
        schema: dict,
        min_contains: int = 1,
        max_contains: Optional[int] = None,
    ) -> bool:
        occurances = self._contains_count(data, schema)
        if max_contains is None:
            max_contains = occurances + 1
        retval = True
        if occurances < min_contains:
            retval = (
                self._report_validation_error(
                    "There were too few occurances {} in array that matched schema".format(
                        occurances
                    ),
                    data,
                    min_contains,
                )
                and retval
            )
        if occurances > max_contains:
            retval = (
                self._report_validation_error(
                    "There were too many occurances {} in array that matched schema".format(
                        occurances
                    ),
                    data,
                    max_contains,
                )
                and retval
            )
        return retval

    def _array_validate(self, data: list, schema: dict) -> bool:
        retval = super()._array_validate(data, schema)
        if "contains" in schema:
            if not isinstance(data, list):
                self._report_validation_error(
                    "Cannot evaluate a 'contains' against a non-array", data, schema
                )
            else:
                max_contains = (
                    schema["maxContains"] if "maxContains" in schema else None
                )
                min_contains = schema["minContains"] if "minContains" in schema else 1
                retval = (
                    self._validate_contains(
                        data, schema["contains"], min_contains, max_contains
                    )
                    and retval
                )
        return retval

    # ------------------------------------------------------------------ #
    # Applicator overrides — merge child annotation frames into current   #
    # ------------------------------------------------------------------ #

    def _validate_allof(self, data: JsonTypes, schemas: list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("allOf schema was not a list")
        retval = True
        for schema in schemas:
            retval = self.validate(data, schema) and retval
            self._merge_last_frame()
        return retval

    def _validate_anyof(self, data: JsonTypes, schemas: list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("anyOf schema was not a list")
        for schema in schemas:
            try:
                self._temp_ignore_errors = True
                if self.validate(data, schema):
                    self._temp_ignore_errors = False
                    self._merge_last_frame()
                    return True
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        return self._report_validation_error(
            "The JSON data did not match any of the provided anyOf schemas",
            data,
            schemas,
        )

    def _validate_oneof(self, data: JsonTypes, schemas: list) -> bool:
        if not isinstance(schemas, list):
            raise InvalidSchemaError("oneOf schema was not a list")
        valid_count = 0
        matching_frame: Optional[AnnotationFrame] = None
        for schema in schemas:
            try:
                self._temp_ignore_errors = True
                if self.validate(data, schema):
                    valid_count += 1
                    matching_frame = self._last_frame
                    self._last_frame = None
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                pass
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        if valid_count != 1:
            return self._report_validation_error(
                "The data matched against {} schemas but was required to match exactly 1".format(
                    valid_count
                ),
                data,
                schemas,
            )
        # Merge the single matching branch's annotations
        if matching_frame is not None and self._annotation_stack:
            current = self._annotation_stack[-1]
            current.evaluated_property_keys.update(
                matching_frame.evaluated_property_keys
            )
            current.evaluated_item_indices.update(
                matching_frame.evaluated_item_indices
            )
        return True

    def _validate_not(self, data: JsonTypes, schema: dict) -> bool:
        try:
            self._temp_ignore_errors = True
            if not self.validate(data, schema):
                self._temp_ignore_errors = False
                self._last_frame = None  # not produces no annotations
                return True
        except InvalidSchemaError:
            raise
        except JsonSchemaValidationError:
            self._temp_ignore_errors = False
            self._last_frame = None  # not produces no annotations
            return True
        except Exception:
            raise
        else:
            self._temp_ignore_errors = False
            self._last_frame = None  # not produces no annotations
            return self._report_validation_error(
                "The data matched against the schema when it was not supposed to",
                data,
                schema,
            )

    def _validate_if_then_else(
        self,
        data: JsonTypes,
        if_schema: dict,
        then_schema: Optional[dict] = None,
        else_schema: Optional[dict] = None,
    ) -> bool:
        try:
            self.validate(data, if_schema)
        except InvalidSchemaError:
            raise
        except JsonSchemaValidationError:
            # if didn't match — collect from else
            if else_schema is not None:
                result = self.validate(data, else_schema)
                self._merge_last_frame()
                return result
            self._last_frame = None
            return True
        except Exception:
            raise
        else:
            # if matched — collect from if AND then
            self._merge_last_frame()
            if then_schema is not None:
                result = self.validate(data, then_schema)
                self._merge_last_frame()
                return result
            return True

    def _validate_dependency(
        self, data: dict, required: Union[list, dict]
    ) -> bool:
        retval = True
        for requirement, consequence in required.items():
            if requirement in data:
                if isinstance(consequence, bool):
                    if not consequence:
                        retval = self._report_validation_error(
                            "For the {} property, false schema invalidates data",
                            requirement,
                        )
                elif isinstance(consequence, list):
                    retval = self._validate_required(data, consequence) and retval
                elif isinstance(consequence, dict):
                    retval = self.validate(data, consequence) and retval
                    self._merge_last_frame()
                else:
                    return InvalidSchemaError(
                        "Dependency must be either a list or a schema"
                    )
        return retval

    # ------------------------------------------------------------------ #
    # unevaluatedProperties                                              #
    # ------------------------------------------------------------------ #

    def _validate_unevaluated_properties(
        self, data: JsonTypes, schema: Union[dict, bool]
    ) -> bool:
        if not isinstance(data, dict):
            return True
        if not self._annotation_stack:
            return True

        # Collect evaluated keys from ALL frames on the stack.
        # unevaluatedProperties must see annotations from ancestor schemas
        # (e.g., a parent's `properties` keyword) as well as from sibling
        # keywords that already ran in the current schema.
        evaluated_keys: set = set()
        for frame in self._annotation_stack:
            evaluated_keys.update(frame.evaluated_property_keys)

        retval = True
        for key in data:
            if key not in evaluated_keys:
                # Record this key as evaluated by unevaluatedProperties
                # so that parent schemas can see it via annotation merging.
                self._record_evaluated_property(key)
                if not self.validate(data[key], schema):
                    retval = (
                        self._report_validation_error(
                            "Property '{}' is unevaluated and didn't match "
                            "the unevaluatedProperties schema".format(key),
                            data[key],
                            schema,
                        )
                        and retval
                    )
        return retval

    def _object_validate(self, data: dict, schema: dict) -> bool:
        retval = super()._object_validate(data, schema)
        if "unevaluatedProperties" in schema:
            if isinstance(data, dict):
                retval = (
                    self._validate_unevaluated_properties(
                        data, schema["unevaluatedProperties"]
                    )
                    and retval
                )
            else:
                retval = self._report_validation_error(
                    "Cannot validate unevaluatedProperties on a non-object",
                    data,
                    schema["unevaluatedProperties"],
                )
        return retval
