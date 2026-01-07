# Cookbook: Creating Tests for Porting Code

This cookbook describes how to use literate tests to port code from one language to another.
The tests become the **contract** that both implementations must satisfy.

## The Problem

You have working code in Language A (e.g., PowerShell) and need to port it to Language B (e.g., bash).
Without tests:
- You might miss edge cases the original handles
- You have no way to verify the port is complete
- Subtle behavioral differences go unnoticed

## The Solution

Create **two parallel test suites** that work together:

### Source Language Tests (e.g., PowerShell)
- Written first to capture the original behavior
- Serve as the **source of truth** for intent and requirements
- Help you understand what the original code does
- Use source language syntax (```ps1 or ```powershell code blocks)

### Target Language Tests (e.g., bash)
- Mirror the source tests with identical intent and assertions
- Use target language syntax (```bash code blocks)
- Validate that the ported implementation achieves the same outcomes
- These are what you'll run against your bash implementation

**Both test suites** capture the same layered requirements:
1. **Intent** — What outcomes should the code produce?
2. **Contracts** — What are the inputs/outputs of each function?
3. **Integration** — How do functions work together?
4. **Implementation** — What patterns does the code use?

The intent is **language-agnostic**, but the test syntax must match the implementation language being tested.

---

## Complete Porting Workflow

Here's the recommended sequence when porting from Language A (PowerShell) to Language B (bash):

1. **Set Up Test Directory Structure**
   - Create `spec-tests-{thing-you-are-porting}/` (e.g., `spec-tests-dev-setup/`)
   - Create language subdirectories: `powershell/` and `bash/`
   - Create shared `mocks/` directory

2. **Create Source Language Tests** (PowerShell tests with ```ps1 blocks)
   - Write tests in `spec-tests-{thing}/powershell/`
   - Capture the behavior of the original implementation
   - Establish the source of truth for intent
   - Validate against the original PowerShell script if possible

