# Writing Tests for Multiple Targets

When a spec file targets multiple files, each test must explicitly reference which target it validates. This prevents ambiguity and catches drift between targets.

## Explicit Target References

```markdown
---
target:
  - docs/API.md
  - src/api.py
  - src/api_test.py
---
# API Validation

## Error Handling

### Documents Error Codes

Users need to know what error codes the API returns. Without this, they
can't write proper error handling in their applications.

\`\`\`
Given the docs/API.md file
Then it documents error codes for:
  - 400 Bad Request (validation errors)
  - 401 Unauthorized (missing/invalid token)
  - 404 Not Found (resource doesn't exist)
Because users need this reference to handle errors correctly
\`\`\`

### Implementation Returns Documented Errors

The API must return the error codes that the docs promise. If implementation
drifts from docs, users get unexpected errors their code can't handle.

\`\`\`
Given the src/api.py file
Then it returns the same error codes documented in API.md:
  - 400 for validation failures
  - 401 for auth failures
  - 404 for missing resources
Because implementation must match documentation
\`\`\`

### Tests Cover Error Cases

Tests must verify error handling works. Without test coverage, regressions
can ship and break user applications.

\`\`\`
Given the src/api_test.py file
Then it has test cases for:
  - 400 response on invalid input
  - 401 response on bad auth
  - 404 response on missing resource
Because untested code is unverified code
\`\`\`
```

**Key principle:** Start each assertion with `Given the <target> file` so the judge knows exactly which file to evaluate. When behavior spans multiple targets (docs describe it, code implements it, tests verify it), write separate tests for each—this catches drift between them.

---

## Tests That Apply to Multiple Files

When the same requirement applies to multiple targets, list them together in the `Given` clause. The judge evaluates whether ALL listed files satisfy the assertion.

**Single file:**
```markdown
\`\`\`
Given the docs/API.md file
Then it documents the rate limit as 100 requests/minute
\`\`\`
```

**Multiple files (same requirement applies to both):**
```markdown
\`\`\`
Given docs/API.md and src/rate_limiter.py
Then both specify the rate limit as 100 requests/minute
Because documentation and implementation must agree
\`\`\`
```

**When to use multi-file Given:**
- Documentation and implementation must match
- Multiple implementations of the same interface
- Config files that must stay in sync
- Any case where drift between files would break users

**When to use separate tests:**
- Files have different roles (one documents, one implements, one tests)
- You need different assertions for each file
- Failures should pinpoint exactly which file is wrong
