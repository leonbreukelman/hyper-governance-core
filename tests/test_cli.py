"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from codex.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.2.0" in result.output

    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Governance as Code" in result.output

    def test_init_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.output

    def test_weave_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["weave", "--help"])
        assert result.exit_code == 0
        assert "--locked" in result.output
        assert "--dry-run" in result.output

    def test_validate_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--ast" in result.output
        assert "--stack" in result.output

    def test_list_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["list", "--help"])
        assert result.exit_code == 0
        assert "--all" in result.output
