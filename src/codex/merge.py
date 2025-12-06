"""
Merge Engine - Semantic deep merge with x-merge-strategy support

Implements the fragment merging logic with:
- Manifest order precedence
- x-merge-strategy: set-union-stable, replace, append
- Security veto system
"""

from typing import Any


def get_merge_strategy(schema: dict[str, Any], key: str) -> str:
    """Get merge strategy from schema annotations."""
    if not schema:
        return "replace"
    properties = schema.get("properties", {})
    key_schema = properties.get(key, {})
    return key_schema.get("x-merge-strategy", "replace")


def set_union_stable(base: list[Any], overlay: list[Any]) -> list[Any]:
    """
    Merge two lists with set-union-stable strategy.

    Preserves first-occurrence order and deduplicates.
    """
    seen: set[Any] = set()
    result: list[Any] = []

    for item in base + overlay:
        # Handle unhashable items
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            # Unhashable item, just append
            result.append(item)

    return result


def merge_with_strategy(
    base: dict[str, Any], overlay: dict[str, Any], schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Deep merge respecting x-merge-strategy annotations.

    Args:
        base: Base dictionary to merge into
        overlay: Dictionary to merge on top
        schema: Optional schema with x-merge-strategy annotations

    Returns:
        Merged dictionary
    """
    if schema is None:
        schema = {}

    result = base.copy()

    for key, value in overlay.items():
        if key not in result:
            result[key] = value
            continue

        existing = result[key]
        strategy = get_merge_strategy(schema, key)

        if isinstance(value, list) and isinstance(existing, list):
            if strategy == "set-union-stable":
                result[key] = set_union_stable(existing, value)
            elif strategy == "append":
                result[key] = existing + value
            else:  # replace
                result[key] = value

        elif isinstance(value, dict) and isinstance(existing, dict):
            # Recursively merge dicts
            nested_schema = schema.get("properties", {}).get(key, {})
            result[key] = merge_with_strategy(existing, value, nested_schema)

        else:
            # Scalar override - last wins
            result[key] = value

    return result


def is_security_fragment(fragment: dict[str, Any]) -> bool:
    """Check if a fragment is a security fragment."""
    metadata = fragment.get("metadata", {})
    domain = metadata.get("domain", "")
    name = metadata.get("name", "")
    return domain == "security" or name.startswith("security-")


def reorder_for_security(fragments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Reorder fragments so security fragments come last.

    Security fragments are moved to the end to ensure their
    restrictions cannot be overridden.
    """
    non_security = []
    security = []

    for frag in fragments:
        if is_security_fragment(frag):
            security.append(frag)
        else:
            non_security.append(frag)

    return non_security + security


def apply_security_veto(merged: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    """
    Apply security veto pass.

    Removes any allowed items that appear in banned lists.
    """
    material = merged.get("rules", {}).get("material", {})

    # Get banned items from stack
    stack = material.get("stack", {})

    banned_libraries = set(stack.get("banned_libraries", []))
    # Note: security.forbidden_patterns handled by AST enforcer, not veto pass

    # Remove banned from allowed
    allowed_libraries = stack.get("allowed_libraries", [])
    if allowed_libraries:
        vetoed = [lib for lib in allowed_libraries if lib in banned_libraries]
        if vetoed and verbose:
            print(f"Vetoed libraries: {vetoed}")
        stack["allowed_libraries"] = [
            lib for lib in allowed_libraries if lib not in banned_libraries
        ]

    return merged


def merge_fragments(
    fragments: list[dict[str, Any]], schema: dict[str, Any] | None = None, verbose: bool = False
) -> dict[str, Any]:
    """
    Merge multiple fragments in order.

    Applies:
    1. Security fragment reordering
    2. Sequential merging with x-merge-strategy
    3. Security veto pass
    """
    if not fragments:
        return {}

    # Reorder for security
    ordered = reorder_for_security(fragments)

    # Merge in order
    result: dict[str, Any] = {}
    for frag in ordered:
        result = merge_with_strategy(result, frag, schema)
        if verbose:
            name = frag.get("metadata", {}).get("name", "unknown")
            print(f"Merged fragment: {name}")

    # Apply security veto
    result = apply_security_veto(result, verbose=verbose)

    return result
