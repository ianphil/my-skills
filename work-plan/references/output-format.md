# Work Plan Output Format

Detailed templates for generating work plan output sections.

---

## 1. Current Status Section

```markdown
## Current Status

- **Feature**: {Feature name from spec.md or tasks.md header}
- **Branch**: {current-branch} {✓ matches | ⚠️ mismatch: should be feature/{feature-id}}
- **Progress**: {completed}/{total} tasks ({percentage}%)
- **Current Phase**: {phase-name} ({status})
```

---

## 2. Phase Overview Table

```markdown
## Phase Overview

| Phase | Tasks | Status | Progress | Blocks |
|-------|-------|--------|----------|--------|
| Phase 1: Setup | T001-T009 | ✅ Complete | 9/9 (100%) | Phase 2 |
| Phase 2: Foundational | T010-T015 | 🔄 In Progress | 3/6 (50%) | Phases 3-6 |
| Phase 3: US1 | T016-T029 | ⏸️ Not Started | 0/14 (0%) | Phase 4 |
...

**Legend**:
- ✅ Complete - All tasks checked
- 🔄 In Progress - Some tasks checked
- ⏸️ Not Started - No tasks checked
- 🔒 Blocked - Dependencies incomplete
```

---

## 3. Recommended Execution Plan

For each incomplete phase:

```markdown
### Step {N}: Phase {X} - {Name} {emoji}

**Status**: {status} ({progress})
**Depends on**: {list prerequisite phases or "None"}
**Blocks**: {list dependent phases or "None"}

#### Manual Approach:
```bash
/implement "Phase {X}"
```
Best for: Interactive work, debugging, learning

#### Automated Approach:
```bash
/implement-agents "Phase {X}"
```
Best for: Single phase with agent orchestration

{If independent phases exist that can run in parallel:}
#### Parallel Approach (if Phase {Y} is also ready):
```bash
/implement-agents "Phase {X}" "Phase {Y}"
```
Best for: Maximum throughput when phases touch different files

#### Phase Goals:
{Phase description from tasks.md}

#### Key Tasks:
- T{XXX} {First significant task}
- T{XXY} {Second significant task}
- ... ({remaining} more tasks)

#### Checkpoint After Phase {X}:
- [ ] {Inferred deliverable from phase name/description}
- [ ] {Another deliverable}
{If exit spec test exists:}
- [ ] Spec tests pass (T{XXX})

{If has spec tests:}
**Spec Tests**:
- Entry (T{XXX}): Expect ALL FAIL ❌
- Exit (T{YYY}): Expect ALL PASS ✅

---
```

---

## 4. Parallel Execution Strategy

```markdown
## Parallel Execution Strategy

{Analyze phases for parallelization opportunities:}
{For each pair of incomplete phases, check:}
{  1. No dependency between them (neither blocks the other)}
{  2. Different files modified (check tasks.md for file paths)}

{If parallelization possible within single session:}
### Single-Session Parallel Execution

Independent phases can run simultaneously using multi-phase `/implement-agents`:

```bash
# Run Phase {X} and Phase {Y} in parallel (different files, no dependencies)
/implement-agents "Phase {X}" "Phase {Y}"
```

**Phase {X}** touches: {list files from tasks}
**Phase {Y}** touches: {list files from tasks}
**Overlap**: None ✓

{If 3+ phases can parallelize:}
```bash
# Run all independent phases together
/implement-agents "Phase {X}" "Phase {Y}" "Phase {Z}"
```

{Show wave structure based on dependencies:}
### Execution Waves

**Wave 1** (start immediately):
```bash
/implement-agents "Phase 1"
```

**Wave 2** (after Wave 1):
```bash
/implement-agents "Phase 3" "Phase 5"  # Independent, run together
```

**Wave 3** (after Wave 2):
```bash
/implement-agents "Phase 4" "Phase 6"  # Independent, run together
```

{If phases must be sequential:}
### Sequential Execution Required

Phases have dependencies or file conflicts. Run one at a time:
```bash
/implement-agents "Phase {X}"
# wait for completion
/implement-agents "Phase {Y}"
```

**Why sequential**: {Phase X and Y both modify src/controller/mcp/manager.rs}
```

---

## 5. Quick Commands Reference

