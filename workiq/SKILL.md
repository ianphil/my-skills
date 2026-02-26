---
name: workiq
description: This skill should be used when the user asks to "install WorkIQ", "set up WorkIQ", "query my emails with AI", "connect AI to Microsoft 365", "query my meetings or documents", "use workiq ask", or wants to use natural language to search Microsoft 365 data (emails, meetings, Teams messages, documents, people) from an AI assistant.
---

# Microsoft Work IQ

Microsoft Work IQ is a CLI that connects AI assistants to Microsoft 365 Copilot data. Use it to query emails, meetings, documents, Teams messages, and people information using natural language—directly from a terminal or from within GitHub Copilot CLI.

> **Note:** Work IQ is currently in public preview. Features and APIs may change.

## Prerequisites

- Node.js installed
- Microsoft 365 subscription with a Copilot license
- Administrative consent for the Work IQ application in your Microsoft Entra tenant

## Admin Consent

Work IQ requires permissions that need administrative consent in your Entra tenant.

- If you are a tenant admin: Grant consent via the Azure portal or Microsoft Entra admin center
- If you are not an admin: Contact your organization administrator to grant consent

Reference: [User and admin consent overview](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview#admin-consent)

## Installation

### Via GitHub Copilot CLI (recommended)

```
/plugin marketplace add github/copilot-plugins
/plugin install workiq@copilot-plugins
```

Restart Copilot CLI, then query M365 data directly in conversation.

### Global install via npm

```bash
npm install -g @microsoft/workiq
```

## First-Time Setup

Accept the EULA before first use:

```bash
workiq accept-eula
```

## Commands

```bash
workiq accept-eula          # Accept the EULA (required once)
workiq ask                  # Interactive mode (multi-turn conversation)
workiq ask -q "..."         # Single question
workiq version              # Show version info
```

### Global options

| Option | Description | Default |
|---|---|---|
| `-t, --tenant-id <id>` | Microsoft Entra tenant ID | `common` |
| `--version` | Show version | |
| `-?, -h, --help` | Help | |

### `workiq ask` options

| Option | Description |
|---|---|
| `-q, --question <question>` | The question to ask |

## Platform Support

- Windows (x64 and ARM64)
- Linux (x64 and ARM64)
- macOS (x64 and ARM64)
- Windows Subsystem for Linux (WSL) with browser support

## What Data Can Be Queried

| Data Type | Example Query |
|---|---|
| Emails | "What did John say about the proposal?" |
| Meetings | "What's on my calendar tomorrow?" |
| Documents | "Find my recent PowerPoint presentations" |
| Teams messages | "Summarize today's messages in the Engineering channel" |
| People | "Who is working on Project Alpha?" |

## Example Queries

### Emails
```bash
workiq ask -q "What did John say about the proposal?"
workiq ask -q "Summarize emails from Sarah about the budget"
workiq ask -q "Find unread emails about Q4 planning"
```

### Meetings / Calendar
```bash
workiq ask -q "What's on my calendar tomorrow?"
workiq ask -q "What was discussed in the standup this morning?"
workiq ask -q "What are my upcoming meetings this week?"
```

### Documents
```bash
workiq ask -q "Find my recent PowerPoint presentations"
workiq ask -q "Find documents I worked on yesterday"
workiq ask -q "Summarize the specification document for the user portal"
```

### Teams Messages
```bash
workiq ask -q "Summarize today's messages in the Engineering channel"
workiq ask -q "What did the team decide about the API design in Teams?"
```

### People
```bash
workiq ask -q "Who is working on Project Alpha?"
workiq ask -q "Who are my manager's direct reports?"
```

## Key Workflows

### Finding project context while coding

To retrieve meeting/email context for a feature under development:

```bash
workiq ask -q "What requirements did Sarah share about the customer portal authentication feature?"
```

Work IQ returns meeting notes, emails, shared documents, and team decisions to give you context before writing code.

### Starting feature implementation from a spec document

To summarize a SharePoint specification before coding:

```bash
workiq ask -q "Summarize the key requirements and features outlined in the specification document for the user portal testing sandbox."
```

### Analyzing client feedback from meeting notes

To extract and triage issues raised in a Teams meeting, use interactive mode:

```bash
workiq ask
# > What were the specific issues raised by Alex in yesterday's meeting with Contoso?
# > Were any of these issues flagged as blocking the rollout?
```

## Query Tips

When calling `workiq ask -q` from other skills or scripts, append these instructions to your query for tighter output:

- **For concise responses:** Add `"Be concise. Bullet points only. No follow-up offers."` at the end of your query. WorkIQ's default responses are conversational and verbose — this suffix reduces output by ~60%.
- **For time-scoped queries:** Use explicit dates (`"messages sent since 2026-02-25"`) rather than relative phrases (`"last 24 hours"`). Some Teams thread types don't reliably support relative time filtering.
- **For structured extraction:** Ask for specific fields: `"List sender, subject, and action needed"` produces cleaner output than open-ended `"Summarize my emails"`.

## Security and Privacy

Work IQ inherits Microsoft 365 Copilot's data protections:

- Accesses only data the authenticated user already has permission to view
- Does not store Microsoft 365 data—retrieves on-demand only
- Follows organizational security policies
- Enterprise admins have visibility and control over usage

## Resources

- [Microsoft Work IQ GitHub repo](https://github.com/microsoft/work-iq-mcp)
- [User and admin consent overview](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview)
- [WorkIQ overview on Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/workiq-overview)
