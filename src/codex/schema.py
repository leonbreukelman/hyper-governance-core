"""
Schema Validator - Validates fragments against codex.schema.json

Provides validation with clear error messages for invalid fragments.
"""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, ValidationError
from jsonschema.validators import validator_for

SCHEMA_FILE = "codex.schema.json"


def get_schema_path() -> Path:
    """Get the path to the schema file."""
    return Path.cwd() / SCHEMA_FILE


def load_schema(verbose: bool = False) -> dict[str, Any]:
    """Load the JSON schema from disk."""
    schema_path = get_schema_path()
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path) as f:
        schema = json.load(f)

    if verbose:
        print(f"Loaded schema from {schema_path}")

    return schema


def create_validator(schema: dict[str, Any]) -> Draft7Validator:
    """Create a JSON Schema validator instance."""
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema)


def validate_fragment(fragment: dict[str, Any], verbose: bool = False) -> list[str]:
    """
    Validate a fragment against the schema.

    Returns a list of error messages (empty if valid).
    """
    try:
        schema = load_schema(verbose=verbose)
    except FileNotFoundError:
        if verbose:
            print("Warning: No schema file found, skipping validation")
        return []

    validator = create_validator(schema)
    errors: list[str] = []

    for error in sorted(validator.iter_errors(fragment), key=lambda e: str(e.path)):
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"{path}: {error.message}")

    if verbose:
        if errors:
            print(f"Validation found {len(errors)} errors")
        else:
            print("Fragment is valid")

    return errors


def validate_fragment_file(path: Path, verbose: bool = False) -> list[str]:
    """Validate a fragment file."""
    import yaml

    with open(path) as f:
        fragment = yaml.safe_load(f)

    if not fragment:
        return [f"Empty fragment file: {path}"]

    errors = validate_fragment(fragment, verbose=verbose)

    # Add file path context to errors
    return [f"{path.name}: {e}" for e in errors]


def get_merge_strategy(schema: dict[str, Any], key: str) -> str:
    """
    Get the merge strategy for a schema key.

    Looks for x-merge-strategy annotation in the schema.
    Returns 'replace' as default.
    """
    properties = schema.get("properties", {})
    key_schema = properties.get(key, {})
    return key_schema.get("x-merge-strategy", "replace")


def is_deprecated(fragment: dict[str, Any]) -> bool:
    """Check if a fragment is marked as deprecated."""
    metadata = fragment.get("metadata", {})
    return metadata.get("deprecated", False)
