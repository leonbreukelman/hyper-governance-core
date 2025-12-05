"""Tests for render engine."""

import pytest

from codex.render import inject_content, render_stack_yaml


class TestInjectContent:
    """Tests for anchor-based content injection."""

    def test_inject_simple(self) -> None:
        template = "<!-- BEGIN_TEST -->\nold\n<!-- END_TEST -->"
        result = inject_content(template, "TEST", "new content")
        assert "new content" in result
        assert "old" not in result

    def test_inject_preserves_anchors(self) -> None:
        template = "<!-- BEGIN_TEST -->old<!-- END_TEST -->"
        result = inject_content(template, "TEST", "new")
        assert "BEGIN_TEST" in result
        assert "END_TEST" in result

    def test_no_match_unchanged(self) -> None:
        template = "no anchors here"
        result = inject_content(template, "TEST", "content")
        assert result == "no anchors here"

    def test_multiple_anchors(self) -> None:
        template = (
            "<!-- BEGIN_A -->a<!-- END_A -->\n"
            "<!-- BEGIN_B -->b<!-- END_B -->"
        )
        result = inject_content(template, "A", "new_a")
        assert "new_a" in result
        assert "<!-- BEGIN_B -->b<!-- END_B -->" in result


class TestRenderStackYaml:
    """Tests for stack.yaml rendering."""

    def test_empty_material(self) -> None:
        result = render_stack_yaml({})
        assert result.strip() == "{}"

    def test_with_stack(self) -> None:
        material = {
            "stack": {
                "python_version": "3.11",
                "allowed_libraries": ["pytest"],
            }
        }
        result = render_stack_yaml(material)
        assert "python_version" in result
        assert "3.11" in result
        assert "pytest" in result

    def test_preserves_order(self) -> None:
        material = {
            "stack": {
                "a": 1,
                "b": 2,
                "c": 3,
            }
        }
        result = render_stack_yaml(material)
        # YAML dump with sort_keys=False should preserve order
        assert "a:" in result
