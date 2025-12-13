# Saddle Status

Show saddle mode status and available commands.

## Instructions

Display the current state of saddle enforcement:

1. **Check TDD Status**:
   ```bash
   if grep -qE "^TDD:\s*enabled" project/CLAUDE.md 2>/dev/null; then
     echo "TDD Enforcement: ENABLED"
   else
     echo "TDD Enforcement: disabled"
   fi
   ```

2. **Check Index**:
   ```bash
   if [ -f "saddle/index/CODEBASE.md" ]; then
     echo "Codebase Index: available"
   else
     echo "Codebase Index: not generated (run /index)"
   fi
   ```

3. **Check Hooks**:
   ```bash
   echo "Hooks configured:"
   ls -1 .claude/hooks/*.py 2>/dev/null | sed 's/.*\//  - /'
   ```

4. **Show Available Commands**:
   ```
   Available Saddle Commands:
   - /saddle       - Show this status
   - /saddle-on    - Enable TDD enforcement
   - /saddle-off   - Disable TDD enforcement
   - /index        - Regenerate codebase index
   - /status       - Quick project health check
   - /cleanup      - Find dead code and stale files
   ```

## Output Format

```
Saddle Mode Status
==================
TDD Enforcement: <enabled/disabled>
Codebase Index: <available/not generated>

Hooks configured:
  - pre-tool-use.py
  - post-tool-use.py
  - user-prompt-submit.py
  - stop.py

Available Commands:
  /saddle-on   - Enable TDD enforcement
  /saddle-off  - Disable TDD enforcement
  /index       - Regenerate codebase index
  /status      - Quick project health check
```
