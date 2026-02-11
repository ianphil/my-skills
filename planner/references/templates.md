# Feature Planning Templates

Templates for each planning artifact. Use these as starting points and adapt as needed.

---

## Phase 1: Analysis (`analysis.md`)

**Goal**: Understand the problem space, existing code, and patterns.

Create `backlog/plans/{NNN}-{slug}/analysis.md`:

```markdown
# {Feature} Analysis

## Executive Summary

| Pattern | Integration Point |
|---------|-------------------|
| Pattern 1 | Where it fits |

## Architecture Comparison

### Current Architecture
[Diagram/description of existing system]

### Target Architecture
[Diagram/description of desired state]

## Pattern Mapping

### 1. {Pattern Name}

**Current Implementation:**
[Code/description from existing codebase]

**Target Evolution:**
[How it maps to the new implementation]

## What Exists vs What's Needed

### Currently Built
| Component | Status | Notes |
|-----------|--------|-------|
| Component A | ✅ | Description |

### Needed
| Component | Status | Source |
|-----------|--------|--------|
| Component X | ❌ | Where to get pattern |

## Key Insights

### What Works Well
1. Insight from analysis

### Gaps/Limitations
| Limitation | Solution |
|------------|----------|
| Gap 1 | How to solve |
```

---

## Phase 2: Specification (`spec.md`)

**Goal**: Define requirements from user perspectives.

Create `backlog/plans/{NNN}-{slug}/spec.md`:

```markdown
# Specification: {Feature Name}

## Overview

### Problem Statement
[What problem does this solve? What happens without it?]

### Solution Summary
[One paragraph describing the solution]

### Business Value
| Benefit | Impact |
|---------|--------|
| Benefit 1 | Impact description |

## User Stories

### {Persona 1}
**As a {role}**, I want to {action}, so that {benefit}.

**Acceptance Criteria:**
- Criterion 1
- Criterion 2

## Functional Requirements

### FR-1: {Capability}
| Requirement | Description |
|-------------|-------------|
| FR-1.1 | Description |
| FR-1.2 | Description |

## Non-Functional Requirements

### Performance
| Requirement | Target |
|-------------|--------|
| Metric | Value |

### Security
| Requirement | Target |
|-------------|--------|
| Metric | Value |

## Scope

### In Scope
- Item 1

### Out of Scope
- Item 1 (reason)

### Future Considerations
- Enhancement 1

## Success Criteria
| Metric | Target | Measurement |
|--------|--------|-------------|
| Metric | Value | How measured |

## Assumptions
1. Assumption 1

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Risk 1 | Medium | High | Strategy |

## Glossary
| Term | Definition |
|------|------------|
| Term | Meaning |
```

---

## Phase 3: Research (`research.md`)

**Goal**: Validate design against external specifications, APIs, or standards.

Create `backlog/plans/{NNN}-{slug}/research.md`:

```markdown
# {Feature} Conformance Research

**Date**: {YYYY-MM-DD}
**Spec Version Reviewed**: [{Version}]({URL})
**Plan Version**: plan.md

## Summary
[Overall conformance assessment]

## Conformance Analysis

### 1. {Aspect}
| Aspect | Plan | Spec | Status |
|--------|------|------|--------|
| Detail | What plan says | What spec says | CONFORMANT/UPDATE NEEDED |

**Recommendation**: [Action if needed]

## New Features in Spec (Not in Plan)
[Features in spec not addressed - OK for MVP or need attention?]

## Recommendations

### Critical Updates
1. Update 1 - why

### Minor Updates
2. Update 2 - why

### Future Enhancements
3. Enhancement - why

## Sources
- [Source 1](url)

## Conclusion
[Summary of conformance and actions needed]
```

---

## Phase 4a: Implementation Plan (`plan.md`)

Create `backlog/plans/{NNN}-{slug}/plan.md`:

