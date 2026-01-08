# Assertion Syntax Reference

This document provides detailed syntax for assertions in spec tests.

## Value Assertions

```py
expression  # expect: <value>
```

The line before `# expect:` must be an **evaluable expression**, not a statement.

```py
# Setup lines run first
result = calculate(10)
# This line is evaluated and compared
result.value  # expect: 42
```

## Error Assertions

```py
statement  # error: [code]
statement  # error: "message substring"
statement  # error: [code] "message substring"
```

## Matchers

For non-exact comparisons:

```py
pi_value()  # expect: approx(3.14159, tol=0.0001)
output      # expect: contains("success")
text        # expect: matches(/^Error: \d+/)
```

## CLI/Shell Tests

```sh
mycommand --bad-flag
# exit: 1
# stderr: contains("[invalid-flag]")
```

## Language-Specific Assertion Formats

### Python
- Code blocks: ` ```py ` or ` ```python `
- Assertions: `# expect:`, `# error:`

### JavaScript/TypeScript
- Code blocks: ` ```js `, ` ```javascript `, ` ```ts `, ` ```typescript `
- Assertions: `// expect:`, `// error:`, `// throws:`

### Bash/Shell
- Code blocks: ` ```sh ` or ` ```bash `
- Assertions: `# exit:`, `# stdout:`, `# stderr:`

### PowerShell
- Code blocks: ` ```ps1 `, ` ```powershell `, ` ```bash `, or ` ```sh `
- Assertions: `# exit:`, `# stdout:`, `# stderr:`, `# throws:`, `# expect:`
- The PowerShell runner supports both PowerShell and Bash code blocks
- The `# expect:` assertion compares stdout to an expected value:

```bash
echo "hello"
# expect: hello
```

```bash
# Check exit code pattern
mycommand --flag
echo $?
# expect: 0
```

```bash
# Contains matcher
echo "success: operation completed"
# expect: contains("success")
```

### Rust
- Code blocks: ` ```rs ` or ` ```rust `
- Assertions: `// expect:`, `// error:`, `// compiles`, `// compile_fails:`

### C#
- Code blocks: ` ```cs ` or ` ```csharp `
- Assertions: `// expect:`, `// error:`
