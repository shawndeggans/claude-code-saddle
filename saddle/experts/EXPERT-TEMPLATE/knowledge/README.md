# Knowledge Base Organization

This directory contains the domain knowledge that powers the {{EXPERT_NAME}} expert.

## Directory Structure

```
knowledge/
  core/           # Essential concepts (always loaded)
  reference/      # Extended documentation (loaded on demand)
  org-patterns/   # Organization-specific conventions
  decision-log/   # Historical decisions (auto-populated)
```

## Core Knowledge (`core/`)

Essential concepts the expert needs for any query. These files are **always loaded** into the expert's context.

**Guidelines**:
- Keep total size under 4000 tokens
- Focus on concepts, not reference material
- Use bullet points over prose
- Include decision criteria, not just facts

**Suggested files**:
- `concepts.md` - Fundamental domain concepts
- `architecture.md` - System architecture overview
- `common-patterns.md` - Frequently used patterns

## Reference Knowledge (`reference/`)

Detailed documentation loaded **on demand** when relevant to a query. No token budget limit.

**Guidelines**:
- Organize by topic
- Include examples and code snippets
- Cross-reference with core concepts
- Update when domain tools change versions

## Organization Patterns (`org-patterns/`)

Your organization's specific conventions, standards, and preferences. Critical for consistent guidance.

**Suggested files**:
- `naming.md` - Naming conventions
- `environments.md` - Environment strategy (dev/staging/prod)
- `deployment.md` - Deployment standards
- `security.md` - Security requirements

**Guidelines**:
- Be specific (not "follow best practices")
- Include rationale for conventions
- Update when organizational standards change

## Decision Log (`decision-log/`)

Automatically populated when the expert makes significant decisions. Each entry records:

- The query that triggered the decision
- The decision made
- The rationale
- Confidence level

**File format**: `YYYY-MM-DD-HHMMSS-decision.md`

**Review periodically** to:
- Identify recurring questions
- Spot inconsistent guidance
- Update core knowledge with patterns

## Writing Effective Knowledge

### Do

- Use concrete examples
- Include code/config snippets
- State when guidance applies (and when it doesn't)
- Provide decision trees for common choices
- Reference authoritative sources

### Don't

- Include verbose prose
- Duplicate information across files
- Include outdated version-specific details
- Make assumptions about context

## Token Budget Management

Monitor token usage:

```bash
# Count approximate tokens in core knowledge
./scripts/test-expert.sh {{expert_name}} --check-tokens
```

If over budget:
1. Move detailed content to `reference/`
2. Summarize verbose sections
3. Convert prose to bullet points
4. Remove redundant information
