# CODEX Weaver – MVP Specification (v1.2.0)

**Version 1.2.0 | December 2025**  
**Status: Ready for Development – Reconciled Edition**  
**Repository:** `hyper-governance-core`

> [!IMPORTANT]
> **Changes from v1.1.0:** Reconciled directory structure, integrated validator migration path, added security domain specification, clarified catalog/lock-file strategy for GitHub hosting.

---

## 1. Objective

Deliver a single, unified "Governance as Code" engine that simultaneously enforces **four pillars** of organisational excellence:

| Architecture | Stack | Process | Security |
|---|---|---|---|

All four domains are merged semantically, rendered into living documentation, and enforced via the same reproducible pipeline.

---

## 2. Executive Summary – What Ships in MVP v1.2

| Feature | Included | Notes |
|---------|----------|-------|
| Immutable Catalog of Fragments | Yes | Versioned fragments in `.codex/fragments/` |
| Declarative manifest | Yes | `codex.manifest.yaml` – ordered list for all domains |
| Semantic deep merge with veto system | Yes | Works identically across all four domains |
| Four rendered artifacts | Yes | `.codex/architecture.md`, `.codex/stack.yaml`, `.codex/process.md`, `.codex/security.md` |
| Anchor-based living documentation | Yes | Base templates in `.codex/standards/` with injection anchors |
| Lock file + reproducible governance | Yes | `codex.lock.json` with Git-native catalog commits |
| Custom user overrides (with veto) | Yes | `governance.custom.yaml` at repo root |
| Integrated validators | Yes | `ast_enforcer` and `stack_police` logic integrated into CLI |
| Migration from legacy `.governance/` | Yes | Parallel operation with clean deprecation path |

---

## 3. Directory Layout (after `codex weave`)

```
hyper-governance-core/
├── codex.manifest.yaml          # User intent – ordered list of fragments
├── codex.lock.json              # Pinned catalog state (Git commit + fragment hashes)
├── codex.schema.json            # Meta-schema for fragment validation
├── governance.custom.yaml       # Optional local overrides (applies to all domains)
├── pyproject.toml               # Python project with UV package manager
├── src/
│   └── codex/
│       ├── __init__.py
│       ├── cli.py               # CLI entry points (Click/Typer)
│       ├── manifest.py          # Manifest parsing
│       ├── catalog.py           # Catalog/fragment management
│       ├── merge.py             # Deep merge + veto logic
│       ├── render.py            # Artifact generation
│       ├── schema.py            # JSON Schema validation
│       └── validators/
│           ├── __init__.py
│           ├── ast_enforcer.py  # Refactored from legacy
│           └── stack_police.py  # Refactored from legacy
├── .codex/
│   ├── standards/               # Base templates with injection anchors
│   │   ├── architecture.md      # <!-- BEGIN_LAYERS --> etc.
│   │   ├── process.md           # <!-- BEGIN_BRANCHING --> etc.
│   │   └── security.md          # <!-- BEGIN_CONTROLS --> etc.
│   ├── fragments/               # Versioned governance fragments
│   │   ├── base@1.0.0.yaml
│   │   ├── architecture-core@1.0.0.yaml
│   │   ├── stack-core@1.0.0.yaml
│   │   ├── process-core@1.0.0.yaml
│   │   └── security-core@1.0.0.yaml
│   ├── architecture.md          # GENERATED – do not edit
│   ├── stack.yaml               # GENERATED – do not edit
│   ├── process.md               # GENERATED – do not edit
│   ├── security.md              # GENERATED – do not edit
│   └── catalog-commit.txt       # Audit trail (Git SHA)
├── tests/
│   ├── test_merge.py
│   ├── test_render.py
│   ├── test_cli.py
│   └── test_validators.py
└── .governance/                 # DEPRECATED – legacy structure (remove after migration)
    └── ...
```

---

