# Behavior Contract: [NAME]

> A specification for coding agents. Defines outcomes and behaviors, not implementation.

## Outcome

[One paragraph: What does success look like? What problem is solved? Who benefits?]

## Boundaries

### In Scope
- [Capability or behavior this contract covers]
- [Another capability]

### Out of Scope
- [What this explicitly does NOT cover]
- [Adjacent functionality to avoid scope creep]

### Constraints
- **NEVER**: [Invariant that must not be violated]
  - *Rationale*: [Why this constraint exists]
- **NEVER**: [Another invariant]
  - *Rationale*: [Why]
- **MUST**: [Required property or compatibility]
  - *Rationale*: [Why]

## Behaviors

### Scenario: [Descriptive name]

**Given**: [Initial state or preconditions]
**When**: [Action or trigger]
**Then**: [Expected outcome]

**Notes**: [Optional: edge cases, clarifications]

---

### Scenario: [Another scenario]

**Given**: [Preconditions]
**When**: [Action]
**Then**: [Outcome]

---

### Scenario: [Error/edge case]

**Given**: [Preconditions including problematic state]
**When**: [Action that triggers edge case]
**Then**: [How system should respond]

## Verification

### Automated
- [ ] [Test or check that can run without human judgment]
- [ ] [Another automated verification]

### Manual
- [ ] [Verification requiring human judgment, if any]

## Context

### Existing Code
- `path/to/relevant/file.py` - [Why it's relevant]
- `path/to/another.py` - [Relationship to this contract]

### External Dependencies
- [API, service, or library this depends on]
- [Data format or protocol that must be respected]

### Prior Decisions
- [Link to previous assessment or decision that constrains this work]

## Open Questions

- [ ] [Unresolved question that may affect implementation]
- [ ] [Another question - agent should ask before proceeding if critical]

---

**Contract Status**: Draft | Ready | In Progress | Verified
