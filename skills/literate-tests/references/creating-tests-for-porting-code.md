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

1. **Create Source Language Tests** (PowerShell tests with ```ps1 blocks)
   - Capture the behavior of the original implementation
   - Establish the source of truth for intent
   - Validate against the original PowerShell script if possible

2. **Port Tests to Target Language** (Convert to bash tests with ```bash blocks)
   - Mirror each PowerShell test with equivalent bash syntax
   - Keep the same intent, assertions, and test structure
   - Use the assertion syntax reference for target language

3. **Set Up Target Language Test Runner**
   - Copy the appropriate runner: `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.sh" tests/`
   - Or use PowerShell runner which supports both: `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ps1" tests/`

4. **Port the Implementation**
   - Write the bash implementation guided by the bash tests
   - Run bash tests frequently: `bash tests/run_tests.sh` or `pwsh tests/run_tests.ps1`
   - Use test failures to guide implementation

5. **Validate the Port**
   - All bash tests should pass
   - Compare behavior with original
   - Verify external side effects match

**Why both test suites?**
- PowerShell tests validate your understanding of the original
- Bash tests validate your ported implementation
- Without both, you can't verify the port preserves behavior

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

Most code you'll port lacks documentation. Use these techniques to discover intent:

**Technique 1: Work Backwards from Side Effects**

Ask these questions about the code:
```
Q: What files does this create, modify, or delete?
Q: What external APIs or services does it call?
Q: What environment variables does it read or set?
Q: What does it print to stdout/stderr?

→ The answers ARE the intents. Each side effect represents something the user needs.
```

Example analysis:
```
Code calls: az servicebus topic create --name "common-events-$env"
Side effect: Service Bus topic exists
Intent: "Developer can publish messages to the common events topic"
```

**Technique 2: Name-Based Inference**

Function and variable names reveal intent, even without documentation:

```
Function: Set-DefaultEnvironment
→ Intent: Establish which environment (dev/ppe/prod) to target
→ Test: "After running, the environment is set and subsequent operations use it"

Variable: $skipEv2Deployment
→ Intent: Allow skipping slow/expensive EV2 deployment
→ Test: "When skip flag is set, EV2 deployment does not run"

Parameter: -Force
→ Intent: Bypass confirmation prompts for automation
→ Test: "With -Force, no interactive prompts appear"
```

**Technique 3: Error Message Mining**

Error messages document validation rules and edge cases:

```powershell
if ($envName.Length -lt 5 -or $envName.Length -gt 8) {
    throw "Environment name must be 5-8 characters"
}
```

This reveals:
- Intent: Validate environment name length
- Constraint: 5-8 characters
- Tests needed: boundary cases at 4, 5, 8, and 9 characters

```powershell
if ($envName -match "(dev|local|ppe|prod)") {
    throw "Environment name cannot contain reserved keywords"
}
```

This reveals:
- Intent: Prevent collisions with standard environment names
- Constraint: Reserved keywords list
- Tests needed: each reserved keyword, plus valid names

**Technique 4: Dependency Graph Analysis**

The order of operations reveals dependencies and intents:

```
1. Authenticate (az login)
2. Create Resource Group
3. Create Service Bus (requires Resource Group)
4. Create Topic (requires Service Bus)
5. Set User Secrets (requires Topic endpoint)
```

This reveals:
- Intent: Each step enables the next
- Tests needed: Verify each step's output feeds the next step's input
- Integration tests: Full workflow from auth to secrets

**Technique 5: Conditional Branch Analysis**

Every `if` statement represents a decision point with intent:

```powershell
if ($projects -contains "User-RP") {
    Setup-DevTunnel
}
```

This reveals:
- Intent: Dev tunnel is only needed for User-RP component
- Tests needed: 
  - "Dev tunnel created when User-RP in projects"
  - "Dev tunnel NOT created when User-RP not in projects"

---

## Phase 2: Create Test Layers

Create test files in order from highest to lowest abstraction:

### Layer 1: Component Intents (`component-intents.md`)

**Purpose:** Document what each component is supposed to achieve.

**Key question:** "After this runs, what can the user do that they couldn't before?"

