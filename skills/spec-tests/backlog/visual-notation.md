# Visual and Domain-Specific Notation in Code Blocks

## Problem

Spec-test code blocks are typically prose-style Given/When/Then statements.
For domains with spatial, structural, or visual relationships (UI layouts,
data pipelines, state machines, network topologies), prose descriptions are
verbose and harder to reason about than visual representations.

## Inspiration

Uncle Bob's empire-2025 uses ASCII map literals directly in test files:

```
GIVEN game map
  Sd
  ~~
```

You can *see* the submarine next to the destroyer. Spatial relationships are
immediately obvious. The parser understands the visual notation and translates
it into structured data.

## Proposed Solution

Encourage and document the use of visual/diagrammatic notation in spec-test
code blocks. The LLM judge can interpret these natively since it understands
ASCII art, diagrams, and structured visual formats.

### Examples by Domain

**UI Layout:**
```markdown
### Sidebar Collapses on Mobile

Users on small screens need maximum content area. The sidebar must collapse
to an icon strip below 768px viewport width.

\`\`\`
Desktop (>768px):        Mobile (<768px):
┌──────┬──────────┐     ┌──┬───────────┐
│ Side │ Content  │     │::│ Content   │
│ bar  │          │  →  │::│           │
│      │          │     │::│           │
└──────┴──────────┘     └──┴───────────┘
\`\`\`
```

**State Machine:**
```markdown
### Order Transitions

Orders must follow the defined lifecycle. Skipping states causes
fulfillment errors and incorrect inventory counts.

\`\`\`
[pending] → [confirmed] → [shipped] → [delivered]
    ↓            ↓
[cancelled]  [cancelled]

- No transition from shipped to cancelled
- No transition from delivered to any state
\`\`\`
```

**Data Pipeline:**
```markdown
### ETL Stages Execute in Order

Downstream stages depend on upstream output. Running out of order
produces corrupt data that silently propagates to dashboards.

\`\`\`
[extract] → [validate] → [transform] → [load]
   CSV         schema       normalize     warehouse
               check        deduplicate
\`\`\`
```

## Value

- More expressive tests for spatial/structural/visual domains
- LLM judge interprets visual notation naturally
- Reduces verbose prose for relationships that are better shown than described
- Aligns with how developers actually think about these domains
