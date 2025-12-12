# Question Patterns by Domain

Common gaps and clarifying questions organized by domain and priority.

## Universal Questions

### Purpose (Always Ask First)
- What problem does this solve?
- Who are the primary users/beneficiaries?
- What does success look like?
- Why now? What triggered this need?

### Scope
- Is this new (greenfield) or modifying existing (brownfield)?
- What's explicitly out of scope?
- Are there related features this should NOT touch?

### Behaviors
- What are the 2-3 core things this must do?
- What triggers each behavior?
- What is the expected outcome of each behavior?

### Constraints
- What must this never do?
- What must this always do?
- Are there regulatory or compliance requirements?

## Domain-Specific Patterns

### Data Processing
- What is the data source?
- What is the expected volume/frequency?
- What format is the input? Output?
- What happens on malformed input?
- Are there retention requirements?

### User Interfaces
- Who are the users (roles, technical level)?
- What devices/browsers must be supported?
- Are there accessibility requirements?
- Are there existing UI patterns to follow?

### Integrations
- What systems does this connect to?
- What are the authentication requirements?
- What happens when the external system is unavailable?
- Are there rate limits or quotas?

### Automation
- What triggers the automation?
- What is the expected frequency?
- What happens on failure?
- Who should be notified of issues?
- Is human approval required at any step?

### APIs
- Who are the consumers?
- What authentication method?
- What are the expected request volumes?
- Are there backwards compatibility requirements?

### Security-Sensitive Features
- What data is being handled?
- What access controls are needed?
- Are there audit/logging requirements?
- What happens to data after processing?

## Brownfield-Specific Questions

- What existing code/systems are affected?
- What must NOT break?
- Are there existing tests that define current behavior?
- Who owns the affected code?
- Are there pending changes that might conflict?

## Greenfield-Specific Questions

- What external dependencies does this have?
- What data stores are needed?
- Are there existing patterns in the codebase to follow?
- What is the deployment target?

## Priority Classification

### Blocking (Must answer before any implementation)
- Purpose and success criteria
- Greenfield vs brownfield
- Core behaviors (at least 2-3)
- Critical constraints ("must never" items)

### Architectural (Must answer before design)
- Data sources and volumes
- Integration points
- Authentication requirements
- Error handling strategy

### Edge Case (Can defer initially)
- Specific error scenarios
- Performance edge cases
- Rare user flows
- Nice-to-have behaviors
