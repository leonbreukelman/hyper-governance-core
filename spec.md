# CODEX Weaver – MVP Specification (v1.1.0)  

**Version 1.1.0 | December 2025**  
**Status: Approved for Development – Four-Domain Edition**  
**New in v1.1**: Explicit support for **Architecture**, **Stack**, **Process**, and **Security** as first-class governance domains.

### 1. Objective  

Deliver a single, unified “Governance as Code” engine that simultaneously enforces **four pillars** of organisational excellence:

| Architecture | Stack | Process | Security |
|---|---|---|---|

All four domains are merged semantically, rendered into living documentation, and enforced via the same reproducible pipeline.

### 2. Executive Summary – What Ships in MVP v1.1

| Feature                                 | Included | Notes |
|-----------------------------------------|----------|-------|
|
| Immutable Catalog of Fragments          | Yes      | Versioned fragments for all four domains |
| Declarative manifest                    | Yes      | Single ordered list applies to all domains |
| Semantic deep merge with veto system    | Yes      | Works identically across all four domains |
| Four rendered artifacts                 | Yes      | `.codex/architecture.md`  <br>`.codex/stack.yaml`  <br>`.codex/process.md`  <br>`.codex/security.md` |
| Anchor-based living documentation       | Yes      | One base file per domain with injection anchors |
| Lock file + reproducible governance     | Yes      | Single lock file covers all domains |
| Custom user overrides (with veto)       | Yes      | Same file works for all domains |

### 3. Directory Layout (after `codex weave`)

```
my-project/
├── codex.manifest.yaml          # User intent – ordered list of fragments
├── codex.lock.json              # Pinned catalog state├── governance.custom.yaml       # Optional local overrides (applies to all domains)├── .codex/
│   ├── stack.yaml               # Material → technology stack (Python, Node, Terraform, etc.)
│   ├── architecture.md          # Architectural decisions, layers, diagrams
│   ├── process.md               # SDLC, branching, review, release mandates
│   ├── security.md              # Security & compliance baseline
│   └── catalog-commit.txt       # Audit trail└── catalog/
    └── fragments/
        ├── base@1.0.0.yaml
        ├── architecture-aws@2.1.0.yaml
        ├── stack-python@3.11.0.yaml
        ├── process-gitflow-enterprise@1.4.0.yaml
        └── security-strict@2.0.0.yaml
```

### 4. Updated Fragment Schema (codex.schema.json) – Four-Domain Edition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CODEX Governance Fragment v1.1",
  "type": "object",
  "required": ["kind", "metadata", "rules"],
  "properties": {
    "kind": { "const": "GovernanceFragment" },
    "metadata": {
      "type": "object",
      "required": ["name", "version", "domain"],
      "properties": {
        "name":        { "type": "string", "pattern": "^[a-z0-9-]+$"},
        "version":     { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "domain":      { "enum": ["architecture", "stack", "process", "security"] },
        "description": { "type": "string" }
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
                "minimum_reviewers":       { "type": "integer" },
                "required_status_checks":  { "type": "array", "items": {"type":"string"}, "x-merge-strategy": "set-union-stable" },
                "release_cadence":         { "type": "string" }
              }
            }
          }
        },
        "structural": {
          "description": "Human-readable content for living documentation",
          "type": "object",
          "properties": {
            "architecture_layer_row":      { "type": "string" },
            "architecture_diagram":        { "type": "string" },
            "process_flowchart":          { "type": "string" },
            "process_checklist_table":    { "type": "string" },
            "security_controls_table":     { "type": "string" },
            "readme_badges":              { "type": "array", "items": {"type":"string"} }
          },
          "additionalProperties": true
        }
      }
    }
  }
}
```

### 5. Rendered Artifacts – One File per Domain (MVP)

| Output File                | Source of Truth Base Template | Injection Anchors (examples) |
|----------------------------|-------------------------------|--------------------------------|
| `.codex/architecture.md`   | catalog/base/architecture.md   | `<!-- BEGIN_LAYERS -->`, `<!-- BEGIN_DECISIONS -->` |
| `.codex/stack.yaml`        | merged material.stack only    | N/A (pure YAML) |
| `.codex/process.md`        | catalog/base/process.md       | `<!-- BEGIN_BRANCHING -->`, `<!-- BEGIN_RELEASE -->` |
| `.codex/security.md`       | catalog/base/security.md      | `<!-- BEGIN_CONTROLS -->`, `<!-- BEGIN_CRYPTO_POLICY -->` |

All four documents are generated from the **same weave run** using identical anchor-based injection logic.

### 6. Example Fragment Snippets

**<architecture-aws@2.1.0.yaml>**

```yaml
metadata:
  name: architecture-aws
  version: 2.1.0
  domain: architecture
rules:
  structural:
    architecture_layer_row: |
      | AWS Services | Cloud Native Services | Platform Team |
      |---------------|------------------------|--------------|
      | Lambda, ECS, RDS | Managed by Platform | platform@company.com |
```

**<process-gitflow-enterprise@1.4.0.yaml>**

```yaml
metadata:
  name: process-gitflow-enterprise
  version: 1.4.0
  domain: process
rules:
  material:
    process:
      branching_model: trunk-based-with-release-branches
      minimum_reviewers: 2
      required_status_checks:
        - unit-tests
        - security-scan
        - license-check
  structural:
    process_checklist_table: |
      | Phase        | Mandatory Artifacts         | Owner          |
      |--------------|-----------------------------|----------------|
      | Release      | Changelog, Rollout Plan     | Release Manager |
```

**<security-strict@2.0.0.yaml>** (auto-moved to last position)

```yaml
metadata:
  name: security-strict
  version: 2.0.0
  domain: security
rules:
  material:
    stack:
      banned_libraries:
        - pickle
        - telnetlib
        - yaml.load  # unsafe loader
```

### 7. Security & Veto Model – Unchanged, Works Across All Domains

1. Normal merge in manifest order  
2. `governance.custom.yaml` merged last  
3. Any fragment with `metadata.domain: security` OR name starting `security-` is **force-moved to the very end** (after custom overlay)  
4. Post-merge veto pass removes anything present in `banned_libraries` (or future banned equivalents in other domains)

### 8. CLI – No Changes Required

```bash
codex init
codex add architecture-aws stack-python process-gitflow-enterprise security-strict
codex weave     # → generates all four .codex/* files in one pass
```

### 9. Delivery Impact of Adding Process Domain

| Area                | Impact | Mitigation |
|---------------------|--------|-----------|
| LoC increase        | ~80–120 additional lines | Negligible |
| Schema complexity    | Moderate | Already handled with domain tag |
| Documentation templates| Need three extra base markdown files in catalog/base/ | One-time effort |
| Testing surface     | +25 % | Still well within 8-week window |

### 10. Updated Success Criteria (v1.1)

- 3+ product teams using all four generated artifacts in CI/CD  
- Process owners can add a new mandatory check in <2 h and see it appear instantly in every repo’s `process.md`  
- Architecture review board can publish a new layer row and see it appear in every service’s `architecture.md`  
- Security bans continue to be non-overridable

**Result:** Zero additional architectural complexity, one extra domain fully supported “for free” by the existing engine.

Ready for immediate development – the four-domain model is the correct production shape from day one.
