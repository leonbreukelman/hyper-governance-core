"""
Catalog Manager - Handles fragment loading and indexing

Fragments are versioned YAML files in .codex/fragments/ following
the naming convention: name@version.yaml

Bundled fragments are included in the package at codex/data/fragments/
and are used as defaults. Local fragments in .codex/fragments/ take precedence.
"""

import hashlib
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from codex.manifest import FRAGMENTS_DIR, load_manifest

FRAGMENT_PATTERN = re.compile(r"^([a-z0-9-]+)@(\d+\.\d+\.\d+)\.yaml$")


@dataclass
class Fragment:
    """Represents a governance fragment."""

    name: str
    version: str
    domain: str
    path: Path
    content: dict[str, Any]
    sha256: str

    @property
    def full_name(self) -> str:
        """Return name@version format."""
        return f"{self.name}@{self.version}"


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def parse_fragment_filename(filename: str) -> tuple[str, str] | None:
    """Parse fragment filename into (name, version) or None if invalid."""
    match = FRAGMENT_PATTERN.match(filename)
    if match:
        return match.group(1), match.group(2)
    return None


def load_fragment(path: Path) -> Fragment:
    """Load a fragment from disk."""
    parsed = parse_fragment_filename(path.name)
    if not parsed:
        raise ValueError(f"Invalid fragment filename: {path.name}")

    name, version = parsed
    sha256 = compute_sha256(path)

    with open(path) as f:
        content = yaml.safe_load(f)

    if not content:
        raise ValueError(f"Empty fragment: {path}")

    # Validate basic structure
    if content.get("kind") != "GovernanceFragment":
        raise ValueError(f"Invalid fragment kind in {path}")

    metadata = content.get("metadata", {})
    domain = metadata.get("domain", "unknown")

    return Fragment(
        name=name,
        version=version,
        domain=domain,
        path=path,
        content=content,
        sha256=sha256,
    )


def get_fragments_dir() -> Path:
    """Get the local fragments directory path."""
    return Path.cwd() / FRAGMENTS_DIR


def get_bundled_fragments_dir():
    """Get the bundled fragments directory from package data."""
    return files("codex.data") / "fragments"


def _load_fragments_from_dir(
    directory, catalog: dict[str, list[Fragment]], verbose: bool = False
) -> None:
    """Load fragments from a directory into the catalog."""
    try:
        # Handle both Path and Traversable (from importlib.resources)
        if hasattr(directory, "iterdir"):
            items = list(directory.iterdir())
        else:
            items = list(directory.glob("*.yaml"))

        for item in items:
            if not str(item).endswith(".yaml"):
                continue

            try:
                # For bundled resources, we need to extract to a temp file
                if hasattr(item, "read_text"):
                    # This is a Traversable from importlib.resources
                    content_text = item.read_text()
                    parsed = parse_fragment_filename(item.name)
                    if not parsed:
                        continue

                    name, version = parsed
                    content = yaml.safe_load(content_text)

                    if not content or content.get("kind") != "GovernanceFragment":
                        continue

                    metadata = content.get("metadata", {})
                    domain = metadata.get("domain", "unknown")

                    # Compute hash from content
                    sha256 = hashlib.sha256(content_text.encode()).hexdigest()

                    fragment = Fragment(
                        name=name,
                        version=version,
                        domain=domain,
                        path=Path(str(item)),  # Store as Path for consistency
                        content=content,
                        sha256=sha256,
                    )
                else:
                    # Regular Path object
                    fragment = load_fragment(item)

                catalog.setdefault(fragment.name, []).append(fragment)
                if verbose:
                    print(f"Discovered: {fragment.full_name} ({fragment.domain})")

            except (ValueError, yaml.YAMLError) as e:
                if verbose:
                    print(f"Skipping invalid fragment: {e}")

    except (FileNotFoundError, TypeError):
        # Directory doesn't exist or isn't traversable
        pass


def discover_fragments(verbose: bool = False) -> dict[str, list[Fragment]]:
    """
    Discover all fragments from bundled package and local catalog.

    Bundled fragments (from package) are loaded first, then local fragments
    in .codex/fragments/ are overlaid. Local fragments with the same name
    and version will override bundled ones.
    """
    catalog: dict[str, list[Fragment]] = {}

    # 1. Load bundled fragments from package
    bundled_dir = get_bundled_fragments_dir()
    _load_fragments_from_dir(bundled_dir, catalog, verbose=verbose)

    # 2. Overlay local fragments (can override bundled)
    local_dir = get_fragments_dir()
    if local_dir.exists():
        _load_fragments_from_dir(local_dir, catalog, verbose=verbose)

    # Sort versions for each fragment (newest first)
    for name in catalog:
        # Deduplicate by version (local overrides bundled)
        seen_versions: dict[str, Fragment] = {}
        for frag in catalog[name]:
            seen_versions[frag.version] = frag
        catalog[name] = sorted(seen_versions.values(), key=lambda f: f.version, reverse=True)

    return catalog


def resolve_fragment(name: str, version: str | None = None, verbose: bool = False) -> Fragment:
    """Resolve a fragment reference to a concrete Fragment."""
    catalog = discover_fragments(verbose=verbose)

    if name not in catalog:
        raise ValueError(f"Fragment not found: {name}")

    fragments = catalog[name]

    if version:
        for frag in fragments:
            if frag.version == version:
                return frag
        raise ValueError(f"Version not found: {name}@{version}")

    # Return latest version
    return fragments[0]


def list_catalog_fragments(
    show_all: bool = False, installed_only: bool = False, verbose: bool = False
) -> list[str]:
    """List fragments in the catalog."""
    catalog = discover_fragments(verbose=verbose)

    if installed_only:
        manifest = load_manifest(verbose=verbose)
        installed = set(manifest.get("fragments", []))
        return [
            frag.full_name
            for frags in catalog.values()
            for frag in frags
            if frag.name in installed or frag.full_name in installed
        ]

    if show_all:
        return [frag.full_name for frags in catalog.values() for frag in frags]

    # Return latest version of each
    return [frags[0].full_name for frags in catalog.values()]
