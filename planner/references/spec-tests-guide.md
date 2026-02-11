# Spec Tests Writing Guide

Detailed guidance for writing effective spec tests.

## How Spec Tests Work

The LLM judge **reads the target files** and evaluates whether the code satisfies each test. This means:
- Tests must be **verifiable by reading code**, not by executing it
- Assertions should reference **specific files** and **observable code structures**
- Tests verify what the code **demonstrates**, not internal method behavior

## Writing Good Intent Statements

Intent explains **WHY users/business care**, not technical details.

**Bad** (technical HOW):
> "LLMs need to chain tool calls correctly. Without parsing outputSchema from MCP servers, the system cannot expose this information."

**Good** (business WHY):
> "LLMs need to know tool output structure before calling tools. Without an output_schema field on McpToolDef, schema information from MCP servers cannot reach LLM clients."

## Writing Verifiable Assertions

Assertions must be things the LLM can verify by reading the target files.

**Bad** (execution-based, internal methods):
```
Given an MCP server provides a tool with outputSchema
When McpClient::list_tools() parses the tool definition
Then McpToolDef.output_schema contains the parsed schema
```

**Good** (code-verifiable, specific files):
```
Given the src/controller/mcp/client.rs file
When examining the McpToolDef struct
Then it has an output_schema field of type Option<serde_json::Value>
And the field can hold JSON Schema data from MCP servers
```

## Multi-Target Test Pattern

For specs with multiple target files, each test should specify which file it examines:

```
Given the src/controller/tools/web_search.rs file
When examining the metadata() implementation
Then return_type.schema contains a JSON Schema value
And the schema describes an object with a "results" array property
```

## What NOT to Test

- **Aspirational behavior** - "LLM writes correct code" can't be verified by reading source
- **Runtime behavior** - "returns X when called with Y" requires execution
- **User story outcomes** - "Agent developer can chain tools" is not code-verifiable
