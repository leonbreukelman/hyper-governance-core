# CODEX Weaver

**Governance as Code** – A unified engine that enforces Architecture, Stack, Process, and Security domains through composable, versioned fragments.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

## Prerequisites

- **Python 3.11+**
- **[UV](https://github.com/astral-sh/uv)** package manager – Install with:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Overview

CODEX Weaver merges governance fragments semantically and renders them into living documentation. Define your organization's standards once, compose them declaratively, and enforce them automatically.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Fragments     │ ──▶ │   Merge Engine  │ ──▶ │   Artifacts     │
│                 │     │                 │     │                 │
│ • stack-core    │     │ • Deep merge    │     │ • architecture.md│
│ • process-core  │     │ • Security veto │     │ • stack.yaml    │
│ • security-core │     │ • x-merge-strategy│   │ • process.md    │
└─────────────────┘     └─────────────────┘     │ • security.md   │
                                                └─────────────────┘
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/leonbreukelman/hyper-governance-core.git
cd hyper-governance-core

# Install with UV
uv sync

# Verify installation
uv run codex --version
```

### Basic Usage

```bash
# List available fragments
codex list

# Initialize a new project
codex init

# Add fragments to your governance
codex add stack-core process-core security-core

# Generate governance artifacts
codex weave

# Validate your codebase
codex validate
```

## Governance Domains

| Domain | Output | Purpose |
|--------|--------|---------|
| **Architecture** | `.codex/architecture.md` | Layers, decisions, module organization |
| **Stack** | `.codex/stack.yaml` | Python version, libraries, tools |
| **Process** | `.codex/process.md` | Branching, reviews, CI/CD |
| **Security** | `.codex/security.md` | Banned patterns, controls, policies |

## Fragments

Fragments are versioned YAML files that define governance rules:

```yaml
# .codex/fragments/stack-core@1.0.0.yaml
kind: GovernanceFragment
metadata:
  name: stack-core
  version: 1.0.0
  domain: stack
rules:
  material:
    stack:
      python_version: "3.11"
      allowed_libraries:
        - pytest
        - click
      banned_libraries:
        - pickle
```

### Merge Strategies

Arrays support smart merging via `x-merge-strategy`:

| Strategy | Behavior |
|----------|----------|
| `set-union-stable` | Union with deduplication, preserving order |
| `replace` | Last value wins (default) |
| `append` | Concatenate arrays |

### Security Veto

Security fragments are always applied last. Items in `banned_libraries` are automatically removed from `allowed_libraries` – **this cannot be overridden**.

## CLI Reference

```bash
codex init              # Initialize manifest and .codex/ structure
codex add <frags...>    # Add fragments to manifest
codex remove <frag>     # Remove fragment from manifest
codex list              # List available fragments
codex weave             # Generate artifacts
codex weave --locked    # Reproducible build from lock file
codex weave --dry-run   # Preview without writing
codex validate          # Run validators
codex validate --ast    # AST enforcer only
codex validate --stack  # Stack police only
codex diff              # Show changes since last weave
```

## Directory Structure

```
hyper-governance-core/
├── codex.manifest.yaml    # Your fragment selections
├── codex.lock.json        # Pinned versions for reproducibility
├── codex.schema.json      # Fragment validation schema
├── .codex/
│   ├── standards/         # Base templates with injection anchors
│   ├── fragments/         # Versioned governance fragments
│   ├── architecture.md    # GENERATED
│   ├── stack.yaml         # GENERATED
│   ├── process.md         # GENERATED
│   └── security.md        # GENERATED
└── src/codex/             # CLI implementation
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Type check
uv run mypy src/
```

## License

Apache License 2.0 – see [LICENSE](LICENSE)
