# Knowledge Base Organization

This directory contains the domain knowledge that powers the Requirements expert.

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

**Current files**:
- `question-patterns.md` - Common gaps by domain, prioritized questions
- `behavior-contract-format.md` - Output format specification

**Guidelines**:
- Keep total size under 4000 tokens
- Focus on decision criteria and patterns
- Use bullet points over prose

## Reference Knowledge (`reference/`)

Detailed documentation loaded **on demand** when relevant. No token budget limit.

**Suggested additions**:
- Domain-specific requirement patterns
- Industry compliance checklists
- Example contracts by domain

## Organization Patterns (`org-patterns/`)

Organization-specific conventions and terminology. Critical for consistent guidance.

**Suggested files**:
- `terminology.md` - Organization-specific terms and definitions
- `conventions.md` - Standard patterns and preferences
- `stakeholders.md` - Common roles and their concerns

## Decision Log (`decision-log/`)

Automatically populated when the expert makes significant decisions. Each entry records:

- The query that triggered the decision
- The decision made
- The rationale
- Confidence level

**File format**: `YYYY-MM-DD-HHMMSS-decision.md`

**Review periodically** to:
- Identify effective question sequences
- Spot patterns in unclear requirements
- Update core knowledge with learnings
