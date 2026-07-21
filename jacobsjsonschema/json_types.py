from typing import Set, Union
from dataclasses import dataclass, field

JsonTypes = Union[str, dict, list, int, float, None]


@dataclass
class AnnotationFrame:
    """Tracks which properties/items were evaluated during a single schema evaluation.

    Used by unevaluatedProperties/unevaluatedItems in draft 2019-09+.
    """

    evaluated_property_keys: Set[str] = field(default_factory=set)
    evaluated_item_indices: Set[int] = field(default_factory=set)
