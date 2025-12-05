"""
Catalog Manager - Handles fragment loading and indexing

Fragments are versioned YAML files in .codex/fragments/ following
the naming convention: name@version.yaml
"""

import hashlib
import re
from dataclasses import dataclass
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
    """Get the fragments directory path."""
    return Path.cwd() / FRAGMENTS_DIR


def discover_fragments(verbose: bool = False) -> dict[str, list[Fragment]]:
    """Discover all fragments in the catalog, indexed by name."""
    fragments_dir = get_fragments_dir()
    if not fragments_dir.exists():
        return {}

    catalog: dict[str, list[Fragment]] = {}

    for path in fragments_dir.glob("*.yaml"):
        try:
            fragment = load_fragment(path)
            catalog.setdefault(fragment.name, []).append(fragment)
            if verbose:
                print(f"Discovered: {fragment.full_name} ({fragment.domain})")
        except ValueError as e:
            if verbose:
                print(f"Skipping invalid fragment: {e}")

    # Sort versions for each fragment
    for name in catalog:
        catalog[name].sort(key=lambda f: f.version, reverse=True)

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
