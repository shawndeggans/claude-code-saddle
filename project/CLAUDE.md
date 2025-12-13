# Project Rules

This file contains project-specific rules and enforcement settings.

## Enforcement

TDD: disabled

To enable TDD enforcement, change the line above to `TDD: enabled` or run `/saddle-on`.

When TDD is enabled:
- Test files must exist before implementation files can be created
- Tests must pass before tasks are marked complete
- Write operations to `project/src/` will be blocked if corresponding tests don't exist

## Guidelines

Add project-specific guidelines here. These supplement the root CLAUDE.md rules.
