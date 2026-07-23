"""Vocabulary-aware keyword filtering for JSON Schema 2019-09 and 2020-12.

Per the spec, a schema's ``$schema`` points to a metaschema that declares
``$vocabulary`` — a map of vocabulary-URI → required-flag.  Only keywords
belonging to a required vocabulary are active.  Keywords from missing or
optional vocabularies are ignored (treated as annotations).

This module hard-codes the vocabulary → keyword sets for the standard
draft-2019-09 and draft-2020-12 vocabularies so that the validator can
prune its dispatch tables accordingly.
"""

from typing import Dict, Optional, Set

# ---------------------------------------------------------------------------
# 2019-09 vocabularies
# ---------------------------------------------------------------------------

DRAFT2019_09_VOCABULARIES: Dict[str, Set[str]] = {
    "https://json-schema.org/draft/2019-09/vocab/core": {
        "$schema",
        "$vocabulary",
        "$id",
        "$anchor",
        "$recursiveRef",
        "$recursiveAnchor",
        "$defs",
        "$ref",
    },
    "https://json-schema.org/draft/2019-09/vocab/applicator": {
        "additionalItems",
        "unevaluatedItems",
        "items",
        "contains",
        "additionalProperties",
        "unevaluatedProperties",
        "properties",
        "patternProperties",
        "dependentSchemas",
        "dependentRequired",
        "propertyNames",
        "if",
        "then",
        "else",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "required",
    },
    "https://json-schema.org/draft/2019-09/vocab/validation": {
        "multipleOf",
        "maximum",
        "exclusiveMaximum",
        "minimum",
        "exclusiveMinimum",
        "maxLength",
        "minLength",
        "pattern",
        "maxItems",
        "minItems",
        "uniqueItems",
        "maxProperties",
        "minProperties",
        "const",
        "enum",
        "type",
    },
    "https://json-schema.org/draft/2019-09/vocab/meta-data": {
        "title",
        "description",
        "default",
        "deprecated",
        "readOnly",
        "writeOnly",
        "examples",
    },
    "https://json-schema.org/draft/2019-09/vocab/format": {
        "format",
    },
    "https://json-schema.org/draft/2019-09/vocab/content": {
        "contentMediaType",
        "contentEncoding",
        "contentSchema",
    },
}

# ---------------------------------------------------------------------------
# 2020-12 vocabularies
# ---------------------------------------------------------------------------

DRAFT2020_12_VOCABULARIES: Dict[str, Set[str]] = {
    "https://json-schema.org/draft/2020-12/vocab/core": {
        "$schema",
        "$vocabulary",
        "$id",
        "$anchor",
        "$dynamicRef",
        "$dynamicAnchor",
        "$defs",
        "$ref",
    },
    "https://json-schema.org/draft/2020-12/vocab/applicator": {
        "prefixItems",
        "items",
        "contains",
        "additionalProperties",
        "properties",
        "patternProperties",
        "dependentSchemas",
        "dependentRequired",
        "propertyNames",
        "if",
        "then",
        "else",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "required",
    },
    "https://json-schema.org/draft/2020-12/vocab/unevaluated": {
        "unevaluatedItems",
        "unevaluatedProperties",
    },
    "https://json-schema.org/draft/2020-12/vocab/validation": {
        "multipleOf",
        "maximum",
        "exclusiveMaximum",
        "minimum",
        "exclusiveMinimum",
        "maxLength",
        "minLength",
        "pattern",
        "maxItems",
        "minItems",
        "uniqueItems",
        "maxContains",
        "minContains",
        "maxProperties",
        "minProperties",
        "const",
        "enum",
        "type",
    },
    "https://json-schema.org/draft/2020-12/vocab/meta-data": {
        "title",
        "description",
        "default",
        "deprecated",
        "readOnly",
        "writeOnly",
        "examples",
    },
    "https://json-schema.org/draft/2020-12/vocab/format-annotation": {
        "format",
    },
    "https://json-schema.org/draft/2020-12/vocab/format-assertion": {
        "format",
    },
    "https://json-schema.org/draft/2020-12/vocab/content": {
        "contentMediaType",
        "contentEncoding",
        "contentSchema",
    },
}


def compute_active_keywords(
    metaschema_vocabulary: Optional[dict],
    all_vocabularies: Dict[str, Set[str]],
) -> Optional[Set[str]]:
    """Compute the set of active keywords from a metaschema's ``$vocabulary``.

    Parameters
    ----------
    metaschema_vocabulary:
        The ``$vocabulary`` dict from the metaschema, mapping vocabulary URIs
        to booleans.  ``None`` or empty means no filtering (all keywords active).
    all_vocabularies:
        The vocabulary-URI → keyword-set mapping for this draft (e.g.
        :data:`DRAFT2019_09_VOCABULARIES`).

    Returns
    -------
    ``None`` if all keywords should be active (fast path), otherwise the set
    of keyword names that are active.
    """
    if not metaschema_vocabulary:
        return None

    active: Set[str] = set()
    for vocab_uri, required in metaschema_vocabulary.items():
        if required is True and vocab_uri in all_vocabularies:
            active |= all_vocabularies[vocab_uri]

    # If the result covers every known keyword, return None for the fast path.
    all_known: Set[str] = set()
    for kw_set in all_vocabularies.values():
        all_known |= kw_set
    if active >= all_known:
        return None

    return active
