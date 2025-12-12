# Requirements Expert

## Domain

Transforms vague or partial project descriptions into structured Behavior Contracts ready for implementation.

## Scope

### This expert handles:
- Interpreting natural language project descriptions
- Identifying gaps, ambiguities, and unstated assumptions
- Generating clarifying questions prioritized by implementation impact
- Producing Behavior Contract drafts from gathered information
- Recognizing when enough information exists to proceed vs. when more is needed
- Adapting to input completeness (full spec vs. vague idea)

### This expert does NOT handle:
- Technical design or architecture decisions
- Implementation planning or task breakdown
- Estimating effort or timeline
- Choosing technologies or frameworks
- Writing code or tests
- Project management artifacts

## Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **consult** | Analyze project descriptions, ask questions | "What should this feature do?" |
| **execute** | Generate Behavior Contract drafts | `action: "generate_contract"` |
| **review** | Assess existing requirements docs | Review a PRD for completeness |
| **troubleshoot** | Diagnose unclear requirements | Why is implementation blocked? |

## Usage Examples

### Consulting the Expert

```python
# Analyze a project description
response = requirements.consult(
    query="I need a feature that watches Confluence for changes",
    context="This is for our internal documentation system"
)
```

### Executing Actions

```python
# Generate a Behavior Contract
response = requirements.execute(
    action="generate_contract",
    parameters={
        "description": "User authentication with SSO support",
        "answers": {"greenfield": true, "primary_users": "internal employees"}
    }
)
```

### Reviewing Artifacts

```python
# Review existing requirements document
response = requirements.review(
    artifact="contents of PRD...",
    artifact_type="requirements_document"
)
```

### Troubleshooting

```python
# Diagnose blocked implementation
response = requirements.troubleshoot(
    error="Implementation team says requirements are unclear",
    context="Feature: automated report generation"
)
```

## Knowledge Structure

```
knowledge/
  core/                 # Essential concepts (always loaded)
    question-patterns.md      # Common gaps by domain
    behavior-contract-format.md  # Output format specification
  reference/            # Extended documentation (on-demand)
  org-patterns/         # Organization-specific context
  decision-log/         # Historical decisions (auto-populated)
templates/
  behavior-contract.md  # Output template
```

## Starting the Expert

```bash
./scripts/start-expert.sh requirements
```

## Testing

```bash
./scripts/test-expert.sh requirements
```

## Output Format

The expert produces documents conforming to the Behavior Contract format. See `templates/behavior-contract.md` for the template structure.

## Maintenance

### Updating Knowledge

1. Add new question patterns to `knowledge/core/question-patterns.md`
2. Update format spec in `knowledge/core/behavior-contract-format.md`
3. Add org-specific patterns to `knowledge/org-patterns/`
4. Review `knowledge/decision-log/` periodically for effective question sequences

### Token Budget

- Core knowledge: Keep under 4000 tokens
- Reference knowledge: No hard limit (loaded on demand)
- SKILL.md: Keep focused and actionable
