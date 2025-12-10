# Diff Summary: $ARGUMENTS

Summarize what changed since a reference point, in human-readable terms.

## Instructions

1. Parse arguments:
   - No args: compare against last commit (HEAD)
   - With ref: compare against that ref (e.g., `main`, `HEAD~5`)

2. Get the diff:
   ```bash
   # Default: since last commit
   git diff --stat HEAD
   git diff --name-status HEAD

   # Or against specified ref
   git diff --stat <ref>
   git diff --name-status <ref>
   ```

3. Analyze the changes and categorize:
   - **Added**: New files (A status)
   - **Modified**: Changed files (M status)
   - **Deleted**: Removed files (D status)

4. For significant files (especially Python), extract what changed:
   - New functions/classes added
   - Functions/classes removed
   - Look at the actual diff to understand the nature of changes

5. Output format:
   ```
   Changes since <ref>:

   Added:
     <file> - <brief description of what was added>

   Modified:
     <file> - <brief description of changes>

   Deleted:
     <file> - <note if archived or permanently removed>

   Stats: +<lines added> lines, -<lines removed> lines, <N> files
   ```

## Example Usage

```
/diff              # Since last commit
/diff HEAD~5       # Last 5 commits
/diff main         # Against main branch
```

Arguments provided: $ARGUMENTS
