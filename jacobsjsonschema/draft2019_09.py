from typing import Optional, List, Union, Set

from .json_types import JsonTypes, AnnotationFrame
from .draft4 import InvalidSchemaError, JsonSchemaValidationError
from .draft7 import Validator as Draft7Validator
from .vocabularies import (
    DRAFT2019_09_VOCABULARIES,
    compute_active_keywords,
)


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

        # 2019-09+ applies $ref alongside sibling keywords, not instead of them.
        self._reference_applies_siblings = True
        # Recognise $recursiveRef as a reference keyword.
        self._ref_keywords = {"$ref", "$recursiveRef"}

        # --- Vocabulary-aware keyword filtering ---
        self._active_keywords: Optional[Set[str]] = None
        self._init_vocabulary_filter()

        self._warnings: List[str] = []

    def _init_vocabulary_filter(self) -> None:
        """Compute the active-keyword set from the root schema's ``$vocabulary``.

        If the root schema has no ``$schema``, or the metaschema is unreachable,
        or no filtering is needed, ``self._active_keywords`` stays ``None`` (fast
        path — all keywords active).
        """
        schema = self._root_schema
        # Only applies to DocObject instances (integrated mode with jacobs-json-doc)
        if not hasattr(schema, "get") or not hasattr(schema, "_pointers"):
            return
        metaschema_uri = schema.get("$schema")  # type: ignore[union-attr]
        if not metaschema_uri:
            return
        try:
            controller = schema._pointers.controller  # type: ignore[union-attr]
            metaschema = controller.get_document(str(metaschema_uri))
            vocabulary = metaschema.get("$vocabulary") if hasattr(metaschema, "get") else None
        except Exception:
            return
        self._active_keywords = compute_active_keywords(
            vocabulary, self._vocabularies_map()
        )
        if self._active_keywords is not None:
            self._prune_dispatch_dicts()

    def _vocabularies_map(self) -> dict:
        """Return the vocabulary-URI → keyword-set mapping for this draft."""
        return DRAFT2019_09_VOCABULARIES

    def _reinit_vocabulary_filter(self) -> None:
        """Re-run vocabulary filtering (used by subclasses with a different vocab map)."""
        self._active_keywords = None
        self._init_vocabulary_filter()

    def _prune_dispatch_dicts(self) -> None:
        """Remove keywords from dispatch dicts that aren't in the active set."""
        assert self._active_keywords is not None
        active = self._active_keywords
        for d in (
            self.generic_validators,
            self.value_validators,
            self.array_validators,
            self.object_validators,
        ):
            for kw in list(d.keys()):
                if kw not in active:
                    del d[kw]

    def _keyword_active(self, keyword: str) -> bool:
        """Return ``True`` if *keyword* is active per the vocabulary filter."""
        return self._active_keywords is None or keyword in self._active_keywords

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
        matched = False
        for schema in schemas:
            try:
                self._temp_ignore_errors = True
                if self.validate(data, schema):
                    self._temp_ignore_errors = False
                    self._merge_last_frame()
                    matched = True
            except InvalidSchemaError:
                raise
            except JsonSchemaValidationError:
                self._last_frame = None
            except Exception:
                raise
            finally:
                self._temp_ignore_errors = False
        if not matched:
            return self._report_validation_error(
                "The JSON data did not match any of the provided anyOf schemas",
                data,
                schemas,
            )
        return True

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

        # Collect evaluated keys ONLY from the current (top) frame.
        #
        # unevaluatedProperties must see annotations from:
        #   - Sibling keywords in the same schema (properties,
        #     patternProperties, additionalProperties) which record into the
        #     current frame directly.
        #   - In-place applicator branches (allOf, anyOf, oneOf,
        #     if/then/else, dependentSchemas, $ref) whose frames are merged
        #     into the current frame via _merge_last_frame().
        #
        # It must NOT see annotations from cousin schemas (sibling branches
        # of a parent allOf/anyOf/oneOf) — those are merged into the PARENT
        # frame, not the current one.  Looking at ancestor frames would
        # incorrectly expose cousin annotations.
        evaluated_keys: set = set()
        evaluated_keys.update(self._annotation_stack[-1].evaluated_property_keys)

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
        # Don't run unevaluatedProperties here — it must run after
        # if/then/else, which is handled in _validate (inherited from draft7).
        return super()._object_validate(data, schema)

    # ------------------------------------------------------------------ #
    # unevaluatedItems                                                    #
    # ------------------------------------------------------------------ #

    def _validate_unevaluated_items(
        self, data: list, schema: Union[dict, bool]
    ) -> bool:
        if not isinstance(data, list):
            return True
        if not self._annotation_stack:
            return True

        # Collect evaluated indices ONLY from the current (top) frame.
        # See _validate_unevaluated_properties for the rationale: ancestor
        # frames contain cousin annotations that must not be visible here.
        evaluated_indices: set = set()
        evaluated_indices.update(self._annotation_stack[-1].evaluated_item_indices)

        retval = True
        for idx, item in enumerate(data):
            if idx not in evaluated_indices:
                self._record_evaluated_item(idx)
                if not self.validate(item, schema):
                    retval = (
                        self._report_validation_error(
                            "Item at index {} is unevaluated and didn't match "
                            "the unevaluatedItems schema".format(idx),
                            item,
                            schema,
                        )
                        and retval
                    )
        return retval

    def _validate(self, data: JsonTypes, schema: Union[dict, bool]) -> bool:
        retval = super()._validate(data, schema)
        # super()._validate is draft7._validate which handles if/then/else.
        # Run unevaluatedProperties/unevaluatedItems AFTER if/then/else so
        # their annotation collection sees the then/else branch's evaluated
        # properties/items.
        if isinstance(schema, dict):
            if isinstance(data, dict) and "unevaluatedProperties" in schema:
                retval = (
                    self._validate_unevaluated_properties(
                        data, schema["unevaluatedProperties"]
                    )
                    and retval
                )
            if isinstance(data, list) and "unevaluatedItems" in schema:
                retval = (
                    self._validate_unevaluated_items(
                        data, schema["unevaluatedItems"]
                    )
                    and retval
                )
        return retval
