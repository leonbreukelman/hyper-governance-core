# GitHub Copilot Instructions

This repository uses **CODEX Weaver** for governance-as-code.

**Primary reference:** See [AGENTS.md](../AGENTS.md) for complete AI agent instructions.

## Quick Rules

1. Run `codex validate` before submitting code
2. Follow stack requirements in `.codex/stack.yaml`
3. Never use banned libraries (see `.codex/security.md`)
4. All code must pass `uv run pytest`

For detailed governance, security controls, and process guidelines,
refer to the `AGENTS.md` file at the repository root.
