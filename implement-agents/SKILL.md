---
name: implement-agents
description: This skill should be used when the user asks to "implement in parallel", "run phases concurrently", "parallel implement", "implement-agents phase X phase Y", or wants to orchestrate multiple agents running /implement simultaneously.
---

# Implement with Agents

Orchestrate multiple agents to run `/implement` in parallel using isolated git worktrees.

This skill is an orchestration layer only. It must preserve fidelity to `/implement` by assigning work, preparing isolated execution environments, launching subagents, and reconciling results afterward. The subagents remain responsible for actually executing `/implement`.

## User Input

ARGUMENTS = $ARGUMENTS

Accept one or more phases, task IDs, or task ranges. Examples:

```bash
# Single (runs one agent)
/implement-agents "Phase 3"
/implement-agents "T011-T014"

# Multiple (runs parallel agents)
/implement-agents "Phase 3" "Phase 5"
/implement-agents "T011-T014" "T018-T023"
```

## Definitions

**Work unit**: one independently assigned chunk of implementation work dispatched to exactly one subagent.

Valid work units:
- A phase, such as `Phase 3`
- A single task, such as `T011`
- A task range, such as `T011-T014`

Each parsed argument becomes one work unit.

## Fidelity Rule

Each subagent must run `/implement` for its assigned work unit.

Do not duplicate, replace, or partially inline the behavior of `/implement` in this skill. In particular, this skill must not redefine task execution rules, TDD behavior, progress logging, or commit policy that belongs in `/implement`.

This skill owns:
- Parsing work units
- Conflict detection
- Worktree and branch setup
- Parallel subagent orchestration
- Result collection and reconciliation

`/implement` owns:
- Task execution
- Test and implementation workflow
- Progress logging
- Commit behavior
- Task completion behavior

## Environment Assumptions

This skill is intended for Copilot-hosted environments such as Copilot in VS Code or Copilot CLI.

Before parallelizing mutating work, verify the environment can do all of the following reliably:
- Run non-interactive `git worktree` commands
- Create and check out dedicated branches per work unit
- Launch each subagent with its assigned worktree as the working directory
- Keep each subagent confined to that worktree during execution

If the host environment cannot guarantee per-subagent working directory isolation, do not run parallel mutating work in a shared checkout. Fall back to one of these options:
- Run `/implement` sequentially for each work unit
- Use an external wrapper that enters each worktree before invoking `/implement`

## Execution Flow

```
/implement-agents "Phase 3" "Phase 5"
              │
              ▼
    ┌─────────────────────┐
    │  Parse Arguments    │
    │  → ["Phase 3",      │
    │     "Phase 5"]      │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Create Worktrees   │
    │  + Branches         │
    └─────────┬───────────┘
          │
          ▼
    ┌─────────────────────┐
    │  Spawn Agents       │
    │  in Worktrees       │
    └─────────┬───────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌─────────┐      ┌─────────┐
│ Agent A │      │ Agent B │
│         │      │         │
│ Runs:   │      │ Runs:   │
│/implement│      │/implement│
│"Phase 3"│      │"Phase 5"│
│in wt A  │      │in wt B  │
└────┬────┘      └────┬────┘
     │                 │
     └────────┬────────┘
              ▼
    ┌─────────────────────┐
    │ Reconcile Branches  │
    │ + Report            │
    └─────────────────────┘
```

## Step 1: Parse Arguments

Parse ARGUMENTS into a list of work units:

```
Input: "Phase 3" "Phase 5"
Output: ["Phase 3", "Phase 5"]

Input: "Phase 3" "T018-T023"
Output: ["Phase 3", "T018-T023"]

Input: "Phase 3"
Output: ["Phase 3"]
```

## Step 2: Preflight Conflict Detection

Before creating worktrees, check whether the requested work units are plausibly independent.

Examples of overlap that should block parallel execution unless the user explicitly approves:
- Two phases that both modify the same source files
- Two work units that both require edits to the same shared module
- Multiple work units expected to update the same planning file in incompatible ways
- Dependency order where one work unit requires another to finish first

If there is meaningful overlap, warn the user and recommend sequential execution.

## Step 3: Create One Worktree Per Work Unit

For each work unit:

1. Derive a deterministic branch name tied to the current feature and work unit
2. Create a dedicated worktree for that branch
3. Record the mapping:
   - Work unit
   - Worktree path
   - Branch name

Use non-interactive git commands only.

Example naming pattern:

```text
Feature branch: feature/001-mcp-integration

Work unit: Phase 3
Branch: feature/001-mcp-integration-phase-3
Worktree: .worktrees/001-mcp-integration-phase-3/

Work unit: T018-T023
Branch: feature/001-mcp-integration-t018-t023
Worktree: .worktrees/001-mcp-integration-t018-t023/
```

The exact naming may vary, but it should be stable and traceable.

## Step 4: Spawn Parallel Agents

For each work unit, spawn a background subagent assigned to its dedicated worktree.

