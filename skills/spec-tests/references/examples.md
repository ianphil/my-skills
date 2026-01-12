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
