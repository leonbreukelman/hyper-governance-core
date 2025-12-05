"""
Render Engine - Generates .codex/* artifacts

Injects structural content from fragments into base templates
and generates all four domain artifacts in a single pass.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from codex.catalog import discover_fragments, resolve_fragment
from codex.manifest import CODEX_DIR, STANDARDS_DIR, get_ordered_fragments, load_manifest
from codex.merge import merge_fragments
from codex.schema import load_schema

LOCK_FILE = "codex.lock.json"
CATALOG_COMMIT_FILE = ".codex/catalog-commit.txt"

# Anchor pattern for injection
ANCHOR_PATTERN = re.compile(r"<!--\s*BEGIN_(\w+)\s*-->.*?<!--\s*END_\1\s*-->", re.DOTALL)


def get_git_commit() -> str:
    """Get the current Git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def inject_content(template: str, anchor: str, content: str) -> str:
    """Inject content between BEGIN/END anchors."""
    pattern = re.compile(
        rf"(<!--\s*BEGIN_{anchor}\s*-->).*?(<!--\s*END_{anchor}\s*-->)", re.DOTALL
    )
    replacement = rf"\1\n{content}\n\2"
    return pattern.sub(replacement, template)


def render_markdown_artifact(
    template_path: Path,
    structural: dict[str, Any],
    anchor_mapping: dict[str, str],
    verbose: bool = False,
) -> str:
    """Render a markdown artifact by injecting structural content."""
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template = template_path.read_text()

    for anchor, key in anchor_mapping.items():
        content = structural.get(key, "")
        if content:
            template = inject_content(template, anchor, content)
            if verbose:
                print(f"Injected {key} into {anchor}")

    return template


def render_stack_yaml(material: dict[str, Any]) -> str:
    """Render stack.yaml from material.stack."""
    stack = material.get("stack", {})
    return yaml.dump(stack, default_flow_style=False, sort_keys=False)


def generate_lock_file(
    fragments: list[dict[str, Any]], manifest_hash: str, verbose: bool = False
) -> dict[str, Any]:
    """Generate lock file data."""
    catalog = discover_fragments(verbose=verbose)

    lock_data = {
        "schema_version": "1.0",
        "catalog_commit": get_git_commit(),
        "weave_timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest_hash": manifest_hash,
        "fragments": [],
    }

    for frag in fragments:
        metadata = frag.get("metadata", {})
        name = metadata.get("name", "")
        version = metadata.get("version", "")

        # Find the fragment in catalog to get path and hash
        if name in catalog:
            for cat_frag in catalog[name]:
                if cat_frag.version == version:
                    lock_data["fragments"].append(
                        {
                            "name": name,
                            "version": version,
                            "path": str(cat_frag.path),
                            "sha256": cat_frag.sha256,
                        }
                    )
                    break

    return lock_data


def weave_artifacts(
    locked: bool = False,
    dry_run: bool = False,
    check: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Generate all .codex/* artifacts.

    Args:
        locked: Use lock file for reproducible build
        dry_run: Don't write files, just show what would happen
        check: Verify output matches lock file
        verbose: Print detailed output

    Returns:
        Result dict with generated/would_generate/matches keys
    """
    cwd = Path.cwd()
    codex_dir = cwd / CODEX_DIR
    standards_dir = cwd / STANDARDS_DIR

    # Ensure output directory exists
    if not dry_run:
        codex_dir.mkdir(exist_ok=True)

    # Load fragments
    fragment_names = get_ordered_fragments(verbose=verbose)
    fragments = []

    for name in fragment_names:
        # Handle name@version or just name
        if "@" in name:
            frag_name, frag_version = name.split("@", 1)
            frag = resolve_fragment(frag_name, frag_version, verbose=verbose)
        else:
            frag = resolve_fragment(name, verbose=verbose)
        fragments.append(frag.content)

    # Load schema for merge strategies
    try:
        schema = load_schema(verbose=verbose)
    except FileNotFoundError:
        schema = {}

    # Merge fragments
    merged = merge_fragments(fragments, schema, verbose=verbose)

    # Extract material and structural
    rules = merged.get("rules", {})
    material = rules.get("material", {})
    structural = rules.get("structural", {})

    # Define outputs
    outputs = {
        "architecture.md": None,
        "stack.yaml": None,
        "process.md": None,
        "security.md": None,
    }

    # Render architecture.md
    arch_template = standards_dir / "architecture.md"
    if arch_template.exists():
        outputs["architecture.md"] = render_markdown_artifact(
            arch_template,
            structural,
            {"LAYERS": "architecture_layer_row", "DECISIONS": "architecture_decisions"},
            verbose=verbose,
        )

    # Render stack.yaml
    outputs["stack.yaml"] = render_stack_yaml(material)

    # Render process.md
    process_template = standards_dir / "process.md"
    if process_template.exists():
        outputs["process.md"] = render_markdown_artifact(
            process_template,
            structural,
            {
                "BRANCHING": "process_flowchart",
                "CHECKLIST": "process_checklist_table",
                "RELEASE": "process_flowchart",
            },
            verbose=verbose,
        )

    # Render security.md
    security_template = standards_dir / "security.md"
    if security_template.exists():
        outputs["security.md"] = render_markdown_artifact(
            security_template,
            structural,
            {"CONTROLS": "security_controls_table", "CRYPTO_POLICY": "security_crypto_policy"},
            verbose=verbose,
        )

    if dry_run:
        return {"would_generate": [k for k, v in outputs.items() if v is not None]}

    # Write outputs
    generated = []
    for filename, content in outputs.items():
        if content is not None:
            output_path = codex_dir / filename
            output_path.write_text(content)
            generated.append(str(output_path))

    # Write lock file
    manifest_hash = "sha256:placeholder"  # TODO: compute actual hash
    lock_data = generate_lock_file(fragments, manifest_hash, verbose=verbose)
    lock_path = cwd / LOCK_FILE
    lock_path.write_text(json.dumps(lock_data, indent=2))
    generated.append(str(lock_path))

    # Write catalog commit
    commit_path = cwd / CATALOG_COMMIT_FILE
    commit_path.write_text(get_git_commit())
    generated.append(str(commit_path))

    return {"generated": generated}


def show_diff(verbose: bool = False) -> list[str]:
    """Show changes between current state and last weave."""
    # TODO: Implement diff logic
    return []
