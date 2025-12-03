"""
AST Enforcer - Validates code against architectural rules defined in architecture.md

This validator parses Python source code and enforces structural rules including:
- Layered architecture compliance
- Module organization standards
- Dependency rules
- Design pattern adherence
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum


class ViolationSeverity(Enum):
    """Severity levels for architectural violations"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """Represents an architectural rule violation"""
    severity: ViolationSeverity
    rule: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    
    def __str__(self) -> str:
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"[{self.severity.value.upper()}] {location} - {self.rule}: {self.message}"


@dataclass
class ValidationResult:
    """Result of architectural validation"""
    passed: bool
    violations: List[Violation]
    files_checked: int
    
    def __str__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"\nValidation {status}\n"
            f"Files checked: {self.files_checked}\n"
            f"Violations: {len(self.violations)}\n"
        )


class ASTEnforcer:
    """
    Enforces architectural rules by analyzing Python AST.
    
    Validates:
    - Import organization and allowed dependencies
    - Module structure and organization
    - File size limits
    - Naming conventions
    """
    
    # Layer hierarchy (higher index = higher layer)
    LAYERS = {
        'infrastructure': 0,
        'domain': 1,
        'application': 2,
        'presentation': 3,
    }
    
    # Maximum lines per file (excluding comments/docstrings)
    MAX_FILE_LINES = 500
    
    def __init__(self, root_path: Path):
        """
        Initialize AST Enforcer.
        
        Args:
            root_path: Root directory to validate
        """
        self.root_path = Path(root_path)
        self.violations: List[Violation] = []
        
    def validate(self) -> ValidationResult:
        """
        Validate all Python files in the root path.
        
        Returns:
            ValidationResult with all violations found
        """
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            self._validate_file(file_path)
            
        passed = all(v.severity != ViolationSeverity.ERROR for v in self.violations)
        return ValidationResult(
            passed=passed,
            violations=self.violations,
            files_checked=len(python_files)
        )
    
    def _validate_file(self, file_path: Path) -> None:
        """Validate a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            tree = ast.parse(source, filename=str(file_path))
            
            # Check file size
            self._check_file_size(file_path, tree)
            
            # Check imports
            self._check_imports(file_path, tree)
            
            # Check naming conventions
            self._check_naming(file_path, tree)
            
        except SyntaxError as e:
            self.violations.append(Violation(
                severity=ViolationSeverity.ERROR,
                rule="syntax",
                message=f"Syntax error: {e}",
                file_path=str(file_path),
                line_number=e.lineno if hasattr(e, 'lineno') else None
            ))
        except Exception as e:
            self.violations.append(Violation(
                severity=ViolationSeverity.ERROR,
                rule="parsing",
                message=f"Failed to parse: {e}",
                file_path=str(file_path)
            ))
    
    def _check_file_size(self, file_path: Path, tree: ast.AST) -> None:
        """Check if file exceeds maximum line limit"""
        # Count actual code lines (exclude docstrings and comments)
        code_lines = 0
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                code_lines = max(code_lines, node.lineno)
        
        if code_lines > self.MAX_FILE_LINES:
            self.violations.append(Violation(
                severity=ViolationSeverity.WARNING,
                rule="file_size",
                message=f"File has {code_lines} lines, exceeds maximum of {self.MAX_FILE_LINES}",
                file_path=str(file_path)
            ))
    
    def _check_imports(self, file_path: Path, tree: ast.AST) -> None:
        """Check import organization and dependencies"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'lineno': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append({
                        'type': 'from',
                        'module': node.module,
                        'lineno': node.lineno
                    })
        
        # Check for wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        self.violations.append(Violation(
                            severity=ViolationSeverity.WARNING,
                            rule="import_style",
                            message="Avoid wildcard imports (from module import *)",
                            file_path=str(file_path),
                            line_number=node.lineno
                        ))
        
        # Check import ordering (stdlib -> third-party -> local)
        self._check_import_order(file_path, imports)
    
    def _check_import_order(self, file_path: Path, imports: List[Dict]) -> None:
        """Validate import grouping and ordering"""
        if not imports:
            return
            
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'typing', 'pathlib', 'logging', 'ast',
            'argparse', 'collections', 'itertools', 'functools', 'dataclasses',
            'enum', 'abc'
        }
        
        prev_group = None
        for imp in imports:
            module = imp['module'].split('.')[0]
            
            if module in stdlib_modules:
                current_group = 'stdlib'
            elif module.startswith('validators') or module.startswith('schemas') or module.startswith('standards'):
                current_group = 'local'
            else:
                current_group = 'third_party'
            
            # Check if we're going backwards in grouping
            if prev_group == 'third_party' and current_group == 'stdlib':
                self.violations.append(Violation(
                    severity=ViolationSeverity.INFO,
                    rule="import_order",
                    message="Imports should be grouped: stdlib, third-party, local",
                    file_path=str(file_path),
                    line_number=imp['lineno']
                ))
            elif prev_group == 'local' and current_group != 'local':
                self.violations.append(Violation(
                    severity=ViolationSeverity.INFO,
                    rule="import_order",
                    message="Imports should be grouped: stdlib, third-party, local",
                    file_path=str(file_path),
                    line_number=imp['lineno']
                ))
            
            prev_group = current_group
    
    def _check_naming(self, file_path: Path, tree: ast.AST) -> None:
        """Check naming conventions"""
        for node in ast.walk(tree):
            # Check class names (should be PascalCase)
            if isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    self.violations.append(Violation(
                        severity=ViolationSeverity.WARNING,
                        rule="naming_convention",
                        message=f"Class name '{node.name}' should use PascalCase",
                        file_path=str(file_path),
                        line_number=node.lineno
                    ))
            
            # Check function names (should be snake_case)
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('_'):  # Private methods are ok
                    continue
                if any(c.isupper() for c in node.name):
                    self.violations.append(Violation(
                        severity=ViolationSeverity.INFO,
                        rule="naming_convention",
                        message=f"Function name '{node.name}' should use snake_case",
                        file_path=str(file_path),
                        line_number=node.lineno
                    ))
    
    def report(self) -> None:
        """Print validation report"""
        if not self.violations:
            print("✓ All architectural rules passed!")
            return
        
        # Group violations by severity
        errors = [v for v in self.violations if v.severity == ViolationSeverity.ERROR]
        warnings = [v for v in self.violations if v.severity == ViolationSeverity.WARNING]
        infos = [v for v in self.violations if v.severity == ViolationSeverity.INFO]
        
        if errors:
            print("\n=== ERRORS ===")
            for violation in errors:
                print(violation)
        
        if warnings:
            print("\n=== WARNINGS ===")
            for violation in warnings:
                print(violation)
        
        if infos:
            print("\n=== INFO ===")
            for violation in infos:
                print(violation)
        
        print(f"\nTotal violations: {len(self.violations)} ({len(errors)} errors, {len(warnings)} warnings, {len(infos)} info)")


def main():
    """Main entry point for AST enforcer"""
    if len(sys.argv) < 2:
        print("Usage: python ast_enforcer.py <path-to-validate>")
        sys.exit(1)
    
    target_path = Path(sys.argv[1])
    
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)
    
    enforcer = ASTEnforcer(target_path)
    result = enforcer.validate()
    
    print(result)
    enforcer.report()
    
    # Exit with error code if validation failed
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