```markdown
## Buildout Intent

**Purpose:** Provision shared foundational infrastructure.

**Why it matters:** Without Buildout, developers have no Service Bus, 
Key Vault, or storage. It's the foundation.

**After Buildout completes, a developer can:**
- Connect to the shared Service Bus namespace
- Store and retrieve secrets from Key Vault
- Upload and download artifacts from storage

### Service Bus Namespace Is Accessible

\`\`\`bash
namespace="aet-cmn-localdev-es2"
[ -n "$namespace" ]
echo $?
# expect: 0
\`\`\`
```

**Why this matters for porting:**
- Intent tests are language-agnostic
- They define success criteria for the port
- New implementation passes when it achieves the same outcomes

### Layer 2: Function Contracts (`function-contracts.md`)

**Purpose:** Define input/output behavior for each function.

**Key question:** "Given input X, what output Y should this function produce?"

```markdown
## set_default_environment()

**PowerShell:** `Set-DefaultEnvironment`

**Contract:**
- **Input:** `env_name` (string, 5-8 chars)
- **Output:** Normalized (lowercase) environment name
- **Side effects:** Persists to environment if changed
- **Errors:** Throws if contains reserved keywords

### Normalizes To Lowercase

\`\`\`bash
env_name="IANPHIL"
normalized=$(echo "$env_name" | tr '[:upper:]' '[:lower:]')
echo "$normalized"
# expect: ianphil
\`\`\`

### Rejects Reserved Keywords

\`\`\`bash
env_name="mydevenv"
if [[ "$env_name" =~ (dev|local|ppe|prod) ]]; then
    echo "rejected"
else
    echo "accepted"
fi
# expect: rejected
\`\`\`
```

**Why this matters for porting:**
- Each function has a clear specification
- The bash implementation must satisfy the same contract
- Edge cases are explicitly documented

### Layer 3: Integration Flow (`integration-flow.md`)

**Purpose:** Verify functions compose correctly.

**Key question:** "When A calls B which calls C, does data flow correctly?"

```markdown
## User-RP Specific Flow

**Scenario:** Developer includes User-RP in projects list.

### Dev Tunnel Created When User-RP Included

\`\`\`bash
projects=("Buildout" "User-RP")
setup_dev_tunnel=false

for p in "${projects[@]}"; do
    if [[ "$p" == "User-RP" ]]; then
        setup_dev_tunnel=true
        break
    fi
done

echo "$setup_dev_tunnel"
# expect: true
\`\`\`

### Both User-RP Projects Get Secrets

\`\`\`bash
userrp_projects=("UserRP.API" "UserRP.FunctionApp")
secrets_set=${#userrp_projects[@]}
echo "$secrets_set"
# expect: 2
\`\`\`
```

**Why this matters for porting:**
- Catches integration bugs the original might have
- Verifies data flows between functions correctly
- Documents implicit dependencies

### Layer 4: Implementation Patterns (`<category>.md`)

**Purpose:** Test language-specific patterns used in the implementation.

Categories to cover:
- **CLI Integration** — How to call external tools
- **File System** — Path handling, file operations
- **Environment Variables** — Reading, writing, persisting
- **Error Handling** — Exit codes, error messages
- **User Interaction** — Prompts, progress output

```markdown
## Azure CLI Integration

### Extracts Subscription ID

\`\`\`bash
output='{"id": "12345678-1234-1234-1234-123456789abc"}'
subscription_id=$(echo "$output" | grep -o '"id": "[^"]*"' | cut -d'"' -f4)
echo "$subscription_id"
# expect: 12345678-1234-1234-1234-123456789abc
\`\`\`
```

**Why this matters for porting:**
- Shows idiomatic patterns in target language
- Validates your understanding of the target language
- Provides reusable snippets for the port

---

## Complete Test Class Reference

Create one file per test class. Each class serves a specific purpose:

### Core Logic Tests (`<script-name>.md`)

**Purpose:** Test the script's core business logic independent of external systems.

**When to create:** Always. This is your starting point.

**What to test:**
- Input validation rules
- String formatting and manipulation
- Conditional logic branches
- Data transformations

**Example tests:**
- Environment name length validation (5-8 chars)
- Reserved keyword detection (dev/ppe/prod)
- Topic name construction from environment
- Secret value placeholder resolution

```markdown
### Validates Environment Name Length

\`\`\`bash
env_name="ianphil"
[[ ${#env_name} -ge 5 && ${#env_name} -le 8 ]]
echo $?
# expect: 0
\`\`\`
```