## 4. Fragment Schema (codex.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/leonbreukelman/hyper-governance-core/codex.schema.json",
  "title": "CODEX Governance Fragment v1.2",
  "type": "object",
  "required": ["kind", "metadata", "rules"],
  "properties": {
    "kind": { "const": "GovernanceFragment" },
    "metadata": {
      "type": "object",
      "required": ["name", "version", "domain"],
      "properties": {
        "name":        { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "version":     { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "domain":      { "enum": ["architecture", "stack", "process", "security"] },
        "description": { "type": "string" },
        "deprecated":  { "type": "boolean", "default": false }
      }
    },
    "rules": {
      "type": "object",
      "properties": {
        "material": {
          "description": "Machine-enforceable configuration",
          "type": "object",
          "properties": {
            "stack": {
              "type": "object",
              "properties": {
                "python_version":     { "type": "string" },
                "base_image":         { "type": "string" },
                "allowed_libraries":  { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "banned_libraries":   { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "required_tools":     { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "terraform_version":  { "type": "string" },
                "node_version":       { "type": "string" }
              },
              "additionalProperties": true
            },
            "process": {
              "type": "object",
              "properties": {
                "branching_model":        { "type": "string" },
                "minimum_reviewers":      { "type": "integer" },
                "required_status_checks": { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "release_cadence":        { "type": "string" }
              }
            },
            "security": {
              "type": "object",
              "properties": {
                "scan_dependencies":      { "type": "boolean" },
                "require_signed_commits": { "type": "boolean" },
                "allowed_network_calls":  { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "forbidden_patterns":     { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" }
              }
            }
          }
        },
        "structural": {
          "description": "Human-readable content for living documentation",
          "type": "object",
          "properties": {
            "architecture_layer_row":   { "type": "string" },
            "architecture_diagram":     { "type": "string" },
            "architecture_decisions":   { "type": "string" },
            "process_flowchart":        { "type": "string" },
            "process_checklist_table":  { "type": "string" },
            "security_controls_table":  { "type": "string" },
            "security_crypto_policy":   { "type": "string" },
            "readme_badges":            { "type": "array", "items": {"type":"string"} }
          },
          "additionalProperties": true
        }
      }
    }
  }
}
```

---

## 5. Rendered Artifacts – One File per Domain

| Output File | Source | Injection Anchors |
|-------------|--------|-------------------|
| `.codex/architecture.md` | `.codex/standards/architecture.md` | `<!-- BEGIN_LAYERS -->`, `<!-- BEGIN_DECISIONS -->` |
| `.codex/stack.yaml` | Merged `material.stack` only | N/A (pure YAML export) |
| `.codex/process.md` | `.codex/standards/process.md` | `<!-- BEGIN_BRANCHING -->`, `<!-- BEGIN_RELEASE -->`, `<!-- BEGIN_CHECKLIST -->` |
| `.codex/security.md` | `.codex/standards/security.md` | `<!-- BEGIN_CONTROLS -->`, `<!-- BEGIN_CRYPTO_POLICY -->` |

All four documents are generated from the **same weave run** using identical anchor-based injection logic.

---

## 6. Example Fragments

### 6.1 <stack-core@1.0.0.yaml>

*Migrated from legacy `.governance/standards/stack.yaml`*

```yaml
kind: GovernanceFragment
metadata:
  name: stack-core
  version: 1.0.0
  domain: stack
  description: Core technology stack - migrated from legacy stack.yaml
rules:
  material:
    stack:
      python_version: "3.11"
      allowed_libraries:
        - pyyaml
        - jsonschema
        - click
        - rich
        - pytest
        - ruff
      banned_libraries:
        - pickle
        - telnetlib
      required_tools:
        - ruff
        - mypy
        - pytest
```

### 6.2 <process-core@1.0.0.yaml>

*Migrated from legacy `.governance/standards/process.yaml`*

```yaml
kind: GovernanceFragment
metadata:
  name: process-core
  version: 1.0.0
  domain: process
  description: Core development process - migrated from legacy process.yaml
rules:
  material:
    process:
      branching_model: trunk-based
      minimum_reviewers: 1
      required_status_checks:
        - tests
        - validators
        - linting
        - coverage
  structural:
    process_checklist_table: |
      | Phase | Mandatory Artifacts | Owner |
      |-------|---------------------|-------|
      | Planning | Requirements, Design | Contributor |
      | Implementation | Code, Tests, Docs | Contributor |
      | Validation | All checks passing | CI |
      | Review | Approval | Reviewer |
```

### 6.3 <security-core@1.0.0.yaml>

*New fragment – consolidates security from legacy stack.yaml*

```yaml
kind: GovernanceFragment
metadata:
  name: security-core
  version: 1.0.0
  domain: security
  description: Core security policies
rules:
  material:
    stack:
      banned_libraries:
        - pickle
        - eval
        - exec
        - os.system
        - yaml.load  # unsafe loader
    security:
      scan_dependencies: true
      require_signed_commits: false
      forbidden_patterns:
        - "eval("
        - "exec("
        - "os.system("
  structural:
    security_controls_table: |
      | Control | Enforcement | Notes |
      |---------|-------------|-------|
      | No arbitrary code execution | Strict | Banned: pickle, eval, exec |
      | Safe YAML parsing | Strict | Use safe_load() only |
      | Dependency scanning | Required | Run on every PR |
```

---

## 7. Security & Veto Model

1. **Normal merge** in manifest order
2. **`governance.custom.yaml`** merged last (before security)
3. **Security fragments** (domain: security OR name starting `security-`) are **force-moved to the very end**
4. **Post-merge veto pass**: removes anything present in `banned_libraries` or `forbidden_patterns`
5. **Security bans are non-overridable** – custom overlays cannot whitelist banned items

---

## 8. x-merge-strategy Implementation

The `x-merge-strategy` annotation in the schema controls array merging behavior:

| Strategy | Behavior |
|----------|----------|
| `set-union-stable` | Union of arrays, preserving first-occurrence order, deduplicating |
| `replace` (default) | Later values completely replace earlier values |
| `append` | Concatenate arrays (allows duplicates) |

**Implementation in `merge.py`:**

```python
def merge_with_strategy(base: dict, overlay: dict, schema: dict) -> dict:
    """Deep merge respecting x-merge-strategy annotations."""
    for key, value in overlay.items():
        if key in base:
            strategy = get_merge_strategy(schema, key)  # reads x-merge-strategy
            if isinstance(value, list) and strategy == "set-union-stable":
                # Preserve order, deduplicate
                seen = set()
                merged = []
                for item in base[key] + value:
                    if item not in seen:
                        seen.add(item)
                        merged.append(item)
                base[key] = merged
            elif isinstance(value, dict):
                base[key] = merge_with_strategy(base[key], value, schema.get(key, {}))
            else:
                base[key] = value  # scalar override
        else:
            base[key] = value
    return base
```

---

## 9. Lock File & Catalog Commit (GitHub-Native)

### 9.1 Catalog Definition

The **catalog** is the `.codex/fragments/` directory in this repository. Versioning is Git-native.

### 9.2 Lock File Format

```json
{
  "schema_version": "1.0",
  "catalog_commit": "a1b2c3d4e5f6789...",
  "weave_timestamp": "2025-12-05T12:00:00Z",
  "manifest_hash": "sha256:...",
  "fragments": [
    {
      "name": "base",
      "version": "1.0.0",
      "path": ".codex/fragments/base@1.0.0.yaml",
      "sha256": "..."
    },
    {
      "name": "stack-core",
      "version": "1.0.0",
      "path": ".codex/fragments/stack-core@1.0.0.yaml",
      "sha256": "..."
    }
  ]
}
```

### 9.3 Reproducibility Commands

```bash
codex weave              # Generate from manifest, update lock file
codex weave --locked     # Generate from lock file (exact reproduction)
codex weave --check      # Verify current output matches lock file
```

---

## 10. CLI Commands

```bash
codex init              # Initialize codex.manifest.yaml, create .codex/ structure
codex add <frags...>    # Add fragments to manifest
codex remove <frag>     # Remove fragment from manifest
codex list              # List available fragments in catalog
codex weave             # Generate all .codex/* artifacts
codex weave --locked    # Reproducible build from lock file
codex weave --dry-run   # Show what would be generated
codex validate          # Run all validators on current codebase
codex validate --fix    # Auto-fix where possible
codex diff              # Show changes between current and last weave
```

---

## 11. Integrated Validators

The existing validator logic is preserved and integrated:

| Validator | Source | Invocation |
|-----------|--------|------------|
| AST Enforcer | Refactored from `.governance/validators/ast_enforcer.py` | `codex validate --ast` |
| Stack Police | Refactored from `.governance/validators/stack_police.py` | `codex validate --stack` |

Both validators read from the generated `.codex/` artifacts, ensuring validation is always against the current governance state.

---

## 12. Migration Path from Legacy `.governance/`

### Phase 1: Parallel Structure

- Create `.codex/` alongside existing `.governance/`
- Both structures remain valid during transition
- CI runs both old and new validators

### Phase 2: Content Migration

- Convert `stack.yaml` → `stack-core@1.0.0.yaml`
- Convert `process.yaml` → `process-core@1.0.0.yaml`
- Convert `architecture.md` → base template + `architecture-core@1.0.0.yaml`
- Create `security-core@1.0.0.yaml` from security content in stack.yaml

### Phase 3: Validation

- Verify generated output matches legacy behavior
- Run all tests against new structure
- Document any intentional differences

### Phase 4: Deprecation

- Add deprecation notice to `.governance/README.md`
- Remove references to legacy structure from CI
- Keep legacy for one release cycle

### Phase 5: Removal

- Delete `.governance/` directory
- Update all documentation
- Release as v2.0.0

---

## 13. Success Criteria

- [ ] All four governance domains generating correctly
- [ ] `codex weave --locked` produces byte-identical output
- [ ] Validators pass on generated artifacts
- [ ] Migration from legacy `.governance/` complete without data loss
- [ ] Process owners can add a new mandatory check in <2h
- [ ] Architecture review board can publish new layer rows instantly
- [ ] Security bans are non-overridable

---

## 14. Estimated Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Project setup (pyproject.toml, structure) | 1 day | None |
| Schema + Fragment loader | 1 day | Project setup |
| Merge engine with x-merge-strategy | 2 days | Schema |
| Render engine with anchors | 2 days | Merge engine |
| CLI implementation | 1 day | Render engine |
| Validator integration | 1 day | CLI |
| Migration + Testing | 2 days | All above |

**Total: ~10 days for MVP**
