---
name: daily-report
description: Generate a personalized daily briefing by querying Microsoft 365 for important emails from key contacts and today's calendar, reviewing local notes/todos from inbox folder, and listing active initiatives. Use when user asks for "daily report", "morning briefing", or "what's on my plate today".
---

# daily-report

Generate a personalized daily briefing from emails, calendar, local notes, and initiatives.

## Description

This skill generates a comprehensive daily report by:
1. Querying Microsoft 365 for important emails from key contacts and today's calendar
2. Reviewing local notes/todos from the inbox folder
3. Listing active initiatives

Use this skill when the user asks for their "daily report", "morning briefing", "what's on my plate today", or similar requests for a work day overview.

## Trigger Phrases

- "what's my daily report"
- "daily report"
- "morning briefing"
- "what do I have today"
- "give me my daily summary"

## Instructions

When the user requests their daily report, perform the following steps:

### Step 0: Load the WorkIQ Skill

**Explicitly invoke `skill(workiq)` before any Microsoft 365 queries.** All M365 data (emails, calendar) must be retrieved using the WorkIQ CLI via that skill. Do not use any MCP tools for M365 data.

### Step 1: Gather Important Emails

Using the `workiq` skill, run the following CLI command to query for recent important emails from key contacts:

```bash
workiq ask -q "What recent emails do I have from Kent Klinzman, Michael Roberson, Andrew Edwards, or Douglas Phillips in the last 24 hours? Include both inbox and CC'd emails."
```

Priority contacts:
- Kent Klinzman
- Michael Roberson
- Andrew Edwards
- Douglas Phillips

Focus on:
- Inbox folder
- Inbox - CC folder (emails where user is CC'd)

### Step 2: Get Today's Calendar

Using the `workiq` skill, run:

```bash
workiq ask -q "What meetings do I have scheduled for today?"
```

### Step 3: Gather Next Actions

Collect open next actions from the inbox and all active initiatives. Each `next-actions.md` file uses `## Open` / `## Done` sections with `- [ ]` (open) and `- [x]` (done) checkboxes.

1. Read `C:\src\notes\inbox\next-actions.md` for untriaged actions
2. List folders under `C:\src\notes\initiatives` to discover active initiatives
3. For each initiative folder, read its `next-actions.md` file
4. Extract only `- [ ]` (open) items — skip done items
5. Group open actions by source (inbox vs each initiative name)

Use parallel `view` calls to read all next-actions.md files at once for efficiency.

### Step 4: Review Inbox Notes

Use the `view` tool to list files in `C:\src\notes\inbox` (excluding `next-actions.md` which was already read in Step 3).

1. List the inbox folder: `view` with path `C:\src\notes\inbox`
2. For each markdown file (excluding next-actions.md and READ-THIS.md), read contents to identify action items or tasks
3. Summarize any key items not already captured in next-actions

### Step 5: Format the Daily Report

Present the information in a clear, scannable format:

```
## 📧 Priority Emails

### From [Contact Name]
- Subject: [subject]
- Summary: [brief summary of email content]

(Repeat for each email from priority contacts)

## 📅 Today's Calendar

| Time | Meeting | Duration |
|------|---------|----------|
| [time] | [meeting title] | [duration] |

(List all meetings chronologically)

## ✅ Next Actions

### Inbox
- [ ] [open action from inbox/next-actions.md]

### [Initiative Name]
- [ ] [open action from initiative/next-actions.md]

(List open actions grouped by source. Omit sections with no open actions.)

## 📝 Inbox Notes

- [Summary of any additional inbox notes not captured above]

## 🚀 Active Initiatives

- [Initiative folder name 1]
- [Initiative folder name 2]
- ...

(List all initiative folders - names only)

## 🎯 Key Action Items

- [Any urgent or time-sensitive items identified from emails, calendar, next-actions, or notes]
```

### Notes

- If no emails are found from priority contacts, mention that the inbox is clear from those contacts
- Highlight any urgent or time-sensitive items
- If calendar is empty, note that no meetings are scheduled for today
- For inbox notes, focus on extracting actionable items - skip general notes without todos
- For initiatives, only list folder names - do not dive into the contents