---

### Configuration Structure Tests (`components.md`)

**Purpose:** Test the data structures that configure behavior.

**When to create:** When the script has configurable components with properties like priority, flags, or nested settings.

**What to test:**
- Component priorities/ordering
- Boolean flags (needs_ev2, skip_steps)
- Nested configuration (user_secrets per project)
- Default values

**Example tests:**
- Buildout has priority 1
- TestHarness doesn't need EV2
- Red-Network has 3 skip steps
- User-RP has secrets for both API and FunctionApp

```markdown
### Buildout Has Highest Priority

\`\`\`bash
priority=1
[ $priority -eq 1 ]
echo $?
# expect: 0
\`\`\`
```

---

### Component Intents (`component-intents.md`)

**Purpose:** Document and test the **outcomes** each component should achieve.

**When to create:** When the script has distinct components/modules with different purposes.

**What to test:**
- What the user can do after the component runs
- What resources exist after completion
- What capabilities are enabled

**Structure per component:**
```markdown
## [Component] Intent

**Purpose:** [One sentence]

**Why it matters:** [Business/technical value]

**After [Component] completes, a user can:**
- [Outcome 1]
- [Outcome 2]
```

**Example tests:**
- After Buildout: Service Bus is accessible
- After User-RP: ARM requests route through dev tunnel
- After PI-Management: Orchestrations survive restarts

---

### CLI Integration Tests (`azure-cli-integration.md`, `dotnet-cli.md`, `dev-tunnel.md`)

**Purpose:** Test patterns for calling external CLI tools.

**When to create:** One file per external CLI the script depends on.

**What to test:**
- Command construction
- Output parsing (JSON, text)
- Error detection
- Exit code handling

**Example tests:**
- Extracts subscription ID from az account show
- Constructs Service Bus topic create command
- Parses VNet peering state from JSON
- Detects ResourceNotFound error

```markdown
### Parses Peering State

\`\`\`bash
json='{"peeringState": "Disconnected"}'
state=$(echo "$json" | grep -o '"peeringState": "[^"]*"' | cut -d'"' -f4)
echo "$state"
# expect: Disconnected
\`\`\`
```

---

### File System Tests (`file-system.md`)

**Purpose:** Test path manipulation and file operations.

**When to create:** When the script reads/writes files, constructs paths, or navigates directories.

**What to test:**
- Path construction and normalization
- File/directory existence checks
- Directory stack (pushd/popd)
- Cross-platform path handling

**Example tests:**
- Constructs ServiceGroupRoot path
- Validates project path exists
- Restores directory on exit
- Handles symlinked paths

---

### Environment Variables (`environment-variables.md`)

**Purpose:** Test reading, writing, and persisting environment variables.

**When to create:** When the script uses environment variables for configuration or state.

**What to test:**
- Reading from environment
- Detecting unset/empty variables
- Persisting to shell profiles (.bashrc, .profile)
- Variable inheritance in subshells

**Example tests:**
- Reads SCALocalEnvName from environment
- Detects unset variable
- Constructs export statement for persistence
- Variable available in subshell

---

### Error Handling (`error-handling.md`)

**Purpose:** Test error detection, messages, and exit codes.

**When to create:** Always. Every script needs error handling tests.

**What to test:**
- Exit codes (success=0, failure=non-zero)
- Error message formatting
- Prerequisite checks (required tools installed)
- Error propagation from subcommands

**Example tests:**
- Returns exit code 1 on failure
- Formats error with red color
- Detects missing Azure CLI
- Propagates az command failure

```markdown
### Detects Auth Failure

\`\`\`bash
error_msg="Please run 'az login'"
echo "$error_msg" | grep -q "az login"
echo $?
# expect: 0
\`\`\`
```

---

### Script Execution (`script-execution.md`)

**Purpose:** Test subprocess calls and script composition.

**When to create:** When the script calls other scripts or manages subprocesses.

**What to test:**
- Script path construction
- Argument passing
- Exit code capture
- Sourcing vs executing scripts

**Example tests:**
- Constructs login script path
- Passes environment name to EV2 script
- Captures subprocess exit code
- Continues after expected failure

---

### User Interaction (`user-interaction.md`)

