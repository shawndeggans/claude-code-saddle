# Expert Systems Snippet for project/CLAUDE.md

Copy this section to your project's CLAUDE.md when expert systems are available.
Customize for each expert you've created.

---

## Available Expert Systems

The following expert systems are available via MCP. Use them for domain-specific
questions, tasks, and decisions. **Do not attempt to handle these domains yourself - delegate to the expert.**

### [Expert Name]

**Domain**: [Brief description of what the expert covers]

**Invoke**: Use the `[expert_name]` MCP tools:
- `consult` - Ask questions about the domain
- `execute` - Perform domain-specific actions
- `review` - Review configurations, scripts, or plans
- `troubleshoot` - Diagnose and fix errors

**Use for**:
- [Example use case 1]
- [Example use case 2]
- [Example use case 3]

**Do NOT use for**:
- [Out-of-scope topic 1]
- [Out-of-scope topic 2]

---

## Example: Databricks Expert

```markdown
### Databricks Expert

**Domain**: Databricks platform, Asset Bundles, MLFlow, Unity Catalog

**Invoke**: Use the `databricks` MCP tools (consult, execute, review, troubleshoot)

**Use for**:
- Databricks Asset Bundle configuration
- Job and workflow design
- Cluster configuration decisions
- MLFlow model management
- Unity Catalog permissions
- Troubleshooting job failures

**Do NOT use for**:
- General Python questions (not Databricks-specific)
- Infrastructure provisioning (use Terraform expert)
- Cost/pricing decisions (ask stakeholders)
```

---

## How to Add an Expert

1. Create the expert:
   ```bash
   ./scripts/init-expert.sh <name> "<domain description>"
   ```

2. Customize its knowledge:
   - Edit `saddle/experts/<name>/SKILL.md`
   - Add files to `saddle/experts/<name>/knowledge/`

3. Test and start:
   ```bash
   ./scripts/test-expert.sh <name>
   ./scripts/start-expert.sh <name>
   ```

4. Add section above to `project/CLAUDE.md`

See `saddle/experts/README.md` for full documentation.
