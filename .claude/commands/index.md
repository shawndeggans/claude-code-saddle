# Regenerate Codebase Index

Force regeneration of the codebase index without waiting for a commit.

## Instructions

1. Determine mode from arguments:
   - Default: `--full` (complete rebuild)
   - If user specified `--incremental`: only process changed files

2. Run the index generator:
   ```bash
   python saddle/index/generator/index_generator.py --full
   ```
   Or for incremental:
   ```bash
   python saddle/index/generator/index_generator.py --incremental
   ```

3. Output a summary:
   ```
   Index updated: X files, Y functions, Z classes
   Output: saddle/index/CODEBASE.md
   ```

4. If there are stale file candidates, mention them:
   ```
   Stale files: N candidates (run /cleanup for details)
   ```

Arguments provided: $ARGUMENTS