```markdown
# Plan: {Feature Name}

## Summary
[One paragraph overview]

## Architecture
```
[ASCII diagram showing components and data flow]
```

## Detailed Architecture
[More detailed diagram with component interactions]

### Component Responsibilities
| Component | Role | Integrates With |
|-----------|------|-----------------|
| Component | What it does | Other components |

### Data Flow: {Scenario}
```
[Sequence diagram for key flow]
```

## File Structure
```
src/
├── new-module/
│   ├── mod.rs
│   └── component.rs
├── existing.rs  # MODIFY: change description
```

## Critical: {Key Challenge}
**Problem**: [What's tricky]
**Solution**: [How to solve it]

## Implementation Phases
[Brief overview - details in tasks.md]

## Key Design Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Decision | What | Why |

## Configuration Example
[Example config file if applicable]

## Files to Modify
| File | Change |
|------|--------|
| path | Description |

## New Files
| File | Purpose |
|------|---------|
| path | Description |

## Verification
1. Test command
2. Integration test

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Risk | Strategy |

## Limitations (MVP)
1. Limitation and why acceptable

## References
- [Reference](url)
```

---

## Phase 4b: Data Model (`data-model.md`)

Create `backlog/plans/{NNN}-{slug}/data-model.md`:

```markdown
# Data Model: {Feature}

## Entities

### {EntityName}
[Description]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| field | type | Yes/No | value | what it is |

**Relationships:**
- Owns/References N {OtherEntity}

**Invariants:**
- Rule 1

## State Transitions

### {Entity} Lifecycle
```
[State diagram]
```

| State | Description |
|-------|-------------|
| State | What it means |

## Data Flow

### {Scenario}
```
[Sequence diagram]
```

## Validation Summary
| Entity | Rule | Error |
|--------|------|-------|
| Entity | Validation | Error type |
```

---

## Phase 4c: Contracts (`contracts/`)

Create `backlog/plans/{NNN}-{slug}/contracts/README.md`:

```markdown
# {Feature} Contracts

Interface definitions for {feature}.

## Contract Documents

| Contract | Purpose |
|----------|---------|
| [{interface}.md]({interface}.md) | Description |

## Contract Principles
- Principle 1
```

Create individual contract files as needed (e.g., `grpc-api.md`, `config.schema.json`).

---

## Phase 5a: Spec Tests (`specs/tests/{NNN}-{slug}.md`)

**Goal**: Intent-based acceptance tests evaluated by LLM-as-judge.

```markdown
---
target:
  - src/path/to/file1.rs
  - src/path/to/file2.rs
---

# {Feature} Spec Tests

Brief description of what these tests validate.

## {Requirement Group}

### {Test Name}

{Intent: WHY users/business care. What breaks if this doesn't work?}

```
Given the {specific file path}
When examining {struct/function/impl}
Then {observable code property}
And {additional verifiable detail}
```
```

### Spec Test Principles

| Principle | Do | Don't |
|-----------|-----|-------|
| Intent | Explain WHY users care | Describe technical implementation |
| Assertions | Reference specific files | Describe runtime behavior |
| Scope | Test observable code structure | Test method return values |
| Targets | Only include files tests examine | List every related file |

---

## Phase 5b: Task Breakdown (`tasks.md`)

Create `backlog/plans/{NNN}-{slug}/tasks.md`:

```markdown
# {Feature} Tasks (TDD)

## TDD Approach

All implementation follows strict Red-Green-Refactor:
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Clean up while keeping tests green

### Two Test Layers
| Layer | Purpose | When to Run |
|-------|---------|-------------|
| **Unit Tests** | Implementation TDD (Red-Green-Refactor) | During implementation |
| **Spec Tests** | Intent-based acceptance validation | After all phases complete |

## User Story Mapping
| Story | spec.md Reference | Spec Tests |
|-------|-------------------|------------|
| US1 | Section reference | Test names |

## Dependencies
```
Phase 1 ──► Phase 2 ──► Phase 3
                  └──► Phase 4
```

## Phase 1: {Name}

### {Category}
- [ ] T001 [TEST] Write test for {functionality}
- [ ] T002 [IMPL] Implement {functionality}

## Phase 2: {Name}

### {Category}
- [ ] T003 [TEST] Write test for {functionality}
- [ ] T004 [IMPL] Implement {functionality}

## Task Summary
| Phase | Tasks | [TEST] | [IMPL] |
|-------|-------|--------|--------|
| Phase 1 | T001-T002 | X | Y |
| Phase 2 | T003-T004 | X | Y |
| **Total** | **N** | **X** | **Y** |

## Final Validation

After all implementation phases are complete:

- [ ] `make check` passes
- [ ] `make test` passes
- [ ] Run spec tests with `/spec-tests` skill using `specs/tests/{NNN}-{slug}.md`
- [ ] All spec tests pass → feature complete
```
