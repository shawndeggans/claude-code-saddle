# Archive File: $ARGUMENTS

Move a file to the archive with metadata for later recovery.

## Instructions

1. Parse arguments:
   - First argument: file path to archive
   - Optional `--reason "..."`: reason for archiving

2. Run the archive manager:
   ```bash
   python saddle/cleanup/archive_manager.py archive <path> --reason "<reason>"
   ```

3. Confirm the action:
   ```
   Archived: <original-path> -> .archive/<original-path>
   Reason: <reason or "not specified">
   Restore with: /restore <original-path>
   ```

## Example Usage

```
/archive src/old_auth.py --reason "replaced by OAuth implementation"
```

## Notes

- The archive preserves the original directory structure under `.archive/`
- Metadata is stored in `.archive/manifest.json`
- Files can be restored with `/restore`

Arguments provided: $ARGUMENTS