3. **Port Tests to Target Language** (Convert to bash tests with ```bash blocks)
   - Write mirrored tests in `spec-tests-{thing}/bash/`
   - Keep the same intent, assertions, and test structure
   - Use the assertion syntax reference for target language
   - Verify test count matches between both directories

4. **Set Up Test Runners**
   - Copy PowerShell runner: `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ps1" spec-tests-{thing}/powershell/`
   - Copy bash runner: `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.sh" spec-tests-{thing}/bash/`
   - Or use PowerShell runner in both (supports both languages)
   - Ensure both runners reference `../mocks/` for shared mocks

5. **Port the Implementation**
   - Write the bash implementation guided by the bash tests
   - Run bash tests frequently: `bash spec-tests-{thing}/bash/run_tests.sh`
   - Use test failures to guide implementation

6. **Validate the Port**
   - All bash tests should pass
   - Compare behavior with original
   - Verify external side effects match

**Why both test suites?**
- PowerShell tests validate your understanding of the original
- Bash tests validate your ported implementation
- Without both, you can't verify the port preserves behavior
- Same filenames in both directories make side-by-side comparison easy

---

## Phase 1: Understand the Original Code

Before writing any tests, analyze the source code to identify:

### Components
What are the major pieces? In a setup script, this might be:
- Authentication
- Resource provisioning
- Configuration management
- Error handling

### Functions
What functions exist and what do they do?
```
Set-DefaultEnvironment  →  Validates and normalizes environment name
Build-ProjectConfig     →  Creates configuration for each project
Set-UserSecrets         →  Configures .NET user secrets
Deploy-EV2Components    →  Deploys infrastructure via EV2
```

### External Dependencies
What external tools/APIs does the code call?
- Azure CLI (`az`)
- dotnet CLI (`dotnet user-secrets`)
- Dev tunnel CLI (`devtunnel`)

### Data Flow
How does data flow through the system?
```
EnvName → TopicName → ServiceBus
EnvName → CosmosEndpoint → UserSecrets
SubscriptionId → CustomerSubnetId → UserSecrets
```

### Extracting Intent from Undocumented Code

| Technique | How to Extract Intent | Example |
|-----------|----------------------|---------|
| **Side Effects** | What files/APIs/env vars/output? → That's what users need | `az servicebus create` → "Developer can publish to Service Bus" |
| **Name-Based** | Function/var names reveal purpose | `Set-DefaultEnvironment` → "Establish target env"<br>`$skipEv2` → "Allow skipping deployment" |
| **Error Messages** | Validation rules in exceptions | `"5-8 chars"` → Test at 4,5,8,9<br>`"no reserved words"` → Test dev/ppe/prod |
| **Dependencies** | Operation order shows what enables what | Auth → RG → ServiceBus → Topic → Secrets (each step feeds next) |
| **Conditionals** | Each `if` is a decision point | `if User-RP then Setup-DevTunnel` → Test both paths |

---

## Phase 2: Create Test Layers

| Layer | Purpose | Key Question | Example Test |
|-------|---------|--------------|--------------|
| **1. Component Intents** | What each component achieves | "After this runs, what can the user do?" | `## Buildout Intent`<br>`After Buildout: developer can connect to Service Bus, store secrets in Key Vault`<br>```bash [ -n "$namespace" ] # expect: 0``` |
| **2. Function Contracts** | Input/output per function | "Given X, what Y?" | `set_default_environment()`<br>Input: "IANPHIL" → Output: "ianphil"<br>Rejects: "mydevenv" (has reserved word "dev") |
| **3. Integration Flow** | Functions compose correctly | "When A→B→C, does data flow?" | User-RP in projects → setup_dev_tunnel=true<br>User-RP projects count → 2 (API + FunctionApp) |
| **4. Implementation Patterns** | Language-specific idioms | "How to do X in target language?" | Azure CLI: Extract subscription ID from JSON<br>File System: Path construction<br>Env Vars: Persist to .bashrc |

---

## Complete Test Class Reference

| Test Class | When to Create | What to Test | Example |
|------------|----------------|--------------|---------|
| **Core Logic** (`<script>.md`) | Always (starting point) | Validation rules, string manipulation, conditional logic, transformations | Env name 5-8 chars, reserved keywords, topic name construction |
| **Config Structure** (`components.md`) | Has configurable components | Priorities, flags, nested config, defaults | Buildout priority=1, User-RP has API+FunctionApp secrets |
| **Component Intents** (`component-intents.md`) | Has distinct modules | User outcomes, resources created, capabilities enabled | After Buildout: Service Bus accessible |
| **CLI Integration** (`azure-cli.md`, etc.) | Calls external tools (one file per CLI) | Command construction, output parsing, error detection, exit codes | Extract subscription from `az account show` |
| **File System** (`file-system.md`) | Reads/writes files or paths | Path construction, existence checks, pushd/popd, cross-platform | Constructs ServiceGroupRoot, validates paths |
| **Environment Vars** (`environment-variables.md`) | Uses env vars | Read, detect unset, persist to .bashrc, subshell inheritance | Reads SCALocalEnvName, constructs export |
| **Error Handling** (`error-handling.md`) | Always | Exit codes, error messages, prerequisite checks, error propagation | Returns 1 on failure, detects missing `az` |
| **Script Execution** (`script-execution.md`) | Calls other scripts | Path construction, argument passing, exit code capture, source vs exec | Passes env name to EV2 script |
| **User Interaction** (`user-interaction.md`) | Has interactive elements | Prompts, progress indicators, colored output, non-interactive mode | Accepts 'y', displays countdown, green checkmark |
| **Function Contracts** (`function-contracts.md`) | After identifying functions | Input/output, return values, side effects, error conditions | `set_default_environment()` normalizes to lowercase |
| **Integration Flow** (`integration-flow.md`) | After contracts defined | Data flow between functions, workflows, error propagation, idempotency | Env name → topic name → Service Bus |
| **Mocks** (`mocks/`) | Has external dependencies | Fake CLI implementations with env var controls | `mocks/az`, `mocks/dotnet`, `mocks/devtunnel` |

---

## Test Count Guidelines

A comprehensive test suite for a ~400 line script typically has:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| Core logic | 15-25 | Basic validation, transformations |
| Config structure | 20-30 | All components and their properties |
| Component intents | 25-35 | 3-5 outcomes per component |
| CLI integration (per CLI) | 10-15 | Commands, parsing, errors |
| File system | 10-15 | Paths, existence, directory ops |
| Environment variables | 10-15 | Read, write, persist, inherit |
| Error handling | 15-20 | Codes, messages, prerequisites |
| Script execution | 15-20 | Subprocesses, arguments, sourcing |
| User interaction | 15-20 | Prompts, output, non-interactive |
| Function contracts | 20-30 | I/O for each function |
| Integration flow | 15-25 | Multi-function workflows |
| **Total** | **170-250** | |

The exact count depends on script complexity, but aim for **comprehensive coverage** of each class.

---

## Phase 3: Create Mocks for External Dependencies

Create shared `spec-tests-{thing}/mocks/` directory with executable scripts that mimic CLI behavior. Both PowerShell and bash tests will reference these using `../mocks/`.

**CLI Mock Example** (spec-tests-dev-setup/mocks/az):
```bash
#!/bin/bash
cmd="$1"; shift
case "$cmd" in
    account) [[ "$1" == "show" ]] && echo '{"id": "12345", "user": {"name": "test@example.com"}}' ;;
    servicebus) [[ "$1 $2" == "topic create" ]] && echo '{"name": "topic-name", "status": "Active"}' ;;
    *) echo "Mock az: unknown command $cmd" >&2; exit 1 ;;
esac
```

**In tests, reference shared mocks:**
```bash
# In bash tests: spec-tests-{thing}/bash/*.md
export PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../mocks" && pwd):$PATH"
```

```powershell
# In PowerShell tests: spec-tests-{thing}/powershell/*.md
$env:PATH = "$(Resolve-Path ../mocks);$env:PATH"
```

**Control with env vars:**
```bash
# In mock: if [[ "${MOCK_VNET_EXISTS:-true}" == "true" ]]; then echo '{"name": "vnet"}'; fi
# In test: export MOCK_VNET_EXISTS=false
```

**Other mock types:**
- HTTP: `mocks/curl` with case on URL patterns
- Database: JSON fixtures in `mocks/fixtures/`, query with `jq`
- Filesystem: `mktemp -d` with expected structure in setup/teardown functions
- API responses: Store complex JSON in `mocks/responses/` and `cat` them

---

## Phase 4: Test File Organization

Organize tests by language with shared mocks:

```
spec-tests-dev-setup/          # Root: spec-tests-{thing-you-are-porting}
│
├── powershell/                # Source language tests (```ps1 blocks)
│   ├── run_tests.ps1          # PowerShell test runner
│   │
│   ├── # Layer 1: Intent (highest abstraction)
│   ├── component-intents.md   # What outcomes should be achieved
│   │
│   ├── # Layer 2: Contracts
│   ├── function-contracts.md  # Input/output per function
│   │
│   ├── # Layer 3: Integration
│   ├── integration-flow.md    # Multi-function workflows
│   │
│   ├── # Layer 4: Implementation patterns
│   ├── azure-cli-integration.md   # az command patterns
│   ├── dotnet-cli.md          # dotnet command patterns
│   ├── dev-tunnel.md          # devtunnel patterns
│   ├── file-system.md         # Path and file operations
│   ├── environment-variables.md   # Env var handling
│   ├── error-handling.md      # Exit codes and errors
│   ├── script-execution.md    # Subprocess and script calls
│   └── user-interaction.md    # Prompts and output
│
├── bash/                      # Target language tests (```bash blocks)
│   ├── run_tests.sh           # Bash test runner (or run_tests.ps1)
│   │
│   ├── # Same structure as powershell/ directory
│   ├── component-intents.md   # Mirrored tests with bash syntax
│   ├── function-contracts.md
│   ├── integration-flow.md
│   ├── azure-cli-integration.md
│   ├── dotnet-cli.md
│   ├── dev-tunnel.md
│   ├── file-system.md
│   ├── environment-variables.md
│   ├── error-handling.md
│   ├── script-execution.md
│   └── user-interaction.md
│
└── mocks/                     # Shared mock external tools
    ├── az                     # Both test suites reference ../mocks/
    ├── dotnet
    ├── devtunnel
    ├── fixtures/              # Shared test data
    └── responses/             # Shared API response fixtures
