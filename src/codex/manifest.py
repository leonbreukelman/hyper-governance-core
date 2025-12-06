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
GITHUB_DIR = ".github"
AGENTS_FILE = "AGENTS.md"
COPILOT_INSTRUCTIONS_FILE = ".github/copilot-instructions.md"
AGENTS_TEMPLATE_FILE = ".codex/standards/agents.md"

DEFAULT_MANIFEST = {
    "version": "1.0",
    "fragments": [],
}

COPILOT_INSTRUCTIONS_TEMPLATE = """# GitHub Copilot Instructions

This repository uses **CODEX Weaver** for governance-as-code.

**Primary reference:** See [AGENTS.md](../AGENTS.md) for complete AI agent instructions.

## Quick Rules

1. Run `codex validate` before submitting code
2. Follow stack requirements in `.codex/stack.yaml`
3. Never use banned libraries (see `.codex/security.md`)
4. All code must pass `uv run pytest`

For detailed governance, security controls, and process guidelines,
refer to the `AGENTS.md` file at the repository root.
"""


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


def initialize_agent_instructions(verbose: bool = False, skip_agents: bool = False) -> list[str]:
    """
    Initialize AI agent instruction files.

    Creates .github/copilot-instructions.md and AGENTS.md if they don't exist.

    Args:
        verbose: Print detailed output
        skip_agents: Skip creation of agent files

    Returns:
        List of created file paths
    """
    if skip_agents:
        if verbose:
            print("Skipping agent instructions (--skip-agents)")
        return []

    cwd = Path.cwd()
    created = []

    # Create .github directory
    github_dir = cwd / GITHUB_DIR
    github_dir.mkdir(exist_ok=True)

    # Create copilot-instructions.md
    copilot_path = cwd / COPILOT_INSTRUCTIONS_FILE
    if not copilot_path.exists():
        copilot_path.write_text(COPILOT_INSTRUCTIONS_TEMPLATE)
        created.append(str(copilot_path))
        if verbose:
            print(f"Created {COPILOT_INSTRUCTIONS_FILE}")
    else:
        if verbose:
            print(f"{COPILOT_INSTRUCTIONS_FILE} already exists")

    # Create AGENTS.md from template
    agents_path = cwd / AGENTS_FILE
    agents_template = cwd / AGENTS_TEMPLATE_FILE
    if not agents_path.exists():
        if agents_template.exists():
            # Copy from template
            agents_path.write_text(agents_template.read_text())
        else:
            # Use default template
            agents_path.write_text(_get_default_agents_template())
        created.append(str(agents_path))
        if verbose:
            print(f"Created {AGENTS_FILE}")
    else:
        if verbose:
            print(f"{AGENTS_FILE} already exists")

    return created


def _get_default_agents_template() -> str:
    """Return the default AGENTS.md template content."""
    return """# AI Agent Instructions

> [!IMPORTANT]
> This file guides AI coding agents (GitHub Copilot, Cursor, Claude, etc.)
> when working in this repository.

## Governance Framework

This project uses **CODEX Weaver** for governance-as-code.
All AI contributions must comply with the following governance artifacts:

<!-- BEGIN_GOVERNANCE_REFS -->
- [Architecture Standards](.codex/architecture.md) – Layers and design
- [Stack Requirements](.codex/stack.yaml) – Libraries, Python version, tools
- [Process Guidelines](.codex/process.md) – Branching, review requirements
- [Security Controls](.codex/security.md) – Banned patterns, policies
<!-- END_GOVERNANCE_REFS -->

## Stack Requirements

<!-- BEGIN_STACK_SUMMARY -->
*Run `codex weave` to populate this section with current stack requirements.*
<!-- END_STACK_SUMMARY -->

## Security Constraints

<!-- BEGIN_SECURITY_RULES -->
*Run `codex weave` to populate this section with current security rules.*
<!-- END_SECURITY_RULES -->

## Process Guidelines

<!-- BEGIN_PROCESS_RULES -->
*Run `codex weave` to populate this section with current process rules.*
<!-- END_PROCESS_RULES -->

## Validation Commands

Before suggesting or committing code, ensure:

```bash
# Run all validators
codex validate

# Run tests
uv run pytest

# Check linting
uv run ruff check src/

# Type check
uv run mypy src/
```

## Key Rules for AI Agents

1. **Never use banned libraries** – Check `.codex/security.md` for the ban list
2. **Follow the layer architecture** – See `.codex/architecture.md`
3. **All code must pass validation** – Run `codex validate` before committing
4. **Use safe patterns only** – No `eval()`, `exec()`, `pickle`, or unsafe YAML loading
5. **Tests are required** – All new code needs test coverage

---

*Generated by CODEX Weaver – Dynamic sections updated on `codex weave`*
"""


def initialize_manifest(verbose: bool = False, skip_agents: bool = False) -> list[str]:
    """
    Initialize a new manifest and .codex/ structure.

    Args:
        verbose: Print detailed output
        skip_agents: Skip creation of agent instruction files

    Returns:
        List of all created file paths
    """
    cwd = Path.cwd()
    created = []

    # Create .codex directories
    (cwd / CODEX_DIR).mkdir(exist_ok=True)
    (cwd / FRAGMENTS_DIR).mkdir(exist_ok=True)
    (cwd / STANDARDS_DIR).mkdir(exist_ok=True)

    # Create manifest if it doesn't exist
    manifest_path = get_manifest_path()
    if not manifest_path.exists():
        save_manifest(DEFAULT_MANIFEST.copy(), verbose=verbose)
        created.append(str(manifest_path))
        if verbose:
            print(f"Created {MANIFEST_FILE}")
    else:
        if verbose:
            print(f"{MANIFEST_FILE} already exists")

    # Create agent instruction files
    agent_files = initialize_agent_instructions(verbose=verbose, skip_agents=skip_agents)
    created.extend(agent_files)

    if verbose:
        print("CODEX structure initialized")

    return created


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
