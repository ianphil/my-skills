# Ian's Skills Marketplace

A collection of reusable agent skills (Claude Code / Agent Skills standard).

## Available Skills

| Skill | Description |
|-------|-------------|
| **ollama-web-search** | Call Ollama's cloud `web_search` / `web_fetch` API, keeping the API key out of chat transcripts and tool-call logs |

## Repository Structure

```
my-skills/
├── ollama-web-search/
│   └── SKILL.md
└── scripts/
    └── Sync-Skills.ps1
```

Each skill lives in `<name>/SKILL.md` at the repo root, with optional `scripts/`
and `references/` subdirectories.

## License

MIT