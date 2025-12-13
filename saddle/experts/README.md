# Expert Systems

Expert systems are MCP servers with embedded LLMs that provide deep domain knowledge for specific tools or technologies. They allow the main Claude Code agent to delegate specialized work without polluting its own context.

## Expert vs Workflow vs Tool

| Type | Purpose | Example |
|------|---------|---------|
| **Tool** | Single operation | Run a SQL query |
| **Workflow** | Predefined sequence of steps | Deploy pipeline (lint, test, deploy) |
| **Expert** | Answer varied questions, make decisions, accumulate knowledge | Databricks configuration guidance |

**Use an expert when**: You need domain-specific guidance, decisions, or troubleshooting that requires accumulated knowledge and judgment.

## Available Experts

| Expert | Domain | Port | Documentation |
|--------|--------|------|---------------|
| **requirements** | Behavior Contract generation from project descriptions | 3001 | `saddle/experts/requirements/README.md` |

### Requirements Expert

Transforms vague or partial project descriptions into structured Behavior Contracts ready for implementation.

**Use for**:
- Analyzing project descriptions for completeness
- Generating prioritized clarifying questions
- Producing Behavior Contract drafts (Outcome, Boundaries, Behaviors, Verification)
- Reviewing existing PRDs or user stories
- Diagnosing why requirements are blocking implementation

**Invoke**: `requirements.consult`, `requirements.execute`, `requirements.review`, `requirements.troubleshoot`

See `saddle/experts/requirements/README.md` for full documentation.

## When to Create an Expert

Signs you need an expert system:

1. **Repeated context pollution**: You keep loading the same domain knowledge into the main agent's context
2. **Forgotten patterns**: The main agent keeps forgetting how to work with a specific tool
3. **Complex decision-making**: The domain requires judgment calls based on organizational conventions
4. **Error translation**: Domain-specific errors need interpretation before the main agent can act
5. **Knowledge accumulation**: Decisions and patterns should persist across sessions

## Architecture

```
Main Claude Code Agent
         |
         | MCP Protocol
         v
+-------------------+
|   Expert Server   |
|  +-------------+  |
|  |   LLM       |  |  <-- Domain-specific system prompt
|  +-------------+  |
|         |         |
|  +-------------+  |
|  | Knowledge   |  |  <-- SKILL.md + knowledge files
|  | Base        |  |
|  +-------------+  |
|         |         |
|  +-------------+  |
|  | Decision    |  |  <-- Persistent decision history
|  | Log         |  |
|  +-------------+  |
+-------------------+
```

**Components**:
- **MCP Server**: Exposes tools (consult, execute, review, troubleshoot) to main agent
- **Embedded LLM**: Processes queries with domain knowledge in context
- **Knowledge Base**: Core concepts, reference material, org patterns
- **Decision Log**: Historical decisions and rationale (persists across sessions)

## Available Tools

Each expert exposes four standard tools:

### consult
Ask the expert a question about its domain.

```python
response = expert.consult(
    query="Should we use a job cluster or all-purpose cluster for this workload?",
    context="Daily batch job, runs for 2 hours, processes 500GB"
)
# Returns: answer, confidence, references, follow_up_questions
```

### execute
Have the expert perform a domain-specific action.

```python
response = expert.execute(
    action="generate_cluster_config",
    parameters={"workload_type": "batch", "data_size_gb": 500}
)
# Returns: status, result, error, next_steps
```

### review
Have the expert review a configuration, script, or plan.

```python
response = expert.review(
    artifact="databricks.yml contents...",
    artifact_type="asset_bundle_config"
)
# Returns: assessment (approved/concerns/rejected), issues, suggestions
```

### troubleshoot
Have the expert diagnose and suggest fixes for an error.

```python
response = expert.troubleshoot(
    error="ClusterNotFoundException: Cluster xyz not found",
    context="Running job via asset bundle deployment"
)
# Returns: diagnosis, root_cause, suggested_fixes, confidence
```

## Creating an Expert

### 1. Initialize from template

```bash
./scripts/init-expert.sh <expert-name> "<domain-description>"
# Example:
./scripts/init-expert.sh databricks "Databricks platform, Asset Bundles, and MLFlow"
```

This creates `saddle/experts/<expert-name>/` with the full structure.

### 2. Customize SKILL.md

Edit `SKILL.md` to include:
- Core concepts the expert must understand
- Your organization's patterns and conventions
- Common tasks with step-by-step guidance
- Error handling for frequent issues
- Decision framework for ambiguous situations
- Clear boundaries (what to refuse)