```markdown
## Quick Commands Reference

| Command | Use Case |
|---------|----------|
| `/prime-feat {N}` | Load feature context |
| `/work-plan {N}` | View this plan |
| `/implement "Phase N"` | Manual implementation |
| `/implement "TXXX"` | Single task |
| `/implement "TXXX-TYYY"` | Task range |
| `/implement-agents "Phase N"` | Single phase with agents |
| `/implement-agents "Phase X" "Phase Y"` | **Parallel phases** (independent) |
| `/implement-agents "T001-T005" "T010-T015"` | **Parallel task ranges** |
```

---

## 6. Success Criteria

```markdown
## Success Criteria

Feature complete when:
- [ ] All {total} tasks checked in `{feature-path}/tasks.md`
- [ ] All spec tests pass: `python specs/tests/run_tests_claude.py specs/tests/{feature-id}.md`
- [ ] All unit tests pass: `make test`
- [ ] Linting passes: `make lint`
- [ ] Build succeeds: `make build`
```

---

## 7. Manual Testing Strategy

```markdown
## Manual Testing Strategy

{Analyze feature type and phase completion to provide targeted guidance}

{Detect if feature involves external integration (MCP, gRPC, network, Docker, etc.)}
{If pure internal refactoring, show: "No manual testing required - unit tests provide full coverage"}

{For features with external dependencies, categorize phases:}

### Phases Not Requiring Manual Testing
{List phases that are pure internal/foundation work}
- ✅ **Phase {N} ({name})**: {reason - e.g., "Internal APIs only - unit tests sufficient"}
- ✅ **Phase {M} ({name})**: {reason - e.g., "Dependencies/scaffolding only"}

### Phases With Optional Manual Testing
{List phases where manual testing adds confidence but isn't critical}
- 🟡 **Phase {N} ({name})**: {status emoji if incomplete: ⏸️ Not Started | 🔄 In Progress | ✅ Complete}
  - **What to test**: {brief description}
  - **Commands**:
    ```bash
    {actual commands to run}
    ```
  - **Why optional**: {explanation - e.g., "Config parsing well-covered by unit tests"}

### Phases Requiring Manual Testing ⭐
{List phases where manual testing is critical - usually integration/E2E}
- ⚠️ **Phase {N} ({name})**: {status emoji} **CRITICAL**
  - **What to test**: {description of what manual test validates}
  - **When to test**: {e.g., "After T{XXX} (all spec tests pass)"}
  - **Commands**:
    ```bash
    {step-by-step manual test commands}
    ```
  - **Why critical**: {explanation - e.g., "Validates real MCP server communication, credential flow, sandbox isolation"}
  - **Expected outcome**: {what success looks like}

{If all phases complete:}
### Final Manual Verification
Run the critical manual tests one more time before creating PR:
```bash
{consolidated manual test commands}
```

---

**Manual Testing Principle**:
- ⏭️ **Skip** for internal APIs and pure logic (unit tests catch issues)
- 🟡 **Optional** for config/parsing (adds confidence, not critical)
- ⚠️ **Required** for external integration and E2E flows (unit tests can't catch integration issues)
```

---

## 8. Next Action Templates

### On wrong branch or no tasks complete:
```markdown
**Recommended**: Prime and start Phase 1
```bash
git checkout feature/{feature-id}
/prime-feat {feature-number}
/implement-agents "Phase 1"
```
Why: Foundation setup (dependencies, scaffolding). Quick win.
```

### Current phase in progress:
```markdown
**Recommended**: Continue current phase
```bash
/implement "Phase {X}"
```
Current: {completed}/{total} tasks ({percentage}%) in Phase {X}
Remaining: {remaining} tasks
```

### Current phase blocked by dependencies:
```markdown
**Status**: Phase {X} blocked by incomplete dependencies
Next: Complete blocking phase first
```bash
/implement-agents "Phase {blocking-phase}"
```
This will unblock Phase {X}.
```

### Ready for next phase:
```markdown
**Recommended**: Start next phase
```bash
/implement-agents "Phase {next}"
```
Why: Previous phase complete ✓, dependencies satisfied.
```

### Multiple independent phases ready:
```markdown
**Recommended**: Run independent phases in parallel
```bash
/implement-agents "Phase {X}" "Phase {Y}"
```
Why: Both phases ready, no file conflicts, maximizes throughput.

Phase {X} files: {list}
Phase {Y} files: {list}
Overlap: None ✓
```

### All complete:
```markdown
**Status**: Feature complete! 🎉

Final verification:
```bash
python specs/tests/run_tests_claude.py specs/tests/{feature-id}.md
make test
make lint
```

Ready to create PR or move to next feature.
```
