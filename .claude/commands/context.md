# Session Context

Dump key context for resuming work after a break or new session.

## Instructions

Gather and display:

1. **Current Branch and Recent Commits**:
   ```bash
   echo "Branch: $(git branch --show-current)"
   echo ""
   echo "Recent commits:"
   git log --oneline -5
   ```

2. **Uncommitted Changes**:
   ```bash
   echo ""
   echo "Uncommitted changes:"
   git status --short
   ```

3. **Files Changed Since Last Commit** (if any):
   ```bash
   git diff --name-only HEAD 2>/dev/null
   ```

4. **Recent Assessment** (if exists):
   ```bash
   # Find most recent assessment file
   ls -t project/assessments/*.md 2>/dev/null | head -1
   ```

## Output Format

```
Branch: <branch-name>

Recent commits:
  <hash> <message>
  <hash> <message>
  ...

Uncommitted changes:
  M <file>
  A <file>
  ...

Recent assessment: <path or "none">
```

This helps quickly understand where work left off.
