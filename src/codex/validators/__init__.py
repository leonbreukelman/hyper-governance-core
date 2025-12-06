"""
CODEX Validators - AST Enforcer and Stack Police

Integrated validation suite for governance enforcement.
"""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of validation run."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    files_checked: int = 0
    warnings: list[str] = field(default_factory=list)


def run_validators(
    ast_only: bool = False,
    stack_only: bool = False,
    verbose: bool = False,
) -> ValidationResult:
    """
    Run validators on the current codebase.

    Args:
        ast_only: Run only AST enforcer
        stack_only: Run only stack police
        verbose: Print detailed output

    Returns:
        ValidationResult with pass/fail and violations
    """
    violations: list[str] = []
    warnings: list[str] = []
    files_checked = 0

    if not stack_only:
        # Run AST enforcer
        from codex.validators.ast_enforcer import ASTEnforcer

        enforcer = ASTEnforcer(verbose=verbose)
        ast_result = enforcer.validate()
        violations.extend(ast_result.violations)
        warnings.extend(ast_result.warnings)
        files_checked += ast_result.files_checked

    if not ast_only:
        # Run Stack police
        from codex.validators.stack_police import StackPolice

        police = StackPolice(verbose=verbose)
        stack_result = police.validate()
        violations.extend(stack_result.violations)
        warnings.extend(stack_result.warnings)
        files_checked += stack_result.files_checked

    return ValidationResult(
        passed=len(violations) == 0,
        violations=violations,
        files_checked=files_checked,
        warnings=warnings,
    )
