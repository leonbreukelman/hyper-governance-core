# CODEX Weaver – Implementation Plan

**Based on:** [spec.md](file:///home/leonb/workspaces/hypergov/spec.md) (v1.1.0)  
**Created:** December 2025  
**Status:** Ready for Development

---

## Overview

This plan outlines the steps to build CODEX Weaver, a "Governance as Code" CLI engine that enforces four governance domains: **Architecture**, **Stack**, **Process**, and **Security**.

---

## Phase 1: Project Foundation

### 1.1 Initialize Python Project with UV

- [ ] Create `pyproject.toml` with UV as the package manager
- [ ] Configure project metadata (name: `codex-weaver`, version: `1.1.0`)
- [ ] Add dependencies:
  - `pyyaml` – YAML parsing
  - `jsonschema` – Fragment validation
  - `click` or `typer` – CLI framework
  - `rich` – Terminal output formatting
- [ ] Add dev dependencies:
  - `pytest` – Testing
  - `ruff` – Linting/formatting

### 1.2 Create Directory Structure

```
hypergov/
├── pyproject.toml
├── src/
│   └── codex/
│       ├── __init__.py
│       ├── cli.py              # CLI entry points
│       ├── manifest.py         # Manifest parsing
│       ├── catalog.py          # Catalog management
│       ├── merge.py            # Deep merge + veto logic
│       ├── render.py           # Artifact generation
│       └── schema.py           # JSON Schema validation
├── catalog/
│   ├── base/
│   │   ├── architecture.md     # Base template with anchors
│   │   ├── process.md          # Base template with anchors
│   │   └── security.md         # Base template with anchors
│   └── fragments/
│       └── base@1.0.0.yaml     # Starter fragment
├── tests/
│   ├── test_merge.py
│   ├── test_render.py
│   └── test_cli.py
└── codex.schema.json           # Fragment validation schema
```

---

## Phase 2: Core Schema & Validation

### 2.1 Create JSON Schema

- [ ] Implement `codex.schema.json` as defined in spec Section 4
- [ ] Support all four domains: `architecture`, `stack`, `process`, `security`
- [ ] Include custom `x-merge-strategy` annotations for array handling

### 2.2 Build Schema Validator

- [ ] Create `src/codex/schema.py`
- [ ] Validate fragments against schema on load
- [ ] Provide clear error messages for invalid fragments

---

## Phase 3: Catalog & Fragment Management

### 3.1 Fragment Loader

- [ ] Create `src/codex/catalog.py`
- [ ] Load fragments from `catalog/fragments/`
- [ ] Parse versioned filenames (`name@version.yaml`)
- [ ] Index fragments by name and version

### 3.2 Base Templates

- [ ] Create `catalog/base/architecture.md` with injection anchors:
  - `<!-- BEGIN_LAYERS -->` / `<!-- END_LAYERS -->`
  - `<!-- BEGIN_DECISIONS -->` / `<!-- END_DECISIONS -->`
- [ ] Create `catalog/base/process.md` with injection anchors:
  - `<!-- BEGIN_BRANCHING -->` / `<!-- END_BRANCHING -->`
  - `<!-- BEGIN_RELEASE -->` / `<!-- END_RELEASE -->`
- [ ] Create `catalog/base/security.md` with injection anchors:
  - `<!-- BEGIN_CONTROLS -->` / `<!-- END_CONTROLS -->`
  - `<!-- BEGIN_CRYPTO_POLICY -->` / `<!-- END_CRYPTO_POLICY -->`

---

## Phase 4: Manifest & Lock File

### 4.1 Manifest Parser

- [ ] Create `src/codex/manifest.py`
- [ ] Parse `codex.manifest.yaml` (ordered fragment list)
- [ ] Resolve fragment references to catalog entries

### 4.2 Lock File Generator

- [ ] Generate `codex.lock.json` after successful weave
- [ ] Pin exact versions and catalog commit hash
- [ ] Support reproducible builds from lock file

---

## Phase 5: Semantic Deep Merge Engine

### 5.1 Merge Logic

- [ ] Create `src/codex/merge.py`
- [ ] Implement deep merge with manifest order precedence
- [ ] Handle `x-merge-strategy: set-union-stable` for arrays
- [ ] Support scalar override (last wins)

### 5.2 Security Veto System

- [ ] Auto-move `security-*` fragments to end of merge order
- [ ] Apply `governance.custom.yaml` before security fragments
- [ ] Post-merge veto pass: remove items from `banned_libraries`
- [ ] Ensure security bans are non-overridable

---

## Phase 6: Artifact Rendering

### 6.1 Render Engine

- [ ] Create `src/codex/render.py`
- [ ] Inject structural content into anchor points
- [ ] Generate all four artifacts in single pass

### 6.2 Output Files

| Output | Generator |
|--------|-----------|
| `.codex/architecture.md` | Inject `architecture_layer_row`, `architecture_diagram` into base template |
| `.codex/stack.yaml` | Export merged `material.stack` as pure YAML |
| `.codex/process.md` | Inject `process_flowchart`, `process_checklist_table` into base template |
| `.codex/security.md` | Inject `security_controls_table` into base template |

### 6.3 Audit Trail

- [ ] Write `.codex/catalog-commit.txt` with catalog state hash

---

## Phase 7: CLI Implementation

### 7.1 Commands

```bash
codex init          # Initialize codex.manifest.yaml in current directory
codex add <frags>   # Add fragments to manifest
codex remove <frag> # Remove fragment from manifest
codex weave         # Generate all .codex/* artifacts
codex validate      # Validate manifest and fragments without weaving
codex list          # List available catalog fragments
```

### 7.2 CLI Entry Point

- [ ] Create `src/codex/cli.py` with Click/Typer
- [ ] Register as `codex` command in `pyproject.toml`
- [ ] Add `--verbose`, `--dry-run` flags

---

## Phase 8: Testing

### 8.1 Unit Tests

- [ ] `test_merge.py` – Verify deep merge, array union, scalar override
- [ ] `test_render.py` – Verify anchor injection, template rendering
- [ ] `test_schema.py` – Verify fragment validation

### 8.2 Integration Tests

- [ ] Full `codex weave` cycle with sample fragments
- [ ] Verify all four output files generated correctly
- [ ] Test security veto behavior

### 8.3 Edge Cases

- [ ] Empty manifest
- [ ] Missing fragments
- [ ] Invalid fragment schema
- [ ] Conflicting banned/allowed libraries

---

## Phase 9: Sample Fragments

Create starter fragments as defined in spec Section 6:

- [ ] `base@1.0.0.yaml` – Minimal starter fragment
- [ ] `architecture-aws@2.1.0.yaml` – AWS architecture layer
- [ ] `stack-python@3.11.0.yaml` – Python stack configuration
- [ ] `process-gitflow-enterprise@1.4.0.yaml` – GitFlow process rules
- [ ] `security-strict@2.0.0.yaml` – Strict security bans

---

## Phase 10: Documentation & Polish

- [ ] Write `README.md` with quickstart guide
- [ ] Add inline docstrings and type hints
- [ ] Create example project in `examples/`
- [ ] Add GitHub Actions workflow for CI

---

## Success Criteria (from spec v1.1)

- [ ] 3+ product teams using all four generated artifacts in CI/CD
- [ ] Process owners can add a new mandatory check in <2h
- [ ] Architecture review board can publish new layer rows instantly
- [ ] Security bans are non-overridable

---

## Estimated Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1-2 | 1 day | None |
| Phase 3-4 | 2 days | Phase 1-2 |
| Phase 5 | 2 days | Phase 3-4 |
| Phase 6 | 2 days | Phase 5 |
| Phase 7 | 1 day | Phase 6 |
| Phase 8-10 | 2 days | Phase 7 |

**Total: ~10 days for MVP**
