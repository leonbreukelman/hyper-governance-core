"""
Stack Police - Validates imports against approved technology stack

Refactored from legacy .governance/validators/stack_police.py
Now reads from .codex/stack.yaml for governance state.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

import yaml

STACK_FILE = ".codex/stack.yaml"


@dataclass
class StackValidationResult:
    """Result of stack validation."""

    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: int = 0


class StackPolice:
    """
    Validates code imports against approved technology stack.

    Ensures:
    - Only approved libraries are imported
    - Banned libraries are not used
    - Dangerous patterns are detected
    """

    # Standard library modules (always allowed)
    STDLIB = {
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
        "abc",
        "contextlib",
        "io",
        "copy",
        "importlib",
    }

    # Known dangerous patterns
    DANGEROUS_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
    }

    def __init__(self, root_path: Path | None = None, verbose: bool = False):
        """Initialize Stack Police."""
        self.root_path = root_path or Path.cwd()
        self.verbose = verbose
        self.violations: list[str] = []
        self.warnings: list[str] = []
        self.files_checked = 0

        # Load stack configuration
        self._load_stack_config()

    def _load_stack_config(self) -> None:
        """Load stack configuration from .codex/stack.yaml."""
        stack_path = self.root_path / STACK_FILE

        self.allowed_libraries: set[str] = set()
        self.banned_libraries: set[str] = set()

        if not stack_path.exists():
            if self.verbose:
                print(f"Warning: {STACK_FILE} not found, using defaults")
            # Defaults
            self.allowed_libraries = {"yaml", "jsonschema", "click", "rich", "pytest"}
            self.banned_libraries = {"pickle", "telnetlib"}
            return

        with open(stack_path) as f:
            config = yaml.safe_load(f) or {}

        self.allowed_libraries = set(config.get("allowed_libraries", []))
        self.banned_libraries = set(config.get("banned_libraries", []))

        if self.verbose:
            print(f"Loaded {len(self.allowed_libraries)} allowed libraries")
            print(f"Loaded {len(self.banned_libraries)} banned libraries")

    def validate(self) -> StackValidationResult:
        """Validate all Python files in the root path."""
        self.violations = []
        self.warnings = []
        self.files_checked = 0

        # Find Python files
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

        return StackValidationResult(
            violations=self.violations,
            warnings=self.warnings,
            files_checked=self.files_checked,
        )

    def _validate_file(self, file_path: Path) -> None:
        """Validate imports in a single Python file."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except SyntaxError:
            return  # AST enforcer will catch this

        self._check_imports(file_path, tree)
        self._check_dangerous_calls(file_path, tree)

    def _check_imports(self, file_path: Path, tree: ast.AST) -> None:
        """Check all imports in the file."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._validate_import(file_path, alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._validate_import(file_path, node.module, node.lineno)

    def _validate_import(self, file_path: Path, module: str, lineno: int) -> None:
        """Validate a single import against stack rules."""
        top_level = module.split(".")[0]

        # Always allow stdlib
        if top_level in self.STDLIB:
            return

        # Always allow local imports
        if top_level in {"codex", "tests"}:
            return

        # Check banned
        if top_level in self.banned_libraries or module in self.banned_libraries:
            self.violations.append(
                f"{file_path}:{lineno}: Banned import '{module}'"
            )
            return

        # Check allowed
        if top_level not in self.allowed_libraries:
            self.warnings.append(
                f"{file_path}:{lineno}: Import '{module}' not in approved stack"
            )

    def _check_dangerous_calls(self, file_path: Path, tree: ast.AST) -> None:
        """Check for dangerous function calls."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check direct calls like eval()
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_CALLS:
                        self.violations.append(
                            f"{file_path}:{node.lineno}: "
                            f"Dangerous call to '{node.func.id}()'"
                        )

                # Check attribute calls like os.system()
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == "system":
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == "os":
                                self.violations.append(
                                    f"{file_path}:{node.lineno}: "
                                    "Dangerous call to 'os.system()'"
                                )
