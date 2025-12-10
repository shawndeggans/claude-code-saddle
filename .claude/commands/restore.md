# Restore Archived File: $ARGUMENTS

Recover a file from the archive to its original location.

## Instructions

1. Parse arguments:
   - First argument: original file path (before archiving)

2. Run the archive manager:
   ```bash
   python saddle/cleanup/archive_manager.py restore <path>
   ```

3. Confirm the action:
   ```
   Restored: <path>
   ```

## Example Usage

```
/restore src/old_auth.py
```

## To List Archived Files

If the user wants to see what's archived:
```bash
python saddle/cleanup/archive_manager.py list
```

Arguments provided: $ARGUMENTS
