# Assess Task: $ARGUMENTS

Create a structured planning document for this task.

## Instructions

1. Create the assessments directory if it doesn't exist:
   ```bash
   mkdir -p project/assessments
   ```

2. Generate filename from task description:
   - Use today's date: YYYY-MM-DD format
   - Slugify the task name (lowercase, hyphens for spaces)
   - Example: `project/assessments/2024-01-15-user-authentication-with-oauth.md`

3. Copy the template and populate it:
   - Read `saddle/templates/assessment.md`
   - Replace `[TASK_NAME]` with: $ARGUMENTS
   - Write to the generated filename

4. Output the file path so the user can edit it:
   ```
   Assessment created: project/assessments/<filename>.md
   ```

5. Optionally, help the user fill in key sections by analyzing the codebase for:
   - Files likely to be modified
   - Existing patterns to follow
   - Related test files

## No Enforcement

This is purely for planning. The assessment is optional and has no gates.
