# Contributing to CODEX Weaver

Thank you for your interest in contributing!

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/leonbreukelman/hyper-governance-core.git
   cd hyper-governance-core
   ```

2. **Install UV** (if not already installed)

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**

   ```bash
   uv sync --all-extras
   ```

4. **Verify setup**

   ```bash
   uv run codex --version
   uv run pytest
   ```

## Code Quality

Before submitting a PR, ensure all checks pass:

```bash
# Lint check
uv run ruff check src/

# Type check
uv run mypy src/

# Tests
uv run pytest

# Governance validation
uv run codex validate
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all checks pass
6. Submit PR with clear description

## Governance

This project uses **CODEX Weaver** to manage its own governance. See [AGENTS.md](AGENTS.md) for AI agent instructions and governance references.