**Purpose:** Test prompts, progress output, and terminal handling.

**When to create:** When the script has interactive elements or formatted output.

**What to test:**
- Confirmation prompts (y/n)
- Progress indicators (countdown, spinners)
- Colored output (success=green, error=red)
- Non-interactive mode detection

**Example tests:**
- Accepts 'y' as confirmation
- Displays countdown from 5
- Formats success with green checkmark
- Skips prompts in CI environment

---

### Function Contracts (`function-contracts.md`)

**Purpose:** Define input/output specifications for each function.

**When to create:** After identifying all functions in the original code.

**What to test:**
- Input parameters and types
- Return values
- Side effects
- Error conditions

**Structure per function:**
```markdown
## function_name()

**Original:** `Original-FunctionName` (PowerShell)

**Contract:**
- **Input:** parameter descriptions
- **Output:** return value description
- **Side effects:** what it modifies
- **Errors:** when it fails
```

**Example tests:**
- set_default_environment() normalizes to lowercase
- build_project_config() returns priority for each project
- set_user_secrets() clears before setting

---

### Integration Flow (`integration-flow.md`)

**Purpose:** Test that multiple functions work together correctly.

**When to create:** After function contracts are defined.

**What to test:**
- Data flow between functions
- Multi-step workflows
- Error propagation across functions
- Idempotency (running twice is safe)

**Example tests:**
- Environment name flows to topic name
- User-RP inclusion triggers dev tunnel setup
- Service Bus failure stops execution
- Running twice produces same result

```markdown
### Environment Flows To Topic Name

\`\`\`bash
env_name="ianphil"
topic_name="common-events-$env_name"
echo "$topic_name" | grep -q "$env_name"
echo $?
# expect: 0
\`\`\`
```

---

### Mocks Directory (`mocks/`)

**Purpose:** Provide fake implementations of external CLIs for testing.

**When to create:** For each external CLI the script calls.

**What to include:**
- Executable scripts that mimic CLI behavior
- Environment variable controls for different scenarios
- Logging to verify calls were made correctly

**Mock per CLI:**
- `mocks/az` — Azure CLI
- `mocks/dotnet` — .NET CLI
- `mocks/devtunnel` — Dev tunnel CLI

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

External tools (az, dotnet, devtunnel) can't be called in tests. Create mocks:

### Mock Structure

```
spec-tests/
└── mocks/
    ├── az           # Mock Azure CLI
    ├── dotnet       # Mock dotnet CLI
    └── devtunnel    # Mock dev tunnel CLI
```

### Mock Implementation Pattern

```bash
#!/bin/bash
# mocks/az - Mock Azure CLI

cmd="$1"
shift

case "$cmd" in
    account)
        case "$1" in
            show)
                echo '{"id": "12345678-...", "user": {"name": "test@example.com"}}'
                exit 0
                ;;
        esac
        ;;
    servicebus)
        case "$1" in
            topic)
                case "$2" in
                    create)
                        echo '{"name": "topic-name", "status": "Active"}'
                        exit 0
                        ;;
                esac
                ;;
        esac
        ;;
    *)
        echo "Mock az: unknown command $cmd" >&2
        exit 1
        ;;
esac
```

### Using Mocks in Tests

```bash
# Prepend mocks to PATH
export PATH="$(pwd)/mocks:$PATH"

# Now 'az' calls the mock
result=$(az account show)
echo "$result" | grep -q "user"
echo $?
# expect: 0
```

### Mock Environment Variables

Use environment variables to control mock behavior:

```bash
# In mock
if [[ "${MOCK_VNET_EXISTS:-true}" == "true" ]]; then
    echo '{"name": "vnet-name"}'
    exit 0
else
    echo "ERROR: ResourceNotFound" >&2
    exit 1
fi

# In test
export MOCK_VNET_EXISTS=false
# Now az network vnet show will fail
```

### Mocking HTTP/API Dependencies

For scripts that call REST APIs directly (curl, wget, Invoke-RestMethod):