**Token budget**: Keep core knowledge under 4000 tokens. Use `knowledge/reference/` for extended material loaded on demand.

### 3. Populate knowledge base

```
knowledge/
  core/           # Always loaded (essential concepts)
  reference/      # Loaded on demand (detailed reference)
  org-patterns/   # Your organization's conventions
  decision-log/   # Decisions made (auto-populated)
```

### 4. Configure the expert

Edit `mcp-server/config.yaml`:
- Set expert name and domain
- Configure LLM provider and model
- Define knowledge file patterns
- Set boundary patterns (queries to refuse)
- Assign unique port number

### 5. Test the expert

```bash
./scripts/test-expert.sh <expert-name>
```

This validates:
- Knowledge files exist and are under token budget
- MCP server starts successfully
- All tools respond correctly
- Boundary handling works (refuses out-of-domain queries)

### 6. Start the expert

```bash
./scripts/start-expert.sh <expert-name>
```

### 7. Register in .mcp.json

Expert MCP servers must be registered in `.mcp.json` at the project root (NOT in `.claude/settings.json`):

```json
{
  "mcpServers": {
    "databricks-expert": {
      "type": "stdio",
      "command": "python3",
      "args": ["saddle/experts/databricks/mcp-server/server.py"]
    }
  }
}
```

### 8. Register in project CLAUDE.md

Add the expert to your project's CLAUDE.md so the main agent knows to use it.
See `saddle/templates/expert-claude-snippet.md` for the format.

## Invoking Experts

The main agent invokes experts via MCP tools. Example interaction:

```
User: "Set up a new Databricks job for the daily ETL pipeline"

Main Agent thinking: "This is Databricks-specific. I should delegate to the Databricks expert."

Main Agent: [calls databricks.consult with query about job configuration]

Expert responds: {
  answer: "For a daily ETL pipeline, use a job cluster with...",
  confidence: "high",
  references: ["knowledge/core/jobs.md", "knowledge/org-patterns/naming.md"],
  follow_up_questions: ["What's the expected data volume?"]
}

Main Agent: [uses expert guidance to proceed, may call expert.execute or expert.review]
```

## Knowledge Management

### Core Knowledge (Always Loaded)
Essential concepts the expert needs for any query. Keep concise.

### Reference Knowledge (On Demand)
Detailed documentation loaded when relevant. Can be larger.

### Organization Patterns
Your specific conventions, standards, and preferences. Critical for consistent guidance.

### Decision Log
Automatically populated when experts make significant decisions. Format:

```markdown
# Decision: [Brief title]
Date: YYYY-MM-DD
Query: [What was asked]
Decision: [What was decided]
Rationale: [Why]
Confidence: [high/medium/low]
Outcome: [If known later]
```

## Expert Boundaries

Experts must know what they don't know. Configure `boundaries.refuse_patterns` in config.yaml:

```yaml
boundaries:
  refuse_patterns:
    - "kubernetes"      # Not our domain
    - "aws lambda"      # Different platform
    - "pricing"         # Business decision, not technical
  redirect_to:
    main_agent: "Return to main agent for questions outside Databricks"
```

When an expert receives an out-of-domain query, it returns:
```python
ConsultResponse(
    answer="This question is outside my domain (Databricks). Please ask the main agent.",
    confidence="high",
    outside_domain=True
)
```

## Troubleshooting

### Expert not responding
1. Check server is running: `./scripts/start-expert.sh <name>`
2. Verify port is not in use
3. Check logs in expert directory

### Low confidence responses
1. Review SKILL.md for gaps in knowledge
2. Add relevant content to `knowledge/core/`
3. Check if query is actually in-domain

### Token budget exceeded
1. Move detailed content to `knowledge/reference/`
2. Summarize verbose sections in `knowledge/core/`
3. Use bullet points instead of prose

### Expert gives wrong guidance
1. Check `knowledge/org-patterns/` for missing conventions
2. Review decision log for conflicting past decisions
3. Update SKILL.md with corrections

## Design Principles

These principles derive from 12-Factor Agents methodology:

1. **Own your context window**: Each expert loads only domain-relevant knowledge
2. **Small, focused scope**: One domain deeply, not many domains poorly
3. **Tools as structured outputs**: Responses are structured, not free-form text
4. **Unify execution state**: Experts maintain persistent state across invocations
5. **Compact errors into context**: Domain errors become actionable guidance
6. **Expert boundaries**: Know what you don't know; decline rather than guess
