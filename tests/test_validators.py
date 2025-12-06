"""Tests for validators."""

import tempfile
from pathlib import Path

from codex.validators.ast_enforcer import ASTEnforcer
from codex.validators.stack_police import StackPolice


class TestASTEnforcer:
    """Tests for AST Enforcer."""

    def test_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "valid.py").write_text("def foo(): pass")

            enforcer = ASTEnforcer(root_path=path)
            result = enforcer.validate()

            assert result.files_checked == 1
            assert len(result.violations) == 0

    def test_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "invalid.py").write_text("def foo(")

            enforcer = ASTEnforcer(root_path=path)
            result = enforcer.validate()

            assert len(result.violations) > 0
            assert "Syntax error" in result.violations[0]

    def test_class_naming(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "test.py").write_text("class bad_name: pass")

            enforcer = ASTEnforcer(root_path=path)
            result = enforcer.validate()

            # Should warn about non-PascalCase class
            assert any("PascalCase" in w for w in result.warnings)


class TestStackPolice:
    """Tests for Stack Police."""

    def test_stdlib_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "test.py").write_text("import os\nimport sys")

            police = StackPolice(root_path=path)
            result = police.validate()

            assert len(result.violations) == 0

    def test_dangerous_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "test.py").write_text("x = eval('1+1')")

            police = StackPolice(root_path=path)
            result = police.validate()

            assert any("eval" in v for v in result.violations)

    def test_dangerous_os_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "test.py").write_text("import os\nos.system('ls')")

            police = StackPolice(root_path=path)
            result = police.validate()

            assert any("os.system" in v for v in result.violations)
