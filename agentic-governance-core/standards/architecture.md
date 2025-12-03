# Architecture Standards - Structural Law

## Purpose

This document defines the structural and spatial rules for organizing code within the governance framework. It serves as the **Structural Law** that governs how components should be arranged, interact, and evolve.

## Core Principles

### 1. Layered Architecture

The system follows a strict layered architecture pattern:

```
┌─────────────────────────────┐
│     Presentation Layer      │  ← UI, CLI, API endpoints
├─────────────────────────────┤
│      Application Layer      │  ← Use cases, orchestration
├─────────────────────────────┤
│       Domain Layer          │  ← Business logic, entities
├─────────────────────────────┤
│    Infrastructure Layer     │  ← External services, DB, I/O
└─────────────────────────────┘
```

**Rules:**
- Higher layers may depend on lower layers
- Lower layers MUST NOT depend on higher layers
- Cross-layer dependencies are forbidden
- Each layer has a single, well-defined responsibility

### 2. Module Organization

#### Validators Module
```
validators/
├── __init__.py
├── ast_enforcer.py      # AST validation logic
├── stack_police.py      # Import validation logic
└── common/
    ├── __init__.py
    ├── parser.py        # Common parsing utilities
    └── reporter.py      # Result reporting
```

#### Standards Module
```
standards/
├── architecture.md      # This file
├── stack.yaml          # Technology stack definition
└── process.yaml        # Process and workflow definition
```

#### Schemas Module
```
schemas/
├── stack.schema.json    # JSON Schema for stack.yaml
└── process.schema.json  # JSON Schema for process.yaml
```

### 3. Dependency Rules

**Allowed Dependencies:**
- `validators` → `standards` (read-only)
- `validators` → `schemas` (read-only)
- Any module → Python standard library
- Any module → Approved external libraries (see stack.yaml)

**Forbidden Dependencies:**
- `standards` → any other module (must remain pure data)
- `schemas` → any other module (must remain pure definitions)
- Circular dependencies between any modules

### 4. Design Patterns

#### Validator Pattern
All validators must implement the following interface:

```python
class BaseValidator:
    def validate(self, target: str) -> ValidationResult:
        """
        Validate the target against defined rules.
        
        Args:
            target: Path to file or directory to validate
            
        Returns:
            ValidationResult object with status and messages
        """
        pass
    
    def report(self, result: ValidationResult) -> None:
        """Generate human-readable report of validation results."""
        pass
```

#### Configuration Pattern
All configuration files must:
- Be declarative (no executable code)
- Support schema validation
- Use YAML or JSON format
- Include version information
- Document all fields with comments

### 5. Code Organization Rules

**File Structure:**
- Each Python file should have a single primary responsibility
- Maximum file length: 500 lines (excluding comments and docstrings)
- Related functionality should be grouped in modules
- Test files should mirror source file structure

**Naming Conventions:**
- Snake_case for Python files and functions
- PascalCase for classes
- UPPER_CASE for constants
- Descriptive names that reveal intent

**Import Organization:**
```python
# Standard library imports
import os
import sys

# Third-party imports
import yaml
from jsonschema import validate

# Local application imports
from validators.common import parser
from validators.common import reporter
```

### 6. Testing Requirements

**Test Structure:**
```
tests/
├── unit/
│   ├── test_ast_enforcer.py
│   └── test_stack_police.py
├── integration/
│   └── test_validation_flow.py
└── fixtures/
    ├── valid_code/
    └── invalid_code/
```

**Rules:**
- Unit tests for each validator component
- Integration tests for end-to-end workflows
- Test coverage minimum: 80%
- All tests must be deterministic and isolated

### 7. Documentation Standards

**Required Documentation:**
- Module-level docstrings for all Python files
- Function/method docstrings using Google or NumPy style
- README files for each major component
- Inline comments for complex logic only
- Examples for public APIs

### 8. Error Handling

**Rules:**
- Use specific exception types, not generic `Exception`
- Provide meaningful error messages with context
- Log errors with appropriate severity levels
- Clean up resources in finally blocks or context managers
- Never silently catch and ignore exceptions

### 9. Security Considerations

**Rules:**
- Validate all external inputs
- Never execute arbitrary code from configuration files
- Use safe parsing methods (avoid `eval()`, `exec()`)
- Sanitize file paths to prevent directory traversal
- Follow principle of least privilege

### 10. Performance Guidelines

**Rules:**
- Validate files incrementally when possible
- Cache parsed results for repeated validations
- Use generators for processing large file sets
- Profile validators before optimizing
- Document any performance-critical sections

## Enforcement

These architectural rules are enforced by:
1. **AST Enforcer** - Validates code structure automatically
2. **Code Review** - Human review for architectural compliance
3. **CI/CD Pipeline** - Automated checks on every commit
4. **Documentation Review** - Ensures standards are documented

## Evolution

This document may be updated through:
1. Proposal submission via pull request
2. Review by governance committee
3. Testing of proposed changes
4. Consensus approval
5. Versioned update to this document

### Version History

- **v1.0.0** (2025-12-03) - Initial structural law definition
