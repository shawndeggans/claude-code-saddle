# Behavior Contract Format Specification

The Behavior Contract is the output format for requirements. It defines outcomes and behaviors, not implementation.

## Required Sections

### Outcome (Required)
One paragraph answering:
- What does success look like?
- What problem is solved?
- Who benefits?

**Good**: "Users can reset their password without contacting support, reducing support tickets and improving user autonomy."

**Bad**: "Implement password reset functionality."

### Boundaries (Required)

Three subsections:

**In Scope**: Capabilities or behaviors this contract covers
- Use bullet points
- Be specific about what's included

**Out of Scope**: What this explicitly does NOT cover
- Adjacent functionality to prevent scope creep
- Related features handled elsewhere

**Constraints**: Invariants that must hold
- Format: `**NEVER**: [invariant]` with `*Rationale*: [why]`
- Format: `**MUST**: [required property]` with `*Rationale*: [why]`
- Every constraint needs a rationale

### Behaviors (Required)
Scenarios using Given/When/Then format:

```markdown
### Scenario: [Descriptive name]

**Given**: [Initial state or preconditions]
**When**: [Action or trigger]
**Then**: [Expected outcome]

**Notes**: [Optional: edge cases, clarifications]
```

Include scenarios for:
- Happy path (primary use cases)
- Error cases (what happens when things go wrong)
- Edge cases (boundary conditions)

### Verification (Required)

**Automated**: Tests or checks that can run without human judgment
- Specific, testable conditions
- Format as checklist `- [ ]`

**Manual**: Verification requiring human judgment (if any)
- User acceptance criteria
- Subjective quality checks

### Open Questions (Required if any gaps exist)
- Unresolved questions that may affect implementation
- Format: `- [ ] [Question]`
- Agent should ask before proceeding if critical

## Optional Sections

### Context
Only include if relevant:

**Existing Code**: Files/modules this affects (brownfield only)
- `path/to/file.py` - Why it's relevant

**External Dependencies**: APIs, services, libraries
- What this depends on
- Protocols or formats that must be respected

**Prior Decisions**: Links to assessments or decisions that constrain this work

## Contract Status

End every contract with:

```markdown
---

**Contract Status**: Draft | Ready | In Progress | Verified
```

- **Draft**: Still gathering requirements
- **Ready**: Requirements complete, ready for implementation
- **In Progress**: Implementation started
- **Verified**: Implementation complete and verified

## Quality Checklist

Before marking a contract as Ready:

- [ ] Outcome clearly states success criteria
- [ ] In Scope items are specific and actionable
- [ ] Out of Scope prevents obvious scope creep
- [ ] Every constraint has a rationale
- [ ] Core behaviors have scenarios
- [ ] Error cases are covered
- [ ] Verification criteria are testable
- [ ] Open questions are documented (or none remain)
- [ ] No implementation decisions in Behaviors section
- [ ] User's original language preserved where meaningful
