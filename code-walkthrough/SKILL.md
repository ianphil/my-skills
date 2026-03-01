---
name: code-walkthrough
description: Generate structured, hallucination-proof code walkthroughs using Showboat. Use when the user asks to "walk me through this code", "explain this codebase", "create a walkthrough", "document how this works", "give me a tour of this repo", or wants a readable narrative document that explains code with real verified snippets. Also triggers on "showboat", "linear walkthrough", or "code documentation". Not for quick code questions — this produces a full markdown document.
---

# Code Walkthrough

Generate a structured, **linear** walkthrough of a codebase (or a single file) using [Showboat](https://github.com/simonw/showboat). The output is a markdown document meant to be read top-to-bottom in one sitting — a single narrative thread that builds understanding incrementally, not a reference manual you jump around in.

**What "linear" means:** The agent decides on a teaching sequence and the reader follows it from beginning to end. This is deliberately different from API docs (jump to what you need), READMEs (overview), code comments (scattered inline), or wiki pages (interlinked, no single path). A linear walkthrough has a beginning, middle, and end — like a guided tour where the guide chooses the route.

The walkthrough mixes narrative explanation with real code snippets extracted via shell commands — never from memory.

## Why Showboat

The agent writes `showboat exec demo.md bash "cat src/main.py | head -30"` instead of pasting code from its context window. The document contains *executed output*, not *recalled content*. This eliminates hallucination risk entirely — every snippet is ground truth from the filesystem.

Showboat also supports `showboat verify` to re-run all code blocks and diff against recorded output — making walkthroughs reproducible proof of work, not just documentation.

## Prerequisites

Showboat must be installed. Check with `showboat --version`. If missing:
```bash
uv tool install showboat
# or: pip install showboat
# or: go install github.com/simonw/showboat@latest
```

## Showboat Commands

Familiarize yourself with the full command set before starting:

| Command | Purpose |
|---------|---------|
| `showboat init <file> <title>` | Create a new document |
| `showboat note <file> [text]` | Append narrative/commentary (text or stdin) |
| `showboat exec <file> <lang> [code]` | Run code, capture command + output |
| `showboat image <file> <path>` | Copy image into document |
| `showboat pop <file>` | Remove the most recent entry (undo) |
| `showboat verify <file>` | Re-run all code blocks, diff against recorded output |
| `showboat extract <file>` | Emit commands that would recreate the document |

**Key details:**
- `exec` prints output to stdout AND appends to the document. React to errors — use `pop` to remove failed entries.
- `exec` supports multiple languages: `bash`, `python`, `python3`, etc. Use the appropriate lang for the snippet.
- `--workdir <dir>` sets the working directory for code execution (useful when the target code is in a different directory).
- Commands accept stdin when the text/code argument is omitted: `cat script.sh | showboat exec demo.md bash`

## Workflow

### 1. Scope the walkthrough

Determine what to cover:
- **Single file**: walk through one file in logical order (e.g., entry point, config, a complex module)
- **Multi-file / repo**: walk through the codebase in teaching order — entry point first, then data model, then business logic, then edge cases

Ask the user what they want covered if it's ambiguous. Default to the most useful scope — for a small repo, cover everything; for a large one, focus on the entry points and core logic.

### 2. Read and plan

Before writing anything, read the target code thoroughly:
- Traverse imports and dependencies to understand the call graph
- Identify the entry point(s)
- Note the key abstractions, data models, and design decisions
- Decide on a **teaching sequence** — the order a human would want to learn this, not the order files appear alphabetically

The teaching sequence matters. Build understanding incrementally — don't reference concepts before they're introduced.

### 3. Initialize the document

```bash
showboat init <output-path> "<Title> — Walkthrough"
```

Default output location: `docs/<name>-walkthrough.md` in the current repo. Create the `docs/` directory if it doesn't exist. The walkthrough is a repo artifact — it should live alongside the code it describes, not in a temp directory.

### 4. Build the walkthrough

Alternate between `showboat note` (narrative) and `showboat exec` (code) to build the document:

**For narrative sections:**
```bash
showboat note <file> "## Section Title

Explanation of what this section covers and why it matters."
```

**For code snippets — use shell commands to extract real code:**
```bash
showboat exec <file> bash "sed -n '10,25p' src/main.py"
```

Good extraction commands:
- `sed -n '10,25p' <file>` — line range (most common)
- `head -n 20 <file>` — first N lines
- `grep -A 5 'def main' <file>` — function signature + context
- `cat <file>` — whole file (only for short files)

Use sed, grep, cat, head, or whatever shell command best extracts the relevant snippet. The point is: **the code must come from the filesystem via a shell command, never pasted from your context window.** This is the core anti-hallucination mechanism — the document contains executed output, not recalled content.

For non-bash code (e.g., demonstrating a Python script), use the appropriate language:
```bash
showboat exec <file> python3 "print('Hello from the walkthrough')"
```

**After each code block, explain what it does:**
```bash
showboat note <file> "This function does X because Y. Notice the Z pattern — it connects to the W we saw earlier."
```

### 5. Maintain the rhythm

A good walkthrough alternates: context → code → explanation → context → code → explanation. Each code block should be preceded by *why we're looking at this* and followed by *what it means*.

Keep code blocks focused — 10-30 lines is ideal. Don't dump an entire 200-line file; extract the relevant section and explain it.

### 6. Close with perspective

End with a brief section summarizing the overall shape — how many files, what the architecture looks like at a glance, what's deliberate about the design. This gives the reader a mental model to hold onto.

### 7. Verify (optional)

If the user wants to confirm the walkthrough still matches the code:
```bash
showboat verify <output-path>
```

This re-executes every code block and diffs against the recorded output.

## Key Constraints

- **Never paste code from memory.** Every code snippet must come through `showboat exec` running a real shell command. This is the core anti-hallucination mechanism — as Simon Willison puts it, use "sed or grep or cat or whatever you need to include snippets of code you are talking about" so the document can't contain hallucinated or paraphrased code.
- **Teaching order, not file order.** Arrange sections so understanding builds incrementally.
- **Explain the why, not just the what.** "This function validates input" is weak. "This function validates input before it hits the database — without it, malformed requests would silently corrupt the session store" is useful.
- **Use `showboat pop`** if a command produces an error or unwanted output. Remove it and redo.
- **Use `showboat image`** when a screenshot or diagram would help explain the code (e.g., UI output, architecture diagrams).

## Example

Here's what the workflow looks like for a single-file walkthrough:

```bash
# Initialize
showboat init docs/api-walkthrough.md "API Server — Walkthrough"

# Intro
showboat note docs/api-walkthrough.md "server.py is the entry point. It does three things: configure the app, register routes, and start the server."

# Show the first section of code
showboat exec docs/api-walkthrough.md bash "sed -n '1,25p' src/server.py"

# Explain it
showboat note docs/api-walkthrough.md "The configuration phase loads environment variables and sets up the database connection pool."

# Show the next section
showboat exec docs/api-walkthrough.md bash "sed -n '27,45p' src/server.py"

# Explain it
showboat note docs/api-walkthrough.md "Two groups of routes: public (health check, auth) and protected (the actual API surface)."

# Verify everything still matches
showboat verify docs/api-walkthrough.md
```
