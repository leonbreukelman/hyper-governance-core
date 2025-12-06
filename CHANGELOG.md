# Changelog

All notable changes to CODEX Weaver will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed

- Ruff lint errors resolved (unused variables and imports)
- MyPy type checking passes (added type stubs, fixed annotations)
- Lock file uses relative paths for cross-machine portability
- **Bundled fragments with package** – `codex list` now shows available fragments after `uv tool install` without needing to clone repo

### Added

- CONTRIBUTING.md guide
- SECURITY.md policy
- This CHANGELOG.md
- Integration tests for bundled fragment discovery

## [1.2.0] - 2025-12-05

### Added

- Four governance domains: Architecture, Stack, Process, Security
- Fragment-based composable governance with semantic deep merge
- Security veto system (banned items cannot be overridden)
- Lock file (`codex.lock.json`) for reproducible builds
- AI agent instructions (`AGENTS.md`) auto-sync via `codex weave`
- CLI commands: `init`, `add`, `remove`, `list`, `weave`, `validate`, `diff`
- Validators: AST Enforcer and Stack Police
- x-merge-strategy support: `set-union-stable`, `replace`, `append`
