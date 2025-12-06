"""
Render Engine - Generates .codex/* artifacts

Injects structural content from fragments into base templates
and generates all four domain artifacts in a single pass.
"""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from codex.catalog import discover_fragments, resolve_fragment
from codex.manifest import CODEX_DIR, STANDARDS_DIR, get_ordered_fragments
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
    cwd = Path.cwd()

    lock_data: dict[str, Any] = {
        "schema_version": "1.0",
        "catalog_commit": get_git_commit(),
        "weave_timestamp": datetime.now(UTC).isoformat(),
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
                    # Use relative path for portability
                    try:
                        rel_path = cat_frag.path.relative_to(cwd)
                    except ValueError:
                        rel_path = cat_frag.path
                    lock_data["fragments"].append(
                        {
                            "name": name,
                            "version": version,
                            "path": str(rel_path),
                            "sha256": cat_frag.sha256,
                        }
                    )
                    break

    return lock_data


def weave_artifacts(
    locked: bool = False,
    dry_run: bool = False,
    check: bool = False,
    skip_agents: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Generate all .codex/* artifacts.

    Args:
        locked: Use lock file for reproducible build
        dry_run: Don't write files, just show what would happen
        check: Verify output matches lock file
        skip_agents: Skip updating AGENTS.md
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
    outputs: dict[str, str | None] = {
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
        would_generate = [k for k, v in outputs.items() if v is not None]
        if not skip_agents:
            would_generate.append("AGENTS.md")
        return {"would_generate": would_generate}

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

    # Update AGENTS.md with current governance state
    if not skip_agents:
        agents_path = update_agents_md(material, structural, verbose=verbose)
        if agents_path:
            generated.append(agents_path)

    return {"generated": generated}


def generate_stack_summary(material: dict[str, Any]) -> str:
    """Generate a markdown summary of stack requirements."""
    stack = material.get("stack", {})
    if not stack:
        return "*No stack requirements defined.*"

    lines = []

    if "python_version" in stack:
        lines.append(f"- **Python Version:** {stack['python_version']}")

    if "allowed_libraries" in stack:
        libs = ", ".join(f"`{lib}`" for lib in stack["allowed_libraries"][:10])
        if len(stack["allowed_libraries"]) > 10:
            libs += f" (+{len(stack['allowed_libraries']) - 10} more)"
        lines.append(f"- **Allowed Libraries:** {libs}")

    if "banned_libraries" in stack:
        banned = ", ".join(f"`{lib}`" for lib in stack["banned_libraries"])
        lines.append(f"- **Banned Libraries:** {banned}")

    if "required_tools" in stack:
        tools = ", ".join(f"`{tool}`" for tool in stack["required_tools"])
        lines.append(f"- **Required Tools:** {tools}")

    return "\n".join(lines) if lines else "*No stack requirements defined.*"


def generate_security_summary(material: dict[str, Any]) -> str:
    """Generate a markdown summary of security rules."""
    security = material.get("security", {})
    stack = material.get("stack", {})
    if not security and not stack.get("banned_libraries"):
        return "*No security rules defined.*"

    lines = []

    if stack.get("banned_libraries"):
        banned = ", ".join(f"`{lib}`" for lib in stack["banned_libraries"])
        lines.append(f"- **Banned Libraries:** {banned}")

    if security.get("forbidden_patterns"):
        patterns = ", ".join(f"`{p}`" for p in security["forbidden_patterns"])
        lines.append(f"- **Forbidden Patterns:** {patterns}")

    if security.get("scan_dependencies"):
        lines.append("- **Dependency Scanning:** Required")

    if security.get("require_signed_commits"):
        lines.append("- **Signed Commits:** Required")

    return "\n".join(lines) if lines else "*No security rules defined.*"


def generate_process_summary(material: dict[str, Any]) -> str:
    """Generate a markdown summary of process rules."""
    process = material.get("process", {})
    if not process:
        return "*No process rules defined.*"

    lines = []

    if "branching_model" in process:
        lines.append(f"- **Branching Model:** {process['branching_model']}")

    if "minimum_reviewers" in process:
        lines.append(f"- **Minimum Reviewers:** {process['minimum_reviewers']}")

    if "required_status_checks" in process:
        checks = ", ".join(f"`{c}`" for c in process["required_status_checks"])
        lines.append(f"- **Required Checks:** {checks}")

    if "release_cadence" in process:
        lines.append(f"- **Release Cadence:** {process['release_cadence']}")

    return "\n".join(lines) if lines else "*No process rules defined.*"


def update_agents_md(
    material: dict[str, Any], structural: dict[str, Any], verbose: bool = False
) -> str | None:
    """
    Update AGENTS.md with current governance state.

    Uses anchor-based injection to update dynamic sections while
    preserving user customizations outside anchors.

    Returns:
        Path to updated file, or None if file doesn't exist
    """
    cwd = Path.cwd()
    agents_path = cwd / "AGENTS.md"

    if not agents_path.exists():
        if verbose:
            print("AGENTS.md not found, skipping update")
        return None

    content = agents_path.read_text()

    # Check if it has our anchors
    if "<!-- BEGIN_STACK_SUMMARY -->" not in content:
        if verbose:
            print("AGENTS.md missing anchors, skipping update")
        return None

    # Generate summaries from material
    stack_summary = generate_stack_summary(material)
    security_summary = generate_security_summary(material)
    process_summary = generate_process_summary(material)

    # Inject content
    content = inject_content(content, "STACK_SUMMARY", stack_summary)
    content = inject_content(content, "SECURITY_RULES", security_summary)
    content = inject_content(content, "PROCESS_RULES", process_summary)

    # Write updated content
    agents_path.write_text(content)

    if verbose:
        print("Updated AGENTS.md with current governance state")

    return str(agents_path)


def show_diff(verbose: bool = False) -> list[str]:
    """Show changes between current state and last weave."""
    # TODO: Implement diff logic
    return []