```bash
#!/bin/bash
# mocks/curl - Mock HTTP client

# Parse URL from arguments (curl -s URL or curl -s -X GET URL)
for arg in "$@"; do
    if [[ "$arg" == http* ]]; then
        url="$arg"
        break
    fi
done

case "$url" in
    *"api.github.com/user"*)
        echo '{"login": "testuser", "id": 12345}'
        exit 0
        ;;
    *"management.azure.com"*/resourceGroups*)
        echo '{"value": [{"name": "rg-dev", "location": "eastus"}]}'
        exit 0
        ;;
    *)
        echo "Mock curl: unhandled URL $url" >&2
        exit 1
        ;;
esac
```

For SDK-based API calls, create response fixture files:

```
mocks/
├── az                          # CLI mock
├── curl                        # HTTP mock
└── responses/                  # Fixture data for complex responses
    ├── service_bus_topic.json
    ├── cosmos_account.json
    └── key_vault_secrets.json
```

Load fixtures in your mock:

```bash
# In mock, return fixture file content
case "$cmd" in
    cosmos)
        cat "$(dirname "$0")/responses/cosmos_account.json"
        ;;
esac
```

### Mocking Database Dependencies

For scripts that query databases, create file-based fixtures:

```bash
# Setup: Create test database state
mkdir -p /tmp/test_db
echo '[{"id": 1, "name": "test-user", "role": "admin"}]' > /tmp/test_db/users.json
echo '[{"id": 100, "env": "dev", "endpoint": "https://dev.example.com"}]' > /tmp/test_db/configs.json

# Mock query function reads from fixture
mock_sql_query() {
    local table="$1"
    cat "/tmp/test_db/${table}.json"
}

# In tests
result=$(mock_sql_query "users" | jq '.[0].name')
echo "$result"
# expect: "test-user"
```

For more complex queries, use jq to filter:

```bash
mock_sql_query_where() {
    local table="$1"
    local field="$2"
    local value="$3"
    cat "/tmp/test_db/${table}.json" | jq --arg v "$value" ".[] | select(.${field} == \$v)"
}
```

### Mocking File System State

Use temp directories with known structure for tests that depend on file layout:

```bash
setup_test_filesystem() {
    export TEST_ROOT=$(mktemp -d)
    
    # Create expected directory structure
    mkdir -p "$TEST_ROOT/src/MyProject"
    mkdir -p "$TEST_ROOT/config"
    mkdir -p "$TEST_ROOT/.azure"
    
    # Create expected files with known content
    echo "key=value" > "$TEST_ROOT/config/settings.ini"
    echo '{"subscription": "12345"}' > "$TEST_ROOT/.azure/config.json"
    
    # Create a mock project file
    cat > "$TEST_ROOT/src/MyProject/MyProject.csproj" << 'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
EOF
}

teardown_test_filesystem() {
    rm -rf "$TEST_ROOT"
}
```

Use in tests:

```markdown
### Finds Project File In Expected Location

\`\`\`bash
setup_test_filesystem
project_file=$(find "$TEST_ROOT" -name "*.csproj" | head -1)
[ -f "$project_file" ]
echo $?
# expect: 0
teardown_test_filesystem
\`\`\`
```

---

## Phase 4: Test File Organization

Organize tests by abstraction level and category:

```
spec-tests/
├── run_tests.ps1              # Test runner (supports bash + powershell)
│
├── # Layer 1: Intent (highest abstraction)
├── component-intents.md       # What outcomes should be achieved
│
├── # Layer 2: Contracts
├── function-contracts.md      # Input/output per function
│
├── # Layer 3: Integration
├── integration-flow.md        # Multi-function workflows
│
├── # Layer 4: Implementation patterns
├── azure-cli-integration.md   # az command patterns
├── dotnet-cli.md              # dotnet command patterns
├── dev-tunnel.md              # devtunnel patterns
├── file-system.md             # Path and file operations
├── environment-variables.md   # Env var handling
├── error-handling.md          # Exit codes and errors
├── script-execution.md        # Subprocess and script calls
├── user-interaction.md        # Prompts and output
│
├── # Original code analysis
├── dev-setup.md               # Core script logic tests
├── components.md              # Component configuration tests
│
└── mocks/                     # Mock external tools
    ├── az
    ├── dotnet
    └── devtunnel
```

---

## Phase 5: Port the Tests to Target Language

**CRITICAL:** Before porting the implementation, port the tests first. You need bash tests to validate your bash implementation.

See "Phase 5b: Porting Tests Between Languages" below for the complete process of converting PowerShell test syntax to bash test syntax while preserving intent.

