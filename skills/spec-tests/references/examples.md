# Spec Test Examples

## Complete Example

```markdown
# User Authentication

## Login Flow

### Valid Credentials Succeed

Users expect immediate access with correct credentials. Friction here
directly impacts conversion—users abandon apps that make login difficult.

\`\`\`
Given a user with valid email and password
When they submit the login form
Then they are redirected to the dashboard
And a session token is created
\`\`\`

### Invalid Password Shows Generic Error

Don't reveal whether the email exists—attackers use specific errors to
enumerate accounts.

\`\`\`
Given a user submits an incorrect password
When the login is processed
Then the error is "Invalid email or password" (not "wrong password")
\`\`\`
```

---

## Business-Focused Intent

Intent explains why USERS or the PRODUCT care, not technical implementation details. Intent answers: "What breaks for the user if this test fails?"

**Good intent (business-focused):**
> Users perceive delays over 50ms as laggy. This operation runs on every keystroke, so exceeding this threshold makes the editor feel unresponsive.

**Bad intent (technical implementation):**
> We use a HashMap with O(1) lookup so this should be fast.

The good example explains user impact. The bad example describes implementation details that don't help the judge understand what matters.

---

## Porting Tests Across Languages

Intent is preserved when porting code between languages—the business reason doesn't change, only the assertion syntax.

**Python spec:**
```markdown
### Completes Quickly

Users perceive delays over 50ms as laggy. This operation runs on every
keystroke, so exceeding this threshold makes the editor feel unresponsive.

\`\`\`python
elapsed < 50  # expect: True
\`\`\`
```

**Same test ported to Rust:**
```markdown
### Completes Quickly

Users perceive delays over 50ms as laggy. This operation runs on every
keystroke, so exceeding this threshold makes the editor feel unresponsive.

\`\`\`rust
elapsed < 50  // expect: true
\`\`\`
```

The intent statement is identical—user perception of lag doesn't change with implementation language. Only the assertion syntax changes.

---

## One Behavior Per Test

Each test should cover a single behavior. When tests combine multiple behaviors, failures become ambiguous—you don't know which behavior broke. This also makes tests harder to understand and maintain.

**Bad: Multiple behaviors in one test**
```markdown
### User Management Works

Users need to create accounts and update profiles.

\`\`\`
Given a new user registration
Then the account is created
And the welcome email is sent
And the profile can be updated
And the avatar uploads correctly
\`\`\`
```

If this test fails, which behavior broke? Account creation? Email? Profile updates? Avatar uploads?

**Good: One behavior per test**
```markdown
### Account Creation Succeeds

Users need accounts to access the system.

\`\`\`
Given valid registration data
Then the account is created
\`\`\`

### Welcome Email Sends

New users expect confirmation that registration worked.

\`\`\`
Given a newly created account
Then a welcome email is sent within 30 seconds
\`\`\`
```

Now each failure points to exactly one behavior.