**CRITICAL**: The subagent must run `/implement` within its assigned worktree. Do not tell the subagent to manually reproduce `/implement`.

```
For each WORK_UNIT in parsed arguments:

  Task(
    subagent_type: "general-purpose",
    description: "Implement {WORK_UNIT}",
    prompt: """
You are assigned:
- Work unit: {WORK_UNIT}
- Worktree: {WORKTREE_PATH}
- Branch: {BRANCH_NAME}

Change to the assigned worktree and run /implement for {WORK_UNIT}.

Use the Skill tool exactly as follows:
  skill: "implement"
  args: "{WORK_UNIT}"

Do not substitute or inline /implement.

Report back:
- Whether /implement completed successfully
- Commit(s) created, if any
- Files changed
- Any blockers or failures
""",
    run_in_background: true
  )
```

**IMPORTANT**: Spawn ALL agents in a **single message** with multiple Task tool calls to ensure true parallelism.

## Step 5: Monitor Progress

Check agent progress periodically:

```bash
# Read output files returned by Task tool
tail -100 {output_file_A}
tail -100 {output_file_B}
```

Or use `TaskOutput` with `block: false` for non-blocking status checks.

## Step 6: Wait for Completion

Wait for all agents to finish:

```
TaskOutput(task_id: agent_A_id, block: true, timeout: 600000)
TaskOutput(task_id: agent_B_id, block: true, timeout: 600000)
```

## Step 7: Reconcile Resulting Branches

After all subagents complete, reconcile the resulting branches back into the main feature branch.

Recommended approach:

1. Review each subagent result
2. Merge or cherry-pick work units one at a time in a deliberate order
3. Resolve conflicts centrally in the orchestrator flow
4. Update any shared planning files that should be reconciled centrally rather than by each subagent

Prefer central reconciliation over asking subagents to merge their own branches.

If multiple work units modified the same shared planning artifacts, reconcile those explicitly after code integration.

## Step 8: Report Results

After all agents complete, summarize what happened:

```
✅ Phase 3: Complete (T011-T014)
✅ Phase 5: Complete (T018-T023)
```

Include, when available:
- Work unit status
- Assigned branch
- Assigned worktree
- Reconciliation result
- Any remaining conflicts or follow-up required

## Error Handling

If an agent fails:

1. **Report which agent failed** and what work unit it was assigned
2. **Report the worktree and branch** assigned to that agent
3. **Show the error** from the agent's output
4. **Preserve the worktree** for inspection unless the user asks for cleanup
5. **Check tasks.md** or equivalent planning artifacts for partial progress only if `/implement` may have updated them before failing
6. **Ask user** how to proceed:
   - Retry failed agent
   - Continue with remaining agents
   - Abort and investigate

If `/implement` could not be run in the assigned worktree because the environment does not support correct cwd isolation, stop and report that as an orchestration failure. Do not silently replace `/implement` with manual implementation.

## Shared File Guidance

Even with separate worktrees, some files are natural merge hotspots.

Common examples:
- `tasks.md`
- Progress logs
- Generated manifests or lockfiles
- Shared integration modules

When possible:
- Let subagents focus on code and tests for their work unit
- Reconcile shared planning artifacts centrally after branch integration
- Avoid fine-grained parallelization that guarantees merge conflicts in shared files

## Conflict Detection Examples

Before spawning agents, check for potential conflicts:

```
Phase 3 files: proto/aegis.proto, src/grpc/service.rs
Phase 5 files: src/controller/tools/*.rs

Overlap: None → Safe to parallelize
```

If files overlap, warn the user:

```
⚠️ Phase 3 and Phase 4 both modify src/controller/mcp/manager.rs

Options:
1. Run sequentially (Phase 3 first, then Phase 4)
2. Proceed anyway (may cause merge conflicts)
```

## When to Use

**Good for parallelization:**
- Independent phases touching different files
- Multiple task ranges in different modules
- Large features where throughput matters
- Work units that can be isolated cleanly into separate worktrees

**Run sequentially instead (`/implement` twice):**
- Phases with dependencies
- Tasks that modify the same files
- Work units that all need to update the same planning or generated files
- Environments that cannot guarantee per-agent worktree isolation
- When review between phases is needed

## Example Session

```
User: /implement-agents "Phase 3" "Phase 5"

Claude: Creating 2 worktrees and spawning 2 agents in parallel...
- Agent A: /implement "Phase 3" in .worktrees/001-mcp-integration-phase-3/
- Agent B: /implement "Phase 5" in .worktrees/001-mcp-integration-phase-5/

[Waits for completion]

[Reconciles branches]

✅ Phase 3: Complete
✅ Phase 5: Complete
```

## Notes

- Each successful subagent run should produce the same result as if the user had run `/implement` directly inside that worktree
- Each agent runs `/progress` via `/implement`, so the orchestrator should not duplicate that behavior unless recovering from a failed run
- If an agent fails, its output file and worktree show what went wrong
- Clean up worktrees only after reconciliation is complete or the user explicitly asks to discard them
