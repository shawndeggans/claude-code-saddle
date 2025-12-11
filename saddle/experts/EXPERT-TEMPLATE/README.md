# {{EXPERT_NAME}} Expert

## Domain

{{DOMAIN_DESCRIPTION}}

## Scope

### This expert handles:
- [List specific capabilities]
- [Add domain-specific tasks]
- [Include review and troubleshooting areas]

### This expert does NOT handle:
- [List out-of-scope areas]
- [Include related but separate domains]
- [Note business decisions vs technical guidance]

## Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **consult** | Answer domain questions | "What cluster type for batch jobs?" |
| **execute** | Perform domain actions | Generate configuration files |
| **review** | Assess configurations/code | Review deployment manifest |
| **troubleshoot** | Diagnose and fix errors | Debug job failures |

## Configuration

### Required Environment Variables

```bash
# Add any required API keys or configuration
# {{EXPERT_NAME_UPPER}}_API_KEY=xxx
```

### Optional Configuration

Edit `mcp-server/config.yaml` to customize:
- LLM model and parameters
- Knowledge file patterns
- Boundary patterns
- Server port

## Usage Examples

### Consulting the Expert

```python
# Ask about best practices
response = {{expert_name}}.consult(
    query="What is the recommended approach for...",
    context="Additional context about the situation"
)
```

### Executing Actions

```python
# Generate a configuration
response = {{expert_name}}.execute(
    action="generate_config",
    parameters={"type": "...", "options": {...}}
)
```

### Reviewing Artifacts

```python
# Review a configuration file
response = {{expert_name}}.review(
    artifact="contents of file...",
    artifact_type="config_file"
)
```

### Troubleshooting Errors

```python
# Diagnose an error
response = {{expert_name}}.troubleshoot(
    error="Error message...",
    context="What was being attempted"
)
```

## Knowledge Structure

```
knowledge/
  core/                 # Essential concepts (always loaded)
  reference/            # Extended documentation (on-demand)
  org-patterns/         # Organization-specific conventions
  decision-log/         # Historical decisions (auto-populated)
```

## Starting the Expert

```bash
./scripts/start-expert.sh {{expert_name}}
```

## Testing

```bash
./scripts/test-expert.sh {{expert_name}}
```

## Maintenance

### Updating Knowledge

1. Add new concepts to `knowledge/core/` (keep concise)
2. Add detailed reference to `knowledge/reference/`
3. Update `knowledge/org-patterns/` when conventions change
4. Review `knowledge/decision-log/` periodically for patterns

### Token Budget

- Core knowledge: Keep under 4000 tokens
- Reference knowledge: No hard limit (loaded on demand)
- SKILL.md: Keep focused and actionable

### Version Updates

When {{DOMAIN_DESCRIPTION}} tools update:
1. Review SKILL.md for outdated information
2. Update `knowledge/core/` with new concepts
3. Add deprecation notes for removed features
4. Test expert with new scenarios
