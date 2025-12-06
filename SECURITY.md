# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly.

**Do NOT file public issues for security vulnerabilities.**

Please email security concerns to the repository maintainer directly.

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:               |

## Security Measures

This project enforces security through:

- **Banned libraries** – See `.codex/security.md`
- **Forbidden patterns** – No `eval()`, `exec()`, `pickle`, unsafe YAML
- **Dependency scanning** – Run `codex validate` to check
- **AST enforcement** – Automated code scanning for security violations
