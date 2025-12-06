"""
CODEX Weaver CLI - Command Line Interface

Commands:
    codex init              Initialize manifest and .codex/ structure
    codex add <frags...>    Add fragments to manifest
    codex remove <frag>     Remove fragment from manifest
    codex list              List available catalog fragments
    codex weave             Generate all .codex/* artifacts
    codex validate          Run all validators
    codex diff              Show changes since last weave
"""

import click
from rich.console import Console

from codex import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="codex")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """CODEX Weaver - Governance as Code CLI Engine."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.option(
    "--skip-agents",
    is_flag=True,
    help="Skip creating AGENTS.md and .github/copilot-instructions.md",
)
@click.pass_context
def init(ctx: click.Context, skip_agents: bool) -> None:
    """Initialize codex.manifest.yaml and .codex/ structure."""
    from codex.manifest import initialize_manifest

    verbose = ctx.obj.get("verbose", False)
    try:
        created = initialize_manifest(verbose=verbose, skip_agents=skip_agents)
        console.print("[green]✓[/green] Initialized CODEX structure")
        for path in created:
            console.print(f"  → {path}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("fragments", nargs=-1, required=True)
@click.pass_context
def add(ctx: click.Context, fragments: tuple[str, ...]) -> None:
    """Add fragments to manifest."""
    from codex.manifest import add_fragments

    verbose = ctx.obj.get("verbose", False)
    try:
        added = add_fragments(list(fragments), verbose=verbose)
        for frag in added:
            console.print(f"[green]✓[/green] Added {frag}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to add fragments: {e}")
        raise SystemExit(1)


@main.command()
@click.argument("fragment", required=True)
@click.pass_context
def remove(ctx: click.Context, fragment: str) -> None:
    """Remove fragment from manifest."""
    from codex.manifest import remove_fragment

    verbose = ctx.obj.get("verbose", False)
    try:
        remove_fragment(fragment, verbose=verbose)
        console.print(f"[green]✓[/green] Removed {fragment}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to remove fragment: {e}")
        raise SystemExit(1)


@main.command("list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all available fragments")
@click.option("--installed", "-i", is_flag=True, help="Show only installed fragments")
@click.pass_context
def list_fragments(ctx: click.Context, show_all: bool, installed: bool) -> None:
    """List available catalog fragments."""
    from codex.catalog import list_catalog_fragments

    verbose = ctx.obj.get("verbose", False)
    try:
        fragments = list_catalog_fragments(
            show_all=show_all, installed_only=installed, verbose=verbose
        )
        if not fragments:
            console.print("[yellow]No fragments found[/yellow]")
        else:
            for frag in fragments:
                console.print(f"  • {frag}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list fragments: {e}")
        raise SystemExit(1)


@main.command()
@click.option("--locked", is_flag=True, help="Use lock file for reproducible build")
@click.option("--dry-run", is_flag=True, help="Show what would be generated")
@click.option("--check", is_flag=True, help="Verify output matches lock file")
@click.option("--skip-agents", is_flag=True, help="Skip updating AGENTS.md")
@click.pass_context
def weave(ctx: click.Context, locked: bool, dry_run: bool, check: bool, skip_agents: bool) -> None:
    """Generate all .codex/* artifacts."""
    from codex.render import weave_artifacts

    verbose = ctx.obj.get("verbose", False)
    try:
        result = weave_artifacts(
            locked=locked,
            dry_run=dry_run,
            check=check,
            skip_agents=skip_agents,
            verbose=verbose,
        )
        if dry_run:
            console.print("[blue]Dry run:[/blue] No files were written")
            for artifact in result.get("would_generate", []):
                console.print(f"  → {artifact}")
        elif check:
            if result.get("matches", False):
                console.print("[green]✓[/green] Output matches lock file")
            else:
                console.print("[red]✗[/red] Output differs from lock file")
                raise SystemExit(1)
        else:
            console.print("[green]✓[/green] Generated artifacts:")
            for artifact in result.get("generated", []):
                console.print(f"  → {artifact}")
    except Exception as e:
        console.print(f"[red]✗[/red] Weave failed: {e}")
        raise SystemExit(1)


@main.command()
@click.option("--ast", is_flag=True, help="Run AST enforcer only")
@click.option("--stack", is_flag=True, help="Run stack police only")
@click.pass_context
def validate(ctx: click.Context, ast: bool, stack: bool) -> None:
    """Run all validators on current codebase (no auto-fix)."""
    from codex.validators import run_validators

    verbose = ctx.obj.get("verbose", False)
    try:
        result = run_validators(ast_only=ast, stack_only=stack, verbose=verbose)
        if result.passed:
            console.print("[green]✓[/green] All validations passed")
        else:
            console.print("[red]✗[/red] Validation failed:")
            for violation in result.violations:
                console.print(f"  • {violation}")
            raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Validation error: {e}")
        raise SystemExit(1)


@main.command()
@click.pass_context
def diff(ctx: click.Context) -> None:
    """Show changes between current and last weave."""
    from codex.render import show_diff

    verbose = ctx.obj.get("verbose", False)
    try:
        changes = show_diff(verbose=verbose)
        if not changes:
            console.print("[green]No changes since last weave[/green]")
        else:
            console.print("[yellow]Changes detected:[/yellow]")
            for change in changes:
                console.print(f"  {change}")
    except Exception as e:
        console.print(f"[red]✗[/red] Diff failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