```

**Benefits:**
- Same filenames in both directories enable easy comparison: `diff powershell/function-contracts.md bash/function-contracts.md`
- Shared mocks reduce duplication
- Clear separation of source vs target language tests
- Scalable: add `python/`, `ruby/`, etc. for additional ports

---

## Phase 5: Port the Tests to Target Language

**CRITICAL:** Before porting the implementation, port the tests first. You need bash tests to validate your bash implementation.

See "Phase 5b: Porting Tests Between Languages" below for the complete process of converting PowerShell test syntax to bash test syntax while preserving intent.

---

## Phase 6: Write the Port

With **bash tests** in place (in `spec-tests-{thing}/bash/`), write the bash implementation:

### 1. Start with Function Stubs

```bash
#!/bin/bash
# dev-setup.sh

set_default_environment() {
    local env_name="$1"
    # TODO: implement
}

build_project_config() {
    local env_name="$1"
    # TODO: implement
}

# ... etc
```

### 2. Implement One Function at a Time

Run bash tests after each function:
```bash
# From project root
bash spec-tests-dev-setup/bash/run_tests.sh

# Or if using PowerShell runner
pwsh spec-tests-dev-setup/bash/run_tests.ps1
```

### 3. Use Test Failures as a Guide

Test output tells you exactly what's wrong:
```
✗ Normalizes To Lowercase
    Expected 'ianphil', got 'IANPHIL'
    File: spec-tests-dev-setup/bash/function-contracts.md
