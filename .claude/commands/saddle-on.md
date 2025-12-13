# Enable TDD Enforcement

Enable TDD (Test-Driven Development) enforcement for this project.

## Instructions

1. **Check if project/CLAUDE.md exists**:
   - If it doesn't exist, create it with the TDD enforcement section
   - If it exists, add or update the TDD setting

2. **Update project/CLAUDE.md**:
   - Look for an existing `## Enforcement` section
   - If found, update or add `TDD: enabled` under it
   - If not found, append the enforcement section

3. **File Format** (create or update to include):
   ```markdown
   ## Enforcement
   TDD: enabled
   ```

4. **Confirm the change**:
   - Read back the file to verify the change was made
   - Output confirmation message

## Expected Behavior After Enabling

When TDD is enabled:
- Pre-tool-use hook will BLOCK writes to implementation files in `project/` that don't have corresponding test files
- Stop hook will verify tests pass before allowing task completion
- User prompt submit hook will remind about TDD requirements

## Output

After enabling:
```
TDD Enforcement: ENABLED

When TDD is enabled:
- You must create test files before implementation files
- Tests must pass before tasks can be completed
- Write operations to project/ will be blocked if tests are missing

To disable: /saddle-off
```
