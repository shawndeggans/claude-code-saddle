# Project Status

Quick project health check - answer "where am I?" in one command.

## Instructions

Gather and display:

1. **Git Status**:
   ```bash
   git branch --show-current
   git status --short
   ```

2. **Test Status** (if tests exist):
   ```bash
   # Check if pytest is available and tests exist
   if [ -d "project/tests" ]; then
     pytest project/tests/ --collect-only -q 2>/dev/null | tail -1
   fi
   ```
   Or note when tests were last run if that info is available.

3. **Lint Status**:
   ```bash
   ruff check project/ --statistics 2>/dev/null | head -5
   ```

4. **Index Freshness**:
   ```bash
   ls -la saddle/index/codebase-index.json 2>/dev/null | awk '{print "Index last updated:", $6, $7, $8}'
   ```

## Output Format

```
Branch: <branch-name>
Changes: <N files modified, M untracked>
Tests: <status or "not configured">
Lint: <N warnings/errors or "clean">
Index: <freshness info>
```

Keep output concise - this is a quick glance, not a deep dive.