```

### 4. Integration Tests Catch Composition Bugs

Unit tests pass but integration fails? Check data flow between functions.

### 5. Compare with PowerShell Tests

Verify your understanding by comparing test files:
```bash
diff spec-tests-dev-setup/powershell/function-contracts.md \
     spec-tests-dev-setup/bash/function-contracts.md
```
Differences should only be in code block language and syntax, not intent.

---

## Phase 5b: Porting Tests Between Languages

**ESSENTIAL STEP:** When porting code using literate tests, you MUST port the tests alongside the code. You'll have two test suites:
- PowerShell tests (source of truth for understanding the original)
- Bash tests (validation for your bash implementation)

This phase shows how to convert test syntax from one language to another while preserving intent.

### When This Applies

**Always applies when:**
- Porting code with literate tests from Language A to Language B
- You created PowerShell tests and now need bash tests
- Both test suites test the same behavior in different syntax

**Also applies when:**
- Original code has tests in a language-specific framework (pytest, Jest, xUnit)
- You're migrating from traditional test frameworks to literate tests

### Step 1: Extract Language-Agnostic Assertions

Strip away language-specific syntax to find the core contract.

**From PowerShell literate tests:**
```markdown
### Normalizes Environment Name

\`\`\`powershell
$envName = "MYENV"
$normalized = $envName.ToLower()
Write-Output $normalized
# expect: myenv
\`\`\`

### Rejects Reserved Keywords

\`\`\`powershell
$envName = "devlocal"
if ($envName -match "(dev|local|ppe|prod)") {
    throw [ValidationError]::new("reserved-keyword", "Contains reserved word")
}
# error: [reserved-keyword]
\`\`\`
```

**Extracted contracts:**
```
Test: normalizes_environment_name
  Input: "MYENV"
  Expected output: "myenv"

Test: rejects_reserved_keywords
  Input: "devlocal"
  Expected error: [reserved-keyword]
```

**To bash literate tests:**
```markdown
### Normalizes Environment Name

\`\`\`bash
env_name="MYENV"
normalized=$(echo "$env_name" | tr '[:upper:]' '[:lower:]')
echo "$normalized"
# expect: myenv
\`\`\`

### Rejects Reserved Keywords

\`\`\`bash
env_name="devlocal"
if [[ "$env_name" =~ (dev|local|ppe|prod) ]]; then
    echo "[reserved-keyword]" >&2
    exit 1
fi
# stderr: [reserved-keyword]
# exit: 1
\`\`\`
```

**Key differences:**
- Code block language: ```powershell → ```bash
- Variable syntax: `$envName` → `env_name` (bash convention)
- String methods: `.ToLower()` → `tr '[:upper:]' '[:lower:]'`
- Regex matching: `-match` → `=~`
- Error handling: PowerShell exceptions → exit codes + stderr
- Assertions: Same format (`# expect:`, `# error:`) but bash also uses `# exit:` and `# stderr:`

---

**For traditional framework tests:**

Strip away framework syntax to find the core contract:

**From pytest:**
```python
def test_normalizes_to_lowercase():
    result = normalize("HELLO")
    assert result == "hello"

def test_rejects_empty_input():
    with pytest.raises(ValidationError) as exc:
        normalize("")
    assert exc.value.code == "empty-input"
```

**Extracted contracts:**
```
Test: normalizes_to_lowercase
  Input: "HELLO"
  Expected output: "hello"
  
Test: rejects_empty_input
  Input: ""
  Expected error: [empty-input]
```

