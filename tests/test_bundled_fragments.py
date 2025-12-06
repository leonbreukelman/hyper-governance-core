"""Integration tests for bundled fragment discovery."""


from codex.catalog import discover_fragments, get_bundled_fragments_dir


class TestBundledFragments:
    """Tests for bundled fragment discovery."""

    def test_bundled_fragments_dir_exists(self) -> None:
        """Bundled fragments directory should be accessible."""
        bundled_dir = get_bundled_fragments_dir()
        # Should be a traversable resource
        assert bundled_dir is not None

    def test_bundled_fragments_discoverable(self) -> None:
        """Bundled core fragments should be discoverable without local setup."""
        catalog = discover_fragments()

        # Check that core fragments are found
        assert "base" in catalog, "base fragment not found"
        assert "stack-core" in catalog, "stack-core fragment not found"
        assert "process-core" in catalog, "process-core fragment not found"
        assert "security-core" in catalog, "security-core fragment not found"

    def test_bundled_fragment_content(self) -> None:
        """Bundled fragments should have valid content."""
        catalog = discover_fragments()

        # Check stack-core has expected content
        assert "stack-core" in catalog
        stack_core = catalog["stack-core"][0]
        assert stack_core.name == "stack-core"
        assert stack_core.version == "1.0.0"
        assert stack_core.domain == "stack"
        assert stack_core.content.get("kind") == "GovernanceFragment"
