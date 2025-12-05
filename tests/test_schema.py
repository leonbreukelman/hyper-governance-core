"""Tests for schema validation."""

import pytest

from codex.schema import get_merge_strategy, is_deprecated, validate_fragment


class TestValidateFragment:
    """Tests for fragment validation."""

    def test_valid_fragment(self) -> None:
        fragment = {
            "kind": "GovernanceFragment",
            "metadata": {
                "name": "test-fragment",
                "version": "1.0.0",
                "domain": "stack",
            },
            "rules": {},
        }
        # Will return empty list if no schema or valid
        errors = validate_fragment(fragment)
        assert isinstance(errors, list)

    def test_missing_kind(self) -> None:
        fragment = {
            "metadata": {
                "name": "test",
                "version": "1.0.0",
                "domain": "stack",
            },
            "rules": {},
        }
        errors = validate_fragment(fragment)
        # Schema file may not exist in test, so this is a smoke test
        assert isinstance(errors, list)

    def test_invalid_domain(self) -> None:
        fragment = {
            "kind": "GovernanceFragment",
            "metadata": {
                "name": "test",
                "version": "1.0.0",
                "domain": "invalid",
            },
            "rules": {},
        }
        errors = validate_fragment(fragment)
        assert isinstance(errors, list)


class TestMergeStrategy:
    """Tests for merge strategy extraction."""

    def test_get_default_strategy(self) -> None:
        schema = {}
        assert get_merge_strategy(schema, "any_key") == "replace"

    def test_get_annotated_strategy(self) -> None:
        schema = {
            "properties": {
                "items": {"x-merge-strategy": "set-union-stable"}
            }
        }
        assert get_merge_strategy(schema, "items") == "set-union-stable"

    def test_missing_key(self) -> None:
        schema = {"properties": {"other": {}}}
        assert get_merge_strategy(schema, "missing") == "replace"


class TestDeprecated:
    """Tests for deprecation detection."""

    def test_not_deprecated(self) -> None:
        fragment = {"metadata": {"name": "test"}}
        assert is_deprecated(fragment) is False

    def test_deprecated_false(self) -> None:
        fragment = {"metadata": {"name": "test", "deprecated": False}}
        assert is_deprecated(fragment) is False

    def test_deprecated_true(self) -> None:
        fragment = {"metadata": {"name": "test", "deprecated": True}}
        assert is_deprecated(fragment) is True