**From Jest:**
```javascript
test('validates email format', () => {
    expect(isValidEmail('user@example.com')).toBe(true);
    expect(isValidEmail('invalid')).toBe(false);
});
```

**Extracted contracts:**
```
Test: validates_email_format
  Input: "user@example.com" → Expected: true
  Input: "invalid" → Expected: false
```

### Step 2: Rewrite in Target Format

Convert extracted contracts to literate tests in target language:

**To bash literate tests:**
```markdown
### Normalizes To Lowercase

\`\`\`bash
input="HELLO"
result=$(echo "$input" | tr '[:upper:]' '[:lower:]')
echo "$result"
# expect: hello
\`\`\`

### Rejects Empty Input

\`\`\`bash
input=""
if [ -z "$input" ]; then
    echo "[empty-input]"
    exit 1
fi
# expect: [empty-input]
# exit: 1
\`\`\`
```

**To Python literate tests:**
```markdown
### Normalizes To Lowercase

\`\`\`py
normalize("HELLO")  # expect: "hello"
\`\`\`

### Rejects Empty Input

\`\`\`py
normalize("")  # error: [empty-input]
\`\`\`
```

### Step 3: Preserve Test Coverage

Create a mapping to ensure nothing is lost:

| Original Test (pytest) | Ported Test (bash) | Status |
|------------------------|-------------------|--------|
| `test_normalizes_to_lowercase` | `Normalizes To Lowercase` | ✓ |
| `test_rejects_empty_input` | `Rejects Empty Input` | ✓ |
| `test_handles_unicode` | `Handles Unicode` | ✓ |
| `test_strips_whitespace` | `Strips Whitespace` | ✓ |

### Step 4: Verify Test Equivalence

Both test suites should:

1. **Same number of test cases** — Count should match (or document why it differs)
2. **Same input values** — Use identical test data where possible
3. **Same edge cases covered** — Boundary conditions, error cases, null handling
4. **Same assertions** — Expected outputs must match exactly

**Automated check:**
```bash
# When porting from PowerShell to bash (both using literate tests)
ps_count=$(grep -c "^### " spec-tests-dev-setup/powershell/*.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
bash_count=$(grep -c "^### " spec-tests-dev-setup/bash/*.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')

echo "PowerShell tests: $ps_count"
echo "Bash tests: $bash_count"
[ "$ps_count" -eq "$bash_count" ] && echo "✓ Test counts match"

# When porting from traditional framework (e.g., pytest) to literate tests
pytest_count=$(grep -c "def test_" tests/test_original.py)
markdown_count=$(grep -c "^### " spec-tests-dev-setup/bash/*.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')

echo "Original (pytest): $pytest_count tests"
echo "Ported (literate): $markdown_count tests"
[ "$pytest_count" -eq "$markdown_count" ] && echo "✓ Counts match"
```

### Handling Framework-Specific Features

Some test features don't translate directly:

| Framework Feature | Literate Test Equivalent |
|------------------|-------------------------|
| `@pytest.fixture` | Setup code block at start of test |
| `@pytest.mark.parametrize` | Multiple test cases with different inputs |
| `beforeEach`/`afterEach` | Explicit setup/teardown in each block |
| Mock libraries | Mock scripts in `spec-tests-{thing}/mocks/` directory (shared between both test suites) |
| Test coverage | Not applicable (tests ARE the spec) |

---

## Phase 7: Validate the Port

All bash tests should pass. Then verify the port achieves the same outcomes as the original.

### Running Both Test Suites

```bash
# Run PowerShell tests (validate understanding of original)
pwsh spec-tests-dev-setup/powershell/run_tests.ps1

# Run bash tests (validate ported implementation)
bash spec-tests-dev-setup/bash/run_tests.sh
```

### Validation Techniques

