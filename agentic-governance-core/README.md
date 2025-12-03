# Agentic Governance Core

A constitutional framework for AI-driven software governance, providing structural, material, and procedural laws for autonomous system development.

## Overview

This repository implements a governance system based on three constitutional artifacts:

1. **Structural Law** (`standards/architecture.md`) - Defines spatial and architectural rules
2. **Material Law** (`standards/stack.yaml`) - Specifies the approved technology stack
3. **Procedural Law** (`standards/process.yaml`) - Outlines workflows, roles, and processes

## Directory Structure

```
agentic-governance-core/
├── README.md                 # This file - Entry point and usage guide
├── standards/                # The Constitutional Artifacts
│   ├── architecture.md       # Structural Law (Spatial)
│   ├── stack.yaml            # Material Law (Tech Stack)
│   └── process.yaml          # Procedural Law (Workflow & Roles)
├── validators/               # The Judicial Reference Implementation (Python)
│   ├── ast_enforcer.py       # Validates architecture.md rules
│   └── stack_police.py       # Validates stack.yaml imports
└── schemas/                  # JSON Schemas to validate the YAML files themselves
    ├── stack.schema.json
    └── process.schema.json
```

## Usage

### Validating Architecture

Use the AST enforcer to validate architectural rules:

```bash
python validators/ast_enforcer.py <path-to-code>
```

### Validating Stack Compliance

Use the stack police to validate import compliance:

```bash
python validators/stack_police.py <path-to-code>
```

### Validating YAML Files

Validate the constitutional artifacts against their schemas:

```bash
# Validate stack.yaml
python -m jsonschema -i standards/stack.yaml schemas/stack.schema.json

# Validate process.yaml
python -m jsonschema -i standards/process.yaml schemas/process.schema.json
```

## Constitutional Artifacts

### Architecture Standards

The `architecture.md` file defines structural rules for how code should be organized, including:
- Module organization
- Dependency rules
- Layering principles
- Design patterns

### Technology Stack

The `stack.yaml` file defines:
- Approved libraries and frameworks
- Version constraints
- Allowed imports
- Forbidden dependencies

### Process Standards

The `process.yaml` file defines:
- Development workflows
- Code review processes
- Testing requirements
- Deployment procedures
- Role definitions and responsibilities

## Validators

### AST Enforcer

The AST enforcer parses source code and validates it against architectural rules defined in `architecture.md`. It ensures:
- Proper module structure
- Compliance with layering rules
- Adherence to design patterns

### Stack Police

The stack police validates imports and dependencies against the approved technology stack in `stack.yaml`. It ensures:
- Only approved libraries are imported
- Version constraints are met
- No forbidden dependencies are used

## License

See the LICENSE file in the root of the repository.
