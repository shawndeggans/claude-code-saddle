# Cleanup Report

Run dead code detection and stale file tracking, then output a combined report.

## Instructions

1. Run dead code detection:
   ```bash
   python saddle/cleanup/dead_code_detector.py project/ --format markdown 2>/dev/null || echo "Dead code detector not available"
   ```

2. Run stale file tracking:
   ```bash
   python saddle/cleanup/stale_file_tracker.py project/ --threshold 180 --format markdown 2>/dev/null || echo "Stale file tracker not available"
   ```

3. Combine the outputs into a single report with sections:
   - **Dead Code**: Functions, classes, imports that appear unused
   - **Stale Files**: Files not modified in 180+ days
   - **Suggested Actions**: Archive candidates, deletion candidates

4. Output format should be markdown, suitable for reading in terminal.

## Optional Flags

If the user specifies `--save`, write the report to `project/cleanup-report.md`
If the user specifies `--json`, output machine-readable JSON instead.

Arguments provided: $ARGUMENTS
