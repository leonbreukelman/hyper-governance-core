# CODEX Weaver – Implementation Plan v1.2.0

**Based on:** [spec_v1.2.0.md](file:///home/leonb/workspaces/hyper-governance-core/spec_v1.2.0.md)  
**Repository:** `hyper-governance-core`  
**Created:** December 2025  
**Status:** Ready for Development

---

## Overview

This plan outlines the steps to build CODEX Weaver, a "Governance as Code" CLI engine that enforces four governance domains: **Architecture**, **Stack**, **Process**, and **Security**.

Key changes from previous plan:

- Directory structure uses `.codex/` (not `catalog/`)
- Includes validator integration from legacy `.governance/`
- Adds 5-phase migration path
- Expands CLI with reproducibility and validation commands

---

## Phase 1: Project Foundation

### 1.1 Initialize Python Project with UV

- [ ] Create `pyproject.toml` with UV as the package manager
- [ ] Configure project metadata:
  - name: `codex-weaver`
  - version: `1.2.0`
- [ ] Add dependencies:
  - `pyyaml` – YAML parsing
  - `jsonschema` – Fragment validation
  - `click` – CLI framework
  - `rich` – Terminal output formatting
- [ ] Add dev dependencies:
  - `pytest` – Testing
  - `pytest-cov` – Coverage
  - `ruff` – Linting/formatting
  - `mypy` – Type checking

### 1.2 Create Directory Structure

```
hyper-governance-core/
├── pyproject.toml
├── codex.manifest.yaml            # User intent – ordered fragment list
├── codex.lock.json                # Pinned catalog state
├── codex.schema.json              # Meta-schema for fragments
├── governance.custom.yaml         # Optional local overrides
├── src/
│   └── codex/
│       ├── __init__.py
│       ├── cli.py                 # CLI entry points
│       ├── manifest.py            # Manifest parsing
│       ├── catalog.py             # Catalog management
│       ├── merge.py               # Deep merge + veto logic
│       ├── render.py              # Artifact generation
│       ├── schema.py              # JSON Schema validation
│       └── validators/
│           ├── __init__.py
│           ├── ast_enforcer.py    # Refactored from legacy
│           └── stack_police.py    # Refactored from legacy
├── .codex/
│   ├── standards/                 # Base templates with anchors
│   │   ├── architecture.md
│   │   ├── process.md
│   │   └── security.md
│   ├── fragments/                 # Versioned governance fragments
│   │   └── base@1.0.0.yaml
│   ├── architecture.md            # GENERATED
│   ├── stack.yaml                 # GENERATED
│   ├── process.md                 # GENERATED
│   ├── security.md                # GENERATED
│   └── catalog-commit.txt         # Audit trail
├── tests/
│   ├── test_merge.py
│   ├── test_render.py
│   ├── test_cli.py
│   ├── test_schema.py
│   └── test_validators.py
└── .governance/                   # DEPRECATED – kept during migration
```

---

## Phase 2: Core Schema & Validation

### 2.1 Create JSON Schema

- [ ] Implement `codex.schema.json` as defined in spec §4
- [ ] Required fields: `kind`, `metadata`, `rules`
- [ ] Metadata fields: `name`, `version`, `domain`, `description`, `deprecated`
- [ ] Support all four domains: `architecture`, `stack`, `process`, `security`
- [ ] Include material rules for:
  - `material.stack` – Python version, libraries, tools
  - `material.process` – Branching, reviewers, status checks
  - `material.security` – Dependency scanning, forbidden patterns
- [ ] Include `x-merge-strategy` annotations:
  - `set-union-stable` – Union with deduplication
  - `replace` – Last value wins (default)
  - `append` – Concatenate arrays

### 2.2 Build Schema Validator

- [ ] Create `src/codex/schema.py`
- [ ] Validate fragments against schema on load
- [ ] Provide clear error messages for invalid fragments
- [ ] Support `deprecated` field warnings

---

## Phase 3: Catalog & Fragment Management

### 3.1 Fragment Loader

- [ ] Create `src/codex/catalog.py`
- [ ] Load fragments from `.codex/fragments/`
- [ ] Parse versioned filenames (`name@version.yaml`)
- [ ] Index fragments by name and version
- [ ] Compute SHA256 hash per fragment for lock file

### 3.2 Base Templates with Anchors

- [ ] Create `.codex/standards/architecture.md`:
  - `<!-- BEGIN_LAYERS -->` / `<!-- END_LAYERS -->`
  - `<!-- BEGIN_DECISIONS -->` / `<!-- END_DECISIONS -->`
- [ ] Create `.codex/standards/process.md`:
  - `<!-- BEGIN_BRANCHING -->` / `<!-- END_BRANCHING -->`
  - `<!-- BEGIN_RELEASE -->` / `<!-- END_RELEASE -->`
  - `<!-- BEGIN_CHECKLIST -->` / `<!-- END_CHECKLIST -->`
- [ ] Create `.codex/standards/security.md`:
  - `<!-- BEGIN_CONTROLS -->` / `<!-- END_CONTROLS -->`
  - `<!-- BEGIN_CRYPTO_POLICY -->` / `<!-- END_CRYPTO_POLICY -->`

### 3.3 Core Fragments (Migration from Legacy)

- [ ] Create `stack-core@1.0.0.yaml` from `.governance/standards/stack.yaml`
- [ ] Create `process-core@1.0.0.yaml` from `.governance/standards/process.yaml`
- [ ] Create `architecture-core@1.0.0.yaml` from `.governance/standards/architecture.md`
- [ ] Create `security-core@1.0.0.yaml` (consolidate security rules)

---

## Phase 4: Manifest & Lock File

### 4.1 Manifest Parser

- [ ] Create `src/codex/manifest.py`
- [ ] Parse `codex.manifest.yaml` (ordered fragment list)
- [ ] Resolve fragment references to catalog entries
- [ ] Handle version resolution (exact, latest, range)

### 4.2 Lock File Generator

- [ ] Generate `codex.lock.json` with structure:

  ```json
  {
    "schema_version": "1.0",
    "catalog_commit": "<git-sha>",
    "weave_timestamp": "<iso-8601>",
    "manifest_hash": "sha256:...",
    "fragments": [
      {"name": "...", "version": "...", "path": "...", "sha256": "..."}
    ]
  }
  ```

- [ ] Compute Git commit SHA for catalog state
- [ ] Support `--locked` mode for reproducible builds
- [ ] Support `--check` mode for verification

---

## Phase 5: Semantic Deep Merge Engine

### 5.1 Merge Logic

- [ ] Create `src/codex/merge.py`
- [ ] Implement deep merge with manifest order precedence
- [ ] Handle `x-merge-strategy` annotations:
  - `set-union-stable`: Union arrays, preserve order, deduplicate
  - `replace`: Last value wins
  - `append`: Concatenate arrays
- [ ] Support scalar override (last wins)

### 5.2 Security Veto System

- [ ] Auto-move `security-*` fragments to end of merge order
- [ ] Apply `governance.custom.yaml` before security fragments
- [ ] Post-merge veto pass:
  - Remove items from `banned_libraries`
  - Remove items matching `forbidden_patterns`
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
| `.codex/architecture.md` | Inject `architecture_layer_row`, `architecture_diagram`, `architecture_decisions` |
| `.codex/stack.yaml` | Export merged `material.stack` as pure YAML |
| `.codex/process.md` | Inject `process_flowchart`, `process_checklist_table` |
| `.codex/security.md` | Inject `security_controls_table`, `security_crypto_policy` |

### 6.3 Audit Trail

- [ ] Write `.codex/catalog-commit.txt` with Git SHA

---

## Phase 7: CLI Implementation

### 7.1 Core Commands

```bash
codex init              # Initialize manifest and .codex/ structure
codex add <frags...>    # Add fragments to manifest
codex remove <frag>     # Remove fragment from manifest
codex list              # List available catalog fragments
codex weave             # Generate all .codex/* artifacts
codex validate          # Run all validators
codex diff              # Show changes since last weave
```

### 7.2 Flags and Options

| Command | Flags |
|---------|-------|
| `codex weave` | `--locked`, `--dry-run`, `--check`, `--verbose` |
| `codex validate` | `--ast`, `--stack`, `--fix`, `--verbose` |
| `codex list` | `--all`, `--installed` |

### 7.3 CLI Entry Point

- [ ] Create `src/codex/cli.py` with Click
- [ ] Register as `codex` command in `pyproject.toml`
- [ ] Add rich output formatting for terminal

---

## Phase 8: Validator Integration

### 8.1 Refactor AST Enforcer

- [ ] Copy logic from `.governance/validators/ast_enforcer.py`
- [ ] Create `src/codex/validators/ast_enforcer.py`
- [ ] Update to read from `.codex/` artifacts
- [ ] Integrate with `codex validate --ast`

### 8.2 Refactor Stack Police

- [ ] Copy logic from `.governance/validators/stack_police.py`
- [ ] Create `src/codex/validators/stack_police.py`
- [ ] Update to read from `.codex/stack.yaml`
- [ ] Integrate with `codex validate --stack`

### 8.3 Validator Runner

- [ ] Create `src/codex/validators/__init__.py`
- [ ] Implement unified runner for all validators
- [ ] Support `--fix` flag for auto-correction where possible

---

## Phase 9: Migration Path

### 9.1 Phase 1 – Parallel Structure

- [ ] Create `.codex/` alongside `.governance/`
- [ ] Both structures remain valid
- [ ] CI runs both old and new validators

### 9.2 Phase 2 – Content Migration

- [ ] Convert existing standards to fragments (Phase 3.3)
- [ ] Verify content preservation

### 9.3 Phase 3 – Validation

- [ ] Run comprehensive tests
- [ ] Verify output matches legacy behavior
- [ ] Document intentional differences

### 9.4 Phase 4 – Deprecation

- [ ] Add deprecation notice to `.governance/README.md`
- [ ] Remove legacy from CI

### 9.5 Phase 5 – Removal

- [ ] Delete `.governance/` directory
- [ ] Update all documentation
- [ ] Tag as v2.0.0

---

## Phase 10: Testing

### 10.1 Unit Tests

- [ ] `test_merge.py` – Deep merge, x-merge-strategy, scalar override
- [ ] `test_render.py` – Anchor injection, template rendering
- [ ] `test_schema.py` – Fragment validation, error messages
- [ ] `test_validators.py` – AST and stack validation

### 10.2 Integration Tests

- [ ] Full `codex weave` cycle
- [ ] `codex weave --locked` reproducibility
- [ ] Verify all four output files
- [ ] Test security veto behavior
- [ ] Migration verification

### 10.3 Edge Cases

- [ ] Empty manifest
- [ ] Missing fragments
- [ ] Invalid fragment schema
- [ ] Conflicting banned/allowed libraries
- [ ] Circular fragment dependencies

---

## Phase 11: Documentation & Polish

- [ ] Write `README.md` with quickstart guide
- [ ] Add inline docstrings and type hints
- [ ] Create example project in `examples/`
- [ ] Add GitHub Actions workflow for CI
- [ ] Add CHANGELOG.md

---

## Success Criteria (from spec v1.2.0)

- [ ] All four governance domains generating correctly
- [ ] `codex weave --locked` produces byte-identical output
- [ ] Validators pass on generated artifacts
- [ ] Migration from legacy `.governance/` complete without data loss
- [ ] Process owners can add a new mandatory check in <2h
- [ ] Architecture review board can publish new layer rows instantly
- [ ] Security bans are non-overridable

---

## Estimated Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Project setup | 1 day | None |
| Phase 2: Schema | 1 day | Phase 1 |
| Phase 3: Catalog & fragments | 1 day | Phase 2 |
| Phase 4: Manifest & lock file | 1 day | Phase 3 |
| Phase 5: Merge engine | 2 days | Phase 4 |
| Phase 6: Render engine | 2 days | Phase 5 |
| Phase 7: CLI | 1 day | Phase 6 |
| Phase 8: Validators | 1 day | Phase 7 |
| Phase 9: Migration | 1 day | Phase 8 |
| Phase 10-11: Testing & docs | 2 days | Phase 9 |

**Total: ~13 days for MVP**

---

## Appendix: Resolved Issues from v1.1 Plan

| Issue | Resolution |
|-------|------------|
| Wrong spec reference path | Updated to `spec_v1.2.0.md` |
| Wrong project version (1.1.0) | Updated to 1.2.0 |
| Wrong root directory (`hypergov/`) | Changed to `hyper-governance-core/` |
| Wrong catalog path (`catalog/`) | Changed to `.codex/` |
| Missing validator integration | Added Phase 8 |
| Missing migration path | Added Phase 9 |
| Missing CLI commands | Added all commands from spec §10 |
| Missing lock file details | Added full schema in Phase 4.2 |
| Inconsistent fragment names | Added core fragments + clarified naming |
| Missing `test_validators.py` | Added to test list |
| Missing x-merge-strategy options | Added all three strategies |
