"""Tests for merge engine."""

import pytest

from codex.merge import (
    apply_security_veto,
    is_security_fragment,
    merge_fragments,
    merge_with_strategy,
    reorder_for_security,
    set_union_stable,
)


class TestSetUnionStable:
    """Tests for set-union-stable merge strategy."""

    def test_empty_lists(self) -> None:
        assert set_union_stable([], []) == []

    def test_first_empty(self) -> None:
        assert set_union_stable([], ["a", "b"]) == ["a", "b"]

    def test_second_empty(self) -> None:
        assert set_union_stable(["a", "b"], []) == ["a", "b"]

    def test_deduplication(self) -> None:
        result = set_union_stable(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]

    def test_order_preservation(self) -> None:
        result = set_union_stable(["c", "a"], ["b", "d"])
        assert result == ["c", "a", "b", "d"]

    def test_all_duplicates(self) -> None:
        result = set_union_stable(["a", "b"], ["a", "b"])
        assert result == ["a", "b"]


class TestMergeWithStrategy:
    """Tests for deep merge with strategy support."""

    def test_simple_merge(self) -> None:
        base = {"a": 1}
        overlay = {"b": 2}
        result = merge_with_strategy(base, overlay)
        assert result == {"a": 1, "b": 2}

    def test_scalar_override(self) -> None:
        base = {"a": 1}
        overlay = {"a": 2}
        result = merge_with_strategy(base, overlay)
        assert result == {"a": 2}

    def test_nested_merge(self) -> None:
        base = {"nested": {"a": 1}}
        overlay = {"nested": {"b": 2}}
        result = merge_with_strategy(base, overlay)
        assert result == {"nested": {"a": 1, "b": 2}}

    def test_list_replace_default(self) -> None:
        base = {"items": [1, 2]}
        overlay = {"items": [3, 4]}
        result = merge_with_strategy(base, overlay)
        assert result == {"items": [3, 4]}

    def test_list_set_union_stable(self) -> None:
        base = {"items": [1, 2]}
        overlay = {"items": [2, 3]}
        schema = {"properties": {"items": {"x-merge-strategy": "set-union-stable"}}}
        result = merge_with_strategy(base, overlay, schema)
        assert result == {"items": [1, 2, 3]}


class TestSecurityFragment:
    """Tests for security fragment detection."""

    def test_security_domain(self) -> None:
        frag = {"metadata": {"domain": "security", "name": "test"}}
        assert is_security_fragment(frag) is True

    def test_security_prefix(self) -> None:
        frag = {"metadata": {"domain": "stack", "name": "security-strict"}}
        assert is_security_fragment(frag) is True

    def test_non_security(self) -> None:
        frag = {"metadata": {"domain": "stack", "name": "stack-core"}}
        assert is_security_fragment(frag) is False


class TestReorderForSecurity:
    """Tests for security fragment reordering."""

    def test_security_moves_to_end(self) -> None:
        fragments = [
            {"metadata": {"domain": "security", "name": "sec"}},
            {"metadata": {"domain": "stack", "name": "stack"}},
        ]
        result = reorder_for_security(fragments)
        assert result[0]["metadata"]["name"] == "stack"
        assert result[1]["metadata"]["name"] == "sec"

    def test_multiple_security_stay_ordered(self) -> None:
        fragments = [
            {"metadata": {"domain": "security", "name": "sec1"}},
            {"metadata": {"domain": "stack", "name": "stack"}},
            {"metadata": {"domain": "security", "name": "sec2"}},
        ]
        result = reorder_for_security(fragments)
        assert result[0]["metadata"]["name"] == "stack"
        assert result[1]["metadata"]["name"] == "sec1"
        assert result[2]["metadata"]["name"] == "sec2"


class TestSecurityVeto:
    """Tests for security veto pass."""

    def test_veto_removes_banned(self) -> None:
        merged = {
            "rules": {
                "material": {
                    "stack": {
                        "allowed_libraries": ["safe", "pickle"],
                        "banned_libraries": ["pickle"],
                    }
                }
            }
        }
        result = apply_security_veto(merged)
        assert "pickle" not in result["rules"]["material"]["stack"]["allowed_libraries"]
        assert "safe" in result["rules"]["material"]["stack"]["allowed_libraries"]
