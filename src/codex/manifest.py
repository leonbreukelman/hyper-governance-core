"""
Manifest Parser - Handles codex.manifest.yaml

The manifest is the user's declaration of which governance fragments
should be applied in what order.
"""

from pathlib import Path
from typing import Any

import yaml

MANIFEST_FILE = "codex.manifest.yaml"
CODEX_DIR = ".codex"
FRAGMENTS_DIR = ".codex/fragments"
STANDARDS_DIR = ".codex/standards"

DEFAULT_MANIFEST = {
    "version": "1.0",
    "fragments": [],
}


def get_manifest_path() -> Path:
    """Get the path to the manifest file."""
    return Path.cwd() / MANIFEST_FILE


def load_manifest(verbose: bool = False) -> dict[str, Any]:
    """Load and parse the manifest file."""
    manifest_path = get_manifest_path()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    if verbose:
        print(f"Loaded manifest from {manifest_path}")

    return manifest or DEFAULT_MANIFEST.copy()


def save_manifest(manifest: dict[str, Any], verbose: bool = False) -> None:
    """Save the manifest to disk."""
    manifest_path = get_manifest_path()
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

    if verbose:
        print(f"Saved manifest to {manifest_path}")


def initialize_manifest(verbose: bool = False) -> None:
    """Initialize a new manifest and .codex/ structure."""
    cwd = Path.cwd()

    # Create .codex directories
    (cwd / CODEX_DIR).mkdir(exist_ok=True)
    (cwd / FRAGMENTS_DIR).mkdir(exist_ok=True)
    (cwd / STANDARDS_DIR).mkdir(exist_ok=True)

    # Create manifest if it doesn't exist
    manifest_path = get_manifest_path()
    if not manifest_path.exists():
        save_manifest(DEFAULT_MANIFEST.copy(), verbose=verbose)
        if verbose:
            print(f"Created {MANIFEST_FILE}")
    else:
        if verbose:
            print(f"{MANIFEST_FILE} already exists")

    if verbose:
        print("CODEX structure initialized")


def add_fragments(fragments: list[str], verbose: bool = False) -> list[str]:
    """Add fragments to the manifest."""
    manifest = load_manifest(verbose=verbose)
    existing = set(manifest.get("fragments", []))
    added = []

    for frag in fragments:
        if frag not in existing:
            manifest.setdefault("fragments", []).append(frag)
            added.append(frag)
            if verbose:
                print(f"Adding fragment: {frag}")

    if added:
        save_manifest(manifest, verbose=verbose)

    return added


def remove_fragment(fragment: str, verbose: bool = False) -> None:
    """Remove a fragment from the manifest."""
    manifest = load_manifest(verbose=verbose)
    fragments = manifest.get("fragments", [])

    if fragment not in fragments:
        raise ValueError(f"Fragment not in manifest: {fragment}")

    fragments.remove(fragment)
    manifest["fragments"] = fragments
    save_manifest(manifest, verbose=verbose)

    if verbose:
        print(f"Removed fragment: {fragment}")


def get_ordered_fragments(verbose: bool = False) -> list[str]:
    """Get the ordered list of fragments from the manifest."""
    manifest = load_manifest(verbose=verbose)
    return manifest.get("fragments", [])