| Validation Technique | How | Example |
|---------------------|-----|---------|
| **Golden Output** | Capture stdout/stderr from both, strip timestamps, diff | `pwsh original.ps1 2>&1 \| grep -v "^\[" > expected.txt`<br>`bash port.sh 2>&1 \| grep -v "^\[" > actual.txt`<br>`diff expected.txt actual.txt` |
| **Side Effect Verification** | Script that checks external state after run | `verify_service_bus()` checks topic exists<br>`verify_user_secrets()` checks secrets set |
| **Smoke Tests** | Can downstream consumers actually use it? | `az servicebus send` succeeds<br>`curl $TUNNEL_URL/health` returns ok |
| **Behavioral Parity Checklist** | Manual checks for hard-to-automate behaviors | Same resources in cloud, files locally, env vars, error helpfulness, Ctrl+C cleanup |
| **Test Count Verification** | Ensure test count matches between languages | `grep -c "^### " spec-tests-dev-setup/powershell/*.md`<br>`grep -c "^### " spec-tests-dev-setup/bash/*.md` |

---

## Key Principles

| Principle | Explanation |
|-----------|-------------|
| **Tests define contract, not implementation** | Good: "Topic name contains environment" (outcome)<br>Bad: "Uses string interpolation" (PowerShell-specific) |
| **Intent tests are the north star** | If intent tests pass, port is functionally complete regardless of implementation differences |
| **Mocks enable isolated testing** | Test logic without real Azure/AWS/etc. resources |
| **Layers catch different bugs** | Intent→missing features, Contracts→wrong behavior, Integration→data flow, Implementation→language errors |
| **Document intent, not mechanics** | Good: "Why it matters: Without this, no Service Bus for messaging"<br>Bad: "Creates Service Bus namespace" |

---

## Checklist

Before starting a port:

- [ ] Set up directory structure
  - [ ] Created `spec-tests-{thing}/` root directory
  - [ ] Created `spec-tests-{thing}/powershell/` subdirectory
  - [ ] Created `spec-tests-{thing}/bash/` subdirectory
  - [ ] Created `spec-tests-{thing}/mocks/` subdirectory
- [ ] Analyzed original code structure (components, functions, dependencies)
- [ ] Created **PowerShell tests** (```ps1 blocks) in `spec-tests-{thing}/powershell/`
  - [ ] `component-intents.md` with outcomes for each component
  - [ ] `function-contracts.md` with I/O specs for each function
  - [ ] `integration-flow.md` with multi-step workflow tests
  - [ ] Implementation pattern tests (azure-cli-integration.md, file-system.md, etc.)
- [ ] Validated PowerShell tests against original implementation (if possible)
- [ ] Created shared mocks in `spec-tests-{thing}/mocks/`
- [ ] Set up PowerShell test runner: `cp run_tests.ps1 spec-tests-{thing}/powershell/`

During test porting:

- [ ] **Ported tests to bash** (```bash blocks) in `spec-tests-{thing}/bash/`
  - [ ] All component-intents tests converted
  - [ ] All function-contracts tests converted
  - [ ] All integration-flow tests converted
  - [ ] All implementation pattern tests converted
- [ ] Set up bash test runner in `spec-tests-{thing}/bash/`
- [ ] Ensured both test suites reference `../mocks/` for shared mocks
- [ ] Verified test count matches: `diff <(ls powershell/) <(ls bash/)`
- [ ] Verified filenames match between `powershell/` and `bash/` directories

During implementation porting:

- [ ] Implement one function at a time
- [ ] Run **bash tests** after each function: `bash spec-tests-{thing}/bash/run_tests.sh`
- [ ] Use test failures as implementation guide
- [ ] Check integration tests after unit tests pass
- [ ] Compare with PowerShell tests when stuck: `diff spec-tests-{thing}/powershell/X.md spec-tests-{thing}/bash/X.md`

After the port:

- [ ] All **bash tests** pass (validates bash implementation)
- [ ] All **PowerShell tests** still pass (validates understanding of original)
- [ ] Bash test output matches expectations
- [ ] Compared bash behavior with original PowerShell behavior
- [ ] Verified external side effects match (Service Bus, files, env vars, etc.)
- [ ] Documented any intentional behavioral differences
- [ ] Both test suites maintained in version control for future reference

---

## Example: PowerShell to Bash

This cookbook was developed while porting `dev-setup.ps1` (428 lines of PowerShell) to bash.

**Test suite created:**
- 226 tests across 13 test files
- 3 mock scripts (az, dotnet, devtunnel)
- Covers intent, contracts, integration, and implementation

**Time investment:**
- ~2 hours to create comprehensive test suite
- Tests serve as documentation for new engineers
- Tests define acceptance criteria for the port
- Tests remain valuable after port is complete

The test suite is more valuable than the port itself—it captures institutional knowledge that would otherwise be lost.
