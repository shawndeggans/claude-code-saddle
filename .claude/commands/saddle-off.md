# Disable TDD Enforcement

Disable TDD (Test-Driven Development) enforcement for this project.

## Instructions

1. **Check if project/CLAUDE.md exists**:
   - If it doesn't exist, nothing to do (TDD is already disabled by default)

2. **Update project/CLAUDE.md**:
   - Look for `TDD: enabled` in the file
   - Change it to `TDD: disabled` or remove the line
   - Preserve other content in the file

3. **Confirm the change**:
   - Read back the file to verify the change was made
   - Output confirmation message

## Expected Behavior After Disabling

When TDD is disabled (default):
- Pre-tool-use hook allows all writes without checking for tests
- Stop hook does not verify tests before completion
- User prompt submit hook reminds to run tests but doesn't enforce

## Output

After disabling:
```
TDD Enforcement: DISABLED

You can now write implementation files without creating tests first.
Tests are still recommended but not enforced.

To enable: /saddle-on
```