---

## Phase 6: Write the Port

With **bash tests** in place, write the bash implementation:

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

Run tests after each function:
```bash
pwsh spec-tests/run_tests.ps1
```

### 3. Use Test Failures as a Guide

Test output tells you exactly what's wrong:
```
✗ Normalizes To Lowercase
    Expected 'ianphil', got 'IANPHIL'
```

### 4. Integration Tests Catch Composition Bugs

Unit tests pass but integration fails? Check data flow between functions.

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
# Count tests in original
pytest_count=$(grep -c "def test_" tests/test_original.py)

# Count tests in ported
markdown_count=$(grep -c "^### " spec-tests/*.md)

echo "Original: $pytest_count tests"
echo "Ported: $markdown_count tests"
[ "$pytest_count" -eq "$markdown_count" ] && echo "✓ Counts match"
```

### Handling Framework-Specific Features

Some test features don't translate directly:

| Framework Feature | Literate Test Equivalent |
|------------------|-------------------------|
| `@pytest.fixture` | Setup code block at start of test |
| `@pytest.mark.parametrize` | Multiple test cases with different inputs |
| `beforeEach`/`afterEach` | Explicit setup/teardown in each block |
| Mock libraries | Mock scripts in `mocks/` directory |
| Test coverage | Not applicable (tests ARE the spec) |

---

## Phase 7: Validate the Port

Passing tests verify *mechanics*. This phase verifies *intent*—that the port actually achieves what users need.

### Run Full Test Suite

```bash
pwsh spec-tests/run_tests.ps1
```

All tests should pass. But passing tests are necessary, not sufficient.

### Compare Behavior

Run both implementations with same inputs:

```bash
# Original
pwsh tools/dev-setup.ps1 -Projects "User-RP" -SkipEv2

# Port
bash tools/dev-setup.sh --projects "User-RP" --skip-ev2
```

### Validate Intent Is Achieved (Not Just Tests Pass)

Tests verify that functions behave correctly in isolation. Intent validation verifies the *outcomes* users actually care about.

**Technique 1: Golden Output Comparison**

Capture output from both implementations and diff:

```bash
# Run original, capture output (strip timestamps/paths that differ)
pwsh tools/dev-setup.ps1 -Projects "User-RP" 2>&1 | \
    grep -v "^\[" | grep -v "^/" > expected_output.txt

# Run port, capture output
bash tools/dev-setup.sh --projects "User-RP" 2>&1 | \
    grep -v "^\[" | grep -v "^/" > actual_output.txt

# Compare (should be empty or show only acceptable differences)
diff expected_output.txt actual_output.txt
```

**Technique 2: Side Effect Verification Script**

Create a script that checks external state *after* the main script runs:

```bash
#!/bin/bash
# verify_intent.sh - Run AFTER dev-setup.sh completes

echo "Verifying intent was achieved..."

# Intent: Service Bus topic is accessible
verify_service_bus() {
    local topic_name="$1"
    if az servicebus topic show --name "$topic_name" --namespace-name "$NAMESPACE" &>/dev/null; then
        echo "✓ Service Bus topic '$topic_name' exists and is accessible"
        return 0
    else
        echo "✗ Service Bus topic '$topic_name' not found"
        return 1
    fi
}

# Intent: User secrets are configured for the project
verify_user_secrets() {
    local project="$1"
    pushd "src/$project" > /dev/null
    if dotnet user-secrets list 2>/dev/null | grep -q "CosmosEndpoint"; then
        echo "✓ User secrets configured for $project"
        popd > /dev/null
        return 0
    else
        echo "✗ User secrets missing for $project"
        popd > /dev/null
        return 1
    fi
}

# Intent: Dev tunnel is established (for User-RP)
verify_dev_tunnel() {
    if devtunnel list 2>/dev/null | grep -q "Active"; then
        echo "✓ Dev tunnel is active"
        return 0
    else
        echo "✗ No active dev tunnel"
        return 1
    fi
}

# Run all verifications
failures=0
verify_service_bus "common-events-$ENV_NAME" || ((failures++))
verify_user_secrets "UserRP.API" || ((failures++))
verify_dev_tunnel || ((failures++))

if [ $failures -eq 0 ]; then
    echo -e "\n✓ All intents achieved"
    exit 0
else
    echo -e "\n✗ $failures intent(s) not achieved"
    exit 1
fi
```

**Technique 3: End-to-End Smoke Test**

Can a downstream consumer actually *use* what was provisioned?

```bash
# Smoke test: Can we send a message to Service Bus?
az servicebus topic send --topic-name "common-events-$ENV_NAME" \
    --namespace-name "$NAMESPACE" \
    --message-body '{"test": true}' && echo "✓ Can send messages"

# Smoke test: Can the app read its secrets?
cd src/UserRP.API && dotnet run --test-secrets-only && echo "✓ App can read secrets"

# Smoke test: Can we reach the dev tunnel?
curl -s "https://$TUNNEL_URL/health" | grep -q "ok" && echo "✓ Tunnel is reachable"
```

**Technique 4: Behavioral Parity Checklist**

Create a manual checklist for behaviors that are hard to automate:

```markdown
## Behavioral Parity Checklist

After running both implementations with identical inputs:

- [ ] Same resources created in Azure (check portal or `az resource list`)
- [ ] Same files created/modified locally
- [ ] Same environment variables set (compare `env | sort`)
- [ ] Error messages are equivalently helpful (not identical, but equally useful)
- [ ] Progress output appears at similar points (user knows what's happening)
- [ ] Ctrl+C cleanup works in both (resources don't leak on interrupt)
```

### Check Side Effects

Verify external state is the same:
- Service Bus topic created
- User secrets configured
- Dev tunnel established

---

## Key Principles

### 1. Tests Define the Contract, Not the Implementation

```markdown
# Good: Tests the outcome
### Topic Name Contains Environment
\`\`\`bash
topic_name="common-events-$env_name"
echo "$topic_name" | grep -q "$env_name"
# expect: 0
\`\`\`

# Bad: Tests PowerShell-specific syntax
### Uses String Interpolation
\`\`\`powershell
$topicName = "common-events-$EnvName"
\`\`\`
```

### 2. Intent Tests Are Your North Star

If intent tests pass, the port is functionally complete—even if implementation differs.

### 3. Mocks Enable Isolated Testing

Without mocks, you'd need real Azure resources to test. Mocks let you test logic in isolation.

### 4. Layer Tests Catch Different Bug Types

| Layer | Catches |
|-------|---------|
| Intent | Missing features |
| Contract | Wrong function behavior |
| Integration | Data flow bugs |
| Implementation | Language-specific errors |

### 5. Document Intent, Not Just Mechanics

```markdown
# Good: Explains why
**Purpose:** Provision shared infrastructure that all components depend on.

**Why it matters:** Without this, developers have no Service Bus for messaging.

# Bad: Just states what
Creates Service Bus namespace.
```

---

## Checklist

Before starting a port:

- [ ] Analyzed original code structure (components, functions, dependencies)
- [ ] Created **PowerShell tests** (```ps1 blocks) to capture original behavior
  - [ ] `component-intents.md` with outcomes for each component
  - [ ] `function-contracts.md` with I/O specs for each function
  - [ ] `integration-flow.md` with multi-step workflow tests
  - [ ] Implementation pattern tests
- [ ] Validated PowerShell tests against original implementation (if possible)
- [ ] Created mocks for all external dependencies
- [ ] Set up PowerShell test runner: `cp run_tests.ps1 tests/`

During test porting:

- [ ] **Ported tests to bash** (```bash blocks) with same intent
  - [ ] All component-intents tests converted
  - [ ] All function-contracts tests converted
  - [ ] All integration-flow tests converted
  - [ ] All implementation pattern tests converted
- [ ] Set up bash test runner: bash runner or PowerShell runner with bash support
- [ ] Verified test count matches (PowerShell test count = bash test count)

During implementation porting:

- [ ] Implement one function at a time
- [ ] Run **bash tests** after each function
- [ ] Use test failures as implementation guide
- [ ] Check integration tests after unit tests pass

After the port:

- [ ] All **bash tests** pass (validates bash implementation)
- [ ] Bash test output matches expectations
- [ ] Compared bash behavior with original PowerShell behavior
- [ ] Verified external side effects match (Service Bus, files, env vars, etc.)
- [ ] Documented any intentional behavioral differences
- [ ] Both test suites maintained for future reference

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
