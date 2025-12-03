"""
Stack Police - Validates imports against approved technology stack in stack.yaml

This validator ensures that:
- Only approved libraries are imported
- Forbidden libraries are not used
- Import patterns match stack definitions
- Version constraints are documented
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(1)


class ViolationSeverity(Enum):
    """Severity levels for stack violations"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class StackViolation:
    """Represents a stack compliance violation"""
    severity: ViolationSeverity
    rule: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    import_name: Optional[str] = None
    
    def __str__(self) -> str:
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        import_info = f" (import: {self.import_name})" if self.import_name else ""
        return f"[{self.severity.value.upper()}] {location} - {self.rule}: {self.message}{import_info}"


@dataclass
class ValidationResult:
    """Result of stack validation"""
    passed: bool
    violations: List[StackViolation]
    files_checked: int
    imports_checked: int
    
    def __str__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"\nStack Validation {status}\n"
            f"Files checked: {self.files_checked}\n"
            f"Imports checked: {self.imports_checked}\n"
            f"Violations: {len(self.violations)}\n"
        )


class StackPolice:
    """
    Validates code imports against approved technology stack.
    
    Ensures:
    - Only approved libraries are imported
    - Forbidden libraries are not used
    - Import patterns comply with stack.yaml
    """
    
    def __init__(self, root_path: Path, stack_yaml_path: Optional[Path] = None):
        """
        Initialize Stack Police.
        
        Args:
            root_path: Root directory to validate
            stack_yaml_path: Path to stack.yaml (defaults to standards/stack.yaml)
        """
        self.root_path = Path(root_path)
        self.violations: List[StackViolation] = []
        self.imports_checked = 0
        
        # Load stack configuration
        if stack_yaml_path is None:
            # Try to find stack.yaml relative to this file
            validator_dir = Path(__file__).parent
            stack_yaml_path = validator_dir.parent / "standards" / "stack.yaml"
        
        self.stack_config = self._load_stack_config(stack_yaml_path)
        
        # Build lookup sets for fast checking
        self._build_lookup_sets()
    
    def _load_stack_config(self, yaml_path: Path) -> Dict:
        """Load and parse stack.yaml configuration"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: stack.yaml not found at {yaml_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing stack.yaml: {e}")
            return {}
    
    def _build_lookup_sets(self) -> None:
        """Build fast lookup sets from stack configuration"""
        self.approved_imports: Set[str] = set()
        self.forbidden_imports: Set[str] = set()
        self.stdlib_allowed: Set[str] = set()
        
        # Extract approved libraries
        for lib in self.stack_config.get('approved_libraries', []):
            for pattern in lib.get('import_patterns', []):
                self.approved_imports.add(pattern.split('.')[0])
        
        # Extract forbidden libraries
        for lib in self.stack_config.get('forbidden_libraries', []):
            self.forbidden_imports.add(lib['name'])
        
        # Extract allowed stdlib modules
        import_rules = self.stack_config.get('import_rules', {})
        self.stdlib_allowed = set(import_rules.get('stdlib_allowed', []))
    
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
            files_checked=len(python_files),
            imports_checked=self.imports_checked
        )
    
    def _validate_file(self, file_path: Path) -> None:
        """Validate imports in a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(file_path))
            
            # Extract and validate imports
            self._check_imports(file_path, tree)
            
            # Check for dangerous function calls
            self._check_dangerous_calls(file_path, tree)
            
        except SyntaxError as e:
            self.violations.append(StackViolation(
                severity=ViolationSeverity.ERROR,
                rule="syntax",
                message=f"Syntax error: {e}",
                file_path=str(file_path),
                line_number=e.lineno if hasattr(e, 'lineno') else None
            ))
        except Exception as e:
            self.violations.append(StackViolation(
                severity=ViolationSeverity.ERROR,
                rule="parsing",
                message=f"Failed to parse: {e}",
                file_path=str(file_path)
            ))
    
    def _check_imports(self, file_path: Path, tree: ast.AST) -> None:
        """Check all imports in the file"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports_checked += 1
                    self._validate_import(file_path, alias.name, node.lineno)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports_checked += 1
                    self._validate_import(file_path, node.module, node.lineno)
    
    def _validate_import(self, file_path: Path, module_name: str, line_number: int) -> None:
        """Validate a single import against stack rules"""
        base_module = module_name.split('.')[0]
        
        # Check if it's a forbidden import
        if base_module in self.forbidden_imports or module_name in self.forbidden_imports:
            forbidden_lib = next(
                (lib for lib in self.stack_config.get('forbidden_libraries', [])
                 if lib['name'] == base_module or lib['name'] == module_name),
                None
            )
            
            message = f"Forbidden library: {module_name}"
            if forbidden_lib:
                message += f" - {forbidden_lib['reason']}"
                if 'alternatives' in forbidden_lib:
                    message += f". Use: {', '.join(forbidden_lib['alternatives'])}"
            
            self.violations.append(StackViolation(
                severity=ViolationSeverity.ERROR,
                rule="forbidden_import",
                message=message,
                file_path=str(file_path),
                line_number=line_number,
                import_name=module_name
            ))
            return
        
        # Check if it's in stdlib (always allowed)
        if base_module in self.stdlib_allowed:
            return
        
        # Check if it's approved
        if base_module in self.approved_imports:
            return
        
        # Check if it's a local import (validators, schemas, standards)
        if base_module in {'validators', 'schemas', 'standards'}:
            return
        
        # Unknown import - warn about it
        self.violations.append(StackViolation(
            severity=ViolationSeverity.WARNING,
            rule="unapproved_import",
            message=f"Import '{module_name}' is not in approved list. Add to stack.yaml if needed.",
            file_path=str(file_path),
            line_number=line_number,
            import_name=module_name
        ))
    
    def _check_dangerous_calls(self, file_path: Path, tree: ast.AST) -> None:
        """Check for dangerous function calls"""
        dangerous_calls = {
            'eval': 'Use ast.literal_eval instead',
            'exec': 'Avoid dynamic code execution',
            'compile': 'Avoid dynamic code compilation',
            '__import__': 'Use importlib instead'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Check for os.system and similar
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'os' and node.func.attr == 'system':
                            self.violations.append(StackViolation(
                                severity=ViolationSeverity.ERROR,
                                rule="dangerous_call",
                                message="os.system() is forbidden. Use subprocess with shell=False",
                                file_path=str(file_path),
                                line_number=node.lineno
                            ))
                
                if func_name in dangerous_calls:
                    self.violations.append(StackViolation(
                        severity=ViolationSeverity.ERROR,
                        rule="dangerous_call",
                        message=f"{func_name}() is forbidden. {dangerous_calls[func_name]}",
                        file_path=str(file_path),
                        line_number=node.lineno
                    ))
    
    def report(self) -> None:
        """Print validation report"""
        if not self.violations:
            print("✓ All imports comply with stack.yaml!")
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
    """Main entry point for stack police"""
    if len(sys.argv) < 2:
        print("Usage: python stack_police.py <path-to-validate> [stack.yaml-path]")
        sys.exit(1)
    
    target_path = Path(sys.argv[1])
    stack_yaml = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)
    
    police = StackPolice(target_path, stack_yaml)
    result = police.validate()
    
    print(result)
    police.report()
    
    # Exit with error code if validation failed
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
