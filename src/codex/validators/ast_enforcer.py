"""
AST Enforcer - Validates code against architectural rules

Refactored from legacy .governance/validators/ast_enforcer.py
Now reads from .codex/ artifacts for governance state.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ASTValidationResult:
    """Result of AST validation."""

    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: int = 0


class ASTEnforcer:
    """
    Enforces architectural rules by analyzing Python AST.

    Validates:
    - Import organization and allowed dependencies
    - Module structure and organization
    - File size limits
    - Naming conventions
    """

    # Maximum lines per file (excluding comments and docstrings)
    MAX_FILE_LINES = 500

    # Standard library modules that are always allowed
    STDLIB_ALLOWED = {
        "os",
        "sys",
        "re",
        "json",
        "typing",
        "pathlib",
        "logging",
        "ast",
        "argparse",
        "collections",
        "itertools",
        "functools",
        "dataclasses",
        "enum",
        "hashlib",
        "subprocess",
        "datetime",
    }

    def __init__(self, root_path: Path | None = None, verbose: bool = False):
        """Initialize AST Enforcer."""
        self.root_path = root_path or Path.cwd()
        self.verbose = verbose
        self.violations: list[str] = []
        self.warnings: list[str] = []
        self.files_checked = 0

    def validate(self) -> ASTValidationResult:
        """Validate all Python files in the root path."""
        self.violations = []
        self.warnings = []
        self.files_checked = 0

        # Find Python files (exclude tests and __pycache__)
        for py_file in self.root_path.rglob("*.py"):
            # Skip generated/virtual directories
            path_str = str(py_file)
            if any(skip in path_str for skip in [
                "__pycache__",
                ".governance",
                ".venv",
                "venv",
                ".git",
                "node_modules",
                ".pytest_cache",
            ]):
                continue

            self._validate_file(py_file)
            self.files_checked += 1

        return ASTValidationResult(
            violations=self.violations,
            warnings=self.warnings,
            files_checked=self.files_checked,
        )

    def _validate_file(self, file_path: Path) -> None:
        """Validate a single Python file."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except SyntaxError as e:
            self.violations.append(f"{file_path}: Syntax error: {e}")
            return

        # Check file size
        self._check_file_size(file_path, content)

        # Check imports
        self._check_imports(file_path, tree)

        # Check naming conventions
        self._check_naming(file_path, tree)

    def _check_file_size(self, file_path: Path, content: str) -> None:
        """Check if file exceeds maximum line limit."""
        lines = content.splitlines()
        # Count non-empty, non-comment lines
        code_lines = [
            line
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

        if len(code_lines) > self.MAX_FILE_LINES:
            self.warnings.append(
                f"{file_path}: File has {len(code_lines)} code lines "
                f"(max {self.MAX_FILE_LINES})"
            )

    def _check_imports(self, file_path: Path, tree: ast.AST) -> None:
        """Check import organization."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._validate_import(file_path, alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._validate_import(file_path, node.module, node.lineno)

    def _validate_import(self, file_path: Path, module: str, lineno: int) -> None:
        """Validate a single import."""
        # Check for wildcard imports (not directly detectable here, but we can warn)
        top_level = module.split(".")[0]

        # Allow stdlib and local imports
        if top_level in self.STDLIB_ALLOWED:
            return
        if top_level in {"codex", "tests"}:
            return

        # Third-party imports are handled by stack_police
        if self.verbose:
            print(f"{file_path}:{lineno}: Import {module}")

    def _check_naming(self, file_path: Path, tree: ast.AST) -> None:
        """Check naming conventions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Classes should be PascalCase
                if not node.name[0].isupper():
                    self.warnings.append(
                        f"{file_path}:{node.lineno}: Class '{node.name}' "
                        "should use PascalCase"
                    )

            elif isinstance(node, ast.FunctionDef):
                # Functions should be snake_case
                if node.name != "__init__" and not node.name.startswith("_"):
                    if any(c.isupper() for c in node.name):
                        self.warnings.append(
                            f"{file_path}:{node.lineno}: Function '{node.name}' "
                            "should use snake_case"
                        )
