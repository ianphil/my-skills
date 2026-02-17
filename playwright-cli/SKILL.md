---
name: playwright-cli
description: Browse the web using playwright-cli connected to your running Edge browser via the MCP Bridge extension. Use when the user asks to "open a webpage", "browse to", "take a screenshot", "read this page", "navigate to", "check this site", or needs to interact with web pages for research and exploration.
allowed-tools: Bash(playwright-cli:*), Bash(npx:@playwright/cli*)
---

# Browser Automation with playwright-cli (Extension Mode)

## Hard Rules

1. **NEVER launch a new browser.** Every `open` command MUST include `--extension --browser=msedge`.
2. **NEVER use MCP.** This skill uses the CLI only. The MCP Bridge extension is just the transport layer.
3. **ALWAYS load the extension token** from `~/.copilot/skills/.env` before the first playwright-cli command.
4. **Gitignore snapshots.** Before first use, check the repo's `.gitignore` for `.playwright-cli/`. If missing, append it and inform the user. The CLI writes snapshot files to this folder in the current working directory.

## Phase 0: Load Token and Config

Before running any playwright-cli command, load the extension token:

```powershell
# Load token from .env
$envFile = Join-Path $HOME ".copilot" "skills" ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), 'Process')
        }
    }
} else {
    Write-Error "Missing ~/.copilot/skills/.env with PLAYWRIGHT_MCP_EXTENSION_TOKEN"
}
```

Verify the token is set:

```powershell
if (-not $env:PLAYWRIGHT_MCP_EXTENSION_TOKEN) {
    Write-Error "PLAYWRIGHT_MCP_EXTENSION_TOKEN not set. Check ~/.copilot/skills/.env"
}
```

### Internal Sites Config

Load `playwright-cli/config.json` (gitignored) which maps internal site URLs to keywords. When the user's request matches keywords for a site, navigate there automatically.

```powershell
$configFile = Join-Path $HOME ".copilot" "skills" "playwright-cli" "config.json"
if (Test-Path $configFile) {
    $sites = (Get-Content $configFile -Raw | ConvertFrom-Json).sites
}
```

## Phase 1: Connect to Edge Browser

```bash
playwright-cli open --extension --browser=msedge
```

If `playwright-cli` is not found:

```bash
npx @playwright/cli@latest open --extension --browser=msedge
```

This connects to your running Edge browser via the MCP Bridge extension. It does NOT launch a new browser.

## Commands

### Navigation

```bash
playwright-cli goto <url>
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
```

### Reading Pages

```bash
playwright-cli snapshot                     # accessibility tree with element refs
playwright-cli snapshot --filename=page.yml # save to specific file
playwright-cli screenshot                   # capture visible page
playwright-cli screenshot --filename=f.png  # save with specific name
playwright-cli screenshot <ref>             # screenshot a specific element
```

### Interacting

```bash
playwright-cli click <ref>          # click an element by ref
playwright-cli type <text>          # type text into focused element
playwright-cli fill <ref> <text>    # fill a specific input
playwright-cli hover <ref>          # hover over element
playwright-cli select <ref> <val>   # select dropdown option
playwright-cli check <ref>          # check a checkbox
playwright-cli uncheck <ref>        # uncheck a checkbox
playwright-cli press <key>          # press a key (Enter, ArrowDown, etc.)
```

### Tabs

```bash
playwright-cli tab-list             # list all tabs
playwright-cli tab-new [url]        # open a new tab
playwright-cli tab-select <index>   # switch to tab by index
playwright-cli tab-close [index]    # close a tab
```

### JavaScript

```bash
playwright-cli eval "document.title"
playwright-cli eval "el => el.textContent" <ref>
```

### Session Management

```bash
playwright-cli list                 # list active sessions
playwright-cli close                # close the connection
playwright-cli close-all            # close all sessions
```

## Snapshots

After each command, playwright-cli returns a snapshot of the page state. Snapshots contain element refs (e.g., `e1`, `e5`, `e12`) that you use with `click`, `fill`, `hover`, etc.

```bash
> playwright-cli goto https://example.com
### Page
- Page URL: https://example.com/
- Page Title: Example Domain
### Snapshot
[Snapshot](.playwright-cli/page-2026-02-14T19-22-42-679Z.yml)
```

Use `playwright-cli snapshot` to take one on demand.

## Example: Research a Web Page

```bash
playwright-cli open --extension --browser=msedge
playwright-cli goto https://example.com/article
playwright-cli snapshot
# Read the snapshot to understand page structure
playwright-cli screenshot --filename=article.png
playwright-cli close
```

## Example: Fill a Form

```bash
playwright-cli open --extension --browser=msedge
playwright-cli goto https://example.com/form
playwright-cli snapshot
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "some text"
playwright-cli click e3
playwright-cli snapshot
playwright-cli close
```
